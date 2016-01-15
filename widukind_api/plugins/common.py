
from flask import current_app as app
from flask import request, Blueprint, url_for, render_template, render_template_string

from bson import json_util

from widukind_api import constants

bp = Blueprint('COMMON', __name__)

@bp.route('/html/providers', endpoint="html-providers")
def html_providers():
    db = app.widukind_db
    query = {}
    projection = {"_id": False, "name": True, "slug": True}
    docs = db[constants.COL_PROVIDERS].find(query, projection)
    return render_template("providers.html", providers=docs)

@bp.route('/html/datasets/<provider>', endpoint="html-datasets-by-provider")
@bp.route('/html/datasets', endpoint="html-datasets")
def html_datasets(provider=None):
    db = app.widukind_db
    projection_provider = {"_id": False, "name": True, "slug": True}
    projection_datasets = {"_id": False, "name": True, "slug": True, "dataset_code": True, "provider_name": True}
    query_datasets = {}
    query_providers = {}
    if provider:
        query_datasets["provider_name"] = provider
        query_providers["name"] = provider
    providers = dict([(doc["name"], doc) for doc in db[constants.COL_PROVIDERS].find(query_providers, projection_provider)])
    datasets = db[constants.COL_DATASETS].find(query_datasets, projection_datasets)
    docs = {}
    for dataset in datasets:
        provider_name = dataset["provider_name"]
        if not provider_name in docs:
            docs[provider_name] = {"provider": providers[provider_name],
                                   "datasets": []}
        docs[provider_name]["datasets"].append(dataset)
    
    return render_template("datasets.html", docs=docs)

# list providers
@bp.route('/providers')
def get_providers():
    db = app.widukind_db
    query = {}
    projection = {"_id": False, "data_tree": False}
    docs = db[constants.COL_PROVIDERS].find(query, projection)
    return json_util.dumps(docs, default=json_util.default)

# list one provider
@bp.route('/<provider>/provider')
def get_provider(provider):
    db = app.widukind_db
    query = {'name': provider}
    projection = {"_id": False, "data_tree": False}
    doc = db[constants.COL_PROVIDERS].find_one(query, projection)
    #TODO: 404
    return json_util.dumps(doc, default=json_util.default)

# liste categories d'un provider. Devrait maintenant renvoyer le data_tree
@bp.route('/<provider>/categories')
def get_categories(provider):
    db = app.widukind_db
    query = {'name': provider}
    projection = {"_id": False, "data_tree": True}
    doc = db[constants.COL_PROVIDERS].find_one(query, projection)
    #TODO: 404
    return json_util.dumps(doc.get("data_tree"), default=json_util.default)

# liste une categories
"""
@bp.route('/<provider>/categories/<id_category>', methods=["GET"])
def get_category(provider,id_category):
    db = app.widukind_db
    return json_util.dumps(db.categories.find(
        {'provider_name': provider, '_id':bson.ObjectId(id_category)}), default=json_util.default)
"""

@bp.route('/<provider>/datasets')
def get_datasets(provider):
    db = app.widukind_db
    query = {'provider_name': provider}
    projection = {"_id": False, "name": True, "slug": True, "dataset_code": True}
    docs = db[constants.COL_DATASETS].find(query, projection)
    return json_util.dumps(docs, default=json_util.default)

# liste un provider/dataset. (meta data)
@bp.route('/<provider>/dataset/<dataset_code>')
def get_dataset(provider, dataset_code):
    db = app.widukind_db
    query = {'provider_name': provider, 'dataset_code': dataset_code}
    projection = {"_id": False}
    doc = db[constants.COL_DATASETS].find_one(query, projection)
    return json_util.dumps(doc, default=json_util.default)

def _get_by_slug(collection, slug, projection=None):
    db = app.widukind_db
    query = {"slug": slug}
    projection = projection or {"_id": False}
    if not "_id" in projection:
        projection["_id"] = False
    doc = db[collection].find_one(query, projection)
    return json_util.dumps(doc, default=json_util.default)

@bp.route('/slug/provider/<slug>', endpoint="provider-by-slug")
def get_provider_by_slug(slug):
    projection = {"_id": False, "data_tree": False}
    return _get_by_slug(constants.COL_PROVIDERS, slug, projection)

@bp.route('/slug/dataset/<slug>', endpoint="dataset-by-slug")
def get_dataset_by_slug(slug):
    projection = {"_id": False}
    return _get_by_slug(constants.COL_DATASETS, slug, projection)

@bp.route('/slug/series/<slug>', endpoint="series-by-slug")
def get_series_by_slug(slug):
    projection = {"_id": False}
    return _get_by_slug(constants.COL_SERIES, slug, projection)

# renvoie les séries d'un provider/dataset
@bp.route('/<provider>/dataset/<dataset_code>/series')
def get_series(provider, dataset_code):
    db = app.widukind_db
    query = {'provider_name': provider, 'dataset_code': dataset_code}
    projection = {"_id": False, "key": True, "name": True, "slug": True}
    cursor = db[constants.COL_SERIES].find(query, projection)
    docs = []
    #TODO: start and end dates ?
    #TODO: count values
    #TODO: url provider, dataset ?
    """
    for doc in cursor:
        print(doc.get("slug"))
        doc["url"] = url_for("series-by-slug", slug=doc["slug"])
        docs.append(doc)
    """
    docs = cursor
    return json_util.dumps(docs, default=json_util.default)

# renvoie renvoie provider/dataset/series
"""
@bp.route('/<provider>/dataset/<dataset_code>/series/<key>', methods=["GET"])
def get_a_series(provider, key, dataset_code=None):
    db = app.widukind_db
    if dataset_code:
        return json_util.dumps(db[constants.COL_SERIES].find(
            {'provider_name': provider, 'dataset_code':dataset_code,'key':key} ), default=json_util.default)
    else:
        return json_util.dumps(db[constants.COL_SERIES].find(
            {'provider_name': provider, 'key':key} ), default=json_util.default)
"""

# renvoie toutes les values d'un dataset. Fixer une taille maximum
@bp.route('/<provider>/dataset/<dataset_code>/values')
def get_values(provider, dataset_code):
    db = app.widukind_db
    query = {'provider_name': provider, 'dataset_code': dataset_code}
    projection = {"_id": False, "values": True} #TODO: 'release_dates': False, 'revisions': False, 'attributes': False}
    
    search_dimension = False
    for r in request.args.lists():
        query['dimensions.'+r[0]] = {'$regex': r[1][0]};
        search_dimension = True
    if search_dimension:
        projection["dimensions"] = True
        
    #TODO: series order ?
    docs = db[constants.COL_SERIES].find(query, projection)
    return json_util.dumps(docs, default=json_util.default)

