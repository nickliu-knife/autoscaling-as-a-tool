import os
import json
import subprocess
import time

#Files for introspection
#/etc/virtualimage.properties
#
#WCA_VIRTUAL_MACHINE=/resources/virtualSystems/77/virtualMachines/96
#WCA_VIRTUAL_SYSTEM=/resources/virtualSystems/77
#WCA_IPADDRESS=fd8c:215d:178e:2222:290:fa72:fa1e:9346,fd8c:215d:178e:888:290:fa72:fa1e:9346
#PURESCALE_IPADDRESS=fd8c:215d:178e:888:290:fa72:fa1e:9346
#curl -u "admin:babyrack" -H "X-IBM-Workload-Deployer-API-Version:5.0.0.1"  -H "X-IBM-Workload-Deployer-API-Session:NONE" -g -kv --url https://[fd8c:215d:178e:888:290:fa72:fa1e:9346]/resources/virtualSystems/77/virtualMachines/


class Topology():
	topology = None
	user = None
	password = None

	def __init__(self, config) :
		self.topology = {}
		self.user = config['user']
		self.password = config['password']
		self.apiversion = config['apiversion']
	
	def create(self) :
		self._load()
		self._search_nodes()

	def list_nodes(self):
		nodes = []
		for n,v in self.topology['nodes'].items() :
			nodes.append(n)
		return nodes

	def scale_out(self):
		'''
		POST /resources/virtualSystems/{vs_id}/virtualMachines/
		--data:
		{
			"desiredcount": 1,
			"virtualmachine": "/resources/virtualSystems/212/virtualMachines/288",
			"identifier": "hello_nick"
		}
		'''
		
		print 'scale out'
		#curl -u "admin:babyrack"  -X POST -H "X-IBM-Workload-Deployer-API-Version:5.0.0.1"  -H "X-IBM-Workload-Deployer-API-Session:NONE" -H "Content-Type:application/json" -kv --data @x.json --url "https://9.111.142.16/resources/virtualSystems/212/virtualMachines"
		url = "https://[%s]%s/virtualMachines/" % ( self.topology['PURESCALE_IPADDRESS'], self.topology['WCA_VIRTUAL_SYSTEM'])
		#print 'url=', url

		cloned = self.topology['WCA_VIRTUAL_MACHINE']
		identifier = 'scaled_'+ str(time.time()).split('.')[0]
		data_string = '{"desiredcount": 1,"virtualmachine": "%s", "identifier": "%s"}'%(cloned, identifier)
		#print 'data=', data_string
		
		datafile = '/tmp/data.json'
		f = None
		try :
			f = open(datafile, 'w')
			f.write(data_string)
		finally :
			if f :
				f.close()

		cmd = "curl -u \"%s:%s\" -X POST -H \"X-IBM-Workload-Deployer-API-Version:%s\" -H \"Content-Type:application/json\" -k  --data @%s -g --url %s" % (self.user, self.password, self.apiversion, datafile,url)
		print 'cmd = ' , cmd
		p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		p.wait()
		#print p.stdout.readlines()
		
		number = len(self.list_nodes())
		self.create()
		while len(self.list_nodes()) <= number :
			print 'wca>>>>Refresh the topology'
			print str(self.list_nodes())
			time.sleep(30)
			self.create()
			
		for n, v in self.topology['nodes'].items() :
			if cmp (identifier, v['wca_identifier']) == 0 :
				return n
	
	def scale_in(self, node = None):
		'''
		TODO
		DELETE /resources/virtualSystems/{vs_id}/virtualMachines/{vm_id}
		'''
		
		# must check it is not this node
		
		vm_id = ''
		if node :
			if self.topology['nodes'].has_key(node):
				vm_id = self.topology['nodes'][node]['wca_id']
		else :
			# TODO pick up a node
			pass
			
		url = "https://[%s]%s/virtualMachines/%s" % ( self.topology['PURESCALE_IPADDRESS'], self.topology['WCA_VIRTUAL_SYSTEM'], vm_id)
		#print 'url=', url
		cmd = "curl -u \"%s:%s\" -X DELETE -H \"X-IBM-Workload-Deployer-API-Version:%s\" -H \"Content-Type:application/json\" -k  -g --url %s" % (self.user, self.password, self.apiversion,url)
		
		#print 'cmd = ' , cmd
		p = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		
		return node
		

	def get_node_info(self, node):                
		for n, v in self.topology['nodes'].items() :
			if cmp (n, node) == 0 :
				return v
	
	def get_node_ipaddress(self, node):
		for n, v in self.topology['nodes'].items() :
			if cmp (n, node) == 0 :
				return v['ip_address']

	
	def _load(self) :
		f = open('/etc/virtualimage.properties', 'r')
		lines = f.readlines()
		for line in lines :
			if line.find('WCA_VIRTUAL_SYSTEM') == 0 :
				self.topology['WCA_VIRTUAL_SYSTEM'] = line[len('WCA_VIRTUAL_SYSTEM='):].rstrip()
			if line.find('PURESCALE_IPADDRESS') == 0 :
				self.topology['PURESCALE_IPADDRESS'] = line[len('PURESCALE_IPADDRESS='):].rstrip()
			if line.find('WCA_VIRTUAL_MACHINE') == 0 :
				self.topology['WCA_VIRTUAL_MACHINE'] = line[len('WCA_VIRTUAL_MACHINE='):].rstrip()

	def _search_nodes(self) :
		nodes = {}
		tmpfile = '/tmp/virtualsystem.json'
		url = "https://[%s]%s/virtualMachines/" % ( self.topology['PURESCALE_IPADDRESS'], self.topology['WCA_VIRTUAL_SYSTEM'])
		print 'url = ', url
		cmd = "curl -u \"%s:%s\" -H \"X-IBM-Workload-Deployer-API-Version:%s\" -k  -g --url %s  -o %s" % (self.user, self.password, self.apiversion, url, tmpfile)
		print 'cmd = ' , cmd
		p = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

		f = open(tmpfile)
		try:
			json_str = f.read()
			vs = json.loads(json_str)
			#print '-------------vs : ', str(vs)
			for vm in vs :
				if vm[u'currentstatus_text'] and cmp(vm['currentstatus_text'], 'Started') == 0 :
					for nic in vm['nics'] :
						#print nic
						if nic['ip_hostname'] and cmp(nic['type'], 'public') == 0:
							nodes[nic['ip_hostname']]= {'ip_address':nic['ip_address'],'wca_id' : vm['id'],'wca_identifier':vm['identifier']}
							#nodes[nic['ip_hostname']] = {'wca_id' : vm['id']}
		finally:
			if f :
				f.close()
				os.remove(tmpfile)

		self.topology['nodes'] = nodes
		
	def get_topology(self):
		return  self.topology
