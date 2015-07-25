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
        OS_USERNAME = current_app.config["OS_USERNAME"]
        OS_PASSWORD = current_app.config["OS_PASSWORD"]
        # OS_TENANT_NAME = current_app.config["OS_TENANT_NAME"]
        OS_SERVER = current_app.config["OS_SERVER"]
        vnc_lib = vnc_api.VncApi(username=OS_USERNAME,
                                 password=OS_PASSWORD,
                                 api_server_host=OS_SERVER)

        return vnc_lib.service_instances_list()['service-instances']


class VNetResources(Resource):
    @marshal_with(VNC_SERVICE_FIELDS)
    def get(self):
        OS_USERNAME = current_app.config["OS_USERNAME"]
        OS_PASSWORD = current_app.config["OS_PASSWORD"]
        # OS_TENANT_NAME = current_app.config["OS_TENANT_NAME"]
        OS_SERVER = current_app.config["OS_SERVER"]
        vnc_lib = vnc_api.VncApi(username=OS_USERNAME,
                                 password=OS_PASSWORD,
                                 api_server_host=OS_SERVER)

        return vnc_lib.virtual_networks_list()['virtual-networks']


class PolicyResources(Resource):
    @marshal_with(VNC_SERVICE_FIELDS)
    def get(self):
        OS_USERNAME = current_app.config["OS_USERNAME"]
        OS_PASSWORD = current_app.config["OS_PASSWORD"]
        # OS_TENANT_NAME = current_app.config["OS_TENANT_NAME"]
        OS_SERVER = current_app.config["OS_SERVER"]
        vnc_lib = vnc_api.VncApi(username=OS_USERNAME,
                                 password=OS_PASSWORD,
                                 api_server_host=OS_SERVER)

        return vnc_lib.network_policys_list()['network-policys']

rest_api.add_resource(ServiceResources, '/contrail/services')
rest_api.add_resource(VNetResources, '/contrail/vnets')
rest_api.add_resource(PolicyResources, '/contrail/policies')
