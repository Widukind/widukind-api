# -*- coding: utf-8 -*-

from datetime import datetime
import re
from pprint import pprint
from collections import OrderedDict

from flask import current_app as app
from flask import request, Blueprint, url_for, abort
import arrow
from bson import json_util
from bson import ObjectId
from json import dumps

from widukind_api import queries

bp = Blueprint('json', __name__)

def json_convert(obj):

    if isinstance(obj, ObjectId):
        return str(obj)
    
    elif isinstance(obj, datetime):
        #'2015-11-16T23:38:04.551214+00:00'
        return arrow.get(obj).for_json()

    return json_util.default(obj)

#def json_response(value_str):
#    return app.response_class(value_str, mimetype='application/json')

def json_response(obj, meta={}):
    indent = None
    if request.is_xhr:
        indent = 4
    context = {"meta": meta, "data": obj}
    value_str = json_util.dumps(context, default=json_convert, indent=indent)
    return app.response_class(value_str, mimetype='application/json')

#---/providers

@bp.route('/providers', endpoint="providers-list")
def providers_list():
    query = {"enable": True}
    projection = {"_id": False}
    docs = queries.col_providers().find(query, projection)
    return json_response(docs)

#---/providers/keys

@bp.route('/providers/keys', endpoint="providers-list-keys")
def providers_list_keys():
    docs = queries.col_providers().distinct("slug", filter={"enable": True})
    return json_response(docs)

"""
#---/categories/<provider>

@bp.route('/categories/<provider>', endpoint="categories")
def categories_view(provider):
    provider_doc = queries.get_provider(provider)
    docs = queries.col_categories().find({"provider_name": provider_doc["name"],
                                          "enable": True},
                                         {"_id": False})
    return json_response(docs)
"""    

#---/providers/<provider>

@bp.route('/providers/<provider>', endpoint="providers-unit")
def providers_unit(provider):
    provider_doc = queries.get_provider(provider)
    return json_response(provider_doc)

#---/providers/<provider>/datasets

@bp.route('/providers/<provider>/datasets', endpoint="providers-datasets-list")
def providers_datasets_list(provider):
    provider_doc = queries.get_provider(provider)
    query = {'provider_name': provider_doc["name"]}
    projection = {"_id": False, "tags": False,
                  "enable": False, "lock": False,
                  "concepts": False, "codelists": False}
    #docs = [doc for doc in queries.col_datasets().find(query, projection)]
    docs = queries.col_datasets().find(query, projection)
    return json_response(docs)

#---/providers/<provider>/datasets/keys

@bp.route('/providers/<provider>/datasets/keys', endpoint="providers-datasets-list-keys")
def datasets_list_keys(provider):
    provider_doc = queries.get_provider(provider)
    query = {'provider_name': provider_doc["name"]}
    docs = queries.col_datasets().distinct("slug", filter=query)
    return json_response(docs)

#---/datasets/<dataset>/series

@bp.route('/datasets/<dataset>/series', endpoint="datasets-series-list")
def datasets_series_list(dataset):
    """Return all series for one dataset
    """
    
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "values": False}
    dataset_doc = queries.col_datasets().find_one(query, projection)
    if not dataset_doc:
        abort(404)

    query = {'provider_name': dataset_doc['provider_name'], 
             'dataset_code': dataset_doc["dataset_code"]}
    projection = {"_id": False, "values": False}
    
    query = queries.complex_queries_series(query)

    limit = request.args.get('limit', default=1000, type=int)
    
    docs = queries.col_series().find(query, projection)

    if limit:
        docs= docs.limit(limit)
    
    return json_response(docs)

"""
@bp.route('/category/<slug>', endpoint="category")
def category_view(slug):
    doc = queries.col_categories().find_one({"slug": slug,
                                          "enable": True})
    if not doc:
        abort(404)
    return json_response(doc)
"""    

#---/dataset/<dataset>

@bp.route('/dataset/<dataset>', endpoint="datasets-unit")
def dataset_unit(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, 
                  "enable": False, "lock": False, "tags": False}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_response(doc)

#---/dataset/<dataset>/frequencies

@bp.route('/dataset/<dataset>/frequencies', endpoint="datasets-unit-frequencies")
def dataset_unit_frequencies(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, 
                  "enable": False, "lock": False, "tags": False}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    
    query = {"provider_name": doc["provider_name"],
             "dataset_code": doc["dataset_code"]}
    
    docs = queries.col_series().distinct("frequency", filter=query)
    return json_response(docs)

#---/datasets/<dataset>/values

@bp.route('/datasets/<dataset>/values', endpoint="datasets-series-list-values")
def dataset_series_list_values(dataset):

    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "provider_name": True, "dataset_code": True }
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
        
    query = {"provider_name": doc["provider_name"], 
             'dataset_code': doc["dataset_code"]}
    projection = {
        "_id": False, 
        "key": True, "slug": True, 
        "name": True, "frequency": True,
        "values.value": True, "values.period": True,
    }

    query = queries.complex_queries_series(query)

    limit = request.args.get('limit', default=1000, type=int)
    
    docs = queries.col_series().find(query, projection)
    if limit:
        docs = docs.limit(limit)

    return json_response(docs)

    """
    indent = None
    if request.is_xhr:
        indent = 4

    def generate():
        yield "["
        for i, row in enumerate(cursor):
            yield json_util.dumps(row, default=json_convert, indent=indent)
            if i < count:
                yield ","
        yield "]"

    return app.response_class(generate(), mimetype='application/json')
    """
                    

"""
Liste dataset_code ou slug des datasets d'un provider
Liste value d'une dimension
Liste des series.key ou series.slug d'un dataset
Liste des dimensions key d'un dataset 
Liste des dimensions key / values d'un dataset
"""

#---/datasets/<dataset>/dimensions

@bp.route('/datasets/<dataset>/dimensions', endpoint="datasets-dimensions-list")
def datasets_dimensions_list(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "dimension_keys": True, "codelists": True}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    dimensions = OrderedDict()
    for key in doc["dimension_keys"]:
        dimensions[key] = doc["codelists"].get(key, {})
    return json_response(dimensions)

#---/datasets/<dataset>/dimensions/keys

@bp.route('/datasets/<dataset>/dimensions/keys', endpoint="datasets-dimensions-keys")
def datasets_dimensions_keys(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "dimension_keys": True }
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_response(doc["dimension_keys"])

#---/datasets/<dataset>/attributes

@bp.route('/datasets/<dataset>/attributes', endpoint="datasets-attributes-list")
def datasets_attributes_list(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "attribute_keys": True, "codelists": True}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    attributes = OrderedDict()
    for key in doc.get("attribute_keys"):
        attributes[key] = doc["codelists"].get(key, {})
    return json_response(attributes)

#---/datasets/<dataset>/attributes/keys

@bp.route('/datasets/<dataset>/attributes/keys', endpoint="datasets-attributes-keys")
def datasets_attributes_keys(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "attribute_keys": True}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_response(doc.get("attribute_keys"))



#---/datasets/<dataset>/codelists

@bp.route('/datasets/<dataset>/codelists', endpoint="datasets-codelists")
def datasets_codelists(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "codelists": True}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_response(doc["codelists"])

#---/series/<series>

@bp.route('/series/<series>', endpoint="series-unit")
def series_unit(series, only_values=False):
    query = {'slug': series}
    projection = {"_id": False}
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
    
    return json_response(doc)

"""
@bp.route('/series/<slug>/values', endpoint="series-values")
def series_values_view(slug):
    query = {'slug': slug}
    projection = {
        "_id": False, "key": True, "slug": True,  
        "values.value": True, "values.period": True,
        "provider_name": True, 'dataset_code': True
    }
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
        
    return json_response(doc)
"""

