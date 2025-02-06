#
# test_logger.py
#
# Test the logger module
#


import unittest 

from logger import Logger



class TestLogger(unittest.TestCase):


	def test_logger(self):

		#
		# Check initial config
		#
		Logger.reset()
		self.assertTrue(Logger.print_output)
		Logger.print_output = False
		self.assertEqual(Logger.level, 1)
		self.assertEqual(len(Logger.logs), 0)

		#
		# Default log levels
		#
		Logger.log(2, "Shouldn't be logged")
		self.assertEqual(len(Logger.logs), 0)
		Logger.log(1, "Should be logged")
		Logger.log(0, "Should be logged")
		self.assertEqual(len(Logger.logs), 2)

		#
		# Change log level
		#
		Logger.level = 3
		self.assertEqual(Logger.level, 3)
