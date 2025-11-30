import 'dart:io';

import 'package:adaptive_learning_app/di/di_base_repository.dart';
import 'package:adaptive_learning_app/features/admin_graph/data/dto/admin_graph_dtos.dart';
import 'package:adaptive_learning_app/features/admin_graph/data/dto/admin_resource_dtos.dart';

abstract interface class IAdminGraphRepository with DiBaseRepository {
  Future<List<AdminConceptDto>> getConcepts();
  Future<AdminConceptDto> createConcept(AdminConceptDto concept);
  Future<AdminConceptDto> updateConcept(String id, AdminConceptDto concept);
  Future<void> deleteConcept(String id);
  Future<void> createRelationship(String startId, String endId);
  Future<void> deleteRelationship(String startId, String endId);

  Future<List<AdminResourceDto>> getResources();
  Future<AdminResourceDto> createResource(AdminResourceDto resource);
  Future<AdminResourceDto> updateResource(String id, AdminResourceDto resource);
  Future<void> deleteResource(String id);
  Future<void> linkResourceToConcept(String conceptId, String resourceId);
  Future<void> unlinkResourceFromConcept(String conceptId, String resourceId);
  Future<String> uploadFile(File file, {void Function(int, int)? onSendProgress});
}
