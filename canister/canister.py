#
# canister/canister.py
#
# Defines the Canister application class. Users wishing to drive Canister
# programmatically will create one of these.
#



class Canister:
	#
	# The main application class.
	#
	# Attributes:
	# ----------
	#
	# version: current app version as a float, major.minor
	#
	version = "1.0"


	def __init__(self, config=None):
		#
		# Parameters:
		# ----------
		#
		# config
		# 	- Dictionary containing configuration strings. If None, use
		#     the defaults which are:
		#       set_url: https://d2abwe599gw1ne.cloudfront.net/websets
		#
		if config is None:
			self.config = {
				"set_url": "https://d2abwe599gw1ne.cloudfront.net/websets",
			}
		else:
			self.config = config
		self.check_config()


	def check_config(self):
		#
		# Sanity check the config, looking for missing and extra fields.
		#
		required_fields = ["set_url"]
		for k,v in self.config.items():
			if k not in required_fields:
				raise ValueError(f'Unexpected field in Canister config: {k}')
		for field in required_fields:
			if field not in self.config:
				raise ValueError(f'Missing field from Canister config: {field}')