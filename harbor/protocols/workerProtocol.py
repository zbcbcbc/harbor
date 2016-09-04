
__filename__ = "worker_f.py"
__description__ = "The harbor worker"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.5"
__status__ = "Development"

import logging, sys
import hello #TODO: python-c api testing
from datetime import *

from twisted.enterprise import adbapi
from twisted.spread import pb
from twisted.python import log
from twisted.internet import defer


from options import WorkerOptions

from zope.interface import Interface, implements, Attribute

from twisted.python import components

from harbor.services.workerService import *
from harbor.interfaces.IProtocols import *
from harbor.message import harbor_pb2
from harbor.db.hmysql import DB_DRIVER, DB_ARGS



class PBWorkerServer(pb.PBServerFactory):
	def startFactory(self):
		log.msg("Worker Server start at %s" % datetime.now())	


class IPBWorkerFactory(Interface):
	"""
	"""

	service = Attribute("")
	registered = Attribute("False")

	def stopFactory():
		"""
		"""

class PBWorkerClientFactoryFromService(pb.PBClientFactory):
	implements(IPBWorkerFactory)
	
	def __init__(self, service):
		pb.PBClientFactory.__init__(self)
		"""
		@param port: The worker port.
		@type port: C{str}
		
		@param workerService: THe worker service instance. Used to 
			un-register worker when worker stops itself.
		@type workerService: C{callable}
	
		@param registered: The flag to indicate whether the worker has 
			registered itself at workerService or not.
		@type registered: C{bool}
		"""
		self.service = service
		self.registered = False
	
	def stopFactory(self):
		if self.registered:
			self.service.unRegisterWorker(self.port)
			self.registered = False

	def startWork(self, expression):
		return self.service.startWork(expression)


components.registerAdapter(PBWorkerClientFactoryFromService, 
							IPBWorkerClientService, 
							IPBWorkerFactory)
