/// {@template i_location_service}
/// Interface for working with user geolocation.
/// {@endtemplate}
abstract interface class ILocationService {
  static const name = 'ILocationService';

  Future<dynamic> getCurrentPosition();
}
