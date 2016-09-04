from twisted.application import service

from harbor.servers.clientServer import makeClientService

options = {


}



application = service.Application('Client Server')
clientService = makeClientService()
clientService.setServiceParent(service.IServiceCollection(application))
