from __future__ import absolute_import
from flask_restful import Resource, current_app, fields, marshal_with
from . import rest_api
from vnc_api import vnc_api

VNC_SERVICE_FIELDS = {
    "uuid": fields.String(),
    "fq_name": fields.String()
}


class ServiceResources(Resource):
    @marshal_with(VNC_SERVICE_FIELDS)
    def get(self):
        services = current_app.vnc_lib.service_instances_list()
        return services['service-instances']


class VNetResources(Resource):
    @marshal_with(VNC_SERVICE_FIELDS)
    def get(self):
        vnets = current_app.vnc_lib.service_instances_list()
        return vnets['virtual-networks']


class PolicyResources(Resource):
    @marshal_with(VNC_SERVICE_FIELDS)
    def get(self):
        policies = current_app.vnc_lib.service_instances_list()
        return policies['network-policys']

rest_api.add_resource(ServiceResources, '/contrail/services')
rest_api.add_resource(VNetResources, '/contrail/vnets')
rest_api.add_resource(PolicyResources, '/contrail/policies')
