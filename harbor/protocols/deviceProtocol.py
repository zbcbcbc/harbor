# coding: utf-8

__filename__ = "deviceProtocol.py"
__description__ = "Device server and broker"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"
 
import os, sys, logging, Queue

from twisted.internet import defer, task
from twisted.internet.protocol import (ServerFactory, ClientFactory, Protocol)
from twisted.python import log, failure, components

from zope.interface import implements

import txcoroutine
import txzmq

from harbor.cli.observer import Controller
from harbor.message import harbor_pb2
from harbor.message.protoWrapper import reply_fail
from harbor.services.deviceService import *
from harbor.interfaces.IProtocols import (IDeviceServerFactory,
	IDeviceServerProtocol, IDeviceClientProtocol, IDeviceClientFactory)
from harbor.interfaces.IServices import IDeviceService

UPDATE_USER_DEVICE_INT = 5



class DeviceServerProtocol(Protocol):
	"""
	"""	

	implements(IDeviceServerProtocol)

	def __init__(self, factory):
		"""

		"""
		#TODO: h_devices should be in service
		self.factory = factory

		self.avatarInterface = None
		self.avatar = None
		self.proc = None
		self.last_cmd = None
		
		# The server only support one owner for now
		# TODO:
		# To enable multiple client control, 
		# Need a dict {ownerId: defer}
		# Which will fireback corresponding to specific owner 
		# to prevent data race

		# make controller a subset
	
	def connectionMade(self):
		print "New connection from %s" % self.transport.getPeer()

	def dataReceived(self, data):
		"""

		"""
		print data
		try:
			cntrl, msg = data.split('.', 1)
			if int(cntrl) == 1:
				deviceCode, pin = msg.split('.', 1)
				print pin
				deviceCode = deviceCode.strip()
				pin = pin.strip()
				self.login(deviceCode, pin)
			elif int(cntrl) == 2:
				# in future forward msg after server processing
				self.avatar.recv_view_msg(msg)
			elif int(cntrl) == 3:
				# ack of cmd
				# forward msg to controllers only
				self.avatar.recv_cmd_ack(msg)
			else:
				pass
		except Exception, err:
			print err


	@defer.inlineCallbacks	
	def login(self, deviceCode, pin):
		"""
		"""
		try:
			# do device login 
			avatarInfo = yield self.factory.login(deviceCode, pin)
			# login succeed
			self.avatarInterface, self.avatar, _ = avatarInfo
			self.avatar.assign_protocol(self)
			# remember connection at HarborServerFactory
			yield self.factory.registerDevice(self.avatar, self)
			# redundant check int type 

			log.msg("device %s log in" % self.avatar.name, logLevel=logging.DEBUG)

			self.transport.write("Device login\n")
			
			self.proc = self.forward_command()

		except Exception, err:
			# device login fail
			# need to add manual device login technique
			log.msg(err, logLevel=logging.DEBUG)


	# TODO: jammed version
	@defer.inlineCallbacks
	def forward_command(self):
		"""
		Repeat forward same command if no ack back
		"""
		while 1:
			try:
				pri, cmd = yield self.avatar.cmds.get()
				self.send_to_device(cmd)
			except Exception, err:
				print err
				break
		

	def send_to_device(self, msg):
		self.transport.write(msg)
				

	def Logout(self):
		"""

		"""
		self.avatar.login = False


	
	def connectionLost(self, reason):
		"""
		Reason is the area to categorize types
		"""
		err = reason.getErrorMessage()
		log.msg(err, logLevel=logging.DEBUG)
		if self.avatar:
			self.factory.unregisterDevice(self.avatar.id)
			self.avatar.notify_all(err)	
		if self.proc:
			self.proc.cancel()
						
	def terminateConnection(self):
		self.transport.loseConnection()
	

		

class DeviceServerFactoryFromService(ServerFactory):

	implements(IDeviceServerFactory)

	def __init__(self, service):
		self.service = service
		self.clientServerPort = service.clientServerPort

	def buildProtocol(self, addr):
		return DeviceServerProtocol(self)
	
	def login(self, deviceCode, pin):
		return self.service.login(deviceCode, pin)
	
	
	def registerDevice(self, device, conn):
		self.service.registerDevice(device, conn)

	def unregisterDevice(self, d_id):
		self.service.unregisterDevice(d_id)

components.registerAdapter(DeviceServerFactoryFromService, 
							IDeviceService,
							IDeviceServerFactory)
			


class ObserverProtocol(Protocol):

	implements(IDeviceClientProtocol)
	
	def __init__(self, factory):
		"""
		@param harborDevices: All devices connected to Harbor Server.
		@type harborDevices: py{dict}
		
		@param clients: All clients connected from clientServer.
		@type clients: py{dict}
	
		@param num_clients: Total number of clients
		@type num_clients: c{int}
		
		"""	


		self.state = "handshake"
		self.factory = factory
		self.l_updateClientDevices = None
		self.controller = None
	
	
	def connectionMade(self):
		self.remoteIp = self.transport.getPeer()
		print "New connection from ", self.remoteIp

	def dataReceived(self, data):
		if self.state == "handshake":
			self.handshake(data)
		elif self.state == "user_control":
			self.handleRequest(data)

	@defer.inlineCallbacks
	def handshake(self, data):
		"""
		record userid, and user devicesid
		found online devices from harbor and record in user devices
		keep updating user devices at loop
		Active Control Scheme:(current implementation)
		The user will take control of device whenever the device is free
		Passive Control Scheme:(future patch)
		The user will only take control of device when the user asked for 
		it and the device is free
		"""
		try:
			reply = harbor_pb2.Reply()
			reply.ParseFromString(data)
			if reply.success == True:
				self.state = "user_control"
				# if this is a success message
				userId = reply.user.id
				self.controller = Controller(userId)
				self.factory.addClient(userId, self)
				print "user %s on harbor!" % userId
				# get user owned devices
				free, busy, offline = yield self.factory.matchClientDevices(
										reply.user.devices, self.controller.devices,
										self.controller.observing)

				# inform devices and clients
				for d_id in free:
					self.send_to_client(
					"your deivce %s is free\n" % self.controller.devices[d_id].name)
					self.controller.subscribe(d_id, self)

				for d_id in busy:
					self.send_to_client(
					"your deivce %s is busy\n" % self.controller.devices[d_id].name)
					self.controller.subscribe(d_id, self)
	

				# start updating client device list
				self.l_updateClientDevices = task.LoopingCall(self.updateClientDevices)
				# The update user device interval should be dynamic
				self.l_updateClientDevices.start(UPDATE_USER_DEVICE_INT)
				
			else:
				# if the reply is fail
				pass
		except Exception, err:
			err = str(err)
			print err


	def send_to_client(self, data):
		self.transport.write(data)


	@txcoroutine.coroutine
	def updateClientDevices(self):
		"""
		Passive update. Now automatic control is allowed here.	
		"""
		try:
			new_online, new_offline = yield self.factory.updateClientDevices(
									self.controller.devices,
									self.controller.observing)

			for d_id in new_online:
				self.send_to_client(
					"your deivce %s is online\n" % self.controller.devices[d_id].name)
				self.controller.subscribe(d_id, self)
												
			for d_id in new_offline:
				self.send_to_client(
					"your deivce %s is offline\n" % self.controller.devices[d_id].name)
				self.controller.cancel_all_subscribe(d_id)
					
		except Exception, err:
			err = yield str(err)
			self.send_to_client(err)



	def handleRequest(self, data):
		cmd = harbor_pb2.Command()
		cmd.ParseFromString(data)
		d_id = cmd.deviceId
		msg = cmd.msg.encode('utf-8')

		if 'control' in msg:
			# request for control
			if d_id not in self.controller.devices.keys():
				self.send_to_client("The device %s is not yours\n" % d_id)	
			elif d_id not in self.controller.observing:
				# device offline
				self.send_to_client("The device %s is offline\n" % d_id)
			elif d_id in self.controller.controlling:
				# device has been controlled by client
				self.send_to_client("You are controlling device %s\n" % d_id)
			else:
				# device is online
				if self.controller.takeControl(d_id, self):
					self.send_to_client("You are controlling device %s\n" % d_id)
				else:
					# device is busy
					self.send_to_client("Device %s is busy, your are waiting..\n" % d_id)
		
		elif 'stop' in msg:
			# request to stop controlling
			print "stop cntrl\n"
			self.controller.loseControl(d_id)

		elif not self.controller.handleCommand(d_id, msg):
				self.send_to_client("You are not controlling device %s\n" % d_id)


		

	def connectionLost(self, reason):
		"""
		Client connection lost.
		Cancel viewing controlling devices' deferreds
		"""
		# remove from client service
		# optimization!!!
		if self.controller:
			self.factory.removeClient(self.controller.id)	

		# stop looping service
		if self.l_updateClientDevices:
			self.l_updateClientDevices.stop()

		self.controller.unsubscribe_all()	
		
		log.msg(reason.getErrorMessage(), logLevel=logging.DEBUG)


class DeviceClientFactoryFromService(ServerFactory):
	"""
	@param clients: {userId:(protocol, connected)}
	@type clients: py{dict}
	"""

	implements(IDeviceClientFactory)

	def __init__(self, service):
		self.service = service
		self.clients = {}
		self.num_clients = 0
		
	def buildProtocol(self, addr):
		return ObserverProtocol(self)
	
	def addClient(self, client_id, proto):
		self.service.addClient(client_id, proto)

	def removeClient(self, client_id):
		self.service.removeClient(client_id)
	
	def updateClientDevices(self, devices, observes):
		return self.service.updateClientDevices(devices, observes)

	def matchClientDevices(self, usr_devices, devices, observes):
		return self.service.matchClientDevices(usr_devices, devices, observes)


components.registerAdapter(DeviceClientFactoryFromService, 
							IDeviceClientService,
							IDeviceClientFactory)


def mock_device(data):
	# to mock device reply
	d = defer.Deferred()
	from twisted.internet import reactor
	reactor.callLater(2, d.callback, 'action succeed\n')
	return d


