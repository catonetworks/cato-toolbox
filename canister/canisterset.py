#
# canister/canisterset.py
#
# Defines a collection of Canister tests.
#


from logger import Logger

from canistertest import CanisterTest


class CanisterSet:
	#
	# Defines a set of tests.
	#



	def __init__(self, target="127.0.0.1", port=8443):
		#
		# Parameters:
		# ----------
		#
		# target: the IP or hostname of a target host, for use
		#         in tests which require a co-operative target service.
		#
		# port: the port the target is listening on.
		#
		self.tests = []
		self.target = target
		self.port = port

	def __len__(self):
		return len(self.tests)

	def __iter__(self):
		for test in self.tests:
			yield test

	def __str__(self):
		text = ""
		for i,t in enumerate(self.tests):
			text += f'{i}:{t}\n'
		return text.strip('\n')


	def load(self, obj):
		#
		# Load a set of tests from the input object.
		#
		# Parameters:
		# ----------
		#
		# obj: a list of tests (dictionaries).
		#
		# Returns: 
		# -------
		# A list of errors from the set load. If the list is empty, the
		# set loaded successfully. The entire set will not load if there
		# is a single error.
		# 
		errors = []

		#
		# Check the object is a list
		#
		if type(obj) != list:
			error = f'Input object should be a list, not {type(obj)}'
			Logger.log(1, error)
			errors.append(error)
			return errors

		#
		# Iterate over tests, trying to instantiate a CanisterTest object
		# from each one. If any fail, zero the tests.
		#
		for i, item in enumerate(obj):
			try:
				new_test = CanisterTest(item)
			except Exception as e:
				error = f'{i}:{e}'
				Logger.log(1, error)
				errors.append(error)
			else:

				#
				# Substitute target for host==None
				#
				if item["host"] is None:
					new_test.host = self.target

				#
				# Substitute target for port==None
				#
				if item["port"] is None:
					new_test.port = self.port

				#
				# Add to set
				#
				self.tests.append(new_test)

		if len(errors) > 0:
			self.tests = []
		return errors



	def execute(self):
		#
		# Execute the loaded set by iterating over each test,
		# calling the test's execute() method.
		#
		Logger.log(1, f'CanisterSet:execute()')
		for ct in self.tests:
			ct.execute()



	def results(self):
		#
		# Return a dictionary of total, succeeded, failed, unexecuted counts.
		#
		# Call this after execute() to receive a summary of results.
		#
		succeeded = 0
		failed = 0
		unexecuted = 0
		total = 0
		for ct in self.tests:
			total += 1
			if not ct.executed:
				unexecuted += 1
			elif ct.success:
				succeeded += 1
			else:
				failed += 1
		return {
			"total":total, 
			"succeeded":succeeded, 
			"failed":failed, 
			"unexecuted":unexecuted
		}



#
# Define a default set
#
DEFAULT = [
	{
		"name": "Porn Site",
		"feature": "Internet Firewall",
		"description": "Access to adult websites",
		"remediation": "This access can be blocked by the Cato Internet Firewall.",
		"method": "GET",
		"protocol": "https",
		"host": "www.sex.com",
		"port": 443,
		"path": "/",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "EICAR",
		"feature": "Anti Malware",
		"description": "Download of an EICAR test file",
		"remediation": "Infected file downloads can be blocked by Cato Anti Malware.",
		"method": "GET",
		"protocol": "https",
		"host": None,
		"port": None,
		"path": "/eicar.exe",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
	    "name": "Google",
	    "feature": "Internet Firewall",
	    "description": "Access to Google website should be allowed.",
	    "remediation": "This access should not be blocked by the Cato Internet Firewall.",
	    "method": "GET",
	    "protocol": "http",
	    "host": "google.com",
	    "port": 80,
	    "path": "/",
	    "success_criteria": [{"field":"response_code","op":"is","value":200}],
	},
]

