# -*- coding: utf-8 -*-

from flask import current_app as app
from flask import request, Blueprint, url_for, abort, make_response

from bson import json_util

from flask_restplus import Api, Resource, fields
from flask_restful.utils import cors
from flask_restplus import reqparse

from widukind_api import queries

bp = Blueprint('rest', __name__)

api = Api(bp, 
          version='1.0',
          doc='/doc/',
          default_mediatype='application/json',
          decorators=[cors.crossdomain(origin='*')], 
          title='Widukind API',
          description='')

ns_providers = api.namespace('providers', 'Providers related operations')
ns_datasets = api.namespace('datasets', 'Datasets related operations')
ns_series = api.namespace('series', 'Series related operations')

@api.representation('application/json')
def output_json(data, code, headers=None):
    '''Use Flask JSON to serialize'''
    resp = make_response(json_util.dumps(data, default=json_util.default), code)
    resp.headers.extend(headers or {})
    return resp

"""
{
  "metadata": null,
  "region": "France",
  "website": "http://www.insee.fr",
  "lock": false,
  "slug": "insee",
  "enable": true,
  "name": "INSEE",
  "version": 3,
  "long_name": "National Institute of Statistics and Economic Studies"
}
"""
provider_model = api.model('Provider', {
    'name': fields.String,
    'slug': fields.String,
    #'uri': fields.Url('provider_resource'),
    #'date_updated': fields.DateTime(dt_format='rfc822'),
})

provider_list_model = api.model('ProviderList', {
    'providers': fields.List(fields.Nested(provider_model)),
})

@ns_providers.route('/')
class ProviderList(Resource):
    
    #@api.doc('list_providers')
    #@api.marshal_with(provider_list_model, as_list=False)#, envelope='provider')
    def get(self):
        query = {"enable": True}
        projection = {"_id": False}
        return [doc for doc in queries.col_providers().find(query, projection)] 

def get_provider(slug):
        provider_doc = queries.col_providers().find_one({'slug': slug, "enable": True}, 
                                                {"_id": False})
        if not provider_doc:
            api.abort(404, "Provider {} doesn't exist".format(slug))
        
        return provider_doc

def get_dataset(slug):
        dataset_doc = queries.col_datasets().find_one({'slug': slug, "enable": True}, 
                                                {"_id": False})
        if not dataset_doc:
            api.abort(404, "Dataset {} doesn't exist".format(slug))
        
        return dataset_doc

@ns_providers.route('/<provider>', endpoint='provider')
class ProviderUnit(Resource):
    
    @api.marshal_with(provider_model)
    def get(self, provider):
        provider_doc = get_provider(provider)
        return provider_doc

@ns_providers.route('/<provider>/datasets')
@ns_datasets.route('/<provider>')
class DatasetList(Resource):

    def get(self, provider):
        provider_doc = get_provider(provider)
        query = {'provider_name': provider_doc["name"]}
        projection = {"_id": False, "tags": False,
                      "enable": False, "lock": False,
                      "concepts": False, "codelists": False}
        return queries.col_datasets().find(query, projection)

@ns_datasets.route('/<dataset>')
class DatasetUnit(Resource):

    def get(self, dataset):
        query = {'enable': True, 'slug': dataset}
        projection = {"_id": False, "enable": False, "lock": False}
        return queries.col_datasets().find_one(query, projection)

series_list_values_parser = reqparse.RequestParser(bundle_errors=True)
#required=True
series_list_values_parser.add_argument(
    'limit', type=int, location='args', help='Limit results')
series_list_values_parser.add_argument(
    'frequency', type=str, location='args', help='Frequency')
series_list_values_parser.add_argument(
    'tags', type=str, action="append", location='args', help='Tags')

@ns_datasets.route('/<dataset>/values')
@ns_series.route('/<dataset>/values')
class SeriesListValue(Resource):

    @api.doc(parser=series_list_values_parser)
    def get(self, dataset):
        
        query = {'enable': True, 'slug': dataset}
        projection = {"_id": False, "enable": False, "lock": False}
        doc = queries.col_datasets().find_one(query, projection)
        
        query = {"provider_name": doc["provider_name"], 
                 'dataset_code': doc["dataset_code"]}
        projection = {
            "_id": False, 
            "key": True, "name": True, "slug": True,
            "frequency": True,
            "values.value": True, "values.period": True,
        }
        
        args = series_list_values_parser.parse_args()
        
        limit = args.pop("limit", 10)
        frequency = args.pop("frequency", None)
        tags = args.pop("tags", None)
        print("tags : ", tags, type(tags))
        
        search_fields = []
        for k, v in args.items():
            search_fields.append((k, v))
            
        print("search_fields : ", search_fields)
        
        docs = queries.col_series().find(query, projection).limit(limit)
        
        return docs
        
        

@ns_datasets.route('<dataset>/series')
@ns_series.route('/<dataset>')
class SeriesList(Resource):
    
    def get(self, dataset):
        dataset_doc = get_dataset(dataset)
        query = {'provider_name': dataset_doc['provider_name'], 
                 'dataset_code': dataset_doc["dataset_code"]}
        projection = {"_id": False, "tags": False, "values": False}
        return queries.col_series().find(query, projection)

