from twisted.application import service


from harbor.servers.mobileServer import makeMobileService


options = {



}



application = service.Application('Mobile Server')
mobileService = makeMobileService()
mobileService.setServiceParent(service.IServiceCollection(application))


