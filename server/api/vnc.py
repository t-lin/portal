from __future__ import absolute_import
from flask_restful import Resource, current_app, fields, marshal_with, reqparse
from flask import request
from . import rest_api
import requests
import json
import paramiko
import time
import traceback
import random

from subprocess import Popen, PIPE, STDOUT

from kubernetes import client, config

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()
v1Api = client.CoreV1Api()
v1AppsApi = client.AppsV1Api()
v1ExtApi = client.ExtensionsV1beta1Api()

parser = reqparse.RequestParser()
#parser.add_argument('asdfasdf')

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

VNC_POLICY_FIELDS = {
    "id": fields.String(attribute="uuid"),
    "fq_name": fields.String
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
        contrail_service = current_app.vnc_lib.service_instance_read(
            fq_name_str=id)
        service['uuid'] = contrail_service.uuid
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

    def get_policy_details(self, id):
        url = current_app.config["CONTRAIL_URL"] + "/network-policy/" + id
        policy = requests.get(url).json()
        return policy

    def update_policy_details(self, id, jsonbody):
        url = current_app.config["CONTRAIL_URL"] + "/network-policy/" + id
        headers = {"Content-Type": "application/json"}
        results = requests.put(url, headers=headers, data=json.dumps(jsonbody))
        return results


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
    # @marshal_with(VNC_POLICY_FIELDS)
    def getPolicy(self, id):
        return requests.get(
            'http://'+current_app.config['OS_SERVER']+':8082/network-policy/'+id).json()

    def get(self):
        policies = current_app.vnc_lib.network_policys_list()
        res_pol = []
        for p in policies['network-policys']:
            if p['fq_name'][1] == current_app.config["OS_TENANT_NAME"]:
                res_pol.append(self.getPolicy(p['uuid']))
        return res_pol


class VIFaceStats(Resource):
    # @marshal_with(VNC_VMS_INSTANCE_FIELDS)
    def get(self, id):
        url = current_app.config["ANALYTICS_URL"] + \
            "/virtual-machine-interface/" + id + "?flat"
        service = requests.get(url).json()
        return service


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

                    if scalenum > 0:
                        # Create alarms for the instances of the stack
                        cmdLine = "bash -c 'sleep 15; ./scripts/create_scaling_alarms.sh " + serviceid + "&'"
                        p = Popen(cmdLine, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
                        out, err = p.communicate()
                        print out
                        print err

            else:
                retMsg = "Error: Cannot scale number of instances to zero or less"

        return retMsg

class CreateService(VNC):
    def in_net_firewall(self):
        cmdLine = "./scripts/contrail_innet_firewall.sh"
        p = Popen(cmdLine, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        out, err = p.communicate()

        index = out.find("UUID is:")
        return out[index+9:].rstrip('\n')

    def post(self, service_name):
        import time

        # Currently don't have different services, just call firewall
        service_uuid = self.in_net_firewall()
        print service_uuid
        time.sleep(3) # Give instances chance to boot up

        # Create alarms for the instances of the stack
        cmdLine = "./scripts/create_scaling_alarms.sh " + service_uuid
        p = Popen(cmdLine, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        out, err = p.communicate()
        print out
        print err

        return "Deployed service and created alarms"

class DeleteService(VNC):
    def get(self, serviceid):
        return self.delete(serviceid)

    def delete(self, serviceid):
        cmdLine = "./scripts/delete_firewall.sh " + serviceid
        p = Popen(cmdLine, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        out, err = p.communicate()
        print out
        print err

        return "Deleted service %s" % serviceid

class ServiceInstanceVMListUUID(VNC):
    # Specify service using UUID rather than FQ name
    # Returns space-separated list of VM UUIDs
    def get(self, serviceid):
        out = self.get_service_details(serviceid)

        vmList = ""
        for vm in out["service-instance"]["virtual_machine_back_refs"]:
            vmList += vm["to"][0] + " "

        return vmList.rstrip() # Get rid of last space

class ChainService(VNC):
    def post(self, serviceid, policyid):
        return self.put(serviceid, policyid)

    def put(self, serviceid, policyid):
        retMsg = None

        # Get the service's FQ name, needed for insertion into policy
        details = self.get_service_details(serviceid)
        fq_name = ":".join(i for i in details["service-instance"]["fq_name"])

        # Currently default policyid to uoftorro policy
        policyid = "86e13322-7e79-40c4-9e38-83a100e7f12d" # tmp

        policy = self.get_policy_details(policyid)
        # Currently assume only single rule, hence get first element of list
        pol_rule = policy["network-policy"]["network_policy_entries"]["policy_rule"][0]
        service_list = pol_rule["action_list"]["apply_service"]
        if not service_list:
            service_list = [ fq_name ]
        else:
            service_list.append(fq_name)

        policy["network-policy"]["network_policy_entries"]["policy_rule"][0]["action_list"]["apply_service"] = service_list

        ret = self.update_policy_details(policyid, policy)
        if ret.status_code != 200:
            retMsg = "Contrail server error:\n%s" % ret.text
        else:
            retMsg = "Added service %s (%s) into policy %s" % (serviceid, fq_name, policyid)

        return retMsg

    def delete(self, serviceid, policyid):
        retMsg = None

        # Get the service's FQ name, needed for insertion into policy
        details = self.get_service_details(serviceid)
        fq_name = ":".join(i for i in details["service-instance"]["fq_name"])

        # Currently default policyid to uoftorro policy
        policyid = "86e13322-7e79-40c4-9e38-83a100e7f12d" # tmp

        policy = self.get_policy_details(policyid)
        # Currently assume only single rule, hence get first element of list
        pol_rule = policy["network-policy"]["network_policy_entries"]["policy_rule"][0]
        service_list = pol_rule["action_list"]["apply_service"]

        if fq_name in service_list:
            service_list.remove(fq_name)

        policy["network-policy"]["network_policy_entries"]["policy_rule"][0]["action_list"]["apply_service"] = service_list

        ret = self.update_policy_details(policyid, policy)
        if ret.status_code != 200:
            retMsg = "Contrail server error:\n%s" % ret.text
        else:
            retMsg = "Removed service %s (%s) into policy %s" % (serviceid, fq_name, policyid)

        return retMsg

START_TIME = 0 # For NOMS '20 evaluations
class AlertHandler(VNC):
    def get(self):
        return "You called GET!"

    def put(self):
        # TLIN: For NOMS paper evaluation purposes

        # Latency experiments
        sshSession = paramiko.SSHClient()
        sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sshSession.connect("192.168.200.13", username = "ubuntu")

        command = "sudo tc qdisc add dev vxlan_sys_4789 root netem delay 10ms"
        stdin, stdout, stderr = sshSession.exec_command(command)

        # Bandwidth experiments
        #cmdLine = "iperf3 -c 192.168.200.12 -t 180 >/dev/null &"
        #p = Popen(cmdLine, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)

        global START_TIME
        START_TIME = time.time()
        print "\n\nSTART EXPERIMENT: %f\n\n" % START_TIME
        # END TLIN

        return "You called PUT!"

    def scaleDeployment(self, deployName, replicas = 1):
        assert type(deployName) in (str, unicode)
        assert type(replicas) in (int, long)

        namespace = "default" # TODO: Make configurable

        metadataObj = client.V1ObjectMeta()
        metadataObj.namespace = namespace
        metadataObj.name = deployName

        scaleSpecObj = client.ExtensionsV1beta1ScaleSpec()
        scaleSpecObj.replicas = replicas

        scaleObj = client.ExtensionsV1beta1Scale()
        scaleObj.api_version = "extensions/v1beta1"
        scaleObj.kind = "Deployment"
        scaleObj.metadata = metadataObj
        scaleObj.spec = scaleSpecObj

        try:
            ret = v1ExtApi.patch_namespaced_deployment_scale(deployName, namespace, scaleObj)
            # TODO: Figure out how to check for success...
            #       K8s returns a 'status' object, but it only shows the pre-scale replica count
        except:
            traceback.print_exc()

    # Scales out a deployment by adding 'delta' replicas
    #   - Currently limits by increments of 10
    #
    # Returns:
    #   Number of replicas (after scaling) on success
    #   None on failure
    def scaleOut(self, deployName, delta = 1):
        assert type(deployName) in (str, unicode)
        assert type(delta) in (int, long)

        if delta > 10:
            print "ERROR: Can only scale out by increments of at most 10"
        elif delta < 1:
            print "ERROR: Cannot scale out by less than 1"
        else:
            currReplicas = self.getDeployNumReplicas(deployName)
            if currReplicas is not None:
                currReplicas += delta

                print "Scaling out deployment %s to %s replicas" % \
                        (deployName, currReplicas)
                self.scaleDeployment(deployName, currReplicas)

                return currReplicas

        return None

    # Scales in a deployment by subtracting 'delta' replicas
    #   - If the sum after subtraction is less than 1, then scale to 1
    #
    # Maintains QoS policy when deciding which pod(s) to delete
    #   - Current policy is to prioritize deletion of pods with no active
    #     connections and which exists on nodes with higher latencies
    #
    # Returns:
    #   Number of replicas (after scaling) on success
    #   None on failure
    def scaleIn(self, deployName, delta = 1):
        assert type(deployName) in (str, unicode)
        assert type(delta) in (int, long)

        # Currently, scaling in chooses pods with the least uptime to delete
        #   See: https://github.com/kubernetes/kubernetes/blob/d8d680be6e2bd1455bb6861f9bd6ed7d4f7dce43/pkg/controller/controller_utils.go#L731-L763
        #
        # This behaviour may delete pods and violate QoS. The current work-
        # around is to pick a pod to delete based on our QoS metric goal,
        # explicitly delete it, then immediately perform the scale-in. K8s
        # may try to re-spawn the container on a new node, but since it has
        # the lowest uptime, it'll be deleted first.

        currReplicas = self.getDeployNumReplicas(deployName)
        if currReplicas is not None:
            # Don't allow scaling down to 0
            targetReplicas = max(1, currReplicas - delta)

            podsToDelete = currReplicas - targetReplicas
            if podsToDelete > 0:
                podList = self.getDeployPodList(deployName)

                # Get endpoints (IPs) of pods with active connections
                activeIPs = self.promGetDeployPodsActiveConn(deployName)

                # Get list of inactive pods, determined by seeing if their
                # IP address is not in the list of active IPs
                inactivePods = []
                for pod in podList:
                    if pod.status.phase == "Running" and \
                            pod.metadata.deletion_timestamp is None and \
                            pod.status.pod_ip not in activeIPs:
                        inactivePods.append(pod)

                # Get nodes ranked from highest to lowest latency
                # If an inactive pod exists on that node, delete it first
                targetNodes = self.promGetNodesRankedLatency()
                for node in targetNodes:
                    for pod in inactivePods:
                        if node == pod.spec.node_name:
                            self.deletePod(pod.metadata.name)
                            podsToDelete -= 1
                            # TODO: May be slow if podList is very large. Should
                            #       maintain list of pods deleted, and remove
                            #       them from podList after inner for-loop exits

                            if podsToDelete == 0:
                                break

                    if podsToDelete == 0:
                        break

                if podsToDelete > 0:
                    # Will this happen? Maybe if some nodes were cut off...
                    print "Unable to delete desired number of pods, %s are left" % podsToDelete
                    targetReplicas += podsToDelete

                print "Scaling in deployment %s to %s replicas" % \
                        (deployName, targetReplicas)
                self.scaleDeployment(deployName, targetReplicas)

    # Returns a list of replicas w/ active flows in the deployment
    #
    # NOTE: This function leverages the pping service metrics (ensure that
    #       service is up and properly being pulled by Prometheus)
    def promGetDeployPodsActiveConn(self, deployName):
        assert type(deployName) in (str, unicode)

        namespace = "default" # TODO: Make configurable

        # TODO: Currently hard-coded url link to Prom query
        #       Figure out how to make this configurable based on deployName
        url = "http://10.11.0.19:9090/api/v1/query?query=count%20by(dstIP)%20(pping_service_rtt%7BdstPort%3D%229000%22%7D)"
        promRes = requests.get(url).json()

        podEndpoints = set()
        if promRes['status'] == "success":
            promData = promRes['data']['result']

            for series in promData:
                endpoint = series['metric']['dstIP']
                podEndpoints.add(endpoint)

        return list(podEndpoints)

    # Returns # of target replicas in the deployment
    # Returns None on error
    def getDeployNumReplicas(self, deployName):
        assert type(deployName) in (str, unicode)

        namespace = "default" # TODO: Make configurable

        try:
            ret = v1ExtApi.read_namespaced_deployment_status(deployName, namespace)
            return ret.status.replicas
        except:
            traceback.print_exc()

        return None

    # Returns a list of pod objects (kubernetes.client.models.v1_pod.V1Pod)
    # Returns None on error
    def getPodList(self):
        namespace = "default" # TODO: Make configurable
        try:
            ret = v1Api.list_namespaced_pod(namespace)
            if ret and len(ret.items) > 0:
                return ret.items
        except:
            traceback.print_exc()

        return None

    # Returns a list of pod objects (kubernetes.client.models.v1_pod.V1Pod)
    # belonging to a specific deployment
    #
    # Returns None on error
    def getDeployPodList(self, deployName):
        assert type(deployName) in (str, unicode)

        namespace = "default" # TODO: Make configurable

        try:
            deploy = v1AppsApi.read_namespaced_deployment(deployName, namespace)
        except:
            print "ERROR: Unable to get deployment %s" % deployName
            return None

        selector = deploy.spec.selector.match_labels.items()[0] # Turn into tuple
        selector = "%s=%s" % (selector[0], selector[1])

        try:
            podList = v1Api.list_namespaced_pod(namespace, label_selector = selector)
        except:
            print "ERROR: Unable to get pods with label selector %s" % selector
            return None

        return podList.items


    def deletePod(self, podName):
        assert type(podName) in (str, unicode)

        try:
            namespace = "default" # TODO: Make configurable
            ret = v1Api.delete_namespaced_pod(podName, namespace)
            # TODO: How to discern success? The ret seems to have no actual status...
            print "Deleting pod %s" % podName
        except:
            traceback.print_exc()

    # Finds node with lowest latency over a certain time period (e.g. 60s)
    # We scan over a time period to get stability in cases where two or more nodes
    # have similar latencies and the ping_rtt_median_20s flip-flops a lot.
    #
    # Gets list of nodes ranked from highest to lowest latency
    # Returns None if no node found
    def promGetNodesRankedLatency(self):
        TIME_PERIOD_S = 60 # TODO: Make configurable
        unixTime = time.time()
        # This URL fetches the ping_rtt_median_20s time series
        url = "http://10.11.0.19:9090/api/v1/query?query=ping_rtt_median_20s%7Bjob%3D%22vino-gw-rtt%22%7D%20&time={}&_=1559937134649".format(unixTime)
        promRes = requests.get(url).json()

        if promRes['status'] == "success":
            promData = promRes['data']['result']

            # Each element in promData is a different time series (with the latest datapoint)
            # Find and rank the nodes based on the latency, lowest to highest
            nodeLatency = {} # Dict from node => number of times value = 1
            for series in promData:
                hostname = series['metric']['hostname']
                nodeLatency[hostname] = float(series['value'][1])

            sortedValues = sorted(set(nodeLatency.values())) # Eliminates duplicates
            sortedValues.reverse() # Highest value first

            sortedNodes = []
            for val in sortedValues:
                for node, lat in nodeLatency.items():
                    if val == lat:
                        sortedNodes.append(node)

            return sortedNodes

        return None


    def post(self):
        global START_TIME

        # Must have get_data() before parse_args... which somehow pops the data out...
        # Oddly, if put before and after parse_args, it shows up in both places
        data = request.get_data()
        #if False:
        if data:
            data = json.loads(data)
            currTime = time.time()

            print "\n===================="
            print "ALERT RECEIVED: %f (%s)" % (currTime, time.strftime('%Y-%m-%dT%H:%M:%S',
                                                                        time.localtime(currTime)))
            alertName = data["commonLabels"]["alertname"]
            print "Received alert from %s: %s" % (data["externalURL"], alertName)
            if data["commonAnnotations"].get("summary"):
                print "Summary: %s" % data["commonAnnotations"]["summary"]

            alertStatus = data["status"]
            print "Current status: %s" % alertStatus
            print

            #if alertName == "InterSwitchLatencyOver10ms":
            if alertName == "GuidRttOver10ms":
                if alertStatus == "firing":
                    # TODO: Remove hard-coded deployment name
                    #self.scaleOut("guids", 1)

                    #print "Switching service to h3"
                    #sshSession = paramiko.SSHClient()
                    #sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    #sshSession.connect("10.12.69.4", username = "ubuntu")

                    #command = "sudo iptables -t nat -I PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 192.168.200.13:30731"
                    #stdin, stdout, stderr = sshSession.exec_command(command)
                    pass
                elif alertStatus == "resolved":
                    #print "Switching service back to h1"
                    #sshSession = paramiko.SSHClient()
                    #sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    #sshSession.connect("10.12.69.4", username = "ubuntu")

                    #command = "sudo iptables -t nat -D PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 192.168.200.13:30731"
                    #stdin, stdout, stderr = sshSession.exec_command(command)
                    pass
                else:
                    print "ERROR: Unknown status"
            elif alertName == "GuidInstanceUnused":
                if alertStatus == "firing":
                    # TODO: Remove hard-coded deployment name
                    #self.scaleIn("guids", 1)
                    pass
                elif alertStatus == "resolved":
                    pass

            # NetSoft '20 Experiments
            elif alertName == "GuidsAvgFlows":
                if alertStatus == "firing":
                    # TODO: Remove hard-coded deployment name
                    #self.scaleOut("guids", 1)
                    pass
                elif alertStatus == "resolved":
                    pass
            elif alertName == "MininetNodeP0UnderMin":
                if alertStatus == "firing":
                    # FOR NETSOFT 20 EXPERIMENT
                    ## Adding flow to enqueue h2 to mn traffic into high priority queue
                    #sshSession = paramiko.SSHClient()
                    #sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    #sshSession.connect("10.11.69.12", username = "ubuntu")

                    #command = "sudo ovs-ofctl add-flow br0 in_port=3,ip,nw_src=192.168.200.12,nw_dst=192.168.200.69,udp,actions=enqueue:1:1"
                    #stdin, stdout, stderr = sshSession.exec_command(command)
                    pass
                elif alertStatus == "resolved":
                    # Removing flow
                    #sshSession = paramiko.SSHClient()
                    #sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    #sshSession.connect("10.11.69.12", username = "ubuntu")

                    #command = "sudo ovs-ofctl del-flows br0 in_port=3,ip,nw_src=192.168.200.12,nw_dst=192.168.200.69,udp"
                    #stdin, stdout, stderr = sshSession.exec_command(command)
                    pass

            # NOMS chain experiment
            elif alertName == "TLinProxy_to_GUID_Lat":
                if alertStatus == "firing":
                    # TODO: Remove hard-coded deployment name
                    #self.scaleOut("tlin-proxy", 1)
                    pass
                elif alertStatus == "resolved":
                    pass
                else:
                    print "ERROR: Unknown status"
            elif alertName == "TLinProxyInstanceUnused":
                if alertStatus == "firing":
                    # TODO: Remove hard-coded deployment name
                    #self.scaleIn("tlin-proxy", 1)
                    pass
                elif alertStatus == "resolved":
                    pass

            elif alertName == "H3Over10ms":
                if alertStatus == "firing":
                    # TLIN: For NOMS/ICC paper evaluation purposes
                    #elapsedTime = currTime - START_TIME

                    #NOMS_CDF_FILE = open('/home/ubuntu/icc-lat-cdf-med5-EMA-noFor.csv', 'a')
                    #NOMS_CDF_FILE.write("%s,%s\n" % (currTime, elapsedTime))
                    #NOMS_CDF_FILE.close()
                    #print "WRITING TO NOMS FILE: %s,%s\n" % (currTime, elapsedTime)

                    ## Clear qdisc
                    #sshSession = paramiko.SSHClient()
                    #sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    #sshSession.connect("192.168.200.13", username = "ubuntu")

                    #command = "sudo tc qdisc del dev vxlan_sys_4789 root netem"
                    #stdin, stdout, stderr = sshSession.exec_command(command)
                    # END TLIN
                    pass
                elif alertStatus == "resolved":
                    # TLIN: For NOMS paper evaluation purposes
                    #sshSession = paramiko.SSHClient()
                    #sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    #sshSession.connect("192.168.200.13", username = "ubuntu")

                    ## Wait up to 40 seconds before re-starting
                    #waitTime = 160 + random.randrange(20)
                    #print "Waiting up to %s to start next round" % waitTime
                    #command = "sleep %s && sudo tc qdisc add dev vxlan_sys_4789 root netem delay 10ms" % waitTime
                    #stdin, stdout, stderr = sshSession.exec_command(command)

                    #START_TIME = time.time() + waitTime
                    # END TLIN
                    pass
                else:
                    print "ERROR: Unknown status"

            elif alertName == "GuidBWUnderMin":
                if alertStatus == "firing":
                    # TLIN: For NOMS paper evaluation purposes
                    #elapsedTime = currTime - START_TIME
                    #NOMS_CDF_FILE = open('/home/ubuntu/cnsm19/noms-bw-cdf.csv', 'a')
                    #NOMS_CDF_FILE.write("%s,%s\n" % (currTime, elapsedTime))
                    #NOMS_CDF_FILE.close()
                    #print "WRITING TO NOMS BW FILE: %s,%s\n" % (currTime, elapsedTime)
                    # END TLIN

                    # TLIN: For commag (NOMS extension)
                    #self.scaleOut("guids", 1)

                    #sshSession = paramiko.SSHClient()
                    #sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    #sshSession.connect("10.4.69.4", username = "ubuntu")
                    #command = "sudo ovs-ofctl add-flow br1 ip,nw_dst=100.200.1.36,udp,tp_dst=9000,actions=enqueue:2:1"
                    #stdin, stdout, stderr = sshSession.exec_command(command)
                    # END TLIN
                    pass
                elif alertStatus == "resolved":
                    # TLIN: For NOMS paper evaluation purposes
                    # Wait at least 3 minutes between restarts
                    #nextStartTime = START_TIME + 190
                    #if currTime >= nextStartTime:
                    #    waitTime = random.randrange(20)
                    #else:
                    #    waitTime = nextStartTime - currTime + random.randrange(20)

                    #print "Waiting %s seconds until next start" % waitTime

                    #cmdLine = "sleep %s && iperf3 -c 192.168.200.12 -t 120 -u -b 300M >/dev/null &" % waitTime
                    #p = Popen(cmdLine, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)

                    #START_TIME = time.time() + waitTime # Overwrite START_TIME here as Popen() may have latencies
                    # END TLIN

                    # TLIN: For commag (NOMS extension)
                    #sshSession = paramiko.SSHClient()
                    #sshSession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    #sshSession.connect("10.4.69.4", username = "ubuntu")
                    #command = "sudo ovs-ofctl del-flows br1 ip,nw_dst=100.200.1.36,udp,tp_dst=9000"
                    #stdin, stdout, stderr = sshSession.exec_command(command)
                    # END TLIN
                    pass
                else:
                    print "ERROR: Unknown status"

            print "data type is: %s" % type(data)
            print "received data is...\n%s\n" % request.get_data()
            print "\n====================\n"

        #args = parser.parse_args()
        #print "received args are...\n%s\n" % args
        #print "received data is...\n%s\n" % request.get_data()
        return "You called POST!"

#rest_api.add_resource(VNetList, '/vnets')
#rest_api.add_resource(VNetInstance, '/vnets/<string:id>')
#rest_api.add_resource(VNetVMList, '/vnets/<string:vnetid>/vms')
#rest_api.add_resource(VNetVMInstance, '/vnets/<string:vnetid>/vms/<string:id>')
#rest_api.add_resource(ServiceList, '/services')
#rest_api.add_resource(ServiceInstance, '/services/<string:id>')
#rest_api.add_resource(ServiceInstanceVMList,
#                      '/services/<string:serviceid>/vms')
#rest_api.add_resource(ServiceInstanceVM,
#                      '/services/<string:serviceid>/vms/<string:id>')
#rest_api.add_resource(VMInstance, '/vms/<string:id>')
#rest_api.add_resource(VIFaceStats, '/ifaces/<string:id>')
#rest_api.add_resource(PolicyResources, '/policies')
#rest_api.add_resource(ScaleService,
#    '/scaleservice/<string:serviceid>/<string:scalenum>') # UUID for serviceid
#rest_api.add_resource(CreateService,
#    '/createservice/<string:service_name>') #service_name currently a placeholder
#rest_api.add_resource(DeleteService,
#    '/deleteservice/<string:serviceid>') # UUID for serviceid
#rest_api.add_resource(ServiceInstanceVMListUUID,
#    '/services/<string:serviceid>/vm_list') # UUID for serviceid
#rest_api.add_resource(ChainService,                          # UUID for serviceid
#    '/services/<string:serviceid>/policy/<string:policyid>') # policyid currently a placeholder
rest_api.add_resource(AlertHandler, '/promalert')

