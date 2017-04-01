# -*- coding: utf-8 -*-

from collections import OrderedDict

from flask import request, Blueprint, abort

from widukind_api import queries
from widukind_common.flask_utils import json_tools

bp = Blueprint('json', __name__)

#---/providers

@bp.route('/providers', endpoint="providers-list")
def providers_list():
    query = {"enable": True}
    projection = {"_id": False, "lock": False, "metadata": False,
                  "enable": False, "version": False}
    docs = [doc for doc in queries.col_providers().find(query, projection)]
    return json_tools.json_response(docs)

#---/providers/keys

@bp.route('/providers/keys', endpoint="providers-list-keys")
def providers_list_keys():
    docs = queries.col_providers().distinct("slug", filter={"enable": True})
    return json_tools.json_response(docs)

"""
#---/categories/<provider>

@bp.route('/categories/<provider>', endpoint="categories")
def categories_view(provider):
    provider_doc = queries.get_provider(provider)
    docs = queries.col_categories().find({"provider_name": provider_doc["name"],
                                          "enable": True},
                                         {"_id": False})
    return json_tools.json_response(docs)
"""

#---/providers/<provider>

@bp.route('/providers/<provider>', endpoint="providers-unit")
def providers_unit(provider):
    projection = {"_id": False, "lock": False, "metadata": False,
                  "enable": False, "version": False}
    provider_doc = queries.get_provider(provider, projection=projection)
    return json_tools.json_response(provider_doc)

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

    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    if per_page > 50:
        per_page = 50
    pagination = queries.Pagination(docs, page, per_page)
    meta = {
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "total": pagination.total,
    }
    _docs = [doc for doc in pagination.items]
    #return json_tools.json_response(_docs, meta=meta)
    return json_tools.json_response_async(_docs, meta=meta)

#---/providers/<provider>/datasets/keys

@bp.route('/providers/<provider>/datasets/keys', endpoint="providers-datasets-list-keys")
def datasets_list_keys(provider):
    provider_doc = queries.get_provider(provider)
    query = {'provider_name': provider_doc["name"]}
    docs = queries.col_datasets().distinct("slug", filter=query)
    return json_tools.json_response(docs)

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

    docs = queries.col_series().find(query, projection)

    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)
    if per_page > 100:
        per_page = 100
    pagination = queries.Pagination(docs, page, per_page)
    meta = {
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "total": pagination.total,
    }
    _docs = [doc for doc in pagination.items]
    return json_tools.json_response(_docs, meta=meta)

"""
@bp.route('/category/<slug>', endpoint="category")
def category_view(slug):
    doc = queries.col_categories().find_one({"slug": slug,
                                          "enable": True})
    if not doc:
        abort(404)
    return json_tools.json_response(doc)
"""

#---/dataset/<dataset>

@bp.route('/dataset/<dataset>')
@bp.route('/datasets/<dataset>', endpoint="datasets-unit")
def dataset_unit(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False,
                  "enable": False, "lock": False, "tags": False}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_tools.json_response(doc)

#---/dataset/<dataset>/frequencies

@bp.route('/dataset/<dataset>/frequencies')
@bp.route('/datasets/<dataset>/frequencies', endpoint="datasets-unit-frequencies")
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
    return json_tools.json_response(docs)

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
        "start_date": True, "end_date": True,
        "dimensions": True, "attributes": True,
        "values.value": True, "values.period": True,
    }

    query = queries.complex_queries_series(query)
    docs = queries.col_series().find(query, projection)

    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=50, type=int)
    if per_page > 1000:
        per_page = 1000
    pagination = queries.Pagination(docs, page, per_page)
    meta = {
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "total": pagination.total,
    }
    _docs = [doc for doc in pagination.items]
    return json_tools.json_response_async(_docs, meta=meta)


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
    return json_tools.json_response(dimensions)

#---/datasets/<dataset>/dimensions/keys

@bp.route('/datasets/<dataset>/dimensions/keys', endpoint="datasets-dimensions-keys")
def datasets_dimensions_keys(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "dimension_keys": True }
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_tools.json_response(doc["dimension_keys"])

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
    return json_tools.json_response(attributes)

#---/datasets/<dataset>/attributes/keys

@bp.route('/datasets/<dataset>/attributes/keys', endpoint="datasets-attributes-keys")
def datasets_attributes_keys(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "attribute_keys": True}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_tools.json_response(doc.get("attribute_keys"))



#---/datasets/<dataset>/codelists

@bp.route('/datasets/<dataset>/codelists', endpoint="datasets-codelists")
def datasets_codelists(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "codelists": True}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_tools.json_response(doc["codelists"])

#---/series/<series>

def series_unit(series):
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

    return json_tools.json_response(doc)

def series_multi(series):
    query = {'slug': {"$in": series.split("+")}}
    projection = {"_id": False}
    docs = [doc for doc in queries.col_series().find(query, projection)]
    return json_tools.json_response(docs)

@bp.route('/series/<series>', endpoint="series-unit")
def series_view(series):
    if "+" in series:
        return series_multi(series)
    else:
        return series_unit(series)

