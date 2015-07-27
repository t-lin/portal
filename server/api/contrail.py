from __future__ import absolute_import
from flask_restful import Resource, current_app, fields, marshal_with
from . import rest_api

VNC_LIST_FIELDS = {
    "id": fields.String(attribute="uuid"),
    "fq_name": fields.String,
}


VNC_SERVICE_INSTANCE_FIELDS = {
    "id": fields.String(attribute="uuid"),
    "fq_name": fields.String,
    "name": fields.String,
    "type": fields.String(attribute=lambda x: x.get_type()),
    "virtual_machine_back_refs": fields.List(fields.Nested({
            "uuid": fields.String,
        }),
        attribute=lambda x: x.get_virtual_machine_back_refs()),
    "service_instance_properties": {
        "management_virtual_network": fields.String,
        "right_virtual_network": fields.String
    }
}

VNC_VNET_INSTANCE_FIELDS = {
    "id": fields.String(attribute="uuid"),
    "fq_name": fields.String,
    "name": fields.String,
}


def filter_tenant(list, tenant):
    return [item for item in list
            if item["fq_name"][1] == tenant]


class ServiceList(Resource):
    @marshal_with(VNC_LIST_FIELDS)
    def get(self):
        services = current_app.vnc_lib.service_instances_list()
        return filter_tenant(services['service-instances'],
                             current_app.config["OS_TENANT_NAME"])


class ServiceInstance(Resource):
    @marshal_with(VNC_SERVICE_INSTANCE_FIELDS)
    def get(self, id):
        service = current_app.vnc_lib.service_instance_read(id=id)
        return service


class VNetList(Resource):
    @marshal_with(VNC_LIST_FIELDS)
    def get(self):
        vnets = current_app.vnc_lib.virtual_networks_list()
        return filter_tenant(vnets['virtual-networks'],
                             current_app.config["OS_TENANT_NAME"])


class VNetInstance(Resource):
    @marshal_with(VNC_VNET_INSTANCE_FIELDS)
    def get(self, id):
        service = current_app.vnc_lib.virtual_network_read(id=id)
        return service


class PolicyResources(Resource):
    @marshal_with(VNC_LIST_FIELDS)
    def get(self):
        policies = current_app.vnc_lib.network_policys_list()
        return filter_tenant(policies['network-policys'],
                             current_app.config["OS_TENANT_NAME"])


rest_api.add_resource(ServiceList, '/contrail/services')
rest_api.add_resource(ServiceInstance, '/contrail/services/<string:id>')
rest_api.add_resource(VNetList, '/contrail/vnets')
rest_api.add_resource(VNetInstance, '/contrail/vnets/<string:id>')
rest_api.add_resource(PolicyResources, '/contrail/policies')
