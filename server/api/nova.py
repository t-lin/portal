from __future__ import absolute_import
from flask_restful import Resource, current_app
from . import rest_api
import requests

NOVA_PORT = ":8774/v2"
AUTH_PORT = ":5000/v2.0"


class NovaResources(Resource):
    def get(self):
        payload = {
            "auth": {
                "tenantName": current_app.config["OS_TENANT_NAME"],
                "passwordCredentials": {
                    "username": current_app.config["OS_USERNAME"],
                    "password": current_app.config["OS_PASSWORD"]
                }
            }
        }
        AUTH_URL = "%s%s/tokens" % (current_app.config["OS_SERVER"], AUTH_PORT)
        NOVA_URL = "%s%s" % (current_app.config["OS_SERVER"], NOVA_PORT)

        res = requests.post(AUTH_URL, json=payload)
        auth_res = res.json()
        token = auth_res["access"]["token"]["id"]
        tenant_id = auth_res["access"]["token"]["tenant"]["id"]
        nova_url = "%s/%s/%s" % (NOVA_URL, tenant_id, "servers")
        res = requests.get(nova_url,
                           headers={'Content-Type': 'application/json',
                                    'X-Auth-Token': token})
        return res.json()

rest_api.add_resource(NovaResources, '/nova')
