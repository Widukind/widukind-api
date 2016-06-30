# -*- coding: utf-8 -*-

import unittest
from datetime import datetime
from flask import url_for

from widukind_api.tests.base import TestCase, REFERENTIEL

from pprint import pprint

class JsonPluginTestCase(TestCase):
    
    # nosetests -s -v widukind_api.tests.test_views:JsonPluginTestCase
    
    def setUp(self):
        super().setUp()
        self.fixtures()
        
    def test_views_providers_list(self):
        response = self.json_get(url_for('json.providers-list'))
        self.assertOkJson(response)
        response_json = self.response_json(response)
        self.assertEquals(len(response_json["data"]), REFERENTIEL["providers"]["count"])
        pprint(response_json)
        self.assertEquals(response_json["data"], 
                          [{'long_name': 'National Institute of Statistics and Economic Studies',
                            'name': 'INSEE',
                            'region': 'France',
                            'slug': 'insee',
                            'website': 'http://www.insee.fr'}])
    
    """
    providers_list_keys
    
    def test_views_ajax_datasets_list(self):
        response = self.json_get(url_for('views.ajax-datasets-list', provider="NOTEXIST"))
        self.assert_404(response)
        
        response = self.json_get(url_for('views.ajax-datasets-list', provider="insee"))
        self.assertOkJson(response)
        response_json = self.response_json(response)
        self.assertEquals(len(response_json["data"]), REFERENTIEL["datasets"]["count"])
        self.assertEquals(response_json["data"], 
                          [{'dataset_code': 'IPCH-2015-FR-COICOP', 
                            'name': 'Harmonised consumer price index - Base 2015 - France - By product (COICOP classification)', 
                            'slug': 'insee-ipch-2015-fr-coicop',
                            'enable': True}])
    """
    
class HomeViewsTestCase(TestCase):

    # nosetests -s -v widukind_api.tests.test_views:HomeViewsTestCase

    def setUp(self):
        super().setUp()

    def test_views_index(self):
        response = self.client.get(url_for('home'))
        self.assertOkHtml(response)
        self.assert_template_used("index.html")


