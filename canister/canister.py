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


	def __init__(self):
		pass


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
	# Create a Canister set for the specified target,
	# load the default set and execute.
	#
	Logger.level=0
	S = canisterset.CanisterSet(target=ip, port=port)
	S.load(canisterset.DEFAULT)
	S.execute()
	for T in S:
		if T.success:
			result = "Pass"
		else:
			result = "Fail"
		print(f'{T.name:<40} {result}')



if __name__ == "__main__":
	main()
