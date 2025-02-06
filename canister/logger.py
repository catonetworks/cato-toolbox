#
# canister/logger.py
#
# Module-wide logger for consistent logging.
#
# Levels:
#
# 0  Always log
# 1  System start/stop
# 2  Low volume 
# 3  Higher volume logs
# 4+ Stupid volume
#
# Each call to log includes an integer level. If the level of the log entry 
# exceeds the logger level, the entry is ignored.
#


import datetime
import sys


class Logger:
	#
	# Defines the logger class.
	#

	#
	#  Class attributes
	#
	logs = []
	level = 1
	print_output = True


	@classmethod
	def callback(cls, level, text):
		#
		# Callback for additional logging
		# Override for additional output options.
		#
		# Parameters:
		# ----------
		#
		# level:	log level for this entry.
		# text: 	the text being logged.
		#
		pass


	@classmethod
	def log(cls, level, text):
		#
		# Log something
		#
		# Parameters:
		# ----------
		#
		# level: 	the level of this entry.
		# text:		the text being logged.
		# 
		#

		#
		# Might have to run on some older Pythons, especially in AWS
		#
		major = sys.version_info[0]
		minor = sys.version_info[1]
		if major == 3 and minor < 10:
			date_str = f'{datetime.datetime.utcnow()}'
		else:
			date_str = f'{datetime.datetime.now(datetime.UTC)}'
		if level <= cls.level:
			entry = f'LOG{level} {date_str}> {text}'
			cls.logs.append(entry)
			cls.callback(level, text)
			if cls.print_output:
				print(entry)


	@classmethod
	def reset(cls):
		#
		# Return to default configuration
		#
		cls.logs = []
		cls.level = 1
		cls.print_output = True

