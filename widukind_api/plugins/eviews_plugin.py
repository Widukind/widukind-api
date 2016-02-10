# -*- coding: utf-8 -*-

import time
from flask import Blueprint, current_app, request, render_template, abort

import pandas

from widukind_api import queries

bp = Blueprint('eviews', __name__)

def dataset_series_list(series_list, frequency=None):
    
    dmin = float('inf')
    dmax = -float('inf')
    
    for s in series_list:
        if s['start_date'] < dmin:
            dmin = s['start_date']
        if s['end_date'] > dmax:
            dmax = s['end_date']
        if not frequency:
            frequency = s['frequency']
        
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
        
        _row = [val["value"] for val in s['values']]
        row.extend(_row)

        _row = ["" for d in pandas.period_range(p_end_date+1, pDmax, freq=frequency)]
        row.extend(_row)
        
        return row         

    values = [row_process(s) for s in series_list]

    return dates, series_keys, series_names, values

def _EVIEWS_dataset_values(provider_name=None, dataset_code=None):


    #TODO: use dataset slug    
    #TODO: dataset enable
    #TODO: required frequency

    query = {}
    query['provider_name'] = provider_name
    query['dataset_code'] = dataset_code

    limit = request.args.get('limit', default=0, type=int)
    
    for r in request.args.lists():
        if r[0] == 'limit':
            pass
        elif r[0] == 'frequency':
            query['frequency'] = r[1][0]
        else:
            query['dimensions.'+r[0]] = {'$regex': r[1][0]}

    start = time.time()
    
    cursor = queries.col_series().find(query).limit(limit)

    if cursor.count() == 0:
        dates, series_keys, series_names, values = [], [], [], []
    else:
        dates, series_keys, series_names, values = dataset_series_list(cursor)
    
    context = {
        "dates": dates,
        "series_keys": series_keys, 
        "series_names": series_names, 
        "values": values           
    }
    
    end = time.time() - start
    msg = "eviews-series - provider[%s] - dataset[%s] : %.3f"
    current_app.logger.info(msg % (provider_name, dataset_code, end))
    
    return render_template("eviews.html", **context)
    

@bp.route('/values/<slug>', endpoint="values-by-slug")
def EVIEWS_values_by_dataset_slug(slug=None):
    
    """
    http://widukind-api-dev.cepremap.org/api/v1/eviews/values/insee-ipch-2005-fr-coicop

    http://widukind-api-dev.cepremap.org/api/v1/eviews/values/insee-ipch-2005-fr-coicop?frequency=M
    http://widukind-api-dev.cepremap.org/api/v1/eviews/values/insee-ipch-2005-fr-coicop?frequency=M&limit=100
    http://widukind-api-dev.cepremap.org/api/v1/eviews/values/insee-ipch-2005-fr-coicop?frequency=M&PRODUIT=T00
    """
    
    query = {"slug": slug}
    projection = {"_id": False, "provider_name": True, "dataset_code": True}
    dataset_code = queries.col_datasets().find_one(query, projection)
    
    return _EVIEWS_dataset_values(dataset_code["provider_name"], 
                                  dataset_code["dataset_code"])
    
@bp.route('/<provider>/dataset/<dataset_code>/values', endpoint="values")
def EVIEWS_values_by_dataset_code(provider=None, dataset_code=None):
    """
    http://ceres.cepremap.org/INSEE/dataset/158/values
    http://ceres.cepremap.org/INSEE/dataset/158/values?FREQ=M&PRODUIT=T00
    
    http://demeter-dev.cepremap.org/views/series/dataset/insee-ipch-2005-fr-coicop
    http://demeter-dev.cepremap.org/views/slug/series/insee-ipch-2005-fr-coicop-000671193
    
    http://widukind-api-dev.cepremap.org/api/v1/eviews/INSEE/dataset/IPCH-2005-FR-COICOP/values
    http://widukind-api-dev.cepremap.org/api/v1/eviews/INSEE/dataset/IPCH-2005-FR-COICOP/values?frequency=M
    http://widukind-api-dev.cepremap.org/api/v1/eviews/INSEE/dataset/IPCH-2005-FR-COICOP/values?frequency=M&limit=100
    http://widukind-api-dev.cepremap.org/api/v1/eviews/INSEE/dataset/IPCH-2005-FR-COICOP/values?frequency=M&PRODUIT=T00
    """

    return _EVIEWS_dataset_values(provider, dataset_code)
    
    
