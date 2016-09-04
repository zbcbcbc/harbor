#coding: utf-8

__filename__ = "h_db.py"
__description__ = "harbor project database wrapper module"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.6"
__status__ = "Development"



from twisted.enterprise import adbapi
from twisted.python import log
from txredis.protocol import Redis
from twisted.internet.protocol import ClientCreator

from zope.interface import Interface, Attribute, implements


DB_DRIVER = "MySQLdb"
DB_ARGS = {
	'db':'harbor',
	'user':'root',
	'passwd':'NPC8803zbc'
}


class IHarborDB(Interface):
	"""
	"""

	def query(q):
		"""
		"""
	
class HarborDB(object):
	
	def __init__(self):
		self.dbpool = adbapi.ConnectionPool(DB_DRIVER, **DB_ARGS)


	def query(self, query):
		"""
		"""
		pass


class ReconnectingConnectionPool(adbapi.ConnectionPool):
	"""Reconnecting adbapi conection pool for MySQL
	
	see
	https://twistedmatrix.com/pipermail/twisted-python/2009-July/0200007.html
	
	"""

	def _runInteration(self, interation, *args, **kw):
		try:
			return adbapi.ConnectionPool._runInteration(self, interation, *args,
														**kw)
		except MySQLdb.OperationalError, e:
			if e[0] not in (2006, 2013):
				raise
			log.msg("RPC: got error %s, retrying operation" %(e))
			conn = self.connections.get(self.threadID())
			self.disconnect(conn)
			# try the interation again
			return adbapi.ConnectionPool._runInteration(self, interation, *args,
															**kw)
	

