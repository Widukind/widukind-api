# -*- coding: utf-8 -*-

import time
from collections import OrderedDict

from flask import request, Blueprint, abort, render_template, current_app
from flask import make_response

import pandas

from widukind_api import queries
from widukind_common.flask_utils import json_tools
from widukind_common.tasks.export_files import generate_filename

bp = Blueprint('html', __name__, template_folder='templates')
eviews_bp = Blueprint('eviews', __name__, template_folder='templates')

def _dataset_series_list(series_list, frequency, separator='dot'):
    
    dmin = float('inf')
    dmax = -float('inf')
    
    for s in series_list:
        if s['start_date'] < dmin:
            dmin = s['start_date']
        if s['end_date'] > dmax:
            dmax = s['end_date']
        
    series_list.rewind()

    pDmin = pandas.Period(ordinal=dmin, freq=frequency);
    pDmax = pandas.Period(ordinal=dmax, freq=frequency);
    dates = list(pandas.period_range(pDmin, pDmax, freq=frequency).to_native_types())
    
    series_keys = []
    series_names = []
    
    def row_process(s):
        row = []
        series_keys.append(s['key'])
        series_names.append(s['name'])
        
        p_start_date = pandas.Period(ordinal=s['start_date'], freq=frequency)        
        p_end_date = pandas.Period(ordinal=s['end_date'], freq=frequency)

        # Les None sont pour les périodes qui n'ont pas de valeur correspondantes
        _row = ["" for d in pandas.period_range(pDmin, p_start_date-1, freq=frequency)]
        row.extend(_row)
        
        if separator == 'comma':
            _row = [val["value"].replace(".", ",") for val in s['values']]
        else:
            _row = [val["value"] for val in s['values']]
            
        row.extend(_row)

        _row = ["" for d in pandas.period_range(p_end_date+1, pDmax, freq=frequency)]
        row.extend(_row)
        
        return row         

    values = [row_process(s) for s in series_list]

    return dates, series_keys, series_names, values

def _dataset_values(provider_name=None, dataset_code=None, 
                    frequency=None, 
                    separator='dot'):

    query = {}
    query['provider_name'] = provider_name
    query['dataset_code'] = dataset_code

    _format = request.args.get('format', default='html')

    limit = request.args.get('limit', default=0, type=int)
    
    query['frequency'] = frequency

    separator = request.args.get('separator', default=separator)
    if not separator in ['dot', 'comma']:
        abort(400, "separator [%s] not supported. valid separator[dot, comma]" % separator)
    
    query = queries.complex_queries_series(query, 
                                   search_attributes=False, 
                                   bypass_args=['limit', 'tags', 'provider', 'dataset', 'frequency', 'separator', 'format'])    
    
    start = time.time()
    
    cursor = queries.col_series().find(query)
    
    max_limit = current_app.config.get("WIDUKIND_DISPLAY_LIMIT", 1000)
    
    if limit:
        cursor = cursor.limit(limit)
    else:
        if cursor.count() > max_limit:
            abort(400, "The number of result exceeds the allowed limit [%s]. You must use the limit parameter in the query." % max_limit)

    if cursor.count() == 0:
        dates, series_keys, series_names, values = [], [], [], []
        abort(400, "no data found")
    else:
        dates, series_keys, series_names, values = _dataset_series_list(cursor, frequency, separator=separator)
    
    context = {
        "dates": dates,
        "series_keys": series_keys, 
        "series_names": series_names, 
        "values": values           
    }
    
    end = time.time() - start
    msg = "eviews-series - provider[%s] - dataset[%s] - frequency[%s] - limit[%s] - duration[%.3f]"
    current_app.logger.info(msg % (provider_name, dataset_code, frequency, limit, end))
    
    response_str = render_template("html/values.html", **context)
    
    """
    TODO: use lang browser pour choix separator ?
    TODO: header lang ?
    """
    
    EXTENSIONS_MAP = {
        "excel": ("xls", "application/vnd.ms-excel"),
        "xls": ("xls", "application/vnd.ms-excel"),
        "xlsx": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        "calc": ("ods", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    }
    
    if _format and _format in EXTENSIONS_MAP:
        response = make_response(response_str)

        _ext = EXTENSIONS_MAP[_format][0]
        content_type = EXTENSIONS_MAP[_format][1]
        
        filename = generate_filename(provider_name=provider_name, 
                                     dataset_code=dataset_code, 
                                     #key=key,
                                     #slug=slug, 
                                     prefix="series-list")

        filename = "%s.%s" % (filename, _ext)
        response.headers['Content-Type'] = content_type
        response.headers["Content-disposition"] = "attachment; filename=%s" % filename
        #response.content_length = fileobj.length
        #TODO: response.last_modified = fileobj.upload_date
        #TODO: response.set_etag(fileobj.md5)
        response.make_conditional(request)
        return response
    
    return response_str


#---/providers

@bp.route('/providers', endpoint="providers-list")
def providers_list():
    query = {"enable": True}
    projection = {"_id": False}
    docs = [doc for doc in queries.col_providers().find(query, projection)]
    return render_template("html/generic-list.html", 
                           docs=docs, 
                           fields=[("long_name", "Name"), 
                                   ("region", "Region"), 
                                   ("website", "Web Site")])

#---/providers/keys

#TODO: @bp.route('/providers/keys', endpoint="providers-list-keys")
def providers_list_keys():
    docs = queries.col_providers().distinct("slug", filter={"enable": True})
    return json_tools.json_response(docs)

"""
#---/categories/<provider>

#TODO: @bp.route('/categories/<provider>', endpoint="categories")
def categories_view(provider):
    provider_doc = queries.get_provider(provider)
    docs = queries.col_categories().find({"provider_name": provider_doc["name"],
                                          "enable": True},
                                         {"_id": False})
    return json_tools.json_response(docs)
"""    

#---/providers/<provider>

#TODO: @bp.route('/providers/<provider>', endpoint="providers-unit")
def providers_unit(provider):
    provider_doc = queries.get_provider(provider)
    return json_tools.json_response(provider_doc)

#---/providers/<provider>/datasets

#TODO: @bp.route('/providers/<provider>/datasets', endpoint="providers-datasets-list")
def providers_datasets_list(provider):
    provider_doc = queries.get_provider(provider)
    query = {'provider_name': provider_doc["name"]}
    projection = {"_id": False, "tags": False,
                  "enable": False, "lock": False,
                  "concepts": False, "codelists": False}
    #docs = [doc for doc in queries.col_datasets().find(query, projection)]
    docs = [doc for doc in queries.col_datasets().find(query, projection)]
    return json_tools.json_response(docs)

#---/providers/<provider>/datasets/keys

#TODO: @bp.route('/providers/<provider>/datasets/keys', endpoint="providers-datasets-list-keys")
def datasets_list_keys(provider):
    provider_doc = queries.get_provider(provider)
    query = {'provider_name': provider_doc["name"]}
    docs = queries.col_datasets().distinct("slug", filter=query)
    return json_tools.json_response(docs)

#---/datasets/<dataset>/series

#TODO: @bp.route('/datasets/<dataset>/series', endpoint="datasets-series-list")
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
    
    _docs = [doc for doc in docs]
    
    return json_tools.json_response(_docs)

"""
#TODO: @bp.route('/category/<slug>', endpoint="category")
def category_view(slug):
    doc = queries.col_categories().find_one({"slug": slug,
                                          "enable": True})
    if not doc:
        abort(404)
    return json_tools.json_response(doc)
"""    

#---/dataset/<dataset>

#TODO: @bp.route('/dataset/<dataset>', endpoint="datasets-unit")
def dataset_unit(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, 
                  "enable": False, "lock": False, "tags": False}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_tools.json_response(doc)

#---/dataset/<dataset>/frequencies

#TODO: @bp.route('/dataset/<dataset>/frequencies', endpoint="datasets-unit-frequencies")
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

@bp.route('/datasets/<dataset>/<frequency>/values', endpoint="datasets-series-list-values")
@bp.route('/datasets/<dataset>/values')
@eviews_bp.route('/values/<dataset>')
@eviews_bp.route('/values/<dataset>/<frequency>', endpoint="datasets-series-list-values")
def dataset_series_list_values(dataset, frequency=None):

    query = {"slug": dataset}
    projection = {"_id": False, 
                  "provider_name": True, "dataset_code": True,
                  "metadata.frequencies": True, 
                  "enable": True}
    dataset = queries.col_datasets().find_one(query, projection)
    if not dataset:
        abort(404, "dataset %s not found or disable." % dataset)

    if not frequency:
        frequency = request.args.get('frequency')
    if not frequency:
        abort(400, "frequency field is required.")
    
    frequencies = dataset.get("metadata", {}).get("frequencies", [])
    if frequencies and not frequency in frequencies:
        abort(404, "Frequencies available: %s" % frequencies)  
    
    return _dataset_values(dataset["provider_name"], 
                                  dataset["dataset_code"],
                                  frequency=frequency)

@bp.route('/datasets/<provider>/<dataset_code>/<frequency>/values', endpoint="datasets-series-list-values-by-dataset-code")
@bp.route('/datasets/<provider>/<dataset_code>/values')
@eviews_bp.route('/<provider>/dataset/<dataset_code>/values')
@eviews_bp.route('/<provider>/dataset/<dataset_code>/<frequency>/values')
def dataset_series_list_values_by_dataset_code(provider=None, dataset_code=None, frequency=None):
    query = {"provider_name": provider, "dataset_code": dataset_code}
    projection = {"_id": False, 
                  "provider_name": True, "dataset_code": True,
                  "metadata.frequencies": True, 
                  "enable": True}
    dataset = queries.col_datasets().find_one(query, projection)
    if not dataset:
        abort(404, "dataset %s/%s not found or disable." % (provider, dataset_code))

    if not frequency:
        frequency = request.args.get('frequency')
    if not frequency:
        abort(400, "frequency field is required.")

    frequencies = dataset.get("metadata", {}).get("frequencies", [])
    if frequencies and not frequency in frequencies:
        abort(404, "Frequencies available: %s" % frequencies)  

    return _dataset_values(provider, dataset_code, frequency=frequency)


"""
Liste dataset_code ou slug des datasets d'un provider
Liste value d'une dimension
Liste des series.key ou series.slug d'un dataset
Liste des dimensions key d'un dataset 
Liste des dimensions key / values d'un dataset
"""

#---/datasets/<dataset>/dimensions

#TODO: @bp.route('/datasets/<dataset>/dimensions', endpoint="datasets-dimensions-list")
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

#TODO: @bp.route('/datasets/<dataset>/dimensions/keys', endpoint="datasets-dimensions-keys")
def datasets_dimensions_keys(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "dimension_keys": True }
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_tools.json_response(doc["dimension_keys"])

#---/datasets/<dataset>/attributes

#TODO: @bp.route('/datasets/<dataset>/attributes', endpoint="datasets-attributes-list")
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

#TODO: @bp.route('/datasets/<dataset>/attributes/keys', endpoint="datasets-attributes-keys")
def datasets_attributes_keys(dataset):
    query = {'enable': True, 'slug': dataset}
    projection = {"_id": False, "attribute_keys": True}
    doc = queries.col_datasets().find_one(query, projection)
    if not doc:
        abort(404)
    return json_tools.json_response(doc.get("attribute_keys"))



#---/datasets/<dataset>/codelists

#TODO: @bp.route('/datasets/<dataset>/codelists', endpoint="datasets-codelists")
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

#TODO: @bp.route('/series/<series>', endpoint="series-unit")
def series_view(series):
    if "+" in series:
        return series_multi(series)
    else:
        return series_unit(series)

