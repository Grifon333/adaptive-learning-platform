import 'package:geolocator/geolocator.dart';
import 'package:i_app_services/i_app_services.dart';

/// {@template app_location_service}
/// Basic implementation of a service for working with geolocation.
/// {@endtemplate}
class AppLocationService implements ILocationService {
  const AppLocationService();

  static const name = 'BaseAppLocationService';

  @override
  Future<Position> getCurrentPosition() async {
    bool serviceEnabled;
    LocationPermission permission;

    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) return Future.error('Location services are disabled.');

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return Future.error('Location permissions are denied');
      }
    }
    if (permission == LocationPermission.deniedForever) {
      return Future.error(
        'Location permissions are permanently denied, we cannot request permissions.',
      );
    }
    return await Geolocator.getCurrentPosition();
  }
}
