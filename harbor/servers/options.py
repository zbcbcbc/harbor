import sys
from twisted.python import usage

LAB_INTERFACE = '192.168.0.91'
PROXY_PORT = 3333
CLIENT_PORT = 3334
HARBOR_PORT = 3335
WORKER_PORT = 3336
DEVICE_PORT = 3340


class Options(usage.Options):
	optFlags = [
		["debug", "d", "Debug mode incur all debugging messages"]
	]

class ProxyOptions(Options):
	optFlags = []
	optParameters = [
		["interf", "i", LAB_INTERFACE, "Proxy interface"],
		["cinterf", "ci", "localhost", "Client Server interface"],
		["port", "p", PROXY_PORT, "Proxy listening port", int],
		["cport", "cp", CLIENT_PORT, "Client server listening port", int],
		["log", "l", sys.stdout, "The log file path"]
	]

	def parsArgs(self, *args):
		self['left'] = args
	
	def postOptions(self):
		if self["interf"] == self["cinterf"] and self['cport'] == self['port']:
			raise usage.UsageError, "Proxy and Client Server can't listen on " \
									"the same port and same interface."



class ClientServerOptions(Options):
	optFlags = []
	optParameters = [
		["interf", "i", "localhost", "Client Server interface"],
		["winterf", "ci", "localhost", "Worker interface"],
		["hinterf", "hi", "localhost", "Harbor interface"],
		["port", "p", CLIENT_PORT, "Client Server listening port", int],
		["wport", "wp", WORKER_PORT, "Worker listening port", int],
		["hport", "hp", HARBOR_PORT, "Harbor server listening port", int],
		["log", "l", sys.stdout, "The log file path"]
	]

	def parsArgs(self, *args):
		self['left'] = args
	
	def postOptions(self):
		if self["interf"] == self["hinterf"] and self['port'] == self['hport']:
			raise usage.UsageError, "Client and Harbor can't listen on " \
									"the same port and same interface."



class HarborOptions(Options):
	optFlags = []
	optParameters = [
		["interf", "i", LAB_INTERFACE, "Harbor Server interface"],
		["cinterf", "i", 'localhost', "Client Server interface"], 
		["dport", "p", DEVICE_PORT, "Harbor Server listening port", int],
		["port", "wp", HARBOR_PORT, "Harbor Client listening port", int],
		["log", "l", sys.stdout, "The log file path"]
	]

	def parsArgs(self, *args):
		self['left'] = args
	
	def postOptions(self):
		if self['port'] == self['dport']:
			raise usage.UsageError, "Harbor server can't listen on " \
									"the same port and same interface."



class WorkerOptions(Options):
	optFlags = []
	optParameters = [
		["interf", "i", "localhost", "Worker interface"],
		["port", "p", WORKER_PORT, "Worker listening port", int],
		["log", "l", sys.stdout, "The log file path"]
	]

	def parsArgs(self, *args):
		self['left'] = args
	
	def postOptions(self):
		pass
