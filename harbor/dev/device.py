#coding: utf-8

__filename__ = "device.py"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"

from twisted.spread.pb import Avatar
from twisted.internet import defer
from harbor.interfaces.IDevices import IDevice

from zope.interface import implements



class Device(Avatar):
	"""
	This is also an observer object
	TODO
	"""
	implements(IDevice)
	
	def __init__(self, deviceId, owners, deviceCode, devicename, devicetype):
		self.id = deviceId
		self.owners = owners
		self.code = deviceCode
		self.name = devicename
		self.type = devicetype
		self.login = True
		self.protocol = None
		self.free = True
		
		self.observers = dict()
		self.controllers = dict()

	def assign_protocol(self, protocol):
		self.protocol = protocol

	def add_observer(self, userId, proto):
		self.observers[userId] = proto

	def add_controller(self, userId, proto):
		self.controllers[userId] = proto
		self.free = False

	def remove_observer(self, userId):
		if self.observers.has_key(userId):
			del self.observers[userId]

	def remove_controller(self, userId):
		if self.controllers.has_key(userId):
			del self.controllers[userId]
			self.free = True

	
	def notify_observers(self, msg):
		"""
		Static dictionary iteration.
		Has dynamic key problem
		"""
		for id in self.observers.keys():
			self.observers[id].transport.write(msg)	

	def notify_controllers(self, msg):
		"""
		Dynamic key problem
		"""
		for id in self.controllers.keys():
			self.controllers[id].transport.write(msg)

	def notify_all(self, msg):
		self.notify_observers(msg)
		self.notify_controllers(msg)

	def send_to_device(self, msg):
		if self.protocol:
			self.protocol.transport.write(msg)

	
	def available(self):
		return self.free
	


	def logout(self):
		pass


