# -*- coding: utf-8 -*-

import re
from datetime import datetime
import uuid
import time
import logging
from pprint import pprint

from flask import current_app, abort, request

from widukind_api import constants

logger = logging.getLogger(__name__)

def col_providers(db=None):
    db = db or current_app.widukind_db
    return db[constants.COL_PROVIDERS]

def col_datasets(db=None):
    db = db or current_app.widukind_db
    return db[constants.COL_DATASETS]

def col_categories(db=None):
    db = db or current_app.widukind_db
    return db[constants.COL_CATEGORIES]

def col_series(db=None):
    db = db or current_app.widukind_db
    return db[constants.COL_SERIES]

def get_provider(slug):
    provider_doc = col_providers().find_one({'slug': slug, "enable": True}, 
                                                    {"_id": False})
    if not provider_doc:
        abort(404)
        
    return provider_doc

def data_aggregate(query, start_period=None, end_period=None, limit=None):
    
    start = time.time()
    
    project = {
        '_id': 0,
        'key': 1,
        'name': 1,
        'values.period': 1, 
        'values.value': 1,
        'values.ordinal': 1, 
        'dimensions': 1,
        'attributes': 1,
    }
    
    match_values = None
    
    if start_period and end_period:
        match_values = {"values.ordinal": {"$gte": start_period, "$lte": end_period}}
    elif start_period:    
        match_values = {"values.ordinal": {"$gte": start_period}}
    elif end_period:    
        match_values = {"values.ordinal": {"$lte": end_period}}
    
    group = { 
        "_id": {
            "key": "$key",
            "name" : "$name",
            "dimensions" : "$dimensions",
            "attributes" : "$attributes",
        },
        "values": {
            "$push": {
                "value": "$values.value", 
                "period": "$values.period"
            }
        },
    }
    
    pipeline = []
    pipeline.append({"$match": query})
    
    if limit:
        pipeline.append({"$limit": limit })
    
    pipeline.append({'$project': project})
    pipeline.append({"$unwind": "$values"})
    
    if match_values:
        pipeline.append({"$match": match_values})
    
    pipeline.append({"$group": group })
    
    print("----------------------------------")
    pprint(pipeline)
    print("----------------------------------")
    
    result = list(col_series().aggregate(pipeline, allowDiskUse=True))

    end = time.time() - start
    msg = "sdmx-data-aggregate - %.3f"
    logger.info(msg % end)
    
    return result

def data_query(dataset_code, provider_name=None, filters=None, 
               start_period=None, end_period=None,
               limit=None, get_ordinal_func=None):

    query_ds = {'enable': True, 'dataset_code': dataset_code}
    if provider_name:
        query_ds["provider_name"] = provider_name
    projection_ds = {"name": True, "dataset_code": True, "slug": True,
                     "provider_name": True, "dimension_keys": True}
    dataset_doc = col_datasets().find_one(query_ds, projection_ds)
    
    if not dataset_doc:
        abort(404)

    if start_period:
        start_period = get_ordinal_func(start_period)
    if end_period:
        end_period = get_ordinal_func(end_period)

    query = {"provider_name": dataset_doc["provider_name"],
             "dataset_code": dataset_doc["dataset_code"]}
    
    if filters and filters != "all": 
        _filters = filters.split(".")
        if not len(_filters) == len(dataset_doc["dimension_keys"]):
            print("abord not filters !", len(_filters), len(dataset_doc["dimension_keys"]))
            abort(404)
        for i, dim in enumerate(dataset_doc["dimension_keys"]):
            if not _filters[i]:
                continue
            query["dimensions."+ dim] = {"$in": _filters[i].split("+")}
    
    """
    TODO: Compter doc total sans filtrage pour déterminer si obligation filtrage
    """

    print("--------------- QUERY ----------------------")
    pprint(query)
    print("--------------------------------------------")
    
    if not start_period and not end_period:
        projection = {
            "_id": False,
            "key": True, "name": True,
            'values.period': True, 'values.value': True, 'values.ordinal': True, 
            'dimensions': True, 'attributes': True,
        }
        cursor = col_series().find(query, projection)
        if limit:
            cursor = cursor.limit(limit)
        docs = list(cursor)
    else:
        cursor = data_aggregate(query, 
                                        start_period=start_period, 
                                        end_period=end_period, 
                                        limit=limit)
        docs = []
        for doc in cursor:
            docs.append({
                "key": doc["_id"]["key"],
                "name": doc["_id"]["name"],
                "dimensions": doc["_id"]["dimensions"],
                "attributes": doc["_id"]["attributes"],
                "values": doc["values"],
            })
    
    #count = len(docs)

    now = str(datetime.utcnow().isoformat())
    
    return {
        "provider_name": dataset_doc["provider_name"],
        "dataset_name": dataset_doc["name"],
        "dataset_code": dataset_doc["dataset_code"],
        "dataset_slug": dataset_doc["slug"],
        "message_id": str(uuid.uuid4()),
        "prepared_date": now,
        "validFromDate": now,
        "objects": docs,
    }

def complex_queries_series(query={}):

    tags = request.args.get('tags', None)
    
    search_fields = []

    for r in request.args.lists():
        if r[0] in ['limit', 'tags']:
            continue
        elif r[0] == 'frequency':
            query['frequency'] = r[1][0]
        else:
            search_fields.append((r[0], r[1][0]))

    if tags and len(tags.split()) > 0:
        tags = tags.split()
        tags_regexp = [re.compile('.*%s.*' % e, re.IGNORECASE) for e in tags]
        query["tags"] = {"$in": tags_regexp}
        
    if search_fields:
        query_or = []
        query_nor = []
        
        for field, value in search_fields:
            values = value.split()
            value = [v.lower().strip() for v in values]
            
            for v in value:
                if v.startswith("!"):
                    query_nor.append({"dimensions.%s" % field.lower(): v[1:]})
                    query_nor.append({"attributes.%s" % field.lower(): v[1:]})
                else:
                    query_or.append({"dimensions.%s" % field.lower(): v})
                    query_or.append({"attributes.%s" % field.lower(): v})

        if query_or:
            query["$or"] = query_or
        if query_nor:
            query["$nor"] = query_nor

    print("-----complex query-----")
    pprint(query)    
    print("-----------------------")
        
    return query

