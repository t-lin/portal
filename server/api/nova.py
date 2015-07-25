from __future__ import absolute_import
from flask_restful import Resource, current_app, fields, marshal_with
from . import rest_api
from novaclient import client

NOVA_FIELDS = {
    "id": fields.String(attribute="id"),
    "name": fields.String(attribute="name")
}


class NovaResources(Resource):
    @marshal_with(NOVA_FIELDS)
    def get(self):
        OS_USERNAME = current_app.config["OS_USERNAME"]
        OS_PASSWORD = current_app.config["OS_PASSWORD"]
        OS_TENANT_NAME = current_app.config["OS_TENANT_NAME"]
        AUTH_URL = current_app.config["OS_AUTH_URL"]
        nova = client.Client(2, OS_USERNAME,
                             OS_PASSWORD,
                             OS_TENANT_NAME,
                             auth_url=AUTH_URL)
        return nova.servers.list()

rest_api.add_resource(NovaResources, '/nova')
