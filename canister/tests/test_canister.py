#
# test_Canister.py
#
# Tests for the Canister class
#

import canister
import unittest

from logger import Logger
Logger.print_output = False

class InitTests(unittest.TestCase):


	def test_default_load(self):
		C = canister.Canister()
		self.assertEqual(C.version, "1.0")
