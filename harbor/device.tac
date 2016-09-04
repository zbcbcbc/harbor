from twisted.application import service

from harbor.servers.deviceServer import makeDeviceService

options = {


}



application = service.Application('Device Server')
deviceService = makeDeviceService()
deviceService.setServiceParent(service.IServiceCollection(application))
