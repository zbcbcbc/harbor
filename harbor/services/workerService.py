#coding: utf-8

__filename__ = "workerS.py"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"

import sys, logging

from twisted.internet import defer
from twisted.spread import pb
from twisted.python import log
from twisted.enterprise import adbapi
from zope.interface import implements

from twisted.application import internet, service
from harbor.db.hmysql import *
from harbor.interfaces.IServices import *
import txcoroutine


class PBWorkerClientService(service.Service):
	
	implements(IPBWorkerClientService)

	def __init__(self, workerPorts):
		self.workers = {}
		self.offlineWorkers = workerPorts
		self.num_workers = 0

	def startService(self):
		service.Service.startService(self)

	def unRegisterWorker(self, port):
		del self.workers[port]
		if port not in self.offlineWorkers:
			self.offlineWorkers.append(port)
		self.num_workers -= 1


	def startWork(self, expression):
		#TODO:Do different types of work and assgin to different workers
		return self.workers[3336][0].callRemote(
			"storebytype", "resturant")




class FindStore(pb.Root): #TODO: This should be referenceable

	def __init__(self):
		self.dbconn = adbapi.ConnectionPool(DB_DRIVER, **DB_ARGS)
	

	@defer.inlineCallbacks
	def remote_storebytype(self, storetype):
		q = """
			SELECT storename, storetype
			FROM Stores
			WHERE storetype = '%s'
		""" % storetype
		try:
			rows = yield self.dbconn.runQuery(q)
			storename, storetype = rows[0]
			store = harbor_pb2.Store()
			store.storename = storename
			store.storetype = storetype
			store = store.SerializeToString()
			returnValue(store)
		except Exception, err:
			print err
			returnValue(err)

	
	# coroutine tail optimization
	@txcoroutine.coroutine
	def remote_fact(self, n, result=1):
		if n <= 1:
			returnValue(result)
		else:
		 	noreturn(fact(n-1, n*result))
		yield
	



