# coding: utf-8

__filename__ = "user.py"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ =  "0.8"
__status__ = "Development"


from datetime import *
from zope.interface import implements, Interface
from twisted.spread.pb import Avatar


class IUnRegisteredUser(Interface):
	"""
	"""

class IRegisteredUser(Interface):
	"""
	"""

	def postComments(self, comment):
		"""
		"""

	def searchStore(self, store):
		"""
		"""

	def retrieveCoupon(self, coupon):
		"""
		"""

	def searchCoupon(self, coupon):
		"""
		"""

class IPaidUser(IRegisteredUser):
	"""
	"""

class UnRegisteredUser(Avatar):
	implements(IUnRegisteredUser)

	def __init__(self):
		pass
	
	def logout(self):
		pass

class RegisteredUser(Avatar):
	implements(IRegisteredUser)

	"""
	User registered will be stored in database. When the User log in, their 
	credentials will be checked with their corresponding info at database
	
	Registered User has basic functionalities, with bonus functions like 
	post comments, favorites, view more coupons and buy coupons.
	"""

	def __init__(self, userId, username, fullname):

		__metaclass__ = type
		"""
		@param userId: userId from database, used as avatarId
		@type userId: C{int}
		
		@param username: username stored in database 'username'
		@type username: C{str}

		@param fullname: firstname + lastname
		@type fullname: C{str}
		
		@param logId: logId assigend by server getUserLogId.
		@type logId: C{int}
		"""
		self.userId = userId
		self.username = username
		self.fullname = fullname
		self.devices = {}
		self.proto_to_harbor = None
		self.factory = None


	def postComment(self, comment):
		#TODO: This is only a stub
		print comment

	def logout(self):
		pass	

		
		




	
	 
