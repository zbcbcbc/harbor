"""
User credential module for Harbor Project
"""

__filename__ = "userCred.py"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.6"
__status__ = "Development"


from twisted.enterprise import adbapi
from twisted.cred import portal, checkers, credentials, error as credError
from twisted.internet import reactor, defer

from zope.interface import Interface, implements


from harbor.cli import user



class UserPasswordChecker(object):
	implements(checkers.ICredentialsChecker)
	
	def __init__(self, dbconn, 
		query="SELECT userid, password FROM Users WHERE username = %s",
		customCheckFunc=None, caseSensitivePasswords=True):

		"""
		@param dbconn: The connection to database. From 
			{twisted.enterprise.adbapi.ConnectionPool}. 
		@type dbconn: C{callable}
		
		@param runQuery: This will be called to getthe info from db.
			Generally to create a L{twisted.enterprise.adbapi.ConnectionPool} 
			and pass it's runQuery method here. Otherwise pass a function with 
			the same prototype.
		@type runQuery: C{callable}
	
		@param query: C{str}
		@type query: query used to authenticate user

		@param customCheckFunc: Use this if the passwords in the db are stored 
			as hashes. We'll just call this, so you can do the checking. It 
			takes the folloing params:
			(username, soppliedPass, dbPass) and must return a boolean.
		@type customCheckFunc: C{callable}
		
		@param caseSensitivePasswords: If true requires that every letter in 
			C{credentials.password} is exactly the same case as the it's 
			counterpart letter in the database.
			This is only relelant if C{customCheckFunc} is not used.
		@type caseSensitivePasswords: C{bool}
		"""
		
		self.q = query
		self.dbconn = dbconn
		self.caseSensitivePasswords = caseSensitivePasswords
		self.customCheckFunc = customCheckFunc

		if customCheckFunc:
			self.credentialInterfaces = (crendentials.IUsernamePassword,)
		else:
			self.credentialInterfaces = (
				credentials.IUsernamePassword, credentials.IUsernameHashedPassword,)
	

	def requestAvatarId(self, cred):
		"""
		Authenticate username against database
		"""
		# check that the credentials instance implements at least one of our 
		# interfaces
		for interface in self.credentialInterfaces:
			if interface.providedBy(cred):
				break
		else:
			raise credError.UnhandledCredentials()
			
		# query database for username and password
		dbDeferred = self.dbconn.runQuery(self.q, (cred.username,))
		# setup deferred result
		deferred = defer.Deferred()
		dbDeferred.addCallbacks(self._cbAuthenticate, self._ebAuthenticate, 
			callbackArgs=(cred, deferred),
			errbackArgs=(cred, deferred))
		return deferred

	
	def _cbAuthenticate(self, result, cred, deferred):
		"""
		Checks to see if authentication was good. Called once the info has
		been retrieved from the DB.
		"""
		if len(result) == 0:
			#username not found in db
			deferred.errback(credError.UnauthorizedLogin('username unknown'))
		else:
			userid, password = result[0]
			if self.customCheckFunc:
				# ownder do the checking
				if self.customCheckFunc(
					userid, cred.password, password):
					deferred.callback(userid)
				else:
					deferred.errback(
						credError.UnauthorizedLogin('password mismatch'))
			else:
				# it's up to us or the credentials object to do checking
				if credentials.IUsernameHashedPassword.providedBy(cred):
					# Let the hashed password checker do the checking
					if credentials.checkPassword(password):
						deferred.callback(userid)
					else:
						deferred.errback(
							error.UnauthorizedLogin('password mismatch'))
				elif credentials.IUsernamePassword.providedBy(cred):
					# Compare passwords, deviding whether to use case sensitivity
					if self.caseSensitivePasswords:
						passOk = (
							password.lower() == cred.password.lower())
					else:
						passOk = password == cred.password
					# See if they match
					if passOk:
						deferred.callback(userid)
					else:
						deferred.errback(
							credError.UnauthorizedLogin('password mismatch'))
				else:
					# We don't know how to check this
					deferred.errback(credError.UnhandledCredentials())


	def _ebAuthenticate(self, message, credentials, deferred):
		"""
		The database lookop failed for some reason.
		"""
		deferred.errback(credError.LoginFailed(message))
		



class UserRealm:
	implements(portal.IRealm)

	def __init__(self, dbconn):
		"""
		@param dbconn: The database connection object.
		@type dbconn: C{callable}

		@param avatarId: The avatar Id which represents an avatar at database.
		@type avatarId: C{int}
	
		
		
		"""
		self.dbconn = dbconn
		self.avatarId = None
		self.q_selectUserInfo = "SELECT username, firstname, lastname FROM Users WHERE userId = %s"
		self.q_findUserDevices = "SELECT deviceId FROM Owns WHERE userId = %s"
	
	@defer.inlineCallbacks
	def requestAvatar(self, avatarId, mind, *interfaces):
		"""
		With given interface and userId, return a deffered obj from query
		*Raise all Exceptions to caller*
		"""
		if user.IRegisteredUser in interfaces:
			# If interface is defined and exists
			self.avatarId = int(avatarId)
			#TODO: This is just a precaution
			rows = yield self.dbconn.runQuery(self.q_selectUserInfo, 
				self.avatarId)
			username, firstname, lastname = rows[0]

			fullname = "%s %s" % (firstname, lastname)
			defer.returnValue((user.IRegisteredUser, 
				user.RegisteredUser(self.avatarId, username, fullname), 
				user.RegisteredUser.logout))
		else:
			raise KeyError("None requested interfaces is supported")	






