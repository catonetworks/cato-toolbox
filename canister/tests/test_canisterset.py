#
# test_set.py
#
# Tests the Canister set class.
#

import unittest

from canisterset import CanisterSet, DEFAULT




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
        self.assertEqual(len(S), 1)