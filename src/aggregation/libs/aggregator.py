import json
import threading
import time

import os
import sys
import tempfile
import subprocess

import logging

log_dir =  os.path.join(os.getcwd(),'logs')
#print log_dir
if not os.path.exists(log_dir) :
	os.mkdir(log_dir)
log_file = os.path.join(log_dir, 'aggregator.log')

logger = logging.getLogger('aggregator')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(filename)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

'''
logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
						datefmt='%a, %d %b %Y %H:%M:%S',
						filename= log_file,
						filemode='a')
'''

from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer

from cache import Cache
from receiver import Receiver
from checker import Checker
from installer import Installer

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
class myHttpHandler(BaseHTTPRequestHandler) :
	def do_GET(self) :

		global topo
		global cache
		global checker

		output = None
		#print self.path
		
		if cmp(self.path, '/topology') == 0 :
			output = topo.get_topology()
			#print str(output)
			
		if cmp(self.path, '/topology/nodes') == 0 :
			output = topo.list_nodes()

		if cmp(self.path, '/monitoring/caches') ==0 :
			output = []
			raw = cache.dump()
			for k, v in raw.items():
				output.append(v)					
			
			
		if cmp(self.path, '/autoscaling/progress') == 0:			
			output = checker.progress()
			
		if cmp(self.path, '/autoscaling/policy') == 0:
			output = checker.get_policy()
		

		if output :
			self.send_response(200)
			self.send_header("Content-Type", "application/json")		
			self.send_header('Access-Control-Allow-Origin','*');
			self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS');
			self.send_header('Access-Control-Allow-Headers','Origin, Content-Type, Accept, Authorization, X-Request-With');
			self.send_header('Access-Control-Allow-Credentials','true');	
			self.end_headers()
			
			self.wfile.write(json.dumps(output))
		else :
			
			self.send_response(500)  
			self.end_headers()

	def do_POST(self) :
		f = self.rfile

		#line = self.rfile.readline().strip()
		line = f.readline()
		#print len(line)
		#print line 
		f.close()
		self.send_response(201)



if __name__ == "__main__":
	
	sys.path.append(os.getcwd())
	sys.path.append(os.path.join(os.getcwd(),'libs'))
	sys.path.append(os.path.join(os.getcwd(),'libs','provisioner'))

	#filepath =  os.path.join(os.getcwd(),'scaling.cfg')
	filepath = os.path.join(os.getcwd(),'conf', 'scaling.cfg')
	f = open(filepath)
	cfg = json.load(f)
	implement = cfg['iaas']['implement']
	logger.info('Load topology implement ' + implement)
	importtopo = "from %s import Topology"%(implement)
	exec importtopo
	
	config = cfg['iaas']['config']
	#print config
	logger.info('Load configuration:')
	logger.info(json.dumps(config))
	
	logger.info('Create topology')
	topo = Topology(config)
	topo.create()
	
	logger.info('Create data cache')
	cache = Cache()
	
	logger.info('Start data receiver')
	receiver = Receiver(cache)
	receiver.start()
		
	logger.info('Plant collectors')
	nodes = topo.list_nodes()	
	
	
	
	installer = Installer(cfg['node'])
	for node in nodes :
		node_ipaddress  = topo.get_node_ipaddress(node)
		#print 'node_ipaddress = ',node_ipaddress
		
		logger.info('Planting collector to ' + node_ipaddress)
		if node_ipaddress :				
			installer.set_trust(node_ipaddress)
			installer.install(node_ipaddress)

	logger.info('Start auto-scaling checker')
	checker = Checker(cache, topo, installer, cfg['policy'])
	checker.start()
	
	logger.info('Start api server')
	http_server = HTTPServer(('', 8001), myHttpHandler)
	http_server.serve_forever()


