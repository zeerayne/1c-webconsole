from v8webconsole.clusterconfig.models import (
    Host,
)
from rest_framework import (
    status,
    permissions,
    viewsets,
)
from rest_framework.response import Response
from rest_framework import exceptions
from .views_mixins import (
    RAgentInterfaceViewMixin,
    MultiSerializerViewSetMixin,
)
from .serializers import (
    HostSerializer,
    ShortClusterSerializer,
    DetailClusterSerializer,
    RegUserSerializer,
    ShortInfobaseSerializer,
    CreateInfobaseSerializer,
    UpdateInfobaseSerializer,
    DetailInfobaseSerializer,
)


class HostViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated, )

    serializer_class = HostSerializer

    def get_queryset(self):
        return Host.objects.all()

    def get_object(self):
        return Host.objects.get(id=self.kwargs['pk'])


class HostAdminViewSet(RAgentInterfaceViewMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated, )

    serializer_class = RegUserSerializer

    def get_queryset(self):
        self.authenticate_agent()
        return self.get_ragent_interface().get_agent_admins()

    def list(self, request, host_pk=None, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClusterViewSet(RAgentInterfaceViewMixin, MultiSerializerViewSetMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated, )

    default_serializer_class = DetailClusterSerializer

    actions_map = {
        'list': ShortClusterSerializer,
        'retrieve': DetailClusterSerializer,
    }

    def get_queryset(self):
        return self.get_ragent_interface().get_clusters()

    def get_object(self):
        cluster_name = self.kwargs['pk']
        try:
            return self.get_ragent_interface().get_cluster(cluster_name)
        except StopIteration:
            raise exceptions.NotFound(f'Cluster with name [{cluster_name}] does not exists')

    def list(self, request, host_pk=None, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, host_pk=None, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        detail_serializer = self.get_default_serializer(instance)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        return serializer.save(ragent_interface=self.get_ragent_interface())

    def retrieve(self, request, host_pk=None, pk=None, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, host_pk=None, cluster_pk=None, pk=None, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_update(serializer)
        detail_serializer = self.get_default_serializer(instance)
        return Response(detail_serializer.data)

    def perform_update(self, serializer):
        return serializer.save(
            ragent_interface=self.get_ragent_interface(),
            cluster_interface=self.get_cluster_interface()
        )

    def partial_update(self, request, host_pk=None, cluster_pk=None, pk=None, **kwargs):
        kwargs['partial'] = True
        return self.update(request, host_pk, cluster_pk, pk, **kwargs)

    def destroy(self, request, host_pk=None, cluster_pk=None, pk=None, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        login, pwd = self.get_cluster_admin_credentials()
        self.get_ragent_interface().unreg_cluster(instance, login, pwd)


class InfobaseViewSet(RAgentInterfaceViewMixin, MultiSerializerViewSetMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated, )

    default_serializer_class = DetailInfobaseSerializer

    actions_map = {
        'list': ShortInfobaseSerializer,
        'create': CreateInfobaseSerializer,
        'update': UpdateInfobaseSerializer,
        'partial_update': UpdateInfobaseSerializer,
        'retrieve': default_serializer_class,
    }

    destroy_mode_map = {
        'persist': 0,
        'drop': 1,
        'clear': 2,
    }

    def get_queryset(self):
        self.authenticate_cluster_admin()
        return self.get_cluster_interface().get_infobases_short()

    def get_object(self):
        ib_name = self.kwargs['pk']
        self.authenticate_cluster_admin()
        self.authenticate_infobase_admin(ib_name)
        try:
            return self.get_cluster_interface().get_infobase(ib_name)
        except StopIteration:
            raise exceptions.NotFound(f'Infobase with name [{ib_name}] does not exists')

    def list(self, request, host_pk=None, cluster_pk=None, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, host_pk=None, cluster_pk=None, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        detail_serializer = self.get_default_serializer(instance)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        self.authenticate_cluster_admin()
        return serializer.save(cluster_interface=self.get_cluster_interface())

    def retrieve(self, request, host_pk=None, cluster_pk=None, pk=None, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, host_pk=None, cluster_pk=None, pk=None, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_update(serializer)
        detail_serializer = self.get_default_serializer(instance)
        return Response(detail_serializer.data)

    def perform_update(self, serializer):
        return serializer.save(cluster_interface=self.get_cluster_interface())

    def partial_update(self, request, host_pk=None, cluster_pk=None, pk=None, **kwargs):
        kwargs['partial'] = True
        return self.update(request, host_pk, cluster_pk, pk, **kwargs)

    def destroy(self, request, host_pk=None, cluster_pk=None, pk=None, **kwargs):
        instance = self.get_object()
        mode = self.destroy_mode_map[request.query_params.get('mode', 'persist')]
        self.perform_destroy(instance, mode)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance, mode):
        self.get_cluster_interface().working_process_connection.drop_infobase(instance, mode)
