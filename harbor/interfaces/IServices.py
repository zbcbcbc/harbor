from zope.interface import Interface, Attribute

class ICommandService(Interface):
	"""
	"""

class ILogService(Interface):
	"""
	Extra service for login client
	"""
	 #TODO: timezone

	def logClient(client_id):
		"""
		inlineCallbacks
		"""

	def unlogClient(client_id):
		"""
		inlineCallbacks
		"""
	

class ILoginService(Interface):
	"""
	"""
	client_id = Attribute("None")
	logTrials = Attribute("None")
	loginTime = Attribute("None")
	isLogin = Attribute("None")

	def register(username, password):
		"""
		"""
	
	def login(username, password):
		"""
		"""
	def logout():
		"""
		"""


	def isLoggedIn():
		"""
		"""


class IProxyClientService(Interface):
	"""
	To record client info and connection status at proxy server.
	Remember user actions and reconnect clients
	Prevent malicious server injections, attacks
	"""
	clients = Attribute("Dict: {(ip:hoverPeriod, request/sec)}")
	num_clients = Attribute("Totoal number of connected clients")

	def isLuckyConnection(self):
		"""
		Generate a lucky number to indicate whether to reject connection or not.
		Return true accept connection, return false to reject
		"""

	
	
	def addClient(client_id, proto):
		"""
		"""


	def removeClient(client_id):
		"""
		"""


	def register(username, password, proto):
		"""
		"""

	def login(self, username, password, proto):
		"""
		"""


	def handleRequest(request, proto):
		"""
		"""


class IServerClientService(Interface):
	"""
	To record client info and connection status at proxy server.
	Remember user actions and reconnect clients
	Prevent malicious server injections, attacks
	"""
	clients = Attribute("Dict: {(ip:hoverPeriod, request/sec)}")
	blacknames = Attribute("Potential maclicious client ips")
	num_clients = Attribute("Totoal number of connected clients")



	def addClient(client_id, proto):
		"""
		"""

	def removeClient(client_id):
		"""
		"""

	def isLuckyConnection():
		"""
		"""

	def logClient(client_id):
		"""
		inlineCallbacks
		"""

	def unlogClient(client_id):
		"""
		inlineCallbacks
		"""

	def register(username, password):
		"""
		"""
	
	def login(username, password):
		"""
		"""
	def logout():
		"""
		"""

	def isLoggedIn():
		"""
		"""

class IDeviceClientService(Interface):
	"""
	"""
	def updateClientDevices():
		"""
		"""

	def handleRequest():
		"""
		"""

	def matchClientDevices(usr_devices, devices):
		"""
		To match client owned devices with Harbor devices.
		If the device shows up at Harbor devices list, the 
		device will be noted as online, ootherwise offline.

		usr_devices are .proto objects which is defined at 
		harbor.proto. The devices is the dictionary to contain 
		user devices status.

		Return cntrl and waiting sets. cntrl sets contains all 
		device ids which can be controlled by client. Waiting sets 
		contains online devices but can not currently be controlled.

		In the future release, no cntrl list is returned, the user will 
		only be able to control the device if he explictly ask to.
		"""


class IDeviceService(Interface):
	"""
	"""
	def login(deviceCode, pin, portal):
		"""
		"""
	def push_to_client(response, proto):
		"""
		"""


class IPBWorkerClientService(Interface):
	"""
	WorkerService at Server side.
	Retrive workers, keep workers online, recall offline workers
	Register workers, unregister workers
	"""

	workers = Attribute("Dict:{(port: obj, factory)}")
	offlineWorkers = Attribute("List:(port)")
	num_workers = Attribute("Total number of available workers")



	"""
	def retriveWorkers():
		Import reactor (not sure if its right to do this).
		Inititate new PBWorkerFactory for each connection to worker.
		Connect to worker and grab pb.root. 
		Callback on registerWorker, and Errback on retriveWorkerFail
	"""
	def unRegisterWorker(port):
		"""
		"""
		#TODO: Exception feature needed!

	def startWork(expression):
		"""
   		Do different types of work and assgin to different workers
		"""
