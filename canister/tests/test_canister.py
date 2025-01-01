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
		self.assertEqual(C.config["set_url"], "https://d2abwe599gw1ne.cloudfront.net/websets")


	def test_custom_load(self):
		good_config = {
			"set_url": "XXX",
		}
		bad_config_extra = {
			"set_url": "XXX",
			"extra_field": "YYY",
		}
		bad_config_missing = {
			"set_urXXX": "YYY",
		}
		#
		# Good load, check inputs
		#
		C = canister.Canister()
		self.assertEqual(C.version, "1.0")
		self.assertEqual(C.config["set_url"], "https://d2abwe599gw1ne.cloudfront.net/websets")
		#
		# Extra config
		#		
		self.assertRaises(ValueError, canister.Canister, {"config":bad_config_extra})
		self.assertRaises(ValueError, canister.Canister, {"config":bad_config_missing})
