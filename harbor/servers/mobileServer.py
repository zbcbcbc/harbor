# coding: utf-8

__filename__ = "mobileServer.py"
__description__ = "Proxy server for Harbor Project"
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


from twisted.application import internet, service
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from twisted.names import server, dns, hosts



from harbor.services.mobileService import MobileAgent
from harbor.protocols.mobileProtocol import IProxyServerFactory


def makeMobileService(config=None):

	
	# Set dns service
	dnsService = service.MultiService()
	hostsResolver = hosts.Resolver('/etc/hosts')
	tcpFactory = server.DNSServerFactory([hostsResolver])
	internet.TCPServer(3330, tcpFactory, interface='192.168.0.91').setServiceParent(dnsService)

	# Set log file
	logfile = DailyLogFile("mobile.log", "/tmp")
	#application.setComponent(ILogObserver, FileLogObserver(logfile).emit)

	# Set redis service

	# Proxy Server
	agent = MobileAgent(3333, 2)
	agent.setServiceParent(dnsService)
	mobileFactory = IProxyServerFactory(agent)
	mobileService = internet.TCPServer(3331, mobileFactory, interface='192.168.0.91')
	mobileService.setServiceParent(dnsService)

	return dnsService

	


	


