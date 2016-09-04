#coding: utf-8


__filename__ = "protoWrapper.py"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.4"
__status__ = "Development"

__description__ = """
				Internal communication wrapper module. Using protocol buffer as parsing
				technique.
				"""


import harbor_pb2



def reply_fail(protocol, reason):
	reply = harbor_pb2.Reply()
	reply.success = False
	reply.reason = reason
	reply = reply.SerializeToString()
	protocol.transport.write(reply)



