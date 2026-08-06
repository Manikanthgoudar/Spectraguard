import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';

import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';
import '../models/nearby_facility.dart';
import '../providers/nearby_provider.dart';
import '../services/route_service.dart';

enum NearbyViewMode { map, split, list }

// ─── Type helpers ─────────────────────────────────────────────────────────────

extension _TypeExt on FacilityType {
  String get label => switch (this) {
        FacilityType.pharmacy => 'Pharmacy',
        FacilityType.laboratory => 'Laboratory',
        FacilityType.hospital => 'Hospital',
        FacilityType.regulator => 'Regulator',
      };

  IconData get icon => switch (this) {
        FacilityType.pharmacy => Icons.local_pharmacy_outlined,
        FacilityType.laboratory => Icons.biotech_outlined,
        FacilityType.hospital => Icons.local_hospital_outlined,
        FacilityType.regulator => Icons.account_balance_outlined,
      };

  Color get color => switch (this) {
        FacilityType.pharmacy => AppColors.primary,
        FacilityType.laboratory => AppColors.secondary,
        FacilityType.hospital => const Color(0xFF5B8DEF),
        FacilityType.regulator => AppColors.warning,
      };
}

// ─── Screen ───────────────────────────────────────────────────────────────────

class NearbyScreen extends ConsumerStatefulWidget {
  const NearbyScreen({super.key});

  @override
  ConsumerState<NearbyScreen> createState() => _NearbyScreenState();
}

class _NearbyScreenState extends ConsumerState<NearbyScreen> {
  final _searchController = TextEditingController();
  final _mapController = MapController();
  NearbyViewMode _viewMode = NearbyViewMode.map; // Full map by default

  RouteResult? _activeRoute;
  bool _isRouting = false;

  @override
  void initState() {
    super.initState();
    // Kick off location + data fetch on first load
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(nearbyProvider.notifier).loadFacilities();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _fetchAndShowRoute(NearbyFacility f) async {
    final state = ref.read(nearbyProvider);
    final uLat = state.userLat;
    final uLon = state.userLon;
    if (uLat == null || uLon == null) return;

    setState(() {
      _isRouting = true;
    });

    final route = await RouteService.fetchRoute(
      startLat: uLat,
      startLon: uLon,
      endLat: f.lat,
      endLon: f.lon,
      destinationName: f.name,
    );

    setState(() {
      _activeRoute = route;
      _isRouting = false;
    });

    // Fit map bounds to encompass start and destination
    if (route.points.isNotEmpty) {
      final bounds = LatLngBounds.fromPoints(route.points);
      _mapController.fitCamera(
        CameraFit.bounds(
          bounds: bounds,
          padding: const EdgeInsets.all(60),
        ),
      );
    }
  }

  void _clearRoute() {
    setState(() {
      _activeRoute = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(nearbyProvider);
    final results = state.filtered;

    Widget body;
    if (state.isLoading) {
      body = _LoadingState(status: state.status);
    } else if (state.status == NearbyStatus.permissionDenied ||
        state.status == NearbyStatus.permissionDeniedForever) {
      body = _PermissionDeniedState(
        isPermanent: state.status == NearbyStatus.permissionDeniedForever,
        onRetry: () => ref.read(nearbyProvider.notifier).loadFacilities(),
      );
    } else if (state.status == NearbyStatus.locationDisabled) {
      body = _LocationDisabledState(
        onRetry: () => ref.read(nearbyProvider.notifier).loadFacilities(),
      );
    } else if (state.status == NearbyStatus.noInternet) {
      body = _NoInternetState(
        onRetry: () => ref.read(nearbyProvider.notifier).loadFacilities(),
      );
    } else if (state.status == NearbyStatus.serviceUnavailable) {
      body = _ServiceUnavailableState(
        message: state.errorMessage,
        onRetry: () => ref.read(nearbyProvider.notifier).loadFacilities(),
      );
    } else if (state.status == NearbyStatus.error) {
      body = _ErrorState(
        message: state.errorMessage,
        onRetry: () => ref.read(nearbyProvider.notifier).loadFacilities(),
      );
    } else if (state.status == NearbyStatus.success) {
      final mapWidget = _NearbyMapView(
        facilities: results,
        userLat: state.userLat,
        userLon: state.userLon,
        mapController: _mapController,
        activeRoute: _activeRoute,
        onGetDirections: _fetchAndShowRoute,
        onClearRoute: _clearRoute,
      );

      final listWidget = ContentContainer(
        maxWidth: 800,
        child: ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: results.length,
          itemBuilder: (_, i) => _FacilityCard(
            facility: results[i],
            isLast: i == results.length - 1,
            onTap: () {
              final f = results[i];
              if (_viewMode == NearbyViewMode.list) {
                setState(() => _viewMode = NearbyViewMode.map);
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  try {
                    _mapController.move(LatLng(f.lat, f.lon), 15.5);
                  } catch (_) {}
                });
              } else {
                try {
                  _mapController.move(LatLng(f.lat, f.lon), 15.5);
                } catch (_) {}
              }
            },
            onGetDirections: () {
              final f = results[i];
              if (_viewMode == NearbyViewMode.list) {
                setState(() => _viewMode = NearbyViewMode.map);
              }
              _fetchAndShowRoute(f);
            },
          ),
        ),
      );

      if (_viewMode == NearbyViewMode.map) {
        body = Stack(
          children: [
            Positioned.fill(child: mapWidget),
            if (_isRouting)
              Positioned.fill(
                child: Container(
                  color: Colors.black26,
                  child: const Center(
                    child: CircularProgressIndicator(),
                  ),
                ),
              ),
          ],
        );
      } else if (_viewMode == NearbyViewMode.list) {
        body = listWidget;
      } else {
        // Split view
        body = LayoutBuilder(
          builder: (context, constraints) {
            final isWide = constraints.maxWidth >= 768;
            if (isWide) {
              return Row(
                children: [
                  Expanded(flex: 6, child: mapWidget),
                  Expanded(flex: 4, child: listWidget),
                ],
              );
            }
            return Column(
              children: [
                Expanded(flex: 5, child: mapWidget),
                Expanded(flex: 5, child: listWidget),
              ],
            );
          },
        );
      }
    } else {
      body = const SizedBox.shrink();
    }

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          _NearbyHeader(
            search: state.search,
            controller: _searchController,
            onSearch: (v) => ref.read(nearbyProvider.notifier).setSearch(v),
            onClear: () {
              _searchController.clear();
              ref.read(nearbyProvider.notifier).setSearch('');
            },
            facilityCount: state.status == NearbyStatus.success
                ? state.facilities.length
                : null,
          ),
          _FilterBar(
            selected: state.filter,
            onSelect: (t) {
              final notifier = ref.read(nearbyProvider.notifier);
              notifier.setFilter(state.filter == t ? null : t);
            },
            viewMode: _viewMode,
            onViewModeChanged: (mode) => setState(() => _viewMode = mode),
          ),
          Expanded(child: body),
        ],
      ),
    );
  }
}

// ─── Header ───────────────────────────────────────────────────────────────────

class _NearbyHeader extends StatelessWidget {
  const _NearbyHeader({
    required this.search,
    required this.controller,
    required this.onSearch,
    required this.onClear,
    this.facilityCount,
  });

  final String search;
  final TextEditingController controller;
  final ValueChanged<String> onSearch;
  final VoidCallback onClear;
  final int? facilityCount;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final subtitle = facilityCount != null
        ? '$facilityCount ${facilityCount == 1 ? "facility" : "facilities"} found nearby'
        : 'Pharmacies, labs & regulatory offices';

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: cs.surface,
        border: Border(bottom: BorderSide(color: cs.outline)),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.map_outlined,
                      color: AppColors.primary,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Nearby Facilities',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w700,
                            color: cs.onSurface,
                          ),
                        ),
                        Text(
                          subtitle,
                          style: TextStyle(
                              fontSize: 12, color: cs.onSurfaceVariant),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              TextField(
                controller: controller,
                onChanged: onSearch,
                style: TextStyle(fontSize: 14, color: cs.onSurface),
                decoration: InputDecoration(
                  hintText: 'Search by name or address...',
                  prefixIcon: const Icon(Icons.search_rounded, size: 20),
                  suffixIcon: search.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.close_rounded, size: 18),
                          onPressed: onClear,
                        )
                      : null,
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 12),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: cs.outline),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: BorderSide(color: cs.outline),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide:
                        const BorderSide(color: AppColors.primary, width: 1.5),
                  ),
                  filled: true,
                  fillColor: Theme.of(context).scaffoldBackgroundColor,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Filter bar ───────────────────────────────────────────────────────────────

class _FilterBar extends StatelessWidget {
  const _FilterBar({
    required this.selected,
    required this.onSelect,
    required this.viewMode,
    required this.onViewModeChanged,
  });

  final FacilityType? selected;
  final ValueChanged<FacilityType> onSelect;
  final NearbyViewMode viewMode;
  final ValueChanged<NearbyViewMode> onViewModeChanged;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    const types = FacilityType.values;

    return Container(
      height: 52,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: cs.surface,
        border: Border(bottom: BorderSide(color: cs.outline)),
      ),
      child: Row(
        children: [
          Expanded(
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: types.length,
              itemBuilder: (_, i) {
                final t = types[i];
                final isSelected = selected == t;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: GestureDetector(
                    onTap: () => onSelect(t),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 180),
                      padding:
                          const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? t.color.withOpacity(0.12)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: isSelected
                              ? t.color.withOpacity(0.4)
                              : cs.outline,
                          width: isSelected ? 1.5 : 1,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(t.icon,
                              size: 14,
                              color: isSelected ? t.color : cs.onSurfaceVariant),
                          const SizedBox(width: 5),
                          Text(
                            t.label,
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight:
                                  isSelected ? FontWeight.w600 : FontWeight.w400,
                              color: isSelected ? t.color : cs.onSurfaceVariant,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Facility card ────────────────────────────────────────────────────────────

class _FacilityCard extends StatelessWidget {
  const _FacilityCard({
    required this.facility,
    this.isLast = false,
    this.onTap,
    this.onGetDirections,
  });

  final NearbyFacility facility;
  final bool isLast;
  final VoidCallback? onTap;
  final VoidCallback? onGetDirections;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final f = facility;

    return Container(
      margin: EdgeInsets.only(bottom: isLast ? 0 : 12),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: cs.outline),
        boxShadow: [
          BoxShadow(
            color: cs.shadow.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: f.type.color.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(f.type.icon, color: f.type.color, size: 22),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              child: Text(
                                f.name,
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w600,
                                  color: cs.onSurface,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            _TypeBadge(type: f.type),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Icon(Icons.near_me_outlined,
                                size: 13, color: cs.onSurfaceVariant),
                            const SizedBox(width: 4),
                            Text(
                              '${f.distance.toStringAsFixed(1)} km away',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                                color: cs.onSurfaceVariant,
                              ),
                            ),
                            if (f.isOpen != null) ...[
                              const SizedBox(width: 8),
                              _OpenBadge(isOpen: f.isOpen!),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              if (f.address != null) ...[
                const SizedBox(height: 10),
                Row(
                  children: [
                    Icon(Icons.location_on_outlined,
                        size: 14, color: cs.onSurfaceVariant),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        f.address!,
                        style:
                            TextStyle(fontSize: 12, color: cs.onSurfaceVariant),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],

              if (f.phone != null) ...[
                const SizedBox(height: 6),
                Row(
                  children: [
                    Icon(Icons.phone_outlined,
                        size: 14, color: cs.onSurfaceVariant),
                    const SizedBox(width: 6),
                    Text(
                      f.phone!,
                      style:
                          TextStyle(fontSize: 12, color: cs.onSurfaceVariant),
                    ),
                  ],
                ),
              ],

              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  ElevatedButton.icon(
                    onPressed: onGetDirections,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 8),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10)),
                    ),
                    icon: const Icon(Icons.navigation_outlined, size: 16),
                    label: const Text(
                      'Directions',
                      style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TypeBadge extends StatelessWidget {
  const _TypeBadge({required this.type});
  final FacilityType type;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: type.color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        type.label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: type.color,
        ),
      ),
    );
  }
}

class _OpenBadge extends StatelessWidget {
  const _OpenBadge({required this.isOpen});
  final bool isOpen;

  @override
  Widget build(BuildContext context) {
    final color = isOpen ? AppColors.success : AppColors.error;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 5,
            height: 5,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 4),
          Text(
            isOpen ? 'Open' : 'Closed',
            style: TextStyle(
                fontSize: 10, fontWeight: FontWeight.w600, color: color),
          ),
        ],
      ),
    );
  }
}

// ─── Map View Widget ─────────────────────────────────────────────────────────

class _NearbyMapView extends StatelessWidget {
  const _NearbyMapView({
    required this.facilities,
    required this.userLat,
    required this.userLon,
    required this.mapController,
    this.activeRoute,
    this.onGetDirections,
    this.onClearRoute,
  });

  final List<NearbyFacility> facilities;
  final double? userLat;
  final double? userLon;
  final MapController mapController;
  final RouteResult? activeRoute;
  final ValueChanged<NearbyFacility>? onGetDirections;
  final VoidCallback? onClearRoute;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final centerLat = userLat ?? 20.5937;
    final centerLon = userLon ?? 78.9629;
    final center = LatLng(centerLat, centerLon);

    final markers = <Marker>[];

    // User Location Pin
    if (userLat != null && userLon != null) {
      markers.add(
        Marker(
          point: center,
          width: 48,
          height: 48,
          child: GestureDetector(
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Your current location'),
                  duration: Duration(seconds: 2),
                ),
              );
            },
            child: Stack(
              alignment: Alignment.center,
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.3),
                    shape: BoxShape.circle,
                  ),
                ),
                Container(
                  width: 20,
                  height: 20,
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2),
                    boxShadow: const [
                      BoxShadow(
                        color: Colors.black26,
                        blurRadius: 4,
                        offset: Offset(0, 2),
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.my_location,
                    size: 10,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    // Facility Markers
    for (final f in facilities) {
      final pos = LatLng(f.lat, f.lon);
      final color = f.type.color;
      final icon = f.type.icon;

      markers.add(
        Marker(
          point: pos,
          width: 42,
          height: 42,
          child: GestureDetector(
            onTap: () => _showFacilitySheet(context, f),
            child: Container(
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 2),
                boxShadow: const [
                  BoxShadow(
                    color: Colors.black38,
                    blurRadius: 5,
                    offset: Offset(0, 2),
                  ),
                ],
              ),
              child: Icon(
                icon,
                size: 20,
                color: Colors.white,
              ),
            ),
          ),
        ),
      );
    }

    return Stack(
      children: [
        FlutterMap(
          mapController: mapController,
          options: MapOptions(
            initialCenter: center,
            initialZoom: 13.5,
          ),
          children: [
            TileLayer(
              urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              userAgentPackageName: 'com.spectra.spectra_app',
            ),
            if (activeRoute != null && activeRoute!.points.isNotEmpty)
              PolylineLayer(
                polylines: [
                  Polyline(
                    points: activeRoute!.points,
                    strokeWidth: 5.0,
                    color: AppColors.primary,
                  ),
                ],
              ),
            MarkerLayer(markers: markers),
          ],
        ),

        // Floating Route Navigation Info Card
        if (activeRoute != null)
          Positioned(
            left: 16,
            right: 16,
            bottom: 24,
            child: Card(
              elevation: 8,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              color: cs.surface,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withOpacity(0.12),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.navigation, color: AppColors.primary, size: 20),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                activeRoute!.destinationName,
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: cs.onSurface,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '${activeRoute!.distanceKm} km • ~${activeRoute!.driveTimeMinutes} mins drive',
                                style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.primary,
                                ),
                              ),
                            ],
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close_rounded),
                          tooltip: 'Clear Directions',
                          onPressed: onClearRoute,
                        ),
                      ],
                    ),
                    const Divider(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _RouteStat(
                          icon: Icons.directions_car_outlined,
                          label: 'Driving',
                          value: '${activeRoute!.driveTimeMinutes} mins',
                        ),
                        _RouteStat(
                          icon: Icons.directions_walk_outlined,
                          label: 'Walking',
                          value: '${activeRoute!.walkTimeMinutes} mins',
                        ),
                        _RouteStat(
                          icon: Icons.straighten_outlined,
                          label: 'Distance',
                          value: '${activeRoute!.distanceKm} km',
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),

        // Map Control Buttons (Recenter, Zoom)
        Positioned(
          right: 16,
          bottom: activeRoute != null ? 180 : 24,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              FloatingActionButton.small(
                heroTag: 'recenter_btn',
                backgroundColor: cs.surface,
                foregroundColor: cs.onSurface,
                onPressed: () {
                  mapController.move(center, 14.0);
                },
                child: const Icon(Icons.my_location_rounded),
              ),
              const SizedBox(height: 6),
              FloatingActionButton.small(
                heroTag: 'zoom_in_btn',
                backgroundColor: cs.surface,
                foregroundColor: cs.onSurface,
                onPressed: () {
                  final zoom = mapController.camera.zoom;
                  mapController.move(mapController.camera.center, zoom + 1.0);
                },
                child: const Icon(Icons.add),
              ),
              const SizedBox(height: 6),
              FloatingActionButton.small(
                heroTag: 'zoom_out_btn',
                backgroundColor: cs.surface,
                foregroundColor: cs.onSurface,
                onPressed: () {
                  final zoom = mapController.camera.zoom;
                  mapController.move(mapController.camera.center, zoom - 1.0);
                },
                child: const Icon(Icons.remove),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _showFacilitySheet(BuildContext context, NearbyFacility f) {
    final cs = Theme.of(context).colorScheme;
    showModalBottomSheet(
      context: context,
      backgroundColor: cs.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: f.type.color.withOpacity(0.15),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(f.type.icon, color: f.type.color, size: 24),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        f.name,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: cs.onSurface,
                        ),
                      ),
                      Text(
                        '${f.type.label} • ${f.distance.toStringAsFixed(1)} km away',
                        style: TextStyle(
                          fontSize: 13,
                          color: cs.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (f.address != null) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(Icons.location_on_outlined, size: 16, color: cs.onSurfaceVariant),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      f.address!,
                      style: TextStyle(fontSize: 14, color: cs.onSurface),
                    ),
                  ),
                ],
              ),
            ],
            if (f.phone != null) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.phone_outlined, size: 16, color: cs.onSurfaceVariant),
                  const SizedBox(width: 6),
                  Text(
                    f.phone!,
                    style: TextStyle(fontSize: 14, color: cs.onSurface),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                icon: const Icon(Icons.navigation_outlined, color: Colors.white),
                label: const Text(
                  'Get Directions (In-App Route)',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                onPressed: () {
                  Navigator.pop(ctx);
                  if (onGetDirections != null) {
                    onGetDirections!(f);
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RouteStat extends StatelessWidget {
  const _RouteStat({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Column(
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: AppColors.primary),
            const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(fontSize: 11, color: cs.onSurfaceVariant),
            ),
          ],
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: cs.onSurface),
        ),
      ],
    );
  }
}

// ─── Status Widgets ───────────────────────────────────────────────────────────

class _LoadingState extends StatelessWidget {
  const _LoadingState({required this.status});
  final NearbyStatus status;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final text = switch (status) {
      NearbyStatus.requestingPermission => 'Requesting location permission…',
      NearbyStatus.locating => 'Getting your location…',
      NearbyStatus.fetching => 'Fetching nearby facilities…',
      _ => 'Loading…',
    };

    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(color: AppColors.primary),
          const SizedBox(height: 16),
          Text(text, style: TextStyle(fontSize: 14, color: cs.onSurfaceVariant)),
        ],
      ),
    );
  }
}

class _PermissionDeniedState extends StatelessWidget {
  const _PermissionDeniedState({
    required this.isPermanent,
    required this.onRetry,
  });

  final bool isPermanent;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _InfoState(
      icon: Icons.location_off_outlined,
      iconColor: AppColors.warning,
      title: 'Location Permission Denied',
      subtitle: isPermanent
          ? 'Location permission was permanently denied. Please enable it in your device settings to find nearby facilities.'
          : 'Location permission is required to find facilities near you.',
      buttonLabel: 'Try Again',
      onButton: onRetry,
    );
  }
}

class _LocationDisabledState extends StatelessWidget {
  const _LocationDisabledState({required this.onRetry});
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _InfoState(
      icon: Icons.location_disabled_outlined,
      iconColor: AppColors.warning,
      title: 'Location Services Disabled',
      subtitle:
          'Please enable GPS / Location Services on your device to find nearby facilities.',
      buttonLabel: 'Try Again',
      onButton: onRetry,
    );
  }
}

class _NoInternetState extends StatelessWidget {
  const _NoInternetState({required this.onRetry});
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _InfoState(
      icon: Icons.wifi_off_rounded,
      iconColor: AppColors.textSecondary,
      title: 'No Internet Connection',
      subtitle:
          'A network connection is needed to fetch nearby facility data. Please check your connection and try again.',
      buttonLabel: 'Retry',
      onButton: onRetry,
    );
  }
}

class _ServiceUnavailableState extends StatelessWidget {
  const _ServiceUnavailableState({this.message, required this.onRetry});
  final String? message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _InfoState(
      icon: Icons.cloud_off_outlined,
      iconColor: AppColors.warning,
      title: 'Facility Data Unavailable',
      subtitle: message ??
          'The facility data service is temporarily unavailable. Please try again in a moment.',
      buttonLabel: 'Try Again',
      onButton: onRetry,
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({this.message, required this.onRetry});
  final String? message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return _InfoState(
      icon: Icons.error_outline_rounded,
      iconColor: AppColors.error,
      title: 'Something Went Wrong',
      subtitle: message ?? 'Could not fetch nearby facilities. Please try again.',
      buttonLabel: 'Try Again',
      onButton: onRetry,
    );
  }
}

class _InfoState extends StatelessWidget {
  const _InfoState({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    required this.buttonLabel,
    required this.onButton,
  });

  final IconData icon;
  final Color iconColor;
  final String title;
  final String subtitle;
  final String buttonLabel;
  final VoidCallback onButton;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: iconColor.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, size: 36, color: iconColor),
            ),
            const SizedBox(height: 16),
            Text(
              title,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: cs.onSurface,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              style: TextStyle(fontSize: 13, color: cs.onSurfaceVariant),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            GestureDetector(
              onTap: onButton,
              child: Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 24, vertical: 12),
                decoration: BoxDecoration(
                  color: AppColors.primary,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  buttonLabel,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
