import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'package:dio/dio.dart';

import 'package:spectra_app/core/api/api_client.dart';
import '../models/nearby_facility.dart';

/// Fetches nearby facilities via the SpectraGuard backend, which proxies
/// OpenStreetMap / Overpass with mirror-based retry logic.
/// If the backend service is unreachable or errors out, falls back to querying
/// public Overpass API mirrors directly.
class OverpassService {
  OverpassService() : _dio = createDio();

  final Dio _dio;

  static const int defaultRadiusMeters = 5000; // 5 km

  /// Fetches facilities near [lat], [lon] within [radiusMeters].
  /// Optionally filters server-side to a single [facilityType].
  Future<List<NearbyFacility>> fetchFacilities({
    required double lat,
    required double lon,
    int radiusMeters = defaultRadiusMeters,
    FacilityType? facilityType,
  }) async {
    final params = <String, dynamic>{
      'lat': lat,
      'lon': lon,
      'radius': radiusMeters,
      if (facilityType != null) 'type': _typeParam(facilityType),
    };

    // 1. Try backend first
    try {
      final response = await _dio
          .get<Map<String, dynamic>>(
            '/nearby',
            queryParameters: params,
            options: Options(receiveTimeout: const Duration(seconds: 15)),
          )
          .timeout(const Duration(seconds: 15));

      final data = response.data;
      if (data != null && data['facilities'] != null) {
        final elements = data['facilities'] as List<dynamic>? ?? [];
        final parsed = elements
            .map((e) => _parseFacility(e as Map<String, dynamic>))
            .whereType<NearbyFacility>()
            .toList();
        if (parsed.isNotEmpty) return parsed;
      }
    } catch (_) {
      // Backend failed or unreachable — proceed to direct Overpass fallback
    }

    // 2. Direct Overpass API fallback
    return await _fetchDirectFromOverpass(
      lat: lat,
      lon: lon,
      radiusMeters: radiusMeters,
      facilityType: facilityType,
    );
  }

  // ---------------------------------------------------------------------------
  // Direct Overpass Fallback
  // ---------------------------------------------------------------------------

  Future<List<NearbyFacility>> _fetchDirectFromOverpass({
    required double lat,
    required double lon,
    required int radiusMeters,
    FacilityType? facilityType,
  }) async {
    final query = _buildOverpassQuery(lat, lon, radiusMeters, facilityType);
    final encodedQuery = Uri.encodeComponent(query);

    final mirrors = [
      'https://overpass-api.de/api/interpreter?data=$encodedQuery',
      'https://overpass.kumi.systems/api/interpreter?data=$encodedQuery',
    ];

    Object? lastError;
    final directDio = Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 25),
    ));

    for (final mirror in mirrors) {
      try {
        final response = await directDio.get<Map<String, dynamic>>(
          mirror,
        );
        final data = response.data;
        if (data != null && data['elements'] != null) {
          final rawElements = data['elements'] as List<dynamic>;
          final parsed = _parseOverpassElements(rawElements, lat, lon);
          parsed.sort((a, b) => a.distance.compareTo(b.distance));
          if (parsed.isNotEmpty) return parsed;
        }
      } catch (e) {
        lastError = e;
      }
    }

    // Fallback: try raw HTTP GET
    final httpClient = Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 15),
    ));
    for (final mirror in mirrors) {
      try {
        final response = await httpClient.get<String>(mirror);
        if (response.data != null) {
          final json = jsonDecode(response.data!) as Map<String, dynamic>;
          final rawElements = json['elements'] as List<dynamic>? ?? [];
          final parsed = _parseOverpassElements(rawElements, lat, lon);
          parsed.sort((a, b) => a.distance.compareTo(b.distance));
          if (parsed.isNotEmpty) return parsed;
        }
      } catch (e) {
        lastError = e;
      }
    }

    throw lastError ?? Exception('All Overpass mirrors unreachable');
  }

  String _buildOverpassQuery(
    double lat,
    double lon,
    int radius,
    FacilityType? type,
  ) {
    final t = type != null ? _typeParam(type) : '';

    final pharmacyBlock = (t == '' || t == 'pharmacy')
        ? 'node["amenity"="pharmacy"](around:$radius,$lat,$lon);\nway["amenity"="pharmacy"](around:$radius,$lat,$lon);\nnode["healthcare"="pharmacy"](around:$radius,$lat,$lon);\nway["healthcare"="pharmacy"](around:$radius,$lat,$lon);'
        : '';
    final hospitalBlock = (t == '' || t == 'hospital')
        ? 'node["amenity"="hospital"](around:$radius,$lat,$lon);\nway["amenity"="hospital"](around:$radius,$lat,$lon);\nnode["amenity"="clinic"](around:$radius,$lat,$lon);\nway["amenity"="clinic"](around:$radius,$lat,$lon);\nnode["healthcare"="hospital"](around:$radius,$lat,$lon);\nway["healthcare"="hospital"](around:$radius,$lat,$lon);\nnode["healthcare"="clinic"](around:$radius,$lat,$lon);\nway["healthcare"="clinic"](around:$radius,$lat,$lon);'
        : '';
    final labBlock = (t == '' || t == 'laboratory')
        ? 'node["amenity"="laboratory"](around:$radius,$lat,$lon);\nway["amenity"="laboratory"](around:$radius,$lat,$lon);\nnode["healthcare"="laboratory"](around:$radius,$lat,$lon);\nway["healthcare"="laboratory"](around:$radius,$lat,$lon);\nnode["office"="pharmaceutical"](around:$radius,$lat,$lon);\nway["office"="pharmaceutical"](around:$radius,$lat,$lon);'
        : '';
    final regulatorBlock = (t == '' || t == 'regulator')
        ? 'node["office"="government"](around:$radius,$lat,$lon);\nway["office"="government"](around:$radius,$lat,$lon);\nnode["amenity"="public_building"](around:$radius,$lat,$lon);\nway["amenity"="public_building"](around:$radius,$lat,$lon);'
        : '';

    final unionBody = [pharmacyBlock, hospitalBlock, labBlock, regulatorBlock]
        .where((b) => b.isNotEmpty)
        .join('\n');

    return '[out:json][timeout:25];\n(\n$unionBody\n);\nout body center;';
  }

  List<NearbyFacility> _parseOverpassElements(
    List<dynamic> elements,
    double userLat,
    double userLon,
  ) {
    final results = <NearbyFacility>[];
    for (final el in elements) {
      if (el is! Map<String, dynamic>) continue;
      final facility = _parseRawOverpassElement(el, userLat, userLon);
      if (facility != null) {
        results.add(facility);
      }
    }
    return results;
  }

  NearbyFacility? _parseRawOverpassElement(
    Map<String, dynamic> el,
    double userLat,
    double userLon,
  ) {
    try {
      final tags = (el['tags'] as Map<String, dynamic>?) ?? {};
      final name = (tags['name'] as String? ?? '').trim();
      if (name.isEmpty) return null;

      double? eLat;
      double? eLon;

      if (el['type'] == 'node') {
        eLat = (el['lat'] as num?)?.toDouble();
        eLon = (el['lon'] as num?)?.toDouble();
      } else {
        final center = el['center'] as Map<String, dynamic>?;
        eLat = (center?['lat'] as num?)?.toDouble();
        eLon = (center?['lon'] as num?)?.toDouble();
      }

      if (eLat == null || eLon == null) return null;

      final type = _detectType(tags);
      if (type == null) return null;

      final distance = _haversineKm(userLat, userLon, eLat, eLon);
      final address = _buildAddress(tags);
      final phone = _extractPhone(tags);
      final openingHours = (tags['opening_hours'] as String? ?? '').trim();
      final website = tags['website'] as String? ?? tags['contact:website'] as String?;

      return NearbyFacility(
        id: (el['id'] as num).toInt(),
        name: name,
        type: type,
        lat: eLat,
        lon: eLon,
        distance: double.parse(distance.toStringAsFixed(3)),
        address: address,
        phone: phone,
        openingHours: openingHours.isEmpty ? null : openingHours,
        isOpen: _parseOpenStatus(tags),
        website: website,
      );
    } catch (_) {
      return null;
    }
  }

  FacilityType? _detectType(Map<String, dynamic> tags) {
    final amenity = tags['amenity'] as String? ?? '';
    final healthcare = tags['healthcare'] as String? ?? '';
    final office = tags['office'] as String? ?? '';
    final name = (tags['name'] as String? ?? '').toLowerCase();

    if (amenity == 'pharmacy') return FacilityType.pharmacy;
    if (amenity == 'hospital' || amenity == 'clinic') return FacilityType.hospital;
    if (amenity == 'laboratory' || healthcare == 'laboratory' || office == 'pharmaceutical') {
      return FacilityType.laboratory;
    }
    if (office == 'government') {
      const keywords = ['drug', 'pharma', 'medicine', 'health', 'regulation', 'regulatory', 'authority', 'control'];
      if (keywords.any((k) => name.contains(k))) return FacilityType.regulator;
    }
    return null;
  }

  double _haversineKm(double lat1, double lon1, double lat2, double lon2) {
    const r = 6371.0;
    final dLat = (lat2 - lat1) * math.pi / 180.0;
    final dLon = (lon2 - lon1) * math.pi / 180.0;
    final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
        math.cos(lat1 * math.pi / 180.0) *
            math.cos(lat2 * math.pi / 180.0) *
            math.sin(dLon / 2) *
            math.sin(dLon / 2);
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
  }

  String? _buildAddress(Map<String, dynamic> tags) {
    final house = tags['addr:housenumber'] as String? ?? '';
    final street = tags['addr:street'] as String? ?? '';
    final suburb = tags['addr:suburb'] as String? ?? '';
    final city = tags['addr:city'] as String? ?? '';

    final parts = <String>[];
    if (street.isNotEmpty && house.isNotEmpty) {
      parts.add('$house $street');
    } else if (street.isNotEmpty) {
      parts.add(street);
    }
    if (suburb.isNotEmpty) parts.add(suburb);
    if (city.isNotEmpty) parts.add(city);

    return parts.isEmpty ? null : parts.join(', ');
  }

  String? _extractPhone(Map<String, dynamic> tags) {
    for (final key in const ['contact:phone', 'phone', 'contact:mobile', 'mobile']) {
      final val = (tags[key] as String? ?? '').trim();
      if (val.isNotEmpty) return val;
    }
    return null;
  }

  bool? _parseOpenStatus(Map<String, dynamic> tags) {
    final raw = (tags['opening_hours'] as String? ?? '').toLowerCase().trim();
    if (raw.isEmpty) return null;
    if (raw == '24/7' || raw.contains('mo-su')) return true;
    return null;
  }

  // ---------------------------------------------------------------------------

  String _typeParam(FacilityType type) => switch (type) {
        FacilityType.pharmacy => 'pharmacy',
        FacilityType.laboratory => 'laboratory',
        FacilityType.hospital => 'hospital',
        FacilityType.regulator => 'regulator',
      };

  NearbyFacility? _parseFacility(Map<String, dynamic> e) {
    try {
      final typeStr = (e['type'] as String? ?? '').toLowerCase();
      final type = _parseType(typeStr);
      if (type == null) return null;

      return NearbyFacility(
        id: (e['id'] as num).toInt(),
        name: (e['name'] as String? ?? '').trim(),
        type: type,
        lat: (e['lat'] as num).toDouble(),
        lon: (e['lon'] as num).toDouble(),
        distance: (e['distance'] as num).toDouble(),
        address: e['address'] as String?,
        phone: e['phone'] as String?,
        openingHours: e['opening_hours'] as String?,
        isOpen: e['is_open'] as bool?,
        website: e['website'] as String?,
      );
    } catch (_) {
      return null;
    }
  }

  FacilityType? _parseType(String s) => switch (s) {
        'pharmacy' => FacilityType.pharmacy,
        'laboratory' => FacilityType.laboratory,
        'hospital' => FacilityType.hospital,
        'regulator' => FacilityType.regulator,
        _ => null,
      };
}

