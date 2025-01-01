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
	# The protocol (http...). Also defines if the test is to be
	# conducted via TLS.
	#
	"protocol",
	#
	# The target host. If None, the containing Set will insert the
	# defined target host.
	#
	"host",
	#
	# The port for the test. If None, the containing set will insert
	# its defined target port.
	#
	"port",
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
				Logger.log(1, f'Test missing mandatory parameter: {parameter}')
				raise KeyError(f'Test missing mandatory parameter: {parameter}')
		Logger.log(2, f'Test:{params["name"]} loading')

		#
		# Check protocols and methods
		#
		if params["protocol"] not in supported_protocols:
			error = f'Test:{params["name"]} unsupported protocol: {params["protocol"]}'
			Logger.log(1, error)
			raise ValueError(error)
		if params["method"] not in supported_methods:
			error = f'Test:{params["name"]} unsupported method: {params["method"]}'
			Logger.log(1, error)
			raise ValueError(error)

		#
		# Check success criteria
		#
		scs = params["success_criteria"]
		if type(scs) != list:
			error = f'Test:{params["name"]} success criteria should be a list, not {type(scs)}'
			Logger.log(1, error)
			raise TypeError(error)
		for sc in scs:
			if type(sc) != dict:
				error = f'Test:{params["name"]} each success criterion must be a dict, not {type(sc)}'
				Logger.log(1, error)
				raise TypeError(error)
			for item in sc.keys():
				if item not in supported_sc_items:
					error = f'Test:{params["name"]} unsupported item in success criteria: {item}'
					Logger.log(1, error)
					raise KeyError(error)
			if sc["field"] not in supported_sc_fields:
				error = f'Test:{params["name"]} unsupported success criteria field: {sc["field"]}'
				Logger.log(1, error)
				raise ValueError(error)
			if sc["op"] not in supported_sc_ops:
				error = f'Test:{params["name"]} unsupported success criteria op: {sc["op"]}'
				Logger.log(1, error)
				raise ValueError(error)

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
		self.port = params["port"]
		self.success_criteria = params["success_criteria"]
		self.executed = False
		self.success = None
		self.reasons = None

		#
		# Log success
		#
		Logger.log(2, f'Test:{self.name} successful load')



	def execute(self):
		#
		# The main test engine.
		#
		Logger.log(2, f'Test:{self.name} executing with {self.protocol}')


		#
		# Reset state
		#
		self.success = None
		self.reasons = None
		self.executed = False

		#
		# http/s tests
		#
		if self.protocol in ["http", "https"]:

			#
			# Construct request
			#
			url = f'{self.protocol}://{self.host}:{self.port}{self.path}'
			Logger.log(3, f'Test:{self.name} url={url}')

			#
			# Make request
			#
			response_code, response_reason, response_headers, response_body = request(
				url,
				self.method
			)
			Logger.log(3, f'Test:{self.name} response_code={response_code}')
			Logger.log(3, f'Test:{self.name} response_reason={response_reason}')
			Logger.log(4, f'Test:{self.name} response_headers={response_headers}')
			Logger.log(4, f'Test:{self.name} response_body={response_body}')

			#
			# Evaluate result
			#
			Logger.log(2, f'Test:{self.name} evaluating response')
			self.success, self.reasons = evaluate(
				{
					"response_code": response_code
				},
				self.success_criteria
			)
			self.executed = True
			Logger.log(2, f'Test:{self.name} success={self.success}')
			Logger.log(3, f'Test:{self.name} reasons={self.reasons}')


		else:

			#
			# Fatal error
			#
			error = f'Test:{self.name} FATAL no execution path for protocol={self.protocol}'
			Logger.log(0, error)
			raise ValueError(error)


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
					reasons.append(f'response_code result {results["response_code"]} = success criteria {sc["value"]}')
					successes += 1
				else:
					errors += 1
					reasons.append(f'response_code result {results["response_code"]} != success criteria {sc["value"]}')

	if errors > 0:
		return False, reasons
	if successes > 0:
		return True, reasons
	return False, ["Indeterminate result"]