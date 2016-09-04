# coding: utf-8

__filename__ = "/protocols/clientProtocol.py"
__description__ = "Client server for Harbor Project"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"
 
import os, sys, logging

from twisted.internet import defer
from twisted.internet import task
from twisted.spread import pb
from twisted.internet.protocol import (ServerFactory, ClientFactory, Protocol,
									ClientCreator)
from twisted.python import log, usage, components
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint

import txcoroutine

from zope.interface import implements

from harbor.message import harbor_pb2
from harbor.message.protoWrapper import reply_fail

from harbor.services.workerService import PBWorkerClientService
from harbor.protocols.workerProtocol import IPBWorkerFactory

from harbor.interfaces.IProtocols import *
from harbor.interfaces.IServices import *

reply_duplicate_username = "Username already exists.\n"
reply_register_fail_general = "Please try again.\n"



"""
@global param WORKER_RETRIVE_INT: The interval in sec to retrive offline workers
@type WORKER_RETRIVE_INT: C{int}
"""
WORKER_RETRIVE_INT = 5

HARBOR_CONNECT_INT = 5



class ClientServerProtocol(Protocol):
	"""
	Just reminder. Python class is created in memory.
	When there is a __metaclass__ attribute, python create in memory a 
	class object.
	"""	
	implements(IClientServerProtocol)

	def __init__(self, factory):
		#TODO: encapsulated at serverClintCacheService
		"""
		@param avatarInterface: Indicates the type of logon user.
		@type avatarInterface: C{Interface}

		@param avatar: The user avatar which includes user information from database.
		@type avatar: C{avatar}
		
		@param onLogout: The logout function called when user log out.
		@type: C{callable}
	
		@param loginFlag: The flag indicates whether the user has logged in or not.
			True: logged in, False: logged out.
		@type: C{bool}
		"""
		self.factory = factory
		self.avatarInterface = None		
		self.avatar = None
		self.isLoggedIn = False
		self.harborConn = None
		self.proc = None
		self.loginTrials = 0
	
	def dataReceived(self, data):
		"""
		Check number of availabe worker first, if there is no worker
			connected, reply back server busy.
		If avatar obj is None, assume user has not logged in. Start 
			authentication process,
		Elif avatar obj is not None, start work process.
		"""
		#TODO: periodically retrieve offline workers
		#TODO: Need control message from proxy
		"""
		if self.factory.workerService.num_workers <= -1:
			# WHen the case no worker is available
			#TODO: This is debug-only reply message
			self.transport.write("f:Server down")
			#TODO: use f for failure and s for success is a naive and 
			# error porne way
			log.msg("No worker available!", logLevel=logging.WARNING)
			return
		"""
		request = harbor_pb2.Request()
		request.ParseFromString(data)

		if request.cntrl == 0:
			# Register
			if not self.isLoggedIn:
				# Register if user has not logged in
				username = request.registerr.username.encode('utf-8')
				password = request.registerr.password.encode('utf-8')
				#TODO: strip is a deprecated method
				username = username.strip()
				password = password.strip()
				self.register(username, password)
			else:
				# In case the user has already logged in. 
				# The proxy could check, but this introduce the 
				# redundancy to ensure service quality
				reply_fail(self, "Please log out first.\n")
		elif request.cntrl == 1:
			#login
			if not self.isLoggedIn:
				# Login if user has not logged in
				username = request.loginer.username.encode('utf-8')
				password = request.loginer.password.encode('utf-8')

				if not self.factory.service.clients.has_key(username):
					# Prevent duplicate login
					# Strip should be deprecated
					username = username.strip()
					password = password.strip()
					self.login(username, password)
				else:
					reply_fail(self, "You have logged in somewhere else.\n")
			else:
				# In case the user has already logged in. 
				# The proxy could check, but this introduce the 
				# redundancy to ensure service quality
				reply_fail(self, "You have already logged in.\n")
		elif request.cntrl == 2:
			# User doesn't have to log in to retrive work now
			self.handleClientCommand(request.msg.encode('utf-8'))

	@defer.inlineCallbacks
	def register(self, username, password):
		"""
		Register user into database.
		Then call login user to login
		Trap error and reply back err msg
		"""
		try:
			r = yield self.factory.register(username, password)
			# register user success, login user afterwards
			self.login(username, password)
		except Exception, err:
			# register user fail
			log.msg(err, logLevel=logging.DEBUG)
			#TODO: convert from err to string
			err = str(err)
			reply = harbor_pb2.Reply()
			
			if "duplicate" in err.lower(): 
				# If duplicate username
				reply_fail(self, reply_duplicate_username)
			else:
				# Other error
				reply_fail(self, reply_register_fail_general)
			

	@defer.inlineCallbacks
	def login(self, username, password):
		"""
		Authentication use twisted portal
		
		"""
		try:
			# do login
			avatarInfo = yield self.factory.login(username, password)
			# login succeed
			self.avatarInterface, self.avatar, _ = avatarInfo
			print self.avatar.devices
			# update login flag
			self.isLoggedIn = True
			# compose reply message
			reply = harbor_pb2.Reply()
			reply.user.id = self.avatar.userId
			reply.user.username = self.avatar.username
			reply.user.usertype = "user" #TODO: need proper interface
			reply.success = True
			try:
				# connect to HarborServer, it is done after reply success to
				# client. This is because the Harbor connection might be fragile
				# or disconnected due to different reasons. But the connection
				# will be reopen if server is free agian.
				# TODO: repeated connection and remember connection state
				self.harborConn = yield self.factory.connect_to_harbor()				
				# connection success	
				# start receving message from harbor
				self.proc = self.recv_from_harbor()
				# fetch user devices
				results = yield self.factory.getUserDevice(self.avatar.userId)
				for r in results:
					# iterfate over tuple
					(deviceId, devicename, devicetype), = r
					self.avatar.devices[deviceId] = {devicename, devicetype}
					# assgin to pb
					new_device = reply.user.devices.add()
					new_device.id = deviceId
					new_device.name = devicename
					new_device.type = devicetype
			except Exception, err:
				# connect to HarborServer fail
				print err
				# TODO:because proxy doens't expect any msg
			finally:
				reply = reply.SerializeToString()
				# forward message to Harbor Server
				if self.harborConn:
					self.write_to_harbor(reply)
				# log user and reply back to client
				defer.maybeDeferred(self.factory.logClient(self.avatar.userId,
					self)).addBoth(lambda _: self.write_to_client(reply))

				# start receving msg from harbor
		except Exception, err:
			# login fail
			self.loginTrials += 1
			err = str(err) + '\n'
			reply_fail(self, err)


	def write_to_client(self, data):
		self.transport.write(data)
	
	def write_to_harbor(self, data):
		if self.harborConn:
			self.harborConn.transport.write(data)


	@txcoroutine.coroutine
	def recv_from_harbor(self):
		"""
		Handle all data received from Harbor since connected to Harbor Server
		"""
		while True:
			try:
				msg = yield self.harborConn.getData()
				print "got msg: %s" % msg
				self.write_to_client(msg)
				#TODO process msg and forward the msg back to proxy
			except Exception, err:
				err = yield str(err)
				if 'closed' in err:
					self.write_to_client("Harbor Server Connection lost\n")
					self.harborConn = None
					#TODO: Try to reconnect to harbor
				break

	
	def handleClientCommand(self, data):
		"""
		Fetch result through worker then logout user immediately
		This is only a test version
		"""
		try:
			if self.harborConn:
				# harbor connection established
				device_id, msg = data.split('.')
				cmd = harbor_pb2.Command()
				cmd.deviceId = int(device_id)
				cmd.msg = msg
				cmd = cmd.SerializeToString()
				self.write_to_harbor(cmd)
			else:
				# should be Harbor error
				raise Exception("Harbor connection closed\n")
		except Exception, err:
			# TODO: Only some err will need to write to client
			# And the word used should be different
			err = str(err)
			self.write_to_client(err)


	@defer.inlineCallbacks
	def userLogout(self):
		"""
		When logout, write user logout time, lasting period and 
		logout reason, logout ip into database.
		But haven't decided if server should do this or the avatar
		itself do this
		"""
		# update login flag
		if self.isLoggedIn is False: return	
		# unlog user
		_ = yield self.factory.unlogClient(self.avatar.userId)
		# cancel recv from harbor process
		if self.proc is not None:
			self.proc.cancel()
		# call avatar logout function
		self.avatar.logout()
		self.loginFlag = False

		

	def connectionLost(self, reason):
		"""
		Reason is the area to categorize types
		"""
		log.msg(reason, logLevel=logging.WARNING)
		self.userLogout()
		if self.harborConn is not None:
			self.harborConn.transport.loseConnection()

	def terminateConnection(self):
		self.transport.loseConnection()


class ClientServerFactoryFromService(ServerFactory):

	implements(IClientServerFactory)

	def __init__(self, service):
		"""
		@param workerService: The workerService ensures server retrive offline 
			workers constantly and monitor worker status at server side.
		@type workerService: C{callable}
		
		@param clientService: The clientService	hasn't been defined yet.
		@type workerService: C{callable}

		@param appService: The appService includes different application services.
			This service won't be defined untill the server establish stability 
			and relibality.
		@type C{callable}

		@param portal: The portal to login.
		@type C{callable}

		@param connections: All connections from proxy to client. It will be 
			encapsulated inside clientService in the future.
		@type C{callable}

		@param numConnections: The total number of connections from proxy to client.
			Should be encapsulated inside clientService in the future.
		@type C{int}	
		"""
		self.service = service
		# this will be moved out in future release
		self.to_harbor_f = ClientToDeviceFactory()
		

		self.q_registerUser = "INSERT Users SET username=%s, password=%s"
		self.q_selectDeviceInfo = """ SELECT deviceId, deviceName, deviceType 
										FROM Devices 
										WHERE deviceId=%s
											"""


	def buildProtocol(self, addr):
		return ClientServerProtocol(self)
	

	def startFactory(self):
		"""
		Connect to Harbor
		"""
		# this will be moved out in future release
		from twisted.internet import reactor	
		self.to_harbor_point = TCP4ClientEndpoint(reactor, 'localhost',
									self.service.harbor_port)



	def login(self, username, password):
		return self.service.login(username, password)

	def register(self, username, password):
		return self.service.register(username, password)

	def logClient(self, client_id, proto):
		return self.service.logClient(client_id, proto)
	
	def unlogClient(self, client_id):
		return self.service.unlogClient(client_id)

	def getUserDevice(self, user_id):
		return self.service.getUserDevice(user_id)	

	def connect_to_harbor(self):
		return self.to_harbor_point.connect(self.to_harbor_f)



components.registerAdapter(ClientServerFactoryFromService,
							IServerClientService,
							IClientServerFactory)


class ClientToDeviceProtocol(Protocol):

	implements(ISecondaryProtocol)

	def __init__(self, factory):
		
		#TODO: need a way to assign userId
		self.factory = factory
		self.state = "handShake"
		self.deferred = defer.Deferred()

	def connectionMade(self):
		log.msg("Im connected to Harbor\n")

	def dataReceived(self, data):
		if self.deferred is not None:
			d, self.deferred = self.deferred, None
			self.deferred = defer.Deferred()
			d.callback(data)	

	def getData(self):
		return self.deferred

	def connectionLost(self, reason):
		err = reason.getErrorMessage()
		log.msg(err, logLevel=logging.DEBUG)
		d, self.deferred = self.deferred, None
		d.errback(err)


class ClientToDeviceFactory(ClientFactory):

	implements(ISecondaryFactory)

	def __init__(self):
		self.conns = {}
		self.num_connected = 0
		
	def buildProtocol(self, addr):
		return ClientToDeviceProtocol(self)
	
	def clientConnectionLost(self, connector, reason):
		#TODO: need to reimplement below. Hack this function later
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
	
	def clientConnectionFailed(self, connector, reason):
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)


