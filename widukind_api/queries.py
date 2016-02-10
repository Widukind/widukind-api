# -*- coding: utf-8 -*-

from flask import current_app, abort

from widukind_api import constants

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
