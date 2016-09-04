# coding: utf-8

__filename__ = "deviceServer.py"
__description__ = "Harbor server configuration for Harbor Project"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"
 

from twisted.application import internet, service


from harbor.protocols.deviceProtocol import IDeviceServerFactory, IDeviceClientFactory
from harbor.services.deviceService import DeviceService, ObserverService


def makeDeviceService(config=None):

	multi_service = service.MultiService()

	drone_service = DeviceService(3335, 1)
	multi_service.addService(drone_service)
	device_factory = IDeviceServerFactory(drone_service)

	device_service = internet.TCPServer(3340, device_factory, 
						interface='192.168.0.91')
	multi_service.addService(device_service)

	client_service = ObserverService(drone_service.h_devices)
	multi_service.addService(client_service)
	device_cli_factory = IDeviceClientFactory(client_service)
	device_cli_service = internet.TCPServer(3335, device_cli_factory, 
						interface='localhost')
	multi_service.addService(device_cli_service)

	return multi_service
	

