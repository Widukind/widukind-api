# -*- coding: utf-8 -*-

from flask import Blueprint, abort, current_app as app

from bson import json_util

from widukind_api import queries

def json_response(value_str):
    return app.response_class(value_str, mimetype='application/json')

bp = Blueprint('r', __name__)

@bp.route('/series/<slug>', endpoint="series")
def series_view(slug):
    query = {'slug': slug}
    projection = {"_id": False, "tags": False}
    doc = queries.col_series().find_one(query, projection)
    if not doc:
        abort(404)
    
    query = {'enable': True, 
             "provider_name": doc["provider_name"], 
             'dataset_code': doc["dataset_code"]}
    projection = {"_id": False, "enable": True}
    dataset_doc = queries.col_datasets().find_one(query, projection)
    if not dataset_doc:
        abort(404)

    values = [v["value"] for v in doc["values"]]
    doc["values"] = values
    
    return json_response(json_util.dumps([doc], default=json_util.default))

