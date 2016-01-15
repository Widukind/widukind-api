# -*- coding: utf-8 -*-

from flask import url_for

from widukind_api.tests.base import TestCase

class ViewsTestCase(TestCase):
    
    # nosetests -s -v widukind_api
    
    """
    TODO:
    /                              home HEAD,OPTIONS,GET
    /EVIEWS/<provider>/dataset/<dataset_code>/values EVIEWS.EVIEWS_query_series POST,HEAD,OPTIONS,GET
    /api/v1/<provider>             COMMON.get_provider HEAD,OPTIONS,GET
    /api/v1/<provider>/categories  COMMON.get_categories HEAD,OPTIONS,GET
    /api/v1/<provider>/dataset/<dataset_code> COMMON.get_dataset HEAD,OPTIONS,GET
    /api/v1/<provider>/dataset/<dataset_code>/series COMMON.get_series HEAD,OPTIONS,GET
    /api/v1/<provider>/dataset/<dataset_code>/series/<key> COMMON.get_a_series HEAD,OPTIONS,GET
    /api/v1/<provider>/dataset/<dataset_code>/values COMMON.get_values HEAD,OPTIONS,GET
    /api/v1/providers              COMMON.get_providers HEAD,OPTIONS,GET
    /static/<path:filename>        static HEAD,OPTIONS,GET        
    """
        
    def test_urls(self):
        url = url_for("home")
        response = self.client.get(url)        
        self.assert200(response)
        self.assert_template_used('index.html')
        
        
