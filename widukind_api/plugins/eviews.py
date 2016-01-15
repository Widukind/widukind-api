# -*- coding: utf-8 -*-

from flask import Blueprint, current_app, request, render_template, abort, url_for, redirect

import pandas

from widukind_api import constants

bp = Blueprint('EVIEWS', __name__)

@bp.route('/<provider>/dataset/<dataset_code>/values', endpoint="values")
def EVIEWS_query_series(provider, dataset_code):
    """
    http://127.0.0.1:8081/EVIEWS/BIS/dataset/PP-LS/values?Reference%20area=BE
    
    N'importe quelle dimension et sa valeur ou regex
    
    http://127.0.0.1:8081/EVIEWS/BIS/dataset/PP-LS/values?Reference%20area=BE|AU
    """
    
    db = current_app.widukind_db

    query = {"provider_name": provider, "dataset_code": dataset_code}
    projection = {'_id': False, 'revisions': False, 'release_dates': False, 'attributes': False}
    
    #TODO: limit
    limit = request.args.get('limit', default=0, type=int)
    
    for r in request.args.lists():
        if r[0] == 'limit':
            pass
        elif r[0] == 'frequency':
            query['frequency'] = r[1][0]
        else:
            query['dimensions.'+r[0]] = {'$regex': r[1][0]}
    
    print("query : ", query)
    results = db[constants.COL_SERIES].find(query, projection).limit(limit)
    
    table = {}
    table['vnames'] = []
    table['desc'] = []
    table['dates'] = []
    table['values'] = []
    init = True

    for r in results:
        if init:
            freq = r['frequency']
            dmin = r['start_date']
            dmax = r['end_date']
            pStartDate = pandas.Period(ordinal=r['start_date'],freq=freq)
            pEndDate = pandas.Period(ordinal=r['end_date'],freq=freq)
            pDmin = pandas.Period(ordinal=dmin,freq=freq);
            pDmax = pandas.Period(ordinal=dmax,freq=freq);
            table['dates'] = pandas.period_range(pStartDate,pEndDate,freq=freq).to_native_types()
            init = False
        if r['frequency'] != freq:
            continue
        if r['start_date'] < dmin:
            dmin = r['start_date']
        if r['end_date'] > dmax:
            dmax = r['end_date']
        table['vnames'].append(r['key'])
        table['desc'].append(r['name'])
        table['values'].append(r['values'])
    
    #TODO: template string ou array
    string = "<table>\n"
    string += "<tr><th>Dates</th>"
    for v in table['vnames']:
        string += "<th>" + v + "</th>"
        
    string += "</tr>\n"
    string += "<tr><th></th>" 
    for d in table['desc']:
        string += "<th>" + d + "</th>"
    string += "</tr>\n"
    for index, p in enumerate(table['dates']):
        string += "<tr><td>" + p + "</td>"
        for v in table['values']:
            string += "<td>" + v[index] + "</td>"
        string += "</tr>\n"
    
    string += "</table>\n"

    return(string)