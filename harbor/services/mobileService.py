#coding: utf-8

__filename__ = "mobileService.py"
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
from datetime import datetime

from zope.interface import implements

from txredis.protocol import Redis

from harbor.interfaces.IServices import IProxyClientService


"""
All errors are raised at service level
"""


class MobileAgent(service.Service):

	implements([IProxyClientService])
	def __init__(self, serverAddr, redis_db):
		"""
		@param maxConn: maximum allowed connection at server side.
			The default value can be tuned.
		@type maxConn: C{int}

		@param protectLevel:
			low: 1
			medium: 2
			high: 3
		@type protectLevel: C{int}

		@param connectedNum: the number of connected connections.
		@type connectedNum: C{int}

		@param hoveredNum: the number of hovered connections
		@type hoveredNum: C{int}
		"""
		self.serverAddr = serverAddr
		self.redis_db = redis_db
		self.clients = {}
		self.conns = {}
		self.redis = None

	
	@defer.inlineCallbacks
	def startService(self):
		service.Service.startService(self)
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


	def isLuckyConnection(self):
		"""
		Generate a lucky number to indicate whether to reject connection or not.
		Return true accept connection, return false to reject
		"""
		#TODO: Needs a fast algorithm to determine if to cut connection or not
		luck = random.getrandbits(10)
		#stub
		return True
	
	@defer.inlineCallbacks
	def addClient(self, clientIp, proto):
		"""
		use inlineCallbacks only to debug
		check duplication should be implemented
		"""
		#TODO: check duplication
		self.clients[clientIp] = (proto, None, datetime.now())
		self.redis.incr('num_clients')
		res = yield self.redis.get('num_clients')
		print "total clients: ", res


	def removeClient(self, clientIp):
		"""
		"""
		try:
			del self.clients[client_id]
		except:
			pass
		self.redis.decr('num_clients')


	def stopService(self):
		if self.redis:
			self.redis.flushdb().addErrback(self._redisBug)
			self.redis.quit().addErrback(self._redisBug)

	
	def _redisBug(self, _):
		print "redis close bug"






	

