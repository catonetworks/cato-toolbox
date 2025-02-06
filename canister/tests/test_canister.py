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


	def test_default_init(self):
		C = canister.Canister("127.0.0.1",8080)
		self.assertEqual(C.version, "1.0")
		self.assertEqual(C.canister_set.target, "127.0.0.1")
		self.assertEqual(C.canister_set.port, 8080)

	def test_load_object(self):
		C = canister.Canister("127.0.0.1",8080)
		success, reasons = C.load_object("XXX")
		self.assertFalse(success)
		self.assertEqual(len(reasons), 1)
		self.assertEqual(reasons[0], "Input object should be a list, not <class 'str'>")
