#coding: utf-8

__filename__ = "deviceCred.py"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.8"
__status__ = "Development"

from twisted.enterprise import adbapi
from twisted.cred import portal, checkers, credentials, error as credError
from twisted.internet import reactor, defer

from zope.interface import Interface, implements

from harbor.interfaces.IDevices import IDrone
from harbor.dev.drone import Drone


class DevicePinChecker(object):
	implements(checkers.ICredentialsChecker)

	def __init__(self, dbconn, 
		query="SELECT deviceId, pin FROM Devices WHERE deviceCode = %s", 
		customCheckFunc=None, caseSensitivePasswords=True):

		self.q = query
		self.dbconn = dbconn
		self.caseSensitivePasswords = caseSensitivePasswords
		self.customCheckFunc = customCheckFunc

		if customCheckFunc:
			self.credentialInterfaces = (credentials.IUsernamePassword,)
		else:
			self.credentialInterfaces = (
				credentials.IUsernamePassword,
				credentials.IUsernameHashedPassword,)
	
	def requestAvatarId(self, cred):

		for interface in self.credentialInterfaces:
			if interface.providedBy(cred):
				break
		else:
			raise credError.UnhandledCredentials()

		dbDeferred = self.dbconn.runQuery(self.q, (cred.username,))

		deferred = defer.Deferred()
		dbDeferred.addCallbacks(self._cbAuthenticate, self._ebAuthenticate, 
			callbackArgs=(cred, deferred),
			errbackArgs=(cred, deferred))
		return deferred

	def _cbAuthenticate(self, result, cred, deferred):
		"""
		"""

		if len(result) == 0:
			deferred.errback(credError.UnauthorizedLogin('deviceCode unknown'))
		else:
			deviceid, pin = result[0]
			if self.customCheckFunc:
				if self.customCheckFunc(
					deviceId, cred.password, pin):
					deferred.callback(deviceId)
				else:
					deferred.errback(
						credError.UnauthorizedLogin('pin mismatch'))
			else:
				if credentials.IUsernameHashedPassword.providedBy(cred):
					if cred.checkPassword(pin):
						deferred.callback(deviceid)
					else:
						deferred.errback(
							error.UnauthorizedLogin('pin mismatch'))
				elif credentials.IUsernamePassword.providedBy(cred):
					if self.caseSensitivePasswords:
						passOk = (
							pin.lower() == cred.password.lower())
					else:
						passOk = pin == cred.password
					if passOk:
						deferred.callback(deviceid)
					else:
						deferred.errback(
							credError.UnauthorizedLogin('pin mismatch'))
				else:
					deferred.errback(credError.UnhandledCredentials())

	def _ebAuthenticate(self, message, credentials, deferred):
		deferred.errback(credError.LoginFailed(message))


class DeviceRealm:
	implements(portal.IRealm)

	def __init__(self, dbconn):
		self.dbconn = dbconn
		self.q_selectDeviceInfo = """SELECT deviceCode, devicename, devicetype FROM
				Devices WHERE deviceId = %s"""
		self.q_findOwnerIds = """ SELECT userId from Owns WHERE deviceId = %s """
	
	@defer.inlineCallbacks
	def requestAvatar(self, avatarId, mind, *interfaces):
		"""
		Raise all Exceptions to caller
		"""
		if IDrone in interfaces:
			avatarId = int(avatarId)
			rows = yield self.dbconn.runQuery(self.q_selectDeviceInfo, 
					avatarId)
			code, name, type = rows[0]

			rows = yield self.dbconn.runQuery(self.q_findOwnerIds, avatarId)
			#TODO: enable multiple owners in future
			
			owners = []
			for i in rows:
				ownerId, = i
				owners.append(int(ownerId))

			defer.returnValue((IDrone, 
					Drone(avatarId, owners, code, name, type), 
					Drone.logout))
		else:
			raise KeyError("None requested interfaces is supported")
	

