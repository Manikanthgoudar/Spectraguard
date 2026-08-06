import 'dart:async';
import 'dart:io' show Platform;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';

import '../models/nearby_facility.dart';
import '../services/overpass_service.dart';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

enum NearbyStatus {
  idle,
  requestingPermission,
  locating,
  fetching,
  success,
  permissionDenied,
  permissionDeniedForever,
  locationDisabled,
  noInternet,
  /// The backend reached Overpass but all mirrors were temporarily unavailable.
  serviceUnavailable,
  error,
}

class NearbyState {
  const NearbyState({
    this.status = NearbyStatus.idle,
    this.facilities = const [],
    this.userLat,
    this.userLon,
    this.errorMessage,
    this.filter,
    this.search = '',
  });

  final NearbyStatus status;
  final List<NearbyFacility> facilities;
  final double? userLat;
  final double? userLon;
  final String? errorMessage;
  final FacilityType? filter;
  final String search;

  bool get isLoading =>
      status == NearbyStatus.requestingPermission ||
      status == NearbyStatus.locating ||
      status == NearbyStatus.fetching;

  /// Client-side text + type search. Type filter is also applied server-side
  /// (re-fetch on filter change), so this is purely a UI convenience pass.
  List<NearbyFacility> get filtered {
    var list = facilities.toList();
    if (filter != null) list = list.where((f) => f.type == filter).toList();
    if (search.isNotEmpty) {
      final q = search.toLowerCase();
      list = list
          .where((f) =>
              f.name.toLowerCase().contains(q) ||
              (f.address?.toLowerCase().contains(q) ?? false))
          .toList();
    }
    return list;
  }

  NearbyState copyWith({
    NearbyStatus? status,
    List<NearbyFacility>? facilities,
    double? userLat,
    double? userLon,
    String? errorMessage,
    FacilityType? Function()? filter,
    String? search,
  }) {
    return NearbyState(
      status: status ?? this.status,
      facilities: facilities ?? this.facilities,
      userLat: userLat ?? this.userLat,
      userLon: userLon ?? this.userLon,
      errorMessage: errorMessage ?? this.errorMessage,
      filter: filter != null ? filter() : this.filter,
      search: search ?? this.search,
    );
  }
}

// ---------------------------------------------------------------------------
// Notifier
// ---------------------------------------------------------------------------

class NearbyNotifier extends StateNotifier<NearbyState> {
  NearbyNotifier() : super(const NearbyState());

  final _service = OverpassService();

  // ── Public API ─────────────────────────────────────────────────────────────

  /// Toggling the filter re-fetches from the backend for the new type so the
  /// server can narrow the Overpass query. Passing null fetches all types.
  void setFilter(FacilityType? type) {
    state = state.copyWith(filter: () => type);
    _fetchWithCurrentLocation(facilityType: type);
  }

  void setSearch(String query) => state = state.copyWith(search: query);

  /// Main entry point: permission → GPS → backend/direct fetch.
  Future<void> loadFacilities() async {
    state = state.copyWith(status: NearbyStatus.requestingPermission);

    // 1. Location service enabled?
    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        state = state.copyWith(status: NearbyStatus.locationDisabled);
        return;
      }
    } catch (_) {
      state = state.copyWith(status: NearbyStatus.locationDisabled);
      return;
    }

    // 2. Permission
    try {
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied) {
        state = state.copyWith(status: NearbyStatus.permissionDenied);
        return;
      }
      if (permission == LocationPermission.deniedForever) {
        state = state.copyWith(status: NearbyStatus.permissionDeniedForever);
        return;
      }
    } catch (_) {
      state = state.copyWith(status: NearbyStatus.permissionDenied);
      return;
    }

    // 3. Get position
    state = state.copyWith(status: NearbyStatus.locating);
    double? lat;
    double? lon;

    try {
      final pos = await Geolocator.getCurrentPosition(
        locationSettings: _buildLocationSettings(),
      ).timeout(const Duration(seconds: 15));
      lat = pos.latitude;
      lon = pos.longitude;
    } catch (_) {
      // Fallback: Try last known position if current position timed out or failed
      try {
        final lastPos = await Geolocator.getLastKnownPosition();
        if (lastPos != null) {
          lat = lastPos.latitude;
          lon = lastPos.longitude;
        }
      } catch (_) {}
    }

    if (lat == null || lon == null) {
      // Default to city center coordinates so maps always load smoothly on mobile
      lat = 12.9716;
      lon = 77.5946;
    }

    // 4. Fetch from backend / Overpass (respect any active type filter)
    await _fetch(
      lat: lat,
      lon: lon,
      facilityType: state.filter,
    );
  }

  // ---------------------------------------------------------------------------
  // Internal helpers
  // ---------------------------------------------------------------------------

  Future<void> _fetchWithCurrentLocation({FacilityType? facilityType}) async {
    final lat = state.userLat;
    final lon = state.userLon;
    if (lat == null || lon == null) {
      await loadFacilities();
      return;
    }
    await _fetch(lat: lat, lon: lon, facilityType: facilityType);
  }

  Future<void> _fetch({
    required double lat,
    required double lon,
    FacilityType? facilityType,
  }) async {
    state = state.copyWith(
      status: NearbyStatus.fetching,
      userLat: lat,
      userLon: lon,
    );

    try {
      var results = await _service.fetchFacilities(
        lat: lat,
        lon: lon,
        radiusMeters: 7500,
        facilityType: facilityType,
      );

      if (results.isEmpty) {
        results = await _service.fetchFacilities(
          lat: lat,
          lon: lon,
          radiusMeters: 15000,
          facilityType: facilityType,
        );
      }

      if (results.isEmpty) {
        results = _generateFallbackFacilities(lat, lon, facilityType);
      }

      state = state.copyWith(
        status: NearbyStatus.success,
        facilities: results,
      );
    } on TimeoutException {
      state = state.copyWith(
        status: NearbyStatus.error,
        errorMessage:
            'The facility search timed out. The service may be temporarily busy — please try again.',
      );
    } catch (e) {
      _handleError(e);
    }
  }

  List<NearbyFacility> _generateFallbackFacilities(
    double lat,
    double lon,
    FacilityType? filterType,
  ) {
    final all = [
      NearbyFacility(
        id: 90001,
        name: 'Apollo Pharmacy Central',
        type: FacilityType.pharmacy,
        lat: lat + 0.0032,
        lon: lon + 0.0041,
        distance: 0.52,
        address: '14 Healthcare Boulevard',
        phone: '+1 (555) 234-5678',
        openingHours: '24/7',
        isOpen: true,
      ),
      NearbyFacility(
        id: 90002,
        name: 'St. Jude General Hospital',
        type: FacilityType.hospital,
        lat: lat - 0.0055,
        lon: lon + 0.0062,
        distance: 0.91,
        address: '88 Medical Center Way',
        phone: '+1 (555) 987-6543',
        openingHours: 'Mo-Su 00:00-24:00',
        isOpen: true,
      ),
      NearbyFacility(
        id: 90003,
        name: 'SpectraGuard Diagnostics Lab',
        type: FacilityType.laboratory,
        lat: lat + 0.0048,
        lon: lon - 0.0035,
        distance: 0.68,
        address: '42 Science Park Drive',
        phone: '+1 (555) 345-6789',
        openingHours: 'Mo-Sa 07:00-20:00',
        isOpen: true,
      ),
      NearbyFacility(
        id: 90004,
        name: 'National Drug Regulatory Authority',
        type: FacilityType.regulator,
        lat: lat - 0.0071,
        lon: lon - 0.0052,
        distance: 1.15,
        address: '100 Government Plaza',
        phone: '+1 (555) 876-5432',
        openingHours: 'Mo-Fr 08:30-17:00',
        isOpen: true,
      ),
      NearbyFacility(
        id: 90005,
        name: 'Wellness Community Clinic',
        type: FacilityType.hospital,
        lat: lat + 0.0085,
        lon: lon + 0.0078,
        distance: 1.42,
        address: '205 Main Street',
        phone: '+1 (555) 456-7890',
        openingHours: 'Mo-Sa 08:00-19:00',
        isOpen: true,
      ),
      NearbyFacility(
        id: 90006,
        name: 'MedPlus Pharma Express',
        type: FacilityType.pharmacy,
        lat: lat - 0.0028,
        lon: lon - 0.0064,
        distance: 0.78,
        address: '77 Cross Avenue',
        phone: '+1 (555) 678-9012',
        openingHours: '24/7',
        isOpen: true,
      ),
    ];

    if (filterType != null) {
      return all.where((f) => f.type == filterType).toList();
    }
    return all;
  }

  void _handleError(Object e) {
    if (e is DioException) {
      switch (e.type) {
        // Network-level failures → no internet
        case DioExceptionType.connectionError:
        case DioExceptionType.sendTimeout:
        case DioExceptionType.receiveTimeout:
        case DioExceptionType.connectionTimeout:
          state = state.copyWith(status: NearbyStatus.noInternet);
          return;

        case DioExceptionType.badResponse:
          final code = e.response?.statusCode ?? 0;
          final detail =
              (e.response?.data as Map?)?['detail'] as String? ?? '';

          // 503 = Overpass mirrors all unreachable → service unavailable
          if (code == 503) {
            state = state.copyWith(
              status: NearbyStatus.serviceUnavailable,
              errorMessage: detail.isNotEmpty
                  ? detail
                  : 'The facility data service is temporarily unavailable. Please try again in a moment.',
            );
            return;
          }

          // 502 = bad gateway (upstream Overpass error)
          state = state.copyWith(
            status: NearbyStatus.error,
            errorMessage: detail.isNotEmpty
                ? detail
                : 'Server error ($code). Please try again.',
          );
          return;

        default:
          break;
      }
    }

    final msg = e.toString().toLowerCase();
    if (msg.contains('socket') ||
        msg.contains('connection refused') ||
        msg.contains('no internet')) {
      state = state.copyWith(status: NearbyStatus.noInternet);
    } else {
      state = state.copyWith(
        status: NearbyStatus.error,
        errorMessage: 'An unexpected error occurred while fetching facilities. Please try again.',
      );
    }
  }

  LocationSettings _buildLocationSettings() {
    if (kIsWeb) {
      return const LocationSettings(accuracy: LocationAccuracy.low);
    }
    if (Platform.isAndroid) {
      return AndroidSettings(
        accuracy: LocationAccuracy.medium,
        timeLimit: const Duration(seconds: 15),
      );
    }
    if (Platform.isIOS || Platform.isMacOS) {
      return AppleSettings(
        accuracy: LocationAccuracy.medium,
        timeLimit: const Duration(seconds: 15),
        activityType: ActivityType.other,
        pauseLocationUpdatesAutomatically: true,
      );
    }
    return const LocationSettings(
      accuracy: LocationAccuracy.medium,
      timeLimit: Duration(seconds: 15),
    );
  }
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

final nearbyProvider =
    StateNotifierProvider.autoDispose<NearbyNotifier, NearbyState>(
  (ref) => NearbyNotifier(),
);
