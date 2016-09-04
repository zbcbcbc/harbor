# coding: utf-8

__filename__ = "deviceService.py"
__description__ = "Device Server Services"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"
 
import os, sys, logging

from twisted.internet import defer
from twisted.internet import task
from twisted.python import log, failure
from twisted.enterprise import adbapi
from twisted.internet.protocol import ClientCreator
from twisted.cred import portal, checkers, credentials, error as credError
from twisted.application import internet, service

from zope.interface import implements

from txredis.protocol import Redis

from harbor.cred import deviceCred
from harbor.dev import drone
from harbor.db.hmysql import *
from harbor.protocols.workerProtocol import IPBWorkerFactory
from harbor.services.workerService import PBWorkerClientService
from harbor.interfaces.IServices import IDeviceService, IDeviceClientService
from harbor.interfaces.IDevices import IDrone




"""
Service module will raise any error to factory which may affect protocols
"""



	
class DeviceService(service.Service):

	implements(IDeviceService)
	"""
	"""
	def __init__(self, port, redis_db):
		self.clientServerPort = port
		self.h_devices = dict()
		self.num_connected = 0
		self.redis_db = redis_db
		self.dbpool = None
		self.portal = None
		self.redis = None
		self.obj = None

	@defer.inlineCallbacks
	def startService(self):
		self.dbpool = ReconnectingConnectionPool(DB_DRIVER, **DB_ARGS)
		self.portal = portal.Portal(deviceCred.DeviceRealm(self.dbpool))
		self.portal.registerChecker(deviceCred.DevicePinChecker(self.dbpool))

		from twisted.internet import reactor
		clientCreator = ClientCreator(reactor, Redis)
		try:
			redis = yield clientCreator.connectTCP('localhost', 6379)	
			print "connected to redis"
			self.redis = redis
			self.redis.select(self.redis_db)
			self.redis.set('num_connected', 0)
		except Exception, err:
			print "can't connect to redis"

		workerFactory = IPBWorkerFactory(PBWorkerClientService([3336]))
		reactor.connectTCP('localhost', 3336, workerFactory)
		try:
			obj = yield workerFactory.getRootObject()
			self.obj = obj
			print "Obtained worker access at 3336"
			self.obj.notifyOnDisconnect(self.loseObjNotify)
		except Exception, err:
			print "Can't access to worker"


	def login(self, deviceCode, pin):
		creds = credentials.UsernamePassword(deviceCode, pin)
		return self.portal.login(creds, None, IDrone)	


	def registerDevice(self, device, conn):
		if not self.h_devices.has_key(device.id):
			# new registered device
			self.h_devices[device.id] = device
			self.redis.incr('num_connected')
		else:
			pass

	def unregisterDevice(self, device_id):
		"""write device status to database inorder to retrive later
		"""
		try:
			del self.h_devices[device_id]
			self.redis.decr('num_connected')
		except LookupError, err:
			print err

	def deleteDeivce(self, device):
		""" Delete device status from database if device 
		hasn't been logged in for a while
		"""

	def push_to_client(self, response, proto):
		pass

	def loseObjNotify(self, _):
		print "Worker lost"
		self.obj = None


	def stopService(self):
		if self.dbpool:
			self.dbpool.close()
		if self.redis:
			self.redis.flushdb().addErrback(self._redisBug)
			self.redis.quit().addErrback(self._redisBug)

	def _redisBug(self, _):
		print "redis close bug"


			
class ObserverService(service.Service):
	"""
	"""
	implements(IDeviceClientService)

	def __init__(self, harborDevices):
		self.h_devices = harborDevices
		self.redis = None
		self.clients = {}

	
	def startService(self):
		service.Service.startService(self)
		from twisted.internet import reactor
		clientCreator = ClientCreator(reactor, Redis)
		clientCreator.connectTCP('localhost', 6379).addCallback(self._tmp)
	
	def _tmp(self, redis):
		print "connected to redis"
		self.redis = redis
		self.redis.select(8)
		self.redis.set('num_clients', 0)

	def addClient(self, client_id, proto):
		"""
		"""
		self.clients[client_id] = proto
		self.redis.incr('num_clients')

	def removeClient(self, client_id):
		"""
		"""				
		try:
			del self.clients[client_id]
			self.redis.decr('num_clients')
		except:
			pass


	def handleRequest(self):
		pass

	def matchClientDevices(self, usr_devices, devices, view):
		"""
		None aggressive match
		Passive match
		view will be changed in the function
		"""
		d = defer.Deferred()
		free = set()
		busy = set()
		offline = set()
		try:
			for device in usr_devices:
				#TODO: redundant int
				d_id = int(device.id)
				if self.h_devices.has_key(d_id):
					# online
					if self.h_devices[d_id].available():
						# free
						free.add(d_id)
					else:
						# busy
						busy.add(d_id)
					devices[d_id] = self.h_devices[d_id]
					view.add(d_id)
				else:
					# offline
					devices[d_id] = None
					offline.add(d_id)
			d.callback([free, busy, offline])
		except Exception, err:
			d.errback(err)
		return d


	def updateClientDevices(self, devices, observes):
		"""
		Raise raw error
		The device will only become free if the client 
		chose to stop controlling it. 
		Can not set device busy to free here

		Nullify the connection if the device is offline.
		But keep the avatar.
		"""
		d = defer.Deferred()
		new_online = set()
		new_offline = set()
		try:
			for d_id in devices.iterkeys():
				# iterate all user own devices
				if self.h_devices.has_key(d_id):
					# device online
					if d_id not in observes:
						# this is new online and not in view
						devices[d_id] = self.h_devices[d_id]
						new_online.add(d_id)
				elif d_id in observes:
					# device newly offline and is in view
					new_offline.add(d_id)
				else:
					# device never online
					pass
			d.callback([new_online, new_offline])
		except Exception, err:
			d.errback(err)
		return d
	


	def stopService(self):
		if self.redis:
			self.redis.flushdb().addErrback(self._redisBug)
			self.redis.quit().addErrback(self._redisBug)

	
	def _redisBug(self, _):
		print "redis close bug"
	


