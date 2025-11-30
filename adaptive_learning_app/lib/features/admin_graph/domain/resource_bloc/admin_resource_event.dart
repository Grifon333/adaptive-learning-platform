part of 'admin_resource_bloc.dart';

@immutable
sealed class AdminResourceEvent extends Equatable {
  const AdminResourceEvent();
  @override
  List<Object?> get props => [];
}

class LoadResourcesRequested extends AdminResourceEvent {}

class SaveResourceRequested extends AdminResourceEvent {
  const SaveResourceRequested(this.resource);
  final AdminResourceDto resource;
}

class DeleteResourceRequested extends AdminResourceEvent {
  const DeleteResourceRequested(this.id);
  final String id;
}

class LinkResourceRequested extends AdminResourceEvent {
  const LinkResourceRequested({required this.conceptId, required this.resourceId});
  final String conceptId;
  final String resourceId;
}

class UnlinkResourceRequested extends AdminResourceEvent {
  const UnlinkResourceRequested({required this.conceptId, required this.resourceId});
  final String conceptId;
  final String resourceId;
}

class UploadFileRequested extends AdminResourceEvent {
  const UploadFileRequested(this.file);
  final File file;
}
