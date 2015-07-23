from __future__ import absolute_import
from flask import Blueprint, current_app
from flask_restful import Api

api = Blueprint('api', __name__)

rest_api = Api(api)
