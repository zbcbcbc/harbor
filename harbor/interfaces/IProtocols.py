# coding: utf-8

__filename__ = "IProtocols.py"
__description__ = "Client server for Harbor Project"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"


from zope.interface import Interface, Attribute

#TODO
"""
1. argument parsing with twisted.
2. python collections
3. redis

"""

class IClientServerProtocol(Interface):
	"""
	"""

class IClientServerFactory(Interface):
	"""
	"""
	#self.workerService = services[0]
	service = Attribute("service")
		# Encapsulate this
	to_harbor_f = Attribute("ServerToHarborFactory()")
	q_registerUser = Attribute("INSERT Users SET username=%s, password=%s")
	q_selectDeviceInfo = Attribute(""" SELECT deviceId, deviceName, deviceType 
										FROM Devices 
										WHERE deviceId=%s
											""")

	def buildProtocol(addr):
		"""
		"""
	
	def startFactory():
		"""
		Connection db and initiate register portal
		"""
		
	def stopFactory(self):
		"""
		#Stopping all workers
		#TODO: sometimes obj or factory only one exists
		#BUG: The factory could be added when calling items,
		# possible factory missing
		#for k, v in self.workerService.workers.items():
		#	v[1].stopFactory()
		"""

	def login(username, password):
		"""
		"""

	def register(username, password):
		"""
		"""

	def logClient(client_id):
		"""
		"""
	
	def unlogClient(client_id):
		"""
		"""

	def getUserDevice(user_id):
		"""
		"""




class ISecondaryProtocol(Interface):
	"""
	"""
	factory = Attribute("factory")
	state = Attribute("handShake")
	deferred = Attribute("defer.Deferred()")

	def connectionMade():
		"""
		"""

	def dataReceived(data):
		"""
		"""

	def getData():
		"""
		"""

	def connectionLost(self, reason):
		"""
		"""

class ISecondaryFactory(Interface):
	"""
	"""



class IDeviceServerProtocol(Interface):
	"""
	"""
	devices = Attribute("devices")
	num_connected = Attribute("")
	factory = Attribute("factory")

	avatarInterface = Attribute("None")
	avatar = Attribute("None")
	loginFlag = Attribute("False")
	
	deferred = Attribute("defer.Deferred()")
	

	def dataReceived(data):
		"""
		"""

	def login(deviceCode, pin):
		"""
		"""


	def replyClient():
		"""
		"""
	
				

	def Logout():
		"""

		"""

	def connectionLost(reason):
		"""
		Reason is the area to categorize types
		"""

	def terminateConnection():
		"""
		"""

class IDeviceServerFactory(Interface):
	"""
	"""
	devices = Attribute("{}")
	num_connected = Attribute("0")
	client_f = Attribute("FromClientServerFactory(self.devices)") 
	clientServerPort = Attribute("int(port)")

	def buildProtocol(addr):
		"""
		"""
	def startFactory():
		"""
		Connection db and initiate register portal
		"""


	def stopFactory():
		"""
		"""
			
class IDeviceClientProtocol(Interface):
	"""
	@param harborDevices: All devices connected to Harbor Server.
	@type harborDevices: py{dict}
	
	@param clients: All clients connected from clientServer.
	@type clients: py{dict}
	
	@param num_clients: Total number of clients
	@type num_clients: c{int}
		
	"""	
	harborDevices = Attribute("harborDevices")
	clients = Attribute("clients")
	num_clients = Attribute("num_clients")

	state = Attribute("handshake")
	userId = Attribute("")
	factory = Attribute("factory")
	devices = Attribute("{}")

	def connectionMade():
		"""
		"""

	def dataReceived(data):
		"""
		"""

	def handshake(data):
		"""
		record userid, and user devicesid
		found online devices from harbor and record in user devices
		keep updating user devices at loop
		"""
		

	def send_to_device(d_id, cmd=None, msg=None):
		"""
		"""

	def send_to_client(data):
		"""
		"""

	def updateUserDevices():
		"""
		"""
				
	def handleRequest(data):
		"""
		"""


	def recv_from_device():
		"""
		"""

	def connectionLost(reason):
		"""
		"""


class IDeviceClientFactory(Interface):
	"""
	@param clients: {userId:(protocol, connected)}
	@type clients: py{dict}
	"""

	harborDevices = Attribute("harborDevices")
	clients = Attribute("{}")
	num_clients = Attribute("0")
		
	
	def buildProtocol(addr):
		"""
		"""
	def updateClientDevices(devices):
		"""
		"""

	def matchClientDevices(self, d_ids, devices):
		"""
		"""



class IProxyServerFactory(Interface):
	"""
		@param s_ip: serverIp. With one server, s_ip is a single value.
			However, the future version should enable multiple, selective
			server connection.
		@type s_ip: C{str}
		
		@param s_port: serverPort. As the same above, the future version 
			should inclue multiple port stored at a list.
		@type s_port: C{str}
			
	"""
	s_port = Attribute("serverAddr")
	toClientServerF = Attribute("MobileToServerFactory()")
	clientServerConn = Attribute("None")

	def buildProtocol(addr):
		"""
		"""
		

	def startFactory(self):
		"""
		"""
		# initiate server end point
	def buildProtocol(self, addr):
		"""
		"""

	def connect_to_server(self):
		"""
		"""	

	def addClient(self, clientIp, proto):
		"""
		"""

	def removeClient(self, clientIp):
		"""
		"""


	def write_to_server(self, data, proto):
		"""
		"""



class IProxyServerProtocol(Interface):


	client_service = Attribute("")
	clients_service = Attribute("")
	proc = Attribute("")

	def connectionMade():
		"""
		Record remote connection ip, and check duplication connection.
		Increment total number of connections, reject new connection. 
		If the total number of connections has reached maximum value,
			return rejection msg.
		"""

	def dataReceived(request):
		"""
		Proxy will unpack data packet to validify the data and do
		pre-processing. The data format between server and proxy needs 
		to be determined.
		"""


	def registerUser(request):
		"""

		"""
	
	def authenticate(request):
		"""
		Initiate new user connection between proxy and server.
		Initiate Deferred object.
		Return Deferred.
		"""

	def writeToClient(data):
		"""
		"""
		
	
	def handleRequest(request):
		"""
		Handle the incoming request from client after authentication.
		Initiate deferred obj in toServerFactory, and send the request to

		if self.val is not None:
			log.msg('Using cached val.', logLevel=logging.INFO)
			return succeed(self.val)

		"""
	
	def recv_from_clientServer():
		"""
		"""	


	def connectionLost(reason):
		"""
		"""

		
	def terminate():
		"""
		"""


