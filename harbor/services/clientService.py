#coding: utf-8

__filename__ = "clientService.py"
__description__ = "Client Server Services"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2013-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"

import logging, random
from twisted.python import log
from twisted.internet import defer
from twisted.application import internet, service
from twisted.internet.protocol import ClientCreator
from twisted.spread import pb
from datetime import datetime

from zope.interface import implements
from twisted.cred import portal, checkers, credentials, error as credError

from txredis.protocol import Redis

from harbor.cred import userCred
from harbor.cli import user

from harbor.db.hmysql import *
from harbor.protocols.workerProtocol import IPBWorkerFactory
from harbor.services.workerService import PBWorkerClientService

from harbor.interfaces.IServices import *


"""
All errors are raised at service level
"""



class Client(service.Service):
	"""
	The Server Client Service is the service to log clients and trace clients 
	actions at server side. Not like the Mobile Client Service, this service 
	aim to deeply examine all clients activity to trace clients history, 
	update database and examine the potential malicious clients that proxy 
	is unable to detect. This service's parameters will affect server healty index.
	"""

	implements(IServerClientService)

	def __init__(self, harbor_port, workerPort, redis_db):
		"""
		@param users: The user_id list include all connected clients'id to server.
		@type users: C{list}
		
		@param num_uses: Total number of users.
		@type num_users: C{int}
		
		@param logIdCounter: The current logId which should be assigned to the 
			next client. This value should be encapsulated in the logging service
			in the future version.
		@type logIdCounter: C{int}

		@param q_logUser: The sql string to insert new logId and corresponding 
			userId into database
		@type q_logUser: C{str}
	
		@param q_unLogUser: The sql to delete row from UserLog by logId
		@type q_unLogUser: C{str}
		"""
		self.clients = {}

		self.redis_db = redis_db
		self.harbor_port = harbor_port
		self.workerPort = workerPort

		self.q_selectDeviceInfo = """ SELECT deviceId, deviceName, deviceType
										FROM Devices
										WHERE deviceId = %s
									"""
		self.redis = None
		self.dbpool = None
		self.obj = None

	@defer.inlineCallbacks
	def startService(self):
		service.Service.startService(self)
		self.dbpool = ReconnectingConnectionPool(DB_DRIVER, **DB_ARGS)
		self.portal = portal.Portal(userCred.UserRealm(self.dbpool))
		self.portal.registerChecker(userCred.UserPasswordChecker(self.dbpool))

		from twisted.internet import reactor
		clientCreator = ClientCreator(reactor, Redis)
		try:
			redis = yield clientCreator.connectTCP('localhost', 6379)
			print "connected to redis"
			self.redis = redis
			self.redis.select(self.redis_db)
			self.redis.set('num_clients', 0)
		except Exception, err:
			print "Can't connect to redis"

		workerFactory = IPBWorkerFactory(PBWorkerClientService([self.workerPort]))
		reactor.connectTCP('localhost', self.workerPort, workerFactory)	
		try:
			obj = yield workerFactory.getRootObject()
			print "Obtained worker access at port %s" % self.workerPort
			self.obj = obj
			self.obj.notifyOnDisconnect(self.loseObjNotify)
		except Exception, err:
			print "Can't access to worker"


	@defer.inlineCallbacks
	def getUserDevice(self, user_id):
		"""
		Fetch database to see what my devices are, return a list
		Then update harbor server status to retrive the device status
		The database stores static information such as device name, id, usage
		But the memory and other (may be redis) database will include 
		Dynamic info such as machine status, locations etc

		Throw all exceptions back
		"""
		q = """SELECT deviceId FROM Owns WHERE userId = %s 
			"""
		rows = yield self.dbpool.runQuery(q, user_id)

		deferreds = []
		for r in rows:
			# iterate over devices tuple
			device_id, = r
			d = self.dbpool.runQuery(self.q_selectDeviceInfo, device_id)
			deferreds.append(d)
		results = yield defer.gatherResults(deferreds, consumeErrors=True)
		defer.returnValue(results)

	
	def logClient(self, client_id, proto):
		#TODO: also update login time
		self._addClient(client_id, proto)
		return	self.dbpool.runOperation(
				"INSERT UserLog SET userId = %s" % client_id)

	def unlogClient(self, client_id):
		#TODO: also update logout time
		self._removeClient(client_id)
		return self.dbpool.runOperation(
				"DELETE FROM UserLog WHERE userId = %s" % client_id)


	@defer.inlineCallbacks
	def _addClient(self, client_id, proto):
		self.clients[client_id] = proto
		self.redis.incr('num_clients')
		res = yield self.redis.get('num_clients')
		print "Server side total clients: ", res


	def _removeClient(self, id):
		if self.clients.has_key(id):
			del self.clients[id] #TODO: Find the appropriate user
			self.redis.decr('num_clients')

	def register(self, username, password):
		"""
		Register user into database.
		Then call login user to login
		Raise error and reply back err msg
		"""
		return self.dbpool.runOperation(
				"INSERT Users SET username=%s, password=%s", 
				(username, password,))
		

	def login(self, username, password):	
		creds = credentials.UsernamePassword(username, password)
		return self.portal.login(creds, None, user.IRegisteredUser)


	def do_intensive_work(self):
		"""
		For testing pb
		"""
		if self.obj:
			# do complicated work on remote machine
			return self.obj.callRemote('storebytype', 'resturant')
		else:
			# do simple verison work on this machine
			raise Exception("No worker connected")


	def loseObjNotify(self, _):
		print "Worker lost"
		self.obj = None

	def broken(self, reason):
		"""
		Remote error handler
		Not used yet
		"""
		print "got remote Exception"
		print ".__class__=", reason.__class__
		print ".getErrorMessage() =", reason.getErrorMessage()
		print ".type =", reason.type
			

	def stopService(self):
		if self.dbpool:
			self.dbpool.close()
		if self.redis:
			self.redis.flushdb().addErrback(self._redisBug)
			self.redis.quit().addErrback(self._redisBug)

	def _redisBug(self, _):
		print "redis close bug"



	

