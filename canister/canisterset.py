#
# canister/canisterset.py
#
# Defines a collection of Canister tests.
#


from logger import Logger

from canistertest import CanisterTest


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
		"protocol": "http",
		"host": "www.sex.com",
		"path": "/",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	}
]


class CanisterSet:
	#
	# Defines a set of tests.
	#


	def __init__(self, target="127.0.0.1"):
		self.tests = []
		self.target = target

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
			errors.append(f'Input object should be a list, not {type(obj)}')
			return errors

		#
		# Iterate over tests, trying to instantiate a CanisterTest object
		# from each one. If any fail, zero the tests.
		#
		for i, item in enumerate(obj):
			try:
				new_test = CanisterTest(item)
			except Exception as e:
				errors.append(f'{i}:{e}')
			else:
				self.tests.append(new_test)
		if len(errors) > 0:
			self.tests = []
		return errors


	def execute(self):
		#
		# Execute the loaded set by iterating over each test,
		# calling the test's execute() method.
		#
		for ct in self.tests:
			ct.execute()
