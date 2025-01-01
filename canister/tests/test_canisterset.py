#
# test_set.py
#
# Tests the Canister set class.
#

import os
import unittest

from canisterset import CanisterSet, DEFAULT
from logger import Logger
Logger.print_output = False




class TestSet(unittest.TestCase):
    #
    # Set tests.
    #


    def test_init(self):
        #
        # Check initialisation.
        #
        S = CanisterSet()
        self.assertEqual(len(S), 0)
        self.assertEqual(len(S.tests), 0)
        self.assertEqual(S.target, "127.0.0.1")


    def test_load(self):
        #
        # Invalid obj type
        #
        S = CanisterSet()
        errors = S.load("Test")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0], "Input object should be a list, not <class 'str'>")
        #
        # Default
        #
        S = CanisterSet()
        errors = S.load(DEFAULT)
        self.assertEqual(len(errors), 0)
        self.assertTrue(len(S) > 2)


    def test_execute(self):
        S = CanisterSet()
        errors = S.load(DEFAULT)
        self.assertEqual(len(errors), 0)
        test_count = len(S)
        self.assertTrue(test_count > 0)
        S.execute()
        results = S.results()
        self.assertEqual(results["unexecuted"], 0)
        self.assertEqual(results["failed"], 0)
        self.assertEqual(results["succeeded"], test_count)
        self.assertEqual(results["total"], test_count)

