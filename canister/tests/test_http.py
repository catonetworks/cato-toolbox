#
# test_http.py
#
# Tests for the net_http functions
#

import unittest

import net_http



class HttpTests(unittest.TestCase):


	def test_200(self):
		code, reason, headers, body = net_http.request("https://www.google.com")
		self.assertEqual(code, 200)
		self.assertEqual(reason, "OK")
		self.assertTrue(len(headers)>1)


	def test_nonexistent_domain(self):
		code, reason, headers, body = net_http.request("https://www.google.notarealdomain")
		self.assertEqual(code, None)


	def test_404(self):
		code, reason, headers, body = net_http.request("https://www.google.com/notarealurl")
		#print(code, reason, headers, body)
		self.assertEqual(code, 404)
		self.assertEqual(reason, "Not Found")

