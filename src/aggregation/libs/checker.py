import  threading
import	time
import	logging
import os
import json

log_dir =  os.path.join(os.getcwd(),'logs')
print log_dir
if not os.path.exists(log_dir) :
	os.mkdir(log_dir)
log_file = os.path.join(log_dir, 'checker.log')

logger = logging.getLogger('checker')
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
						
class Checker(threading.Thread):

	cache = None
	topology = None
	status = None
	policy = None
	installer = None
	
	def __init__(self, cache, topology, installer, policy) :
		threading.Thread.__init__(self)
		self.cache = cache
		self.topology = topology
		self.installer = installer
		self.policy = policy
		
		#print str(policy)
		logger.info('The scaling policy is ')
		logger.info(json.dumps(policy))
		self.status = {'state':'initializing','message' : 'initialize'}

	def get_policy(self):
		return self.policy
	
	def progress(self) :
		return self.status
	
	def run(self):
		#print 'Entering Checker....'
		logger.info('Entering Checker....')
		counting_time = 0
		timing = False
		scaling = False
		
		while True:
			if scaling :
				continue
			
			#print 'autoscaling>>>>new round check.....'
			nodes = self.topology.list_nodes()
			total = 0
			all = True
			#print 'autoscaling>>>>checking nodes : ' , str(nodes)
			if nodes :
				logger.info('Checking nodes : ' + json.dumps(nodes))
				
			for node in nodes :
				data = self.cache.get(node, self.policy['component'])
				#print 'node:%s comp:%s data:%s' %(node, self.policy['component'], str(data))
				logger.debug('%s->%s:%s' %(node, self.policy['component'], json.dumps(data)))
				if data == None :
					all = False
					#print 'Not all server ready'
					logger.info('Not all nodes ready')
					message = 'Not all server ready'
 				else :
					v = data[self.policy['metric']]
					total = total + v
			
			avg = 0
			number = len(nodes)
			if all and number > 0:
				avg = total / number
				#print 'avg = ', str(avg)
				logger.info('Current average value is ' + str(avg))
				message = 'average value = ' + str(avg)

				self.status = {'state':'calculating','message' : message}
				
				if avg > self.policy['scaleout']['threshold'] :
					if not timing :
						#print 'autoscaling>>>>start timing trigger time start'
						logger.info('Start timing trigger time ')
						counting_time = time.time()
						self.status = {'state':'timing','message' : 'start'}
						timing = True
						
					else :							
						current_time = time.time()
						if current_time - counting_time >= self.policy['scaleout']['triggertime'] :
							#print 'autoscaling>>>> scaling out'
							logger.info('Scaling out ')
							self.status = {'state':'scaling','message' : 'adding node '}
							node = self.topology.scale_out()								
							logger.info('Adding node ' + node)					
							scaling = True
							self.status = {'state':'scaling','message' : 'waiting for' + node + ' ready'}
							logger.info('Waiting for the new node ready ')
							time.sleep(120)
							logger.info('Planting collector to the node ' +  node)
							node_ipaddress  = self.topology.get_node_ipaddress(node)
							if node_ipaddress :
								self.installer.set_trust(node_ipaddress)
								self.installer.install(node_ipaddress)
							timing = False
							scaling = False
						else :
							#print 'autoscaling>>>> timing trigger time ' + str(self.policy['scaleout']['triggertime']) + ',' +  str(current_time - counting_time).split('.')[0] + 'elapsed'
							logger.info(str(current_time - counting_time).split('.')[0] + ' seconds elapsed, but not reach trigger time ' + str(self.policy['scaleout']['triggertime']) + ' seconds')
							self.status = {'state':'timing','message' : str(current_time - counting_time).split('.')[0] + ' seconds elapsed, but not reach trigger time ' + str(self.policy['scaleout']['triggertime']) + ' seconds'}
							
				else: 
					#print 'autoscaling>>>>threshold not met'
					logger.info('Yet not reach the threshold ' + str(self.policy['scaleout']['threshold']))
					timing = False
					counting_time = time.time()
					self.status = {'state':'calculating','message' : 'not reach the threshold ' + str(self.policy['scaleout']['threshold'])}
			else :
				self.status = {'state':'checking','message' : 'not all server ready'}			
			
			time.sleep(10)
			
			
			
			