import 'dart:io';

import 'package:adaptive_learning_app/features/admin_graph/data/dto/admin_resource_dtos.dart';
import 'package:adaptive_learning_app/features/admin_graph/domain/repository/i_admin_graph_repository.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:meta/meta.dart';

part 'admin_resource_event.dart';
part 'admin_resource_state.dart';

class AdminResourceBloc extends Bloc<AdminResourceEvent, AdminResourceState> {
  AdminResourceBloc({required this.repository}) : super(ResourceInitial()) {
    on<LoadResourcesRequested>(_onLoad);
    on<SaveResourceRequested>(_onSave);
    on<DeleteResourceRequested>(_onDelete);
    on<LinkResourceRequested>(_onLink);
    on<UnlinkResourceRequested>(_onUnlink);
    on<UploadFileRequested>(_onUpload);
  }

  final IAdminGraphRepository repository;

  Future<void> _onLoad(LoadResourcesRequested event, Emitter<AdminResourceState> emit) async {
    emit(ResourceLoading());
    try {
      final resources = await repository.getResources();
      emit(ResourceLoaded(resources));
    } on Object catch (e) {
      emit(ResourceError(e.toString()));
    }
  }

  Future<void> _onSave(SaveResourceRequested event, Emitter<AdminResourceState> emit) async {
    try {
      if (event.resource.id.isEmpty) {
        await repository.createResource(event.resource);
      } else {
        await repository.updateResource(event.resource.id, event.resource);
      }
      add(LoadResourcesRequested());
    } on Object catch (e) {
      emit(ResourceError("Failed to save: $e"));
    }
  }

  Future<void> _onDelete(DeleteResourceRequested event, Emitter<AdminResourceState> emit) async {
    try {
      await repository.deleteResource(event.id);
      add(LoadResourcesRequested());
    } on Object catch (e) {
      emit(ResourceError("Failed to delete: $e"));
    }
  }

  Future<void> _onLink(LinkResourceRequested event, Emitter<AdminResourceState> emit) async {
    try {
      await repository.linkResourceToConcept(event.conceptId, event.resourceId);
      emit(const ResourceOperationSuccess("Resource linked!"));
      add(LoadResourcesRequested()); // Refresh list state
    } on Object catch (e) {
      emit(ResourceError("Failed to link: $e"));
    }
  }

  Future<void> _onUnlink(UnlinkResourceRequested event, Emitter<AdminResourceState> emit) async {
    try {
      await repository.unlinkResourceFromConcept(event.conceptId, event.resourceId);
      emit(const ResourceOperationSuccess("Resource unlinked!"));
    } on Object catch (e) {
      emit(ResourceError("Failed to unlink: $e"));
    }
  }

  Future<void> _onUpload(UploadFileRequested event, Emitter<AdminResourceState> emit) async {
    emit(const ResourceUploading(0.0));
    try {
      // Determine type based on extension
      final ext = event.file.path.split('.').last.toLowerCase();
      String type = 'Article';
      if (['mp4', 'mov', 'avi'].contains(ext)) type = 'Video';
      if (['pdf'].contains(ext)) type = 'Book';
      if (['mp3', 'wav'].contains(ext)) type = 'Audio';
      if (['md', 'markdown'].contains(ext)) type = 'Markdown';
      if (['txt'].contains(ext)) type = 'Text';

      final url = await repository.uploadFile(
        event.file,
        onSendProgress: (sent, total) {
          // In a real app, you might throttle this emission to avoid rebuilding too fast
          // For simplicity:
          // add(UpdateUploadProgress(sent / total)); // If using a separate event loop
        },
      );

      // Simulate progress for UI smoothness if callback isn't wired perfectly in IHttpClient
      emit(const ResourceUploading(1.0));

      emit(ResourceUploadSuccess(url, type));

      // After success, we might want to reload the list or just stay ready
      // We don't reload list here because we are inside a Dialog usually.
    } on Object catch (e) {
      emit(ResourceError("Upload failed: $e"));
    }
  }
}
