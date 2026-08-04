import 'dart:convert';
import 'dart:math' as math;
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';

class RouteResult {
  const RouteResult({
    required this.points,
    required this.distanceKm,
    required this.driveTimeMinutes,
    required this.walkTimeMinutes,
    required this.destinationName,
  });

  final List<LatLng> points;
  final double distanceKm;
  final int driveTimeMinutes;
  final int walkTimeMinutes;
  final String destinationName;
}

class RouteService {
  /// Fetches real road routing geometry, distance (in km), and travel time
  /// (driving minutes & walking minutes) using OSRM.
  static Future<RouteResult> fetchRoute({
    required double startLat,
    required double startLon,
    required double endLat,
    required double endLon,
    required String destinationName,
  }) async {
    final url = Uri.parse(
      'https://router.project-osrm.org/route/v1/driving/$startLon,$startLat;$endLon,$endLat?overview=full&geometries=geojson',
    );

    try {
      final response = await http.get(url).timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final routes = data['routes'] as List<dynamic>? ?? [];
        if (routes.isNotEmpty) {
          final first = routes.first as Map<String, dynamic>;
          final distMeters = (first['distance'] as num?)?.toDouble() ?? 0.0;
          final durationSecs = (first['duration'] as num?)?.toDouble() ?? 0.0;
          final geometry = first['geometry'] as Map<String, dynamic>? ?? {};
          final rawCoords = geometry['coordinates'] as List<dynamic>? ?? [];

          final points = rawCoords.map((c) {
            final pair = c as List<dynamic>;
            final lon = (pair[0] as num).toDouble();
            final lat = (pair[1] as num).toDouble();
            return LatLng(lat, lon);
          }).toList();

          final distanceKm = distMeters / 1000.0;
          final driveMins = math.max(1, (durationSecs / 60).round());
          final walkMins = math.max(1, (distMeters / 80).round());

          return RouteResult(
            points: points,
            distanceKm: double.parse(distanceKm.toStringAsFixed(1)),
            driveTimeMinutes: driveMins,
            walkTimeMinutes: walkMins,
            destinationName: destinationName,
          );
        }
      }
    } catch (_) {}

    // Fallback: straight-line path + Haversine calculation if OSRM is unreachable
    final start = LatLng(startLat, startLon);
    final end = LatLng(endLat, endLon);
    final distKm = _haversineKm(startLat, startLon, endLat, endLon);
    final driveMins = math.max(1, (distKm / 35.0 * 60).round());
    final walkMins = math.max(1, (distKm / 4.8 * 60).round());

    return RouteResult(
      points: [start, end],
      distanceKm: double.parse(distKm.toStringAsFixed(1)),
      driveTimeMinutes: driveMins,
      walkTimeMinutes: walkMins,
      destinationName: destinationName,
    );
  }

  static double _haversineKm(double lat1, double lon1, double lat2, double lon2) {
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
}
