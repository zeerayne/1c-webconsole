from django.views.generic import ListView
from v8webconsole.clusterconfig.models import Host, Cluster, ClusterCredentials
from django.db import models
from django.db.models.fields import reverse_related
from v8webconsole.core import cluster as core_cluster


class HostListView(ListView):
    model = Host
    template_name = 'host_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = self.model._meta.get_fields()
        ctx['field_names'] = [field.name for field in self.model._meta.get_fields()
                              if not isinstance(field, (models.AutoField, reverse_related.ForeignObjectRel))
                              ]
        return ctx


class ClusterListView(ListView):
    model = Cluster
    template_name = 'cluster_list.html'

    def get_queryset(self):
        return self.model.objects.filter(host__id=self.kwargs['host_id'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['field_names'] = [field.name for field in self.model._meta.get_fields()
                              if not isinstance(field, (models.AutoField, reverse_related.ForeignObjectRel))
                              ]
        return ctx


class InfobaseListView(ListView):

    def get_queryset(self):
        cluster = Cluster.objects.get(host__id=self.kwargs['cluster_id'])
        host = cluster.host
        cluster_credentials = ClusterCredentials.objects.filter(cluster__id=cluster.id)[:1][0]
        cci = core_cluster.ClusterControlInterface(host=host.address, port=host.port,
                                                   cluster_admin_name=cluster_credentials.login,
                                                   cluster_admin_pwd=cluster_credentials.pwd,
                                                   infobases_credentials={}
                                                   )
        agent_connection = cci.get_agent_connection()
        info_bases_short = cci.get_info_bases_short(agent_connection)
        return [ib.Name for ib in info_bases_short]

    template_name = 'infobase_list.html'
