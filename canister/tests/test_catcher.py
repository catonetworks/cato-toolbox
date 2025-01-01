#
# test_catcher.py
#
# Tests the Catcher web service.
#

import ssl
import unittest

import net_http
from catcher import Catcher
from logger import Logger
Logger.print_output = False




class TestCatcherContent(unittest.TestCase):
    #
    # Class to run all Catcher tests.
    #


    @classmethod
    def setUpClass(cls):
        #
        # Call setUp as a class method to provide a single standup.
        #
        cls.http_service = Catcher()
        cls.http_service.start()


    def test_get(self):
        #
        # Test a GET request.
        #
        code, reason, headers, body = net_http.request("https://127.0.0.1:8443")
        self.assertEqual(code, 200)

    def test_eicar(self):
        #
        # Test a GET request.
        #
        code, reason, headers, body = net_http.request("https://127.0.0.1:8443/eicar.exe")
        self.assertEqual(code, 200)
        self.assertTrue("EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in body)


    @classmethod
    def tearDownClass(cls):
        #
        # Call tearDown as a class method to match the single standup.
        # Shut down the server after tests.
        #
        cls.http_service.shutdown()
