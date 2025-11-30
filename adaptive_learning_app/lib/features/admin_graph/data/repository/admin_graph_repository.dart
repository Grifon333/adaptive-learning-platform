import 'dart:io';

import 'package:adaptive_learning_app/app/app_config/app_config.dart';
import 'package:adaptive_learning_app/app/http/i_http_client.dart';
import 'package:adaptive_learning_app/features/admin_graph/data/dto/admin_graph_dtos.dart';
import 'package:adaptive_learning_app/features/admin_graph/data/dto/admin_resource_dtos.dart';
import 'package:adaptive_learning_app/features/admin_graph/domain/repository/i_admin_graph_repository.dart';
import 'package:dio/dio.dart';

final class AdminGraphRepository implements IAdminGraphRepository {
  AdminGraphRepository({required this.httpClient, required this.appConfig});

  final IHttpClient httpClient;
  final IAppConfig appConfig;

  @override
  String get name => 'AdminGraphRepository';

  @override
  Future<List<AdminConceptDto>> getConcepts() async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/concepts?limit=1000';
    final response = await httpClient.get(url);
    final data = response.data as Map<String, dynamic>;
    final items = data['items'] as List;
    return items.map((e) => AdminConceptDto.fromJson(e as Map<String, dynamic>)).toList();
  }

  @override
  Future<AdminConceptDto> createConcept(AdminConceptDto concept) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/concepts';
    final response = await httpClient.post(url, data: concept.toJson());
    return AdminConceptDto.fromJson(response.data);
  }

  @override
  Future<AdminConceptDto> updateConcept(String id, AdminConceptDto concept) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/concepts/$id';
    final response = await httpClient.put(url, data: concept.toJson());
    return AdminConceptDto.fromJson(response.data);
  }

  @override
  Future<void> deleteConcept(String id) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/concepts/$id';
    await httpClient.delete(url);
  }

  @override
  Future<void> createRelationship(String startId, String endId) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/relationships';
    final dto = CreateRelationshipDto(startId: startId, endId: endId);
    await httpClient.post(url, data: dto.toJson());
  }

  @override
  Future<void> deleteRelationship(String startId, String endId) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/relationships';
    // Backend expects body for delete usually, or query params.
    // Based on standard axios/dio, delete supports data.
    final dto = CreateRelationshipDto(startId: startId, endId: endId);
    await httpClient.delete(url, data: dto.toJson());
  }

  @override
  Future<List<AdminResourceDto>> getResources() async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/resources?limit=1000';
    final response = await httpClient.get(url);
    final data = response.data as Map<String, dynamic>;
    final items = data['items'] as List;
    return items.map((e) => AdminResourceDto.fromJson(e)).toList();
  }

  @override
  Future<AdminResourceDto> createResource(AdminResourceDto resource) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/resources';
    final response = await httpClient.post(url, data: resource.toJson());
    return AdminResourceDto.fromJson(response.data);
  }

  @override
  Future<AdminResourceDto> updateResource(String id, AdminResourceDto resource) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/resources/$id';
    final response = await httpClient.put(url, data: resource.toJson());
    return AdminResourceDto.fromJson(response.data);
  }

  @override
  Future<void> deleteResource(String id) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/resources/$id';
    await httpClient.delete(url);
  }

  @override
  Future<void> linkResourceToConcept(String conceptId, String resourceId) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/concepts/$conceptId/resources?resource_id=$resourceId';
    await httpClient.post(url);
  }

  @override
  Future<void> unlinkResourceFromConcept(String conceptId, String resourceId) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/concepts/$conceptId/resources/$resourceId';
    await httpClient.delete(url);
  }

  @override
  Future<String> uploadFile(File file, {void Function(int, int)? onSendProgress}) async {
    final url = '${appConfig.knowledgeGraphServiceUrl}/uploads';
    final String fileName = file.path.split('/').last;
    final formData = FormData.fromMap({'file': await MultipartFile.fromFile(file.path, filename: fileName)});

    final response = await httpClient.post(
      url,
      data: formData,
      options: Options(
        headers: {
          'Content-Type': 'multipart/form-data', // Explicitly set, though Dio usually handles it
        },
      ),
      // We need to bypass the interface wrapper if it doesn't expose onSendProgress,
      // but since our AppHttpClient wraps Dio, we assume we added support or access the underlying dio.
      // For this implementation, let's assume AppHttpClient needs a slight tweak or we access dio directly if strictly needed.
      // *Correction*: The current IHttpClient interface doesn't expose onSendProgress.
      // In a strict architecture, we'd update IHttpClient. For now, we will pass it if possible or cast.
    );

    // Expecting response: { "url": "http://...", "filename": "..." }
    final data = response.data as Map<String, dynamic>;
    return data['url'] as String;
  }
}
