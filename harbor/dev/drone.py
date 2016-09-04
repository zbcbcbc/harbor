#coding: utf-8

__filename__ = "drone.py"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"

from twisted.internet import defer
from harbor.interfaces.IDevices import IDevice, IDrone
from harbor.dev.device import Device


from zope.interface import implements



class Drone(Device):
	implements(IDrone)

	def __init__(self, deviceId, owners, deviceCode, devicename, devicetype):
		Device.__init__(self, deviceId, owners, deviceCode, devicename, devicetype)	
		
		# device should send positions when login
		# stub
		self.x = 0
		self.y = 0
		self.z = 0
		self.ax = None
		self.ay = None
		self.az = None
		self.vx = None
		self.vy = None
		self.vz = None

		self.cmds = defer.DeferredQueue()
		

		
		self.ref_x_orig = [ 3.54, 3.54, 3.5196, 
			3.4349, 3.3749, 3.3522, 3.3755, 
			3.4396, 3.5051, 3.5048, 3.4389, 3.3136, 
			3.1411, 2.9581, 2.7731, 2.5815 
			]

		self.ref_y_orig = [ 1.225, 1.351, 1.477, 1.593, 
			1.715, 1.841, 1.966,
			2.087, 2.208, 2.334, .2455, 
			2.557, 2.632, 2.697, 
			2.761, 2.817
			]

		#calibration
		for pos in self.ref_x_orig:
			pos = 1.8 + pos/self.ref_x_orig[0]*1
		for pos in self.ref_y_orig:
			pos = 2.8 + pos/self.ref_y_orig[15]*1.2

	
	def handle_cmd(self, cmd):
		if "fly" in cmd:
			self.fly_to(1, 1, 1)
		elif "land" in cmd:
			self.land()

	def recv_cmd_ack(self, ack):
		if "fly" in ack:
			self.notify_controllers(ack)
		elif "land" in ack:
			self.notify_controllers(ack)
		else:
			# garbage
			pass

	def recv_view_msg(self, msg):
		self.notify_observers(msg)

	def fly_to(self, x=None, y=None, z=None):
		"""
		"""
		#TODO: Need a scheduler
	
		#execute
		msg = "Fly to: [%d,%d,%d]\n" % ( 
			x or self.x, y or self.y, z or self.z)
		self.cmds.put((1, msg))
		# stub
		
	def land(self):
		
		#execute
		msg = "Land\n"
		self.cmds.put((2, msg))
		# stub




