from zope.interface import Interface, Attribute


class IDevice(Interface):
	"""
	"""
	id = Attribute("")
	owners = Attribute("")
	code = Attribute("")
	name = Attribute("")
	type = Attribute("")
	login = Attribute("login flag")
	protocol = Attribute("Protocol instance")
	viewers = Attribute("dictionary")
	controllers = Attribute("dictionary")

	def assign_protocol(protocol):
		"""
		"""
	
	def add_viewer(userId):
		"""
		"""

	def add_controller(userId):
		"""
		"""

	def remove_viewer(userId):
		"""
		"""

	def remove_controller(userId):
		"""
		"""

	def send_to_viewers(msg):
		"""
		"""

	def send_to_controllers(msg):
		"""
		"""

	def errback_all(err):
		"""
		"""

	def logout():
		"""
		"""


class IDrone(IDevice):
	"""
	"""	

	x = Attribute("")
	y = Attribute("")
	z = Attribute("")

	def fly_to(x=None, y=None, z=None):
		"""
		Parse data specific to the device to handle the command
		"""

	def land():
		"""
		Parse data specific to the device to handle the command
		"""

	def takeOff(height):
		"""
		"""

	def fly_up(incr):
		"""
		"""

	def fly_down(decr):
		"""
		"""


class IBoat(IDevice):
	"""
	"""

class IRefridge(IDevice):
	"""
	"""

	temperature = Attribute("")
	power = Attribute("")
	age = Attribute("")


class ICam(IDevice):
	"""
	"""

class ITV(IDevice):
	"""
	"""

	
