# coding: utf-8

__filename__ = "mobileProtocol.py"
__description__ = "Mobile server Implementation for Harbor Project"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"

#TODO: The logging mechanism should be encapuslated at either:
#		1. A seperate process
#		2. A pb.Root
#		3. A log server

#TODO: The database query should be abstracted

import logging, sys
from datetime import *

from twisted.internet import task
from twisted.internet import defer
from twisted.internet.protocol import (ClientFactory, ServerFactory, 
	Protocol, ReconnectingClientFactory, ProcessProtocol, ClientCreator)
from twisted.python import log, usage, components

import txcoroutine

from zope.interface import implements
from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint


from harbor.message import harbor_pb2


from harbor.interfaces.IProtocols import IProxyServerProtocol
from harbor.interfaces.IProtocols import IProxyServerFactory
from harbor.interfaces.IProtocols import ISecondaryProtocol
from harbor.interfaces.IProtocols import ISecondaryFactory
from harbor.interfaces.IServices import *


reply_server_bug_general = "Server bug\n"
reply_server_down_general = "Server down\n"



class MobileServerProtocol(Protocol):

	implements(IProxyServerProtocol)

	def __init__(self, factory):
		"""
		@param client: The client is initiated to ProxyClientCacheService obj, 
			mainly to store client info states, and client functions which to
			alter the client status.
		@type client: C{callable}	
		"""
		self.factory = factory
		self.proc = None
		self.server_proto = None
		self.isLoggedIn = False
		self.clientIp = None

	@defer.inlineCallbacks
	def connectionMade(self):
		"""
		Record remote connection ip, and check duplication connection.
		Increment total number of connections, reject new connection. 
		If the total number of connections has reached maximum value,
			return rejection msg.
		"""
		# Record remote client ip
		self.clientIp = self.transport.getPeer().host
		log.msg("New connection from %s" % self.clientIp, 
			logLevel=logging.INFO)

		# Wheter the client is granted connection based on curr server status 
		if self.factory.service.isLuckyConnection():
			#if not self.factory.clientService.clients.has_key(clientIp):
			# If the client didn't use same ip to access proxy
			# comment out for debug purpose
			self.factory.addClient(self, self.clientIp)
			# Initiate proxy-server connection
			try:
				self.server_proto = yield self.factory.connect_to_server()
			except Exception, err:
				log.msg(err, logLevel=logging.WARNING)
				self.write_to_client(reply_server_down_general)
				# hard fail if clientServer down
				self.transport.loseConnection()
		else:
			# Rejct unlucky connection
			reply = yield "Server busy, try later"
			self.write_to_client(reply)
			log.msg("Reject connection due to max capacity", 
				logLevel=logging.WARNING)
			self.transport.loseConnection()


	def dataReceived(self, request):
		"""
		Proxy will unpack data packet to validify the data and do
		pre-processing. The data format between server and proxy needs 
		to be determined.
		"""
		#TODO: Unify data format between server and proxy
		try:
			cntrl, msg = request.split('.', 1)
			cntrl = int(cntrl)
		except Exception, data:
			self.write_to_client("wrong data format\n")
			return
	
		#Record request as last request. Compare them and return immediate reply
		if cntrl is 0:
			# client request register
			username, password = request.split('.', 1)
			self.register(username, password)
		elif cntrl is 1:
			# client request login
			if not self.isLoggedIn:
				# client has not logged in
				username, password = msg.split('.', 1)
				self.login(username, password)
			else:
				# The client has already logged in
				self.write_to_client("You have logged in\r\n")
				return
		elif cntrl is 2:
			# client request work
			self.handleRequest(msg)


	@defer.inlineCallbacks
	def register(self, username, password):
		"""

		"""
		try:
			request = harbor_pb2.Request()
			request.cntrl = harbor_pb2.Request.REGISTER
			request.registerr.username = username
			request.registerr.password = password
			request = request.SerializeToString()
			self.write_to_server(request)
			result = yield self.server_proto.deferred
			# message arrived
			reply = harbor_pb2.Reply()
			reply.ParseFromString(result)
			if reply.success == True: 
				# Registered succeeded
				self.client.loginSucceed()
				# Use utf-8 for now. But will use unicode later on
				interface = reply.user.usertype.encode('utf-8')
				username = reply.user.username.encode('utf-8')
			
				self.write_to_client("%s %s registered and login" % (
					interface, username))
			else:
				# Registered failed
				reason = reply.reason.encode('utf-8')
				# Write reason to client
				self.write_to_client(reason)
		except Exception, err:
			"""
			The login fail due to server mechanism. 
			Reply back the fail reason toClient
			Doesn't impose penalty on client
			"""
			print err
			#self.write_to_client(err)

	
	@defer.inlineCallbacks
	def login(self, username, password):
		"""
		Initiate new user connection between proxy and server.
		Initiate Deferred object.
		Return Deferred.
		"""
		#TODO: Data format
		try:
			request = harbor_pb2.Request()
			request.cntrl = harbor_pb2.Request.LOGIN
			request.loginer.username = username
			request.loginer.password = password
			request = request.SerializeToString()
			self.write_to_server(request)
			result = yield self.server_proto.deferred
			# message arrived
			reply = harbor_pb2.Reply()
			reply.ParseFromString(result)
			if reply.success == True: 
				# add client
				# Login succeeded
				self.isLoggedIn = True
				# Use utf-8 for now. But will use unicode later on
				interface = reply.user.usertype.encode('utf-8')
				username = reply.user.username.encode('utf-8')
				userid = reply.user.id
			
				# Assume there is only device for now
				devicenames, devicetypes = [], []
				for device in reply.user.devices:
					devicenames.append(device.name.encode('utf-8'))
					devicetypes.append(device.type.encode('utf-8'))

				self.write_to_client("%s %s login, owns %s:%s\r\n" % (
					interface, username, devicenames, devicetypes))

				self.proc = self.handle_from_clientServer()
				#TODO
			else:
				# Login failed
				# TODO: omitted the case where client has already logged in
				# Retrive data
				reason = reply.reason.encode('utf-8')
				# Write reason to client
				self.write_to_client(reason)
		except Exception, err:
			"""
			The login fail due to server mechanism. 
			Reply back the fail reason toClient
			Doesn't impose penalty on client
			"""
			err = str(err)
			self.write_to_client(err)

	def write_to_client(self, data):
		self.transport.write(data)

	def write_to_server(self, data):
		if self.server_proto:
			self.server_proto.transport.write(data)
		else:
			raise Exception("Client Server Connection closed\n")
	
	def handleRequest(self, request):
		"""
		Handle the incoming request from client after authentication.
		Initiate deferred obj in toServerFactory, and send the request to

		if self.val is not None:
			log.msg('Using cached val.', logLevel=logging.INFO)
			return succeed(self.val)

		"""
		req = harbor_pb2.Request()
		req.cntrl = harbor_pb2.Request.WORK
		req.msg = request
		req = req.SerializeToString()
		self.write_to_server(req)


	@txcoroutine.coroutine
	def handle_from_clientServer(self):
		"""
		use coroutine to cancel deep deferred return
		"""
		while 1:
			try:
				result = yield self.server_proto.deferred
				self.write_to_client(result)
			except Exception, err:
				err = str(err) + '\n'
				if 'closed' in err:
					self.write_to_client(err)
					self.server_proto = None
					# Disable reconnect service
				break
		self.transport.loseConnection()

	def connectionLost(self, reason):

		self.factory.removeClient(self.clientIp)
		# connectionLost unwillingly

		#TODO: Need to wait sometime to wait client reconnect
		# The strategy would be to remember current client state and 
		# Recover to the reconnect-client
		if self.server_proto is not None:
			self.server_proto.deferred.addErrback(self._clientCut)
			self.server_proto.transport.loseConnection()
			

	def _clientCut(self, _):
		print "Client cut connection"

	def _serverCut(self, _):
		print "Server cut connection"

	
class MobileFactoryFromService(ServerFactory):
	implements(IProxyServerFactory)
		
	def __init__(self, service):
		"""
		@param s_ip: serverIp. With one server, s_ip is a single value.
			However, the future version should enable multiple, selective
			server connection.
		@type s_ip: C{str}
		
		@param s_port: serverPort. As the same above, the future version 
			should inclue multiple port stored at a list.
		@type s_port: C{str}
			
		"""
		self.service = service

	def startFactory(self):

		ServerFactory.startFactory(self)

		from twisted.internet import reactor

		self.toServerFactory = MobileToClientServerFactory()
		self.serverPoint = TCP4ClientEndpoint(
				reactor, '192.168.0.91', self.service.serverAddr)


	def buildProtocol(self, addr):
		return MobileServerProtocol(self)

	def connect_to_server(self):
		return self.serverPoint.connect(self.toServerFactory)	

	def addClient(self, clientIp, proto):
		#TODO: check duplication
		self.service.addClient(clientIp, proto)

	def removeClient(self, clientIp):
		self.service.removeClient(clientIp)	

		
	def isLuckyConnection(self):
		return self.service.isLuckyConnection()



components.registerAdapter(MobileFactoryFromService, 
							IProxyClientService, IProxyServerFactory)



class MobileToClientServerProtocol(Protocol):

	implements(ISecondaryProtocol)
	
	def __init__(self, factory):
		self.deferred = defer.Deferred()
		self.factory = factory
	
	def connectionMade(self):
		log.msg("I'm connected to client!")

	def dataReceived(self, data):
		if self.deferred is not None:
			d, self.deferred = self.deferred, None
			# Prepare new deferred to fireback
			# Must be called to prevent error
			self.deferred = defer.Deferred()
			d.callback(data)


	def connectionLost(self, reason):
		# Should notify proxy-client protocol
		# But when the proxy-client protocol close first
		# The defer object could go no where.
		# Either need a way to know when proxy-client closed
		# Or don't reply back when connection lost

		#log.msg(reason, logLevel=logging.DEBUG)
		"""
		if self.deferred is not None:
			d, self.deferred = self.deferred, None
			d.callback(reply)
		"""
		err = reason.getErrorMessage()
		d, self.deferred = self.deferred, None
		d.errback(err)


class MobileToClientServerFactory(ClientFactory):

	implements(ISecondaryFactory)

	def __init__(self):
		"""
		"""
		pass

	def buildProtocol(self, addr):
		return MobileToClientServerProtocol(self)

	def clientConnectionFailed(self, connector, reason):
		log.msg(reason, logLevel=logging.CRITICAL)
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		

	def clientConnectionLost(self, connector, reason):
		log.msg(reason, logLevel=logging.CRITICAL)
		ReconnectionClientFactory.clientConnectionFailed(self, connector, reason)







