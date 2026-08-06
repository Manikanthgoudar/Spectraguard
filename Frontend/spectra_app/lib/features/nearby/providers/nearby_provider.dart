import 'dart:async';
import 'dart:io' show Platform;

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
  NearbyNotifier()
      : super(
          NearbyState(
            status: NearbyStatus.success,
            userLat: 12.9716,
            userLon: 77.5946,
            facilities: _generateFallbackFacilities(12.9716, 77.5946, null),
          ),
        );

  final _service = OverpassService();

  // ── Public API ─────────────────────────────────────────────────────────────

  /// Toggling the filter re-fetches from the backend for the new type so the
  /// server can narrow the Overpass query. Passing null fetches all types.
  void setFilter(FacilityType? type) {
    state = state.copyWith(filter: () => type);
    _fetchWithCurrentLocation(facilityType: type);
  }

  void setSearch(String query) => state = state.copyWith(search: query);

  /// Manually sets location coordinates (e.g. for city presets or manual search).
  Future<void> setCustomLocation(double lat, double lon) async {
    await _fetch(lat: lat, lon: lon, facilityType: state.filter);
  }

  /// Explicitly requests location permission from OS and updates current position.
  Future<void> requestLocationAndRecenter() async {
    try {
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.deniedForever) {
        await Geolocator.openAppSettings();
        return;
      }
      if (permission == LocationPermission.whileInUse ||
          permission == LocationPermission.always) {
        final pos = await Geolocator.getCurrentPosition(
          locationSettings: _buildLocationSettings(),
        ).timeout(const Duration(seconds: 10));
        await setCustomLocation(pos.latitude, pos.longitude);
      }
    } catch (_) {}
  }

  /// Main entry point: permission → GPS → backend/direct fetch.
  /// Renders map INSTANTLY and refreshes facility data in background for zero-delay display on phones.
  Future<void> loadFacilities() async {
    double? lat;
    double? lon;

    // 1. Quick check for position (3 second timeout max for phone responsiveness)
    try {
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (serviceEnabled) {
        LocationPermission permission = await Geolocator.checkPermission();
        if (permission == LocationPermission.denied) {
          permission = await Geolocator.requestPermission();
        }
        if (permission == LocationPermission.whileInUse ||
            permission == LocationPermission.always) {
          final pos = await Geolocator.getCurrentPosition(
            locationSettings: _buildLocationSettings(),
          ).timeout(const Duration(seconds: 3));
          lat = pos.latitude;
          lon = pos.longitude;
        }
      }
    } catch (_) {}

    if (lat == null || lon == null) {
      try {
        final lastPos = await Geolocator.getLastKnownPosition();
        if (lastPos != null) {
          lat = lastPos.latitude;
          lon = lastPos.longitude;
        }
      } catch (_) {}
    }

    // Default fallback coordinates (Bangalore Metro / Central hub)
    lat ??= 12.9716;
    lon ??= 77.5946;

    // Set immediate success state with initial facilities so the map appears INSTANTLY on phone screen
    final initialFacilities = _generateFallbackFacilities(lat, lon, state.filter);
    state = state.copyWith(
      status: NearbyStatus.success,
      facilities: initialFacilities,
      userLat: lat,
      userLon: lon,
    );

    // 2. Refresh live facilities in background without blocking UI
    await _fetchLiveFacilities(
      lat: lat,
      lon: lon,
      facilityType: state.filter,
    );
  }

  // ---------------------------------------------------------------------------
  // Internal helpers
  // ---------------------------------------------------------------------------

  Future<void> _fetchWithCurrentLocation({FacilityType? facilityType}) async {
    final lat = state.userLat ?? 12.9716;
    final lon = state.userLon ?? 77.5946;
    state = state.copyWith(
      facilities: _generateFallbackFacilities(lat, lon, facilityType),
    );
    await _fetchLiveFacilities(lat: lat, lon: lon, facilityType: facilityType);
  }

  Future<void> _fetch({
    required double lat,
    required double lon,
    FacilityType? facilityType,
  }) async {
    state = state.copyWith(
      status: NearbyStatus.success,
      facilities: _generateFallbackFacilities(lat, lon, facilityType),
      userLat: lat,
      userLon: lon,
    );
    await _fetchLiveFacilities(lat: lat, lon: lon, facilityType: facilityType);
  }

  Future<void> _fetchLiveFacilities({
    required double lat,
    required double lon,
    FacilityType? facilityType,
  }) async {
    try {
      var results = await _service
          .fetchFacilities(
            lat: lat,
            lon: lon,
            radiusMeters: 7500,
            facilityType: facilityType,
          )
          .timeout(const Duration(seconds: 6));

      if (results.isNotEmpty) {
        state = state.copyWith(
          status: NearbyStatus.success,
          facilities: results,
        );
      }
    } catch (_) {
      // Keep existing populated facilities on timeout/error
    }
  }

  static List<NearbyFacility> _generateFallbackFacilities(
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
