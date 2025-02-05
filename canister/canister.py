#
# canister/canister.py
#
# Defines the Canister application class. Users wishing to drive Canister
# programmatically can create one of these. The module can also be called
# from the command line as a no-code option.
#

import sys

import canisterset
from logger import Logger




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


	def __init__(self, ip, port):
		#
		# Initialise the Canister client object.
		#
		# Parameters:
		# ----------
		#
		# ip 	The IP address of the target for reflected tests
		# port 	The port of the reflected target
		#
		self.canister_set = canisterset.CanisterSet(target=ip, port=port)


	def load_object(self, cset):
		#
		# Loads a CanisterSet object
		#
		# Parameters:
		# ----------
		# cset 	A CanisterSet as a list of dictionaries.
		#       See canisterset.py for documentation.
		#
		# Returns:
		# -------
		# (success, reasons)
		#
		# success	True if the load was successful, otherwise False.
		#
		# reasons	If the load was false, self.canister_set.errors will
		# 			contain a list of strings indicating the cause(s).
		#
		reasons = self.canister_set.load(cset)
		if len(reasons) > 0:
			return False, reasons
		else:
			return True, reasons


	def execute(self):
		#
		# Executes the loaded set.
		#
		self.canister_set.execute()


	def results(self):
		#
		# Returns the results of the last run.
		#
		return self.canister_set.results()



#
# The main() function allows us to call this module from the command line
# with no additional scripting required, specifying the server IP and port
# for the target (catcher).
#

def main():
	#
	# Example command line would be:
	# 
	# python3 -m canister <server_ip> <server_port>
	#
	# server_ip: the IP or host of the catcher.
	# server_port: the port the catcher is listening on for web attacks.
	#

	#
	# Process the CLI
	#
	if len(sys.argv) < 3:
		print("Error: not enough arguments. Both the server IP and port must be specified.")
		print("For example: python3 -m canister 192.168.1.1 8443")
		sys.exit(1)
	ip = sys.argv[1]
	port = int(sys.argv[2])

	#
	# Initialise the logger
	# 
	def NicePrint(level, text):
		print("*", text)
	Logger.level=1
	Logger.print_output = False
	Logger.callback = NicePrint

	#
	# Create the object
	#
	C = Canister(ip, port)

	#
	# Print the welcome
	#
	print(f'Canister v{C.version} loading default test set')

	#
	# Load the default set
	#
	C.load_object(canisterset.DEFAULT)
	print(f'Loaded {len(C.canister_set)} tests, executing:')

	#
	# Execute with logging 
	#
	C.execute()

	#
	# Print the results
	#
	print("\nResults:\n-------")
	for T in C.canister_set:
		if T.success:
			result = "Pass"
		else:
			result = "Fail"
		print(f'{T.name:<40} {result}')
	results = C.results()
	print("")
	print(f'Total:{results["total"]}\
 Succeeded:{results["succeeded"]} ({results["succeeded"]*100/results["total"]:.1f}%)\
 Failed:{results["failed"]} ({results["failed"]*100/results["total"]:.1f}%)')



if __name__ == "__main__":
	main()
