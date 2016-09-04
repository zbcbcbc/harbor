from threading import Lock

class Observer(object):
	
	def __init__(self, usr_id):
		self.id = usr_id
		self.devices = dict()
		self.observing = set()

		#self.observe_lock = Lock()

	def subscribe(self, obj_id, proto):
		if obj_id not in self.observing:
			self.observing.add(obj_id)
			self.devices[obj_id].add_observer(self.id, proto)
		

	def unsubscribe(self, obj_id):
		if obj_id in self.observing:
			self.observing.remove(obj_id)
			self.devices[obj_id].remove_observer(self.id)


		

class Controller(Observer):
	
	def __init__(self, usr_id):
		Observer.__init__(self, usr_id)

		self.controlling = set()
		#self.control_lock = Lock()

	def takeControl(self, obj_id, proto):
		"""
		"""
		#WARNING: Unexpected threading locks can occur
		#self.control_lock.acquire()
		if self.devices[obj_id].available():
			self.controlling.add(obj_id)
			#self.control_lock.release()
			self.devices[obj_id].add_controller(self.id, proto)
			return True
		else:
			return False
		
	def loseControl(self, obj_id):
		#self.control_lock.acquire()
		self.controlling.remove(obj_id)
		#self.control_lock.release()
		self.devices[obj_id].remove_controller(self.id)

	
	def cancel_all_subscribe(self, obj_id):
		if obj_id in self.observing:
			#self.observe_lock.acquire()
			self.observing.remove(obj_id)
			#self.observe_lock.release()
		if obj_id in self.controlling:
			#self.control_lock.acquire()
			self.controlling.remove(obj_id)
			#self.control_lock.release()

	
	def unsubscribe_all(self):
		for obj_id in self.observing:
			self.devices[obj_id].remove_observer(self.id)
		for obj_id in self.controlling:
			self.devices[obj_id].remove_controller(self.id)

	def handleCommand(self, obj_id, cmd):
		if obj_id in self.controlling:	
			self.devices[obj_id].handle_cmd(cmd)
			return True
		else:
			return False	
