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
		if level <= cls.level:
			entry = f'LOG{level} {datetime.datetime.now(datetime.UTC)}> {text}'
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

