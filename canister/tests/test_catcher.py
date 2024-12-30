#
# test_catcher.py
#
# Tests the Catcher web service.
#

import ssl
import unittest

import net_http
from catcher import Catcher




class TestCatcherContent(unittest.TestCase):
    #
    # Class to run all Catcher tests.
    #


    @classmethod
    def setUpClass(cls):
        #
        # Call setUp as a class method to provide a single standup.
        #
        cls.http_service = Catcher(port=8080, enable_ssl=False)
        cls.http_service.start()


    def test_get(self):
        #
        # Test a GET request.
        #
        code, reason, headers, body = net_http.request("http://127.0.0.1:8080")
        self.assertEqual(code, 200)


    @classmethod
    def tearDownClass(cls):
        #
        # Call tearDown as a class method to match the single standup.
        # Shut down the server after tests.
        #
        cls.http_service.shutdown()
