#
# test_canistertest.py
#
# Tests the Canister test class.
#

import unittest

from canistertest import CanisterTest, mandatory_parameters, supported_protocols, supported_methods



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
        self.assertRaises(ValueError, CanisterTest, params)
        for protocol in supported_protocols:
            params["protocol"] = protocol
            T = CanisterTest(params)
            self.assertEqual(T.protocol, protocol)

    def test_methods(self):
        params = {X:"test" for X in mandatory_parameters}
        params["protocol"] = supported_protocols[0]
        self.assertRaises(ValueError, CanisterTest, params)
        for method in supported_methods:
            params["method"] = method
            T = CanisterTest(params)
            self.assertEqual(T.method, method)
