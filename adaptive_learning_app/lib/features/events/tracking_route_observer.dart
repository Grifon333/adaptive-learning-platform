import 'package:adaptive_learning_app/features/events/service/tracking_service.dart';
import 'package:flutter/material.dart';

class TrackingRouteObserver extends RouteObserver<PageRoute<dynamic>> {
  TrackingRouteObserver(this.trackingService);

  final TrackingService trackingService;

  void _logNavigation(String? routeName, String action) {
    if (routeName != null) {
      trackingService.log('NAVIGATION', metadata: {'route': routeName, 'action': action});
    }
  }

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didPush(route, previousRoute);
    _logNavigation(route.settings.name, 'PUSH');
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didPop(route, previousRoute);
    _logNavigation(previousRoute?.settings.name, 'POP');
  }

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    super.didReplace(newRoute: newRoute, oldRoute: oldRoute);
    _logNavigation(newRoute?.settings.name, 'REPLACE');
  }
}
