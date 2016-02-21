# -*- coding: utf-8 -*-

from widukind_common.constants import *

SESSION_LANG_KEY = "current_lang"
SESSION_TIMEZONE_KEY = "current_tz"
SESSION_THEME_KEY = "current_theme"

COL_SESSION = "session_api"
COL_ALL.append(COL_SESSION)

CHOICES_SORT_DATASETS = (
    ('provider_name', 'provider_name'),
    ("dataset_code", "dataset"),
    ("name", "serie name"),
    ("last_update", "Last update"),
)

CHOICES_SORT_SERIES = (
    ("start_date", "start date"),
    ("end_date", "end date"),
    ('provider_name', 'provider_name'),
    ("dataset_code", "dataset"),
    ("name", "serie name"),
    ("key", "serie key"),
)

