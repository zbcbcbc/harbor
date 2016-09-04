# coding: utf-8

__filename__ = "client_config.py"
__description__ = "Client server configuration for Harbor Project"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"
 

from twisted.application import internet, service
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from twisted.names import server, dns, hosts

from harbor.protocols.clientProtocol import IClientServerFactory
from harbor.services.clientService import Client
from harbor.services.workerService import PBWorkerClientService
from harbor.protocols.workerProtocol import IPBWorkerFactory




"""
Inititate services
"""
def makeClientService(config=None):
	
	# set dns service
	dnsService = service.MultiService()
	hostsResolver = hosts.Resolver('/etc/hosts')
	tcpFactory = server.DNSServerFactory([hostsResolver])
	internet.TCPServer(3332, tcpFactory, interface='192.168.0.91').setServiceParent(dnsService)

	#Client Server Service
	clientService = Client(3335, 3336, 3)
	clientServerFactory = IClientServerFactory(clientService)
	clientService.setServiceParent(dnsService)
		
	clientServerService = internet.TCPServer(3333, clientServerFactory, 
						interface='192.168.0.91')
	clientServerService.setServiceParent(dnsService)

	return dnsService






"""
Client Server to Harbor Service


toHarborFactory = ServerToHarborFactory()
toHarborService = internet.TCPClient('localhost', 3335, toHarborFactory)
serviceCollection.addService(toHarborService)
"""




