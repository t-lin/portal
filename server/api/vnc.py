from __future__ import absolute_import
from flask_restful import Resource, current_app, fields, marshal_with
from . import rest_api
import requests
import json

VNET_PATH_LIST = "/virtual-networks"
VNET_PATH_ID = "/virtual-network/%s"
VM_PATH_LIST = "/virtual-machines"
VM_PATH_ID = "/virtual-machine/%s"

VNC_LIST_FIELDS = {
    "id": fields.String(attribute="name"),
}

VNC_VNET_INSTANCE_FIELDS = {
    "": fields.String(attribute="uuid"),
    "fq_name": fields.String,
    "name": fields.String,
}

VNC_SERVICE_VMS = {
    "id": fields.String(attribute="uuid"),
}

VNC_VNET_VMS = {
    "id": fields.String,
}


def filter_tenant(list, tenant):
    return [item for item in list
            if len(item["name"].split(':')) > 1 and
            item["name"].split(':')[1] == tenant]


class VNC(Resource):
    def get_vnets(self, tenant_id):
        url = current_app.config["ANALYTICS_URL"] + "/virtual-networks"
        vnets = requests.get(url).json()
        return filter_tenant(vnets, tenant_id)

    def get_vnet(self, id):
        url = current_app.config["ANALYTICS_URL"] + "/virtual-network/" + id\
            + "?flat"
        vnet = requests.get(url).json()
        return vnet

    def get_vnet_vms(self, vnetid):
        vnet = self.get_vnet(vnetid)
        vms = []
        try:
            vm_list = vnet['UveVirtualNetworkAgent']['virtualmachine_list']
            vms = [dict([("id", vm)]) for vm in vm_list]
            return vms
        except Exception, e:
            print e
        return vms

    def get_vm(self, id):
        url = current_app.config["ANALYTICS_URL"] + "/virtual-machine/" + id\
            + "?flat"
        vm = requests.get(url).json()
        return vm

    def get_services(self, tenant_id):
        url = current_app.config["ANALYTICS_URL"] + "/service-instances"
        services = requests.get(url).json()
        return filter_tenant(services, tenant_id)

    def get_service(self, id):
        url = current_app.config["ANALYTICS_URL"] + "/service-instance/" + id\
            + "?flat"
        service = requests.get(url).json()
        return service

    def get_services_details(self, tenant_id):
        url = current_app.config["CONTRAIL_URL"] + "/service-instances"
        services = requests.get(url).json().get("service-instances")

        retServs = [serv for serv in services if serv.get("fq_name")[1] == tenant_id]
        return retServs
        #return services

    def get_service_details(self, id):
        url = current_app.config["CONTRAIL_URL"] + "/service-instance/" + id
        service = requests.get(url).json()
        return service

    def update_service_details(self, id, jsonbody):
        url = current_app.config["CONTRAIL_URL"] + "/service-instance/" + id
        headers = {"Content-Type": "application/json"}
        results = requests.put(url, headers=headers, data=json.dumps(jsonbody))
        return results

    def get_service_vms(self, serviceid):
        service = self.get_service(serviceid)
        try:
            vms = service['UveSvcInstanceConfig']['vm_list']
            return vms
        except:
            pass
        return []


class VNetList(VNC):
    @marshal_with(VNC_LIST_FIELDS)
    def get(self):
        return self.get_vnets(current_app.config["OS_TENANT_NAME"])


class VNetInstance(VNC):
    # @marshal_with(VNC_VNET_INSTANCE_FIELDS)
    def get(self, id):
        return self.get_vnet(id)


class VNetVMList(VNC):
    @marshal_with(VNC_VNET_VMS)
    def get(self, vnetid):
        return self.get_vnet_vms(vnetid)


class VNetVMInstance(VNC):
    # @marshal_with(VNC_VMS_INSTANCE_FIELDS)
    def get(self, vnetid, id):
        return self.get_vm(id)


class ServiceList(VNC):
    @marshal_with(VNC_LIST_FIELDS)
    def get(self):
        return self.get_services(current_app.config["OS_TENANT_NAME"])


class ServiceInstance(VNC):
    # @marshal_with(VNC_VNET_INSTANCE_FIELDS)
    def get(self, id):
        return self.get_service(id)


class ServiceInstanceVMList(VNC):
    @marshal_with(VNC_SERVICE_VMS)
    def get(self, serviceid):
        return self.get_service_vms(serviceid)


class ServiceInstanceVM(VNC):
    # @marshal_with(VNC_VNET_INSTANCE_FIELDS)
    def get(self, serviceid, id):
        return self.get_vm(id)


class VMInstance(VNC):
    # @marshal_with(VNC_VMS_INSTANCE_FIELDS)
    def get(self, id):
        return self.get_vm(id)


class PolicyResources(Resource):
    # @marshal_with(VNC_LIST_FIELDS)
    def get(self):
        policies = current_app.vnc_lib.network_policys_list()
        return filter_tenant(policies['network-policys'],
                             current_app.config["OS_TENANT_NAME"])

class ScaleService(VNC):
    def post(self, serviceid, scalenum):
        retMsg = None
        try:
            scalenum = int(scalenum)
        except:
            retMsg = "Error: Specify proper scaling number"

        if not retMsg and (scalenum > 5 or scalenum < -5):
            retMsg = "Error: Cannot scale more than 5 instances at a time"

        # Fetch service details, modify max_instances, then update details
        if not retMsg:
            details = self.get_service_details(serviceid)

            num_instances = details["service-instance"]["service_instance_properties"]["scale_out"]["max_instances"]
            if int(num_instances) + scalenum > 0:
                details["service-instance"]["service_instance_properties"]["scale_out"]["max_instances"] = int(num_instances) + scalenum
                ret = self.update_service_details(serviceid, details)
                if ret.status_code != 200:
                    retMsg = "Contrail server error:\n%s" % ret.text
                else:
                    retMsg = "Scaled service %s to %s instances" % (serviceid, int(num_instances) + scalenum)
            else:
                retMsg = "Error: Cannot scale number of instances to zero or less"

        return retMsg

class CreateService(VNC):
    def in_net_firewall(self):
        from subprocess import Popen, PIPE, STDOUT
        cmdLine = "./scripts/contrail_innet_firewall.sh"
        p = Popen(cmdLine, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        out, err = p.communicate()

        index = out.find("UUID is:")
        return out[index+9:].rstrip('\n')

    def post(self, service_name):
        # Currently don't have different services, just call firewall
        pass

        return self.in_net_firewall()

#class tlintest(VNC):
#    def get(self):
#        #return self.get_service_details("632adb54-6742-4a51-8015-4ead8f3933eb")
#        from subprocess import Popen, PIPE, STDOUT
#        cmdLine = "./scripts/contrail_innet_firewall.sh"
#        p = Popen(cmdLine, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
#        out, err = p.communicate()
#
#        index = out.find("UUID is:")
#        return out[index+9:].rstrip('\n')
#        #return

rest_api.add_resource(VNetList, '/vnets')
rest_api.add_resource(VNetInstance, '/vnets/<string:id>')
rest_api.add_resource(VNetVMList, '/vnets/<string:vnetid>/vms')
rest_api.add_resource(VNetVMInstance, '/vnets/<string:vnetid>/vms/<string:id>')
rest_api.add_resource(PolicyResources, '/contrail/policies')
rest_api.add_resource(ServiceList, '/services')
rest_api.add_resource(ServiceInstance, '/services/<string:id>')
rest_api.add_resource(ServiceInstanceVMList,
                      '/services/<string:serviceid>/vms')
rest_api.add_resource(ServiceInstanceVM,
                      '/services/<string:serviceid>/vms/<string:id>')
rest_api.add_resource(VMInstance, '/vms/<string:id>')
rest_api.add_resource(ScaleService, '/scaleservice/<string:serviceid>/<string:scalenum>')
rest_api.add_resource(CreateService, '/createservice/<string:service_name>')
#rest_api.add_resource(tlintest, '/tlintest')

