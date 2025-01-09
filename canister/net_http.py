#
# canister/net_http.py
#
# Contains functions for making web requests
#

import json
import ssl
import urllib.parse
import urllib.request



def request(url, method="GET", headers={}, body=None):
	#
	# Make a web request. TLS validation is disabled as this is usually
	# a requirement for Canister testing.
	#
	# Parameters:
	# ----------
	#
	# url: the URL to make the request of.
	#
	# method: HTTP method.
	#
	# headers: a dictionary of key:value pairs to add to the sent headers.
	#
	# body: a string to be encoded as the body.
	#
	# Returns:
	# -------
	#
	# (response_code, response_reason, response_headers, response_body)
	# response_code: integer
	# response_reason: string
	# response_headers: dictionary
	# response_body: string
	#
	try:
		if body is None:
			request = urllib.request.Request(
				url=url, 
				method=method,
				headers=headers,
			)
		else:
			request = urllib.request.Request(
				url=url, 
				method=method,
				headers=headers,
				data=json.dumps(body).encode("ascii"),
			)
		response = urllib.request.urlopen(
			request,
			context=ssl._create_unverified_context(),
		)
		response_code = response.code
		response_reason = response.reason
		response_headers = dict(response.headers)
		response_body = response.read().decode("utf-8","replace")
		return response_code, response_reason, response_headers, response_body
	except urllib.error.HTTPError as he:
		response_code = he.code
		response_reason = he.reason
		response_headers = dict(he.headers)
		response_body = he.fp.read().decode("utf-8","replace")
		return response_code, response_reason, response_headers, response_body
	except urllib.error.URLError as ue:
		response_code = None
		response_reason = ue.reason
		response_headers = {}
		response_body = ""
		return response_code, response_reason, response_headers, response_body
	except Exception as e:
		response_code = None
		response_reason = f'{e}'
		response_headers = {}
		response_body = ""
		return response_code, response_reason, response_headers, response_body
