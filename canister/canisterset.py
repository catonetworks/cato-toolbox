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
		"ttype": "web",
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
		"name": "Gambling Site",
		"ttype": "web",
		"feature": "Internet Firewall",
		"description": "Access to gambling websites",
		"remediation": "This access can be blocked by the Cato Internet Firewall.",
		"method": "GET",
		"protocol": "https",
		"host": "www.casino.com",
		"port": 443,
		"path": "/",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "Hacking Site",
		"ttype": "web",
		"feature": "Internet Firewall",
		"description": "Access to security-related websites which may indicate intent if performed by users not in an Infosec team.",
		"remediation": "This access can be blocked by the Cato Internet Firewall.",
		"method": "GET",
		"protocol": "https",
		"host": "www.kali.org",
		"port": 443,
		"path": "/",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "Embargoed Country",
		"ttype": "web",
		"feature": "Internet Firewall",
		"description": "Access to the website of a sanctioned organisation (Libyan Investment Authority).",
		"remediation": "This access can be blocked by the Cato Internet Firewall.",
		"method": "GET",
		"protocol": "https",
		"host": "www.lia.ly",
		"port": 443,
		"path": "/",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "EICAR",
		"ttype": "web",
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
		"name": "NG EICAR",
		"ttype": "web",
		"feature": "NG Anti Malware",
		"description": "Download of a Next Gen EICAR test file",
		"remediation": "Infected file downloads can be blocked by Cato Anti Malware.",
		"method": "GET",
		"protocol": "https",
		"host": None,
		"port": None,
		"path": "/ngeicar.exe",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "Zipped EICAR",
		"ttype": "web",
		"feature": "Anti Malware",
		"description": "Download of a zipped EICAR test file",
		"remediation": "Infected file downloads can be blocked by Cato Anti Malware.",
		"method": "GET",
		"protocol": "https",
		"host": None,
		"port": None,
		"path": "/eicar.zip",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "Mimikatz",
		"ttype": "web",
		"feature": "Anti Malware",
		"description": "Download the Mimikatz hacking tool",
		"remediation": "Malicious file downloads can be blocked by Cato Anti Malware.",
		"method": "GET",
		"protocol": "https",
		"host": "github.com",
		"port": 443,
		"path": "/gentilkiwi/mimikatz/releases/download/2.2.0-20220919/mimikatz_trunk.zip",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "CVE-2022-41828 AWS Redshift RCE",
		"ttype": "web",
		"feature": "IPS",
		"description": "AWS RedShift JDBC driver Remote Code Execution",
		"remediation": "Exploits can be blocked by Cato IPS.",
		"method": "POST",
		"protocol": "https",
		"host": None,
		"port": None,
		"path": "/jdbcset",
		"headers": {"Accept":"*/*", "User-Agent":"eCanister curl"},
		"body": "jdbc=jdbc:redshift://127.0.0.1:5439/testdb;socketFactory=org.springframework.context.support.FileSystemXmlApplicationContext",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "CVE-2021-44228 Log4j",
		"ttype": "web",
		"feature": "IPS",
		"description": "Apache-Log4j Remote Code Execution",
		"remediation": "Exploits can be blocked by Cato IPS.",
		"method": "GET",
		"protocol": "https",
		"host": None,
		"port": None,
		"path": "/",
		"headers": {"User-Agent":"${jndi:ldap://127.0.0.1/a"},
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "CVE-2020-10148 SolarWinds",
		"ttype": "web",
		"feature": "IPS",
		"description": "CVE-2020-10148 SolarWinds Orion authentication bypass and RCE",
		"remediation": "Exploits can be blocked by Cato IPS.",
		"method": "GET",
		"protocol": "https",
		"host": None,
		"port": None,
		"path": "/Orion/WebResource.axd",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "CVE-2020-5902 F5",
		"ttype": "web",
		"feature": "IPS",
		"description": "CVE-2020-5902 - F5 Big-IP 13.1.3 Build 0.0.6 Local File Inclusion",
		"remediation": "Exploits can be blocked by Cato IPS.",
		"method": "GET",
		"protocol": "https",
		"host": None,
		"port": None,
		"path": "/tmui/login.jsp/..;/tmui/locallb/workspace/fileRead.jsp?fileName=/etc/passwd",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "CVE-2020-9484 Apache Tomcat",
		"ttype": "web",
		"feature": "IPS",
		"description": "CVE-2020-9484 - Apache Tomcat RCE",
		"remediation": "Exploits can be blocked by Cato IPS.",
		"method": "GET",
		"protocol": "https",
		"host": None,
		"port": None,
	    "headers": {"Cookie":"cp=JSESSIONID=../.."},
		"path": "/index.jsp",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "CVE-2021-25296 Nagios RCE",
		"ttype": "web",
		"feature": "IPS",
		"description": "CVE-2021-25296 Nagios RCE",
		"remediation": "Exploits can be blocked by Cato IPS.",
		"method": "GET",
		"protocol": "https",
		"host": None,
		"port": None,
		"path": "/monitoringwizard.php?update=x&nsp=sudo",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "CVE-2020-14882 WebLogic RCE",
		"ttype": "web",
		"feature": "IPS",
		"description": "CVE-2020-14882 Oracle WebLogic Server Remote Code Execution",
		"remediation": "Exploits can be blocked by Cato IPS.",
		"method": "GET",
		"protocol": "https",
		"host": None,
		"port": None,
		"path": "/console.portal?weblogic.work.ExecuteThread&com.bea.core.repackaged.springframework.context.support.ClassPathXmlApplicationContext&.mvel2.sh.",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
		"name": "Shellshock",
		"ttype": "web",
		"feature": "IPS",
		"description": "Use Shellshock against a web server.",
		"remediation": "Exploits can be blocked by Cato IPS.",
		"method": "GET",
		"protocol": "https",
		"host": None,
		"port": None,
		"headers": {"User-Agent":"() { :; };"},
		"path": "/",
		"success_criteria": [{"field":"response_code","op":"is","value":403}],
	},
	{
	    "name": "Google",
		"ttype": "web",
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
