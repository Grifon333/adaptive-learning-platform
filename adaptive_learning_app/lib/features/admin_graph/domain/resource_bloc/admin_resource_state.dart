part of 'admin_resource_bloc.dart';

@immutable
sealed class AdminResourceState extends Equatable {
  const AdminResourceState();
  @override
  List<Object?> get props => [];
}

class ResourceInitial extends AdminResourceState {}

class ResourceLoading extends AdminResourceState {}

class ResourceUploading extends AdminResourceState {
  const ResourceUploading(this.progress);
  final double progress;
  @override
  List<Object?> get props => [progress];
}

class ResourceUploadSuccess extends AdminResourceState {
  const ResourceUploadSuccess(this.url, this.detectedType);
  final String url;
  final String detectedType;
}

class ResourceLoaded extends AdminResourceState {
  const ResourceLoaded(this.resources);
  final List<AdminResourceDto> resources;
  @override
  List<Object?> get props => [resources];
}

class ResourceOperationSuccess extends AdminResourceState {
  const ResourceOperationSuccess(this.message);
  final String message;
}

class ResourceError extends AdminResourceState {
  const ResourceError(this.message);
  final String message;
}
