from twisted.internet import protocol, utils, reactor

class GPGProtocol(ProcessProtocol):
	def __init__(self, crypttext):
		self.crypttext = crypttext
		self.plaintext = ""
		self.status = ""
	
	def connectionMade(self):
		self.transport.writeToChild(3, self.passphrase)
		self.transport.closeChildFD(3)
		self.transport.writeToChild(0, self.crypttext)
		self.transport.closeChildFD(0)
	
	def childData
