from __future__ import absolute_import
from flask_restful import Resource, current_app
from . import rest_api
import requests
import json


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
        print payload
        print current_app.config["OS_AUTH_URL"]
        res = requests.post(current_app.config["OS_AUTH_URL"] + "/tokens", json=payload)
        return res.json()

rest_api.add_resource(NovaResources, '/nova')
