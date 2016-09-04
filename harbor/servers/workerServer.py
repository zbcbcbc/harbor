
__filename__ = "worker.py"
__description__ = "The harbor worker"
__author__ = "Bicheng Zhang"
__copyright__ = "Copyright 2012-2013, The Harbor Project"
__credits__ = "Bicheng Zhang"
__email__ = "viczhang1990@gmail.com"
__version__ = "0.5"
__status__ = "Development"

import logging, sys

from twisted.python import log

from options import WorkerOptions

from harbor.protocols.workerProtocol import PBWorkerServer
from harbor.services.workerService import FindStore



def main():

	config = WorkerOptions()

	try:
		config.parseOptions()
	except usage.UsageError, errortext:
		print '%s: %s' % (sys.argv[0], errortext)
		print '%s: Try --help for usage details.' % (sys.argv[0])
		sys.exit(1)

	interface = config['interf']
	log_path = config['log']
	worker_port = config['port']
	
	global LOGLEVEL

	if config['debug']:
		LOGLEVEL = logging.DEBUG
	else:
		LOGLEVEL = logging.INFO
	
	if log_path is sys.stdout:
		log.startLogging(sys.stdout)
	else:
		try:
			fp = open(log_path, 'w')
			log.startLogging(fp)
		except Exception, data:
			log.startLogging(sys.stdout)
			log.msg(Exception, ":", data, 
				logLevel=logging.ERROR)
		
	factory = PBWorkerServer(FindStore())	

	from twisted.internet import reactor

	port = reactor.listenTCP(worker_port, factory,
							 interface=interface)

	print 'Harbor Worker Server on %s.' %(port.getHost(),)

	reactor.run()

if __name__ == '__main__':
	main()

	
