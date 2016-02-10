
from flask import current_app as app
from flask import request, Blueprint, url_for, abort

from bson import json_util

from widukind_api import queries

bp = Blueprint('json', __name__)

def json_response(value_str):
    return app.response_class(value_str, mimetype='application/json')

@bp.route('/providers', endpoint="providers")
def get_providers():
    query = {"enable": True}
    projection = {"_id": False}
    docs = queries.col_providers().find(query, projection)
    return json_response(json_util.dumps(docs, default=json_util.default))

#---LIST

@bp.route('/categories/<provider>', endpoint="categories")
def categories_view(provider):
    provider_doc = queries.get_provider(provider)
    docs = queries.col_categories().find({"provider_name": provider_doc["name"],
                                          "enable": True},
                                         {"_id": False})
    return json_response(json_util.dumps(docs, default=json_util.default))

@bp.route('/datasets/<provider>', endpoint="datasets")
def datasets_view(provider):
    provider_doc = queries.get_provider(provider)
    query = {'provider_name': provider_doc["name"]}
    projection = {"_id": False, "tags": False,
                  "enable": False, "lock": False,
                  "dimension_list": False, "attribute_list": False,
                  "concepts": False, "codelists": False}
    docs = queries.col_datasets().find(query, projection)
    return json_response(json_util.dumps(docs, default=json_util.default))

@bp.route('/series-list/<dataset>', endpoint="series-list")
def series_list_view(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "values": False, "tags": False}
    dataset_doc = queries.col_datasets().find_one(query, projection)
    if not dataset_doc:
        abort(404)

    query = {'provider_name': dataset_doc['provider_name'], 'dataset_code': dataset_doc["dataset_code"]}
    projection = {"_id": False, "tags": False, "values": False}
    docs = queries.col_series().find(query, projection)
    return json_response(json_util.dumps(docs, default=json_util.default))

#---ONE

@bp.route('/provider/<slug>', endpoint="provider")
def provider_view(slug):
    provider_doc = queries.get_provider(slug)
    return json_response(json_util.dumps(provider_doc, default=json_util.default))

@bp.route('/category/<slug>', endpoint="category")
def category_view(slug):
    doc = queries.col_categories().find_one({"slug": slug,
                                          "enable": True})
    if not doc:
        abort(404)
    return json_response(json_util.dumps(doc, default=json_util.default))

@bp.route('/dataset/<slug>', endpoint="dataset")
def dataset_view(slug):
    query = {'enable': True, 'slug': slug}
    projection = {"_id": False, 
                  "enable": False, "lock": False, "tags": False,
                  "dimension_list": False, "attribute_list": False}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_response(json_util.dumps(doc, default=json_util.default))

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
    
    return json_response(json_util.dumps(doc, default=json_util.default))

#---SPECIALS

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
        
    return json_response(json_util.dumps(doc, default=json_util.default))

@bp.route('/dataset/<slug>/values', endpoint="dataset-values")
def dataset_values_view(slug):

    query = {'enable': True, 'slug': slug}
    projection = {"_id": False, "provider_name": True, "dataset_code": True }
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)

    #TODO: rendre obligatoire frequency

    query = {"provider_name": doc["provider_name"], 
             'dataset_code': doc["dataset_code"]}
    projection = {
        "_id": False, "key": True, "slug": True,
        "frequency": True,
        "values.value": True, "values.period": True,
    }

    #TODO: multiple value in dimension    
    limit = request.args.get('limit', default=0, type=int)
    
    for r in request.args.lists():
        if r[0] == 'limit':
            pass
        elif r[0] == 'frequency':
            query['frequency'] = r[1][0]
        else:
            #TODO: case regex
            query['dimensions.'+r[0]] = {'$regex': r[1][0]}
    
    #/api/v1/dataset/bis-pp-ls/values?Reference%20area=FR&Reference%20area=AU
    #query :  {'provider_name': 'BIS', 'dataset_code': 'PP-LS', 'dimensions.Reference area': {'$regex': 'FR'}}    
    
    docs = queries.col_series().find(query, projection).limit(limit)
    #TODO: Period + Value
    count = docs.count() -1
    
    print("dataset-values - query[%s] - result[%s]" % (query, count))

    def generate():
        yield "["
        for i, row in enumerate(docs):
            yield json_util.dumps(row, default=json_util.default)
            if i < count:
                yield ","
        yield "]"

    return app.response_class(generate(), mimetype='application/json')
                    
#---STRUCTURE

"""
Liste dataset_code ou slug des datasets d'un provider
Liste value d'une dimension
Liste des series.key ou series.slug d'un dataset
Liste des dimensions key d'un dataset 
Liste des dimensions key / values d'un dataset
"""

@bp.route('/dataset/<slug>/dimensions', endpoint="dataset-dimensions-key")
def dataset_dimensions_key_view(slug):
    query = {'enable': True, 'slug': slug}
    projection = {"_id": False, "dimension_keys": True }
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_response(json_util.dumps(doc["dimension_keys"], default=json_util.default))

