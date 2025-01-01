#
# test_canistertest.py
#
# Tests the Canister test class.
#

import unittest

from canistertest import CanisterTest, mandatory_parameters, supported_protocols, supported_methods, evaluate
from logger import Logger
Logger.print_output = False


porn_test = {
    "name": "Porn Site",
    "feature": "Internet Firewall",
    "description": "Access to adult websites",
    "remediation": "This access can be blocked by the Cato Internet Firewall.",
    "method": "GET",
    "protocol": "http",
    "host": "www.sex.com",
    "path": "/",
    "success_criteria": [{"field":"response_code","op":"is","value":403}],
}

google_test = {
    "name": "Google",
    "feature": "Internet Firewall",
    "description": "Access to Google website",
    "remediation": "This access can be blocked by the Cato Internet Firewall.",
    "method": "GET",
    "protocol": "http",
    "host": "google.com",
    "path": "/",
    "success_criteria": [{"field":"response_code","op":"is","value":200}],
}



class TestCanisterTest(unittest.TestCase):
    #
    # CanisterTest tests.
    #


    def test_mandatoryparameters(self):
        #
        # Check that all mandatory parameters are present
        #
        for param in mandatory_parameters:
            params = {X:"test" for X in mandatory_parameters if X != param}
            self.assertRaises(KeyError, CanisterTest, params)

    def test_protocols(self):
        params = {X:"test" for X in mandatory_parameters}
        params["method"] = supported_methods[0]
        params["success_criteria"] = [{"field":"response_code","op":"is","value":403}]
        self.assertRaises(ValueError, CanisterTest, params)
        for protocol in supported_protocols:
            params["protocol"] = protocol
            T = CanisterTest(params)
            self.assertEqual(T.protocol, protocol)

    def test_methods(self):
        params = {X:"test" for X in mandatory_parameters}
        params["protocol"] = supported_protocols[0]
        params["success_criteria"] = [{"field":"response_code","op":"is","value":403}]
        self.assertRaises(ValueError, CanisterTest, params)
        for method in supported_methods:
            params["method"] = method
            T = CanisterTest(params)
            self.assertEqual(T.method, method)


    def test_success_criteria(self):
        #
        # Invalid type
        #
        params = {X:"test" for X in mandatory_parameters}
        params["protocol"] = supported_protocols[0]
        params["method"] = supported_methods[0]
        self.assertRaises(TypeError, CanisterTest, params) 

        #
        # Invalid sc type
        #
        params["success_criteria"] = [["field", "response_code","op", "is","value", 403]]
        self.assertRaises(TypeError, CanisterTest, params) 

        #
        # Unsupported item
        #
        params["success_criteria"] = [{"fieldX": "response_code","op":"is","value":403}]
        self.assertRaises(KeyError, CanisterTest, params) 

        #
        # Unsupported field value
        #
        params["success_criteria"] = [{"field": "response_codeX","op":"is","value":403}]
        self.assertRaises(ValueError, CanisterTest, params) 

        #
        # Unsupported op value
        #
        params["success_criteria"] = [{"field": "response_code","op":"isX","value":403}]
        self.assertRaises(ValueError, CanisterTest, params) 


    def test_execution(self):
        #
        # Initial state
        #
        T = CanisterTest(porn_test)
        self.assertFalse(T.executed)
        self.assertIsNone(T.success)
        self.assertIsNone(T.reasons)

        #
        # Execute - porn blocked
        # May fail if no blocking control in place to prevent access
        T.execute()
        self.assertTrue(T.executed)
        self.assertTrue(T.success)
        self.assertEqual(len(T.reasons), 0)

        #
        # Execute - Cato not blocked
        #
        T = CanisterTest(google_test)
        T.execute()
        self.assertTrue(T.executed)
        self.assertTrue(T.success)
        self.assertEqual(len(T.reasons), 0)


    def test_evaluation(self):

        #
        # response_code - missing field
        #
        sc = [{"field": "response_code","op":"is","value":403}]
        result = {"response_body":403}
        result, reasons = evaluate(result, sc)
        self.assertFalse(result)
        self.assertEqual(reasons[0], "No response_code in result")

        #
        # response_code - matching value
        #
        sc = [{"field": "response_code","op":"is","value":403}]
        result = {"response_code":403}
        result, reasons = evaluate(result, sc)
        self.assertTrue(result)
        self.assertEqual(len(reasons),0)
