#coding: utf-8

__filename__ = "logServer.py"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.3"
__status__ = "Development"



from twisted.internet.protocol import Protocol
from twisted.internet.protocol import Factory
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver

class LoggingProtocol(LineReceiver):
	def lineReceived(self, line):
		from time import gmtime, strftime
		self.factory.fp.write(strftime("%d%m%Y%S%M%H", gmtime())+"\n")

class LogfileFactory(Factory):
	protocol = LoggingProtocol
	def __init__(self, filename):
		self.file = filename
	
	def startFactory(self):
		self.fp = open(self.file, "a")
	
	def stopFactory(self):
		self.fp.close()

reactor.listenTCP(8007, LogFileFactory("log.txt")) #TODO
reactor.run()

