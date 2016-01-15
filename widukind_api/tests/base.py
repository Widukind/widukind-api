# -*- coding: utf-8 -*-

from flask_testing import TestCase as BaseTestCase

from widukind_common.utils import create_or_update_indexes
from widukind_common import tests_tools as utils

class TestCase(BaseTestCase):
    
    def setUp(self):
        super().setUp()
        self.db = self.app.widukind_db
        self.assertEqual(self.db.name, "widukind_test")
        utils.clean_mongodb(self.db)
        create_or_update_indexes(self.db, force_mode=True)

    def create_app(self):
        from widukind_api import wsgi
        app = wsgi.create_app('widukind_api.settings.Test')
        return app