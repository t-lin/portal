from __future__ import absolute_import
from flask_restful import Resource, current_app, fields, marshal_with
from . import rest_api

NOVA_FIELDS = {
    "id": fields.String(attribute="id"),
    "name": fields.String(attribute="name")
}


class NovaResources(Resource):
    @marshal_with(NOVA_FIELDS)
    def get(self):
        return current_app.nova.servers.list()

rest_api.add_resource(NovaResources, '/nova/servers')
