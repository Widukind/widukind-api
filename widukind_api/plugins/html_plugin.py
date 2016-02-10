
from flask import Blueprint, render_template, abort

from widukind_api import queries

bp = Blueprint('html', __name__)

#TODO: error enable False

@bp.route('/providers', endpoint="providers")
def html_providers():
    query = {"enable": True}
    projection = {"_id": False, "name": True, "slug": True, "enable": True}
    docs = queries.col_providers().find(query, projection)
    return render_template("providers.html", providers=docs)

@bp.route('/datasets/<provider>', endpoint="datasets-by-provider")
@bp.route('/datasets', endpoint="datasets")
def html_datasets(provider=None):

    query_providers = {"enable": True}
    projection_provider = {"_id": False, 
                           "name": True, "slug": True}

    query_datasets = {"enable": True}
    projection_datasets = {"_id": False, 
                           "name": True, "slug": True, 
                           "dataset_code": True, "provider_name": True}
    
    if provider:
        provider_doc = queries.col_providers().find_one({"slug": provider})
        query_datasets["provider_name"] = provider_doc["name"]
        query_providers["name"] = provider_doc["name"]

    providers = dict([(doc["name"], doc) for doc in queries.col_providers().find(query_providers, 
                                                                                projection_provider)])
    
    query_datasets["provider_name"] = {"$in": list(providers.keys())}
    datasets = queries.col_datasets().find(query_datasets, projection_datasets)
    
    docs = {}
    for dataset in datasets:
        provider_name = dataset["provider_name"]
        if not provider_name in docs:
            docs[provider_name] = {"provider": providers[provider_name],
                                   "datasets": []}
        docs[provider_name]["datasets"].append(dataset)
    
    return render_template("datasets.html", docs=docs)

