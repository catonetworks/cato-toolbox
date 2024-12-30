#
# canister/canistertest.py
#
# Defines the Canister test class. Each instance defines
# a single test, the test types and success conditions.
#


from logger import Logger
from net_http import request


#
# Define the parameters which must be present in each test.
#
mandatory_parameters = [
	#
	# The name of the test.
	#
	"name",
	#
	# The control which can mitigate the test.
	#
	"feature",
	#
	# A brief description.
	#
	"description",
	#
	# Explanation of how to mitigate a failure.
	#
	"remediation",
	#
	# The target host. If None, the containing Set will insert the
	# defined target host.
	#
	"host",
	#
	# The protocol (http...). Also defines if the test is to be
	# conducted via TLS.
	#
	"protocol",
	#
	# The path for the test.
	#
	"path",
	#
	# The request method (GET etc)
	#
	"method",
	#
	# The conditions which must all be true for the test to succeed (i.e.
	# the risky activity is controlled).
	"success_criteria",
	#
]


#
# Define the supported protocols and methods
#
supported_protocols = ["http", "https"]
supported_methods = ["GET"]


#
# Define supported success criteria fields
#
supported_sc_items = ["field","op","value"]
supported_sc_fields = ["response_code"]
supported_sc_ops = ["is"]


class CanisterTest:
	#
	# Defines a single test. Tests are initialised on creation
	# with parameters passed in as a dictionary to init.
	#


	def __init__(self, params):
		#
		# Parameters:
		# ----------
		#
		# params: a dictionary of parameters.
		#
		# If the instance successfully validates, it will be ready
		# for execution. It should not be possible to have an instance
		# of this class which cannot be evaluated.
		#
		
		#
		# Check for missing mandatory parameters.
		#
		for parameter in mandatory_parameters:
			if parameter not in params:
				raise KeyError(f'Test missing mandatory parameter: {parameter}')

		#
		# Check protocols and methods
		#
		if params["protocol"] not in supported_protocols:
			raise ValueError(f'Unsupported protocol: {params["protocol"]}')
		if params["method"] not in supported_methods:
			raise ValueError(f'Unsupported method: {params["method"]}')

		#
		# Check success criteria
		#
		scs = params["success_criteria"]
		if type(scs) != list:
			raise TypeError(f'Success criteria should be a list, not {type(scs)}')
		for sc in scs:
			if type(sc) != dict:
				raise TypeError(f'Each success criterion should be a dict, not {type(sc)}')
			for item in sc.keys():
				if item not in supported_sc_items:
					raise KeyError(f'Unsupported item in success criteria: {item}')
			if sc["field"] not in supported_sc_fields:
				raise ValueError(f'Unsupported success criteria field: {sc["field"]}')
			if sc["op"] not in supported_sc_ops:
				raise ValueError(f'Unsupported success criteria op: {sc["op"]}')

		#
		# Assign params
		#
		self.name = params["name"]
		self.protocol = params["protocol"]
		self.method = params["method"]
		self.feature = params["feature"]
		self.description = params["description"]
		self.remediation = params["remediation"]
		self.host = params["host"]
		self.path = params["path"]
		self.success_criteria = params["success_criteria"]
		self.executed = False
		self.success = None
		self.reasons = None



	def execute(self):
		#
		# The main test engine.
		#

		#
		# Reset state
		#
		self.success = None
		self.reasons = None
		self.executed = False

		#
		# http tests
		#
		if self.protocol == "http":

			#
			# Construct request
			#
			url = f'{self.protocol}://{self.host}{self.path}'

			#
			# Make request
			#
			response_code, response_reason, response_headers, response_body = request(
				url,
				self.method
			)

			#
			# Evaluate result
			#
			self.success, self.reasons = evaluate(
				{
					"response_code": response_code
				},
				self.success_criteria
			)
			self.executed = True



	def __str__(self):
		attributes = {key: value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(value)}
		return f'{attributes}'



def evaluate(results, scs):
	#
	# Evaluates the given results against the success criteria.
	# It is the responsibility of the caller to ensure that the right
	# fields are supplied.
	#
	# Parameters:
	# ----------
	#
	# results: dictionary, contents of which depend on test type
	#
	# scs: list of success criteria.
	#
	# Returns:
	# -------
	#
	# Tuple of outcome (success, true or false) and reasons (list of strings
	# relating to the decision, if false).

	reasons = []
	errors = 0
	successes = 0

	#
	# Iterate over the success criteria, comparing
	# each with the results.
	#
	for sc in scs:

		#
		# response_code
		#
		if sc["field"] == "response_code":

			#
			# Check if field is present
			#
			if "response_code" not in results:
				reasons.append("No response_code in result")
				errors += 1
				continue

			#
			# Compare values
			#
			if sc["op"] == "is":
				if str(sc["value"]).lower() == str(results["response_code"]).lower():
					successes += 1
				else:
					errors += 1
					reasons.append(f'response_code result {results["response_code"]} != success criteria {sc["value"]}')

	if errors > 0:
		return False, reasons
	if successes > 0:
		return True, []
	return False, ["Indeterminate result"]