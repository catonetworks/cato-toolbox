#
# canister/canistertest.py
#
# Defines the Canister test class. Each instance defines
# a single test, the test types and success conditions.
#



from logger import Logger


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
]


#
# Define the supported protocols and methods
#
supported_protocols = ["http"]
supported_methods = ["GET"]


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


	def __str__(self):
		attributes = {key: value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(value)}
		return f'{attributes}'
