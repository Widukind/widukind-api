# -*- coding: utf-8 -*-

from datetime import datetime
import uuid

from flask import Blueprint, render_template, abort, current_app
from flask import make_response, request

from widukind_api import queries
from widukind_api.extensions import cache, limiter
from widukind_api.flask_utils import func_cache_with_args

bp = Blueprint('sdmx', __name__, template_folder='templates')

def get_ordinal_from_period(date_str, freq=None):
    return current_app.get_ordinal_from_period(date_str, freq)

def optional_cache():
    return current_app.config.get("DISABLE_CACHE") is True

#@limiter.limit("100 per minute")
#FIXME: header !!! @cache.memoize(360, make_name=func_cache_with_args)
@bp.route('/<providerRef>/data/<flowRef>/all', defaults={"key": "all"})
@bp.route('/<providerRef>/data/<flowRef>/<key>', endpoint="2-1-data-specific")
@bp.route('/data/<flowRef>', defaults={"key": "all", "providerRef": "all"})
@bp.route('/data/<flowRef>/all/<providerRef>', defaults={"key": "all"})
@bp.route('/data/<flowRef>/<key>/<providerRef>')
@bp.route('/data/<providerRef>/<flowRef>/<key>')
def data_2_1(flowRef, key=None, providerRef=None, version="all"):

    if "application/vnd.sdmx.genericdata+xml;version=2.1" in request.headers.get("Accept", None):
        tmpl_choice = 'sdmx/2.1/data-generic.xml'
    else:
        tmpl_choice = 'sdmx/2.1/data-specific.xml'

    limit = request.args.get('limit', default=200, type=int)
    if limit > 5000:
        limit = 5000

    start_period = request.args.get('startPeriod')
    end_period = request.args.get('endPeriod')

    if key:
        key = key.lower()

    datas = queries.data_query(flowRef,
                               provider_name=providerRef,
                               filters=key,
                               start_period=start_period,
                               end_period=end_period,
                               limit=limit,
                               get_ordinal_func=get_ordinal_from_period)

    tmpl = render_template(tmpl_choice, version="1.0", **datas)
    resp = make_response(tmpl)
    resp.headers["Content-Type"] = "application/xml"
    return resp

"""
http "http://127.0.0.1:8081/api/v1/sdmx/data/IPCH-2015-FR-COICOP/A.07120./INSEE" Accept:application/vnd.sdmx.genericdata+xml;version=2.1
http "http://127.0.0.1:8081/api/v1/sdmx/data/IPCH-2015-FR-COICOP/A.07120./INSEE"
http "http://127.0.0.1:8081/api/v1/sdmx/data/IPCH-2015-FR-COICOP/A.07120./INSEE?startPeriod=2010&endPeriod=2014" Accept:application/xml
http://www.bdm.insee.fr/series/sdmx/data/IPI-2010-A21/M.B.BRUT?startPeriod=2014-01&endPeriod=2015-12

protocol://ws-entry-point/resource/flowRef/key/providerRef
TODO: flowRef: AGENCY_ID,FLOW_ID,VERSION
TODO: providerRef: AGENCY_ID,PROVIDER_ID

firstNObservations
    Nombre maximum d'observation par series
lastNObservations
    Maximum number of observations counting back from the most recent observation
dimensionAtObservation
    Id fof the dimension attached at the observation level TIME_PERIOD
detail
    Desired amount of information to be returned. Values: full, dataonly, serieskeysonly, nodata full
includeHistory
    Whether to return vintages false
updatedAfter
    2009-05-15T14%3A15%3A00%2B01%3A00

Period format:
    Daily/Business YYYY-MM-DD
    Weekly YYYY-W[01-53]
    Monthly YYYY-MM
    Quarterly YYYY-Q[1-4]
    Semi-annual YYYY-S[1-2]        # TODO: exclude
    Annual YYYY


#TODO: If-Modified-Since / Last-Modified

> request:
    If-Modified-Since: Wed, 03 Feb 2016 11:28:46 GMT
> response:
    Status Code: 304 Not Modified
> request:
    If-Modified-Since: Wed, 03 Feb 2016 11:35:46 GMT
> response:
    Status Code: 200 OK
    Date: Wed, 03 Feb 2016 11:32:31 GMT
    Expires: Wed, 03 Feb 2016 11:32:31 GMT
    Last-Modified: Wed, 03 Feb 2016 11:28:46 GMT

"""

"""
itemID: only conceptscheme and agencyscheme

datastructure,
dataflow,
    XML Dataflow: Categorisation, Process, Constraint, DataStructureDefinition, ProvisionAgreement, ReportingTaxonomy, StructureSet

codelist ?
conceptscheme ?
categorisation / categoryscheme

/datastructure/INSEE/IPCH-2015-FR-COICOP/latest/all?queryStringParameters
    detail=allstubs, referencestubs, full (default full)
    references= none, parents, parentsandsiblings, children, descendants, all, any
        default: none

https://ws-entry-point/resource/agencyID/resourceID/version/itemID?queryStringParameters
DEFAULT: /datastructure/all/all/latest/all?detail=full&references=none

"""

@bp.route('/datastructure/<agencyID>/<resourceID>', defaults={"version": "latest"}, endpoint="2-1-datastructure")
@bp.route('/datastructure/<agencyID>/<resourceID>/<version>')
@cache.memoize(360, make_name=func_cache_with_args, unless=optional_cache)
def dsd_2_1(agencyID, resourceID, version="latest"):
    """
    http://127.0.0.1:8081/api/v1/sdmx/datastructure/INSEE/IPCH-2015-FR-COICOP

    http://127.0.0.1:8081/api/v1/sdmx/datastructure/all/IPC-2015-COICOP/latest/?references=children

    http://127.0.0.1:8081/api/v1/sdmx/datastructure/all/IPCH-2015-FR-COICOP/latest/?references=children

    > attendu:
    "2016-01-23T09:09:42.771Z"
    "2013-07-10T11:00:00.000Z","%Y-%m-%dT%H:%M:%S.%fZ")
    "2013-07-12T07:00:00Z","%Y-%m-%dT%H:%M:%SZ"
    datetime.datetime.utcnow().isoformat() + "Z"
    > iso:
    YYYY-MM-DDTHH:MM:SS.mmmmmm
    """

    references = request.args.get('references')

    query_ds = {'enable': True,
                'provider_name': agencyID,
                'dataset_code': resourceID}
    projection_ds = {"tags": False, "_id": False}
    doc = queries.col_datasets().find_one(query_ds, projection_ds)

    if not doc:
        abort(404)

    now = "%sZ" % str(datetime.utcnow().isoformat())
    context = {
        "dataset": doc,
        "datasets": [doc],
        "time_period_concept": "TIME_PERIOD" in doc.get("concepts"),
        "obs_value_concept": "OBS_VALUE" in doc.get("concepts"),
        "load_all": references in ["children", "descendants", "all"],
        "message_id": str(uuid.uuid4()),
        "prepared_date": now,
        "version": "1.0"
    }

    tmpl = render_template('sdmx/2.1/datastructure.xml', **context)
    response = make_response(tmpl)
    response.headers["Content-Type"] = "application/xml"
    return response

@bp.route('/dataflow', endpoint="2-1-dataflow")
@bp.route('/dataflow/<agencyID>', endpoint="2-1-dataflow-agency")
@bp.route('/dataflow/<agencyID>/<resourceID>', defaults={"version": "latest"}, endpoint="2-1-dataflow-dataset")
@bp.route('/dataflow/<agencyID>/<resourceID>/<version>')
@cache.memoize(360, make_name=func_cache_with_args, unless=optional_cache)
def dataflow_2_1(agencyID=None, resourceID=None, version="latest"):
    """
    TODO: option references avec limit sur 1 dataset
    """

    references = request.args.get('references')

    query_ds = {'enable': True}
    if agencyID:
        query_ds["provider_name"] = agencyID.upper()
    if resourceID:
        query_ds["dataset_code"] = resourceID

    projection_ds = {"_id": False,
                     "provider_name": True, "dataset_code": True, "name": True}
    docs = queries.col_datasets().find(query_ds, projection_ds)

    now = "%sZ" % str(datetime.utcnow().isoformat())
    context = {
        "datasets": docs,
        "message_id": str(uuid.uuid4()),
        "prepared_date": now,
        "version": "1.0"
    }

    tmpl = render_template('sdmx/2.1/dataflow.xml', **context)
    response = make_response(tmpl)
    response.headers["Content-Type"] = "application/xml"
    return response

@bp.route('/conceptscheme/<agencyID>/<resourceID>', defaults={"version": "latest", "itemID": None}, endpoint="2-1-conceptscheme")
@bp.route('/conceptscheme/<agencyID>/<resourceID>/<version>', defaults={"version": "latest", "itemID": None})
@bp.route('/conceptscheme/<agencyID>/<resourceID>/<version>/<itemID>')
@cache.memoize(360, make_name=func_cache_with_args, unless=optional_cache)
def conceptscheme_2_1(agencyID, resourceID, version="latest", itemID=None):

    references = request.args.get('references')

    query_ds = {'enable': True,
                'provider_name': agencyID,
                'dataset_code': resourceID}

    projection_ds = {"_id": False, "tags": False}

    if not references or not references in ["children", "descendants", "all"]:
        projection_ds["codelists"] = False
    #TODO: itemID et repercussion sur codelists !
    #if itemID:
    #    projection_ds["concepts.%s" % itemID] = True

    #print("query_ds : ", query_ds)

    doc = queries.col_datasets().find_one(query_ds, projection_ds)

    if not doc:
        abort(404)

    now = "%sZ" % str(datetime.utcnow().isoformat())
    context = {
        "dataset": doc,
        "time_period_concept": "time_period" in doc.get("concepts"),
        "obs_value_concept": "obs_value" in doc.get("concepts"),
        "load_all": references in ["children", "descendants", "all"],
        "message_id": str(uuid.uuid4()),
        "prepared_date": now,
        "version": "1.0"
    }

    tmpl = render_template('sdmx/2.1/conceptscheme.xml', **context)
    response = make_response(tmpl)
    response.headers["Content-Type"] = "application/xml"
    return response

@bp.route('/codelist/<agencyID>/<resourceID>', defaults={"version": "latest", "itemID": None}, endpoint="2-1-codelist")
@bp.route('/codelist/<agencyID>/<resourceID>/<version>', defaults={"version": "latest", "itemID": None})
@bp.route('/codelist/<agencyID>/<resourceID>/<version>/<itemID>')
@cache.memoize(360, make_name=func_cache_with_args, unless=optional_cache)
def codelist_2_1(agencyID, resourceID, version="latest", itemID=None):

    references = request.args.get('references')

    query_ds = {'enable': True,
                'provider_name': agencyID,
                'dataset_code': resourceID}

    projection_ds = {"_id": False, "tags": False}

    #is_concepts = references and references in ["children", "descendants", "all"]
    #if not is_concepts:
    #    projection_ds["concepts"] = False
    is_concepts = True
    #TODO: itemID et repercussion sur codelists !
    #if itemID:
    #    projection_ds["concepts.%s" % itemID] = True

    #print("query_ds : ", query_ds)

    doc = queries.col_datasets().find_one(query_ds, projection_ds)

    if not doc:
        abort(404)

    now = "%sZ" % str(datetime.utcnow().isoformat())
    context = {
        "dataset": doc,
        "load_all": references in ["children", "descendants", "all"],
        "message_id": str(uuid.uuid4()),
        "prepared_date": now,
        "version": "1.0"
    }
    if is_concepts:
        context["time_period_concept"] = "time_period" in doc.get("concepts")
        context["obs_value_concept"] = "obs_value" in doc.get("concepts")

    tmpl = render_template('sdmx/2.1/codelist.xml', **context)
    response = make_response(tmpl)
    response.headers["Content-Type"] = "application/xml"
    return response
