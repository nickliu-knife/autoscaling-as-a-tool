import json
import requests
import time
'''
http://developer.openstack.org/api-ref-orchestration-v1.html
'''
class Topology :
	os_url = None
	domain = None
	user = None
	password = None
	auth_version = None
	
	topology = None
	
	def __init__(self, config) :
		self.os_url = None
		self.domain = config['domain']
		self.user = config['user']
		self.password = config['password']
		self.auth_version = config['auth_version']
		
		self.topology = {}
		
	#Files for introspection
	#/var/lib/cloud/instances/7f916bb4-47f6-4ed3-933c-6435146cc4ba
	#/var/lib/cloud/data/cfn-boto-cfg
	#/var/lib/cloud/data/instance-id
	
	'''
	Information APIs
	'''
	def create(self) :
		self._load()
		
	
	def get_topology(self):
		return  self.topology
	
	def get_node_info(self, node):
		for n, v in self.topology['nodes'].items() :
			if cmp (n, node) == 0 :
				return v
		
	def get_node_ipaddress(self, node):
		#TODO
		print 'node = ', node
		ipaddress = self.topology['nodes'][node]['ipaddress']['net01'][0]['addr']
		print ipaddress
		return ipaddress
	
	def list_nodes(self):
		return self.topology['nodes']	
	
	def _load(self):
		f = open('/var/lib/cloud/data/cfn-boto-cfg', 'r')
		try :
			lines = f.readlines()
			for line in lines :
				if line.find('cfn_region_endpoint') == 0 :
					self.os_url = 'http://%s:5000'%(line.split('=')[1].lstrip().rstrip())
					print self.os_url
					break
		finally :
			if f :
				f.close()
		
		f = open ('/var/lib/cloud/data/instance-id')
		try :
			instance = f.readline().lstrip().rstrip()
		finally :
			if f :
				f.close()
		
		#match current stack by instance id
		stacks = self.stack_list()['stacks']
		for stack in stacks :
			print stack
			stack_id = stack['id']
			stack_name = stack['stack_name']
			(code, r) = self.stack_resources(stack_name, stack_id)
			resources = r['resources']
			for resource in resources :
				if cmp(resource['physical_resource_id'], instance) == 0 :
					self.topology['stack_name'] = stack_name
					self.topology['stack_id'] = stack_id
					nodes = self._find_nodes(resources)
					self.topology['nodes'] = nodes
		
		print self.topology
				
	def _find_nodes (self, resources):
		nodes = {}
		for r in resources :
			if cmp(r['resource_type'], 'OS::Nova::Server') == 0 :
				(code,ipaddress) = self._nova_ips(r['physical_resource_id'])
				nodes[r['resource_name']] = {'resource_id' : r['physical_resource_id'], 'ipaddress' : ipaddress['addresses']}
		return nodes	
	

	
	'''
	Heat APIs
	#http://developer.openstack.org/api-ref-orchestration-v1.html
	'''
	def _heat_call(self, type, heat_api, d=None):

		req_header = {"Content-Type" : "application/json", "Accept" : "application/json"}
		
		req_data = { "auth": {"identity": {"methods": ["password"], "password": {"user": {"domain": {"name": self.domain},"name": self.user,"password": self.password}}}}}

		res = requests.post(self.os_url + "/v3/auth/tokens", data = json.dumps(req_data), headers = req_header)
		if res.status_code == 201:
			token = res.headers['x-subject-token']
			res_json = res.json()
			for service in res_json['token']['catalog']:
				#print 'service=', service['name']
				if cmp(service['name'], 'heat') == 0 :
					heat_base_url = service['endpoints'][0]['url']

		#print token
		#print heat_base_url
		req_header = {"Content-Type" : "application/json", "X-Auth-Token" : token, "Accept" : "application/json"}
		url = heat_base_url + heat_api
		print url
		if type == 'GET' :
			res = requests.get(url, headers = req_header)
		if type == 'PUT' :
			#print json.dumps(d)
			res = requests.put(url, data = json.dumps(d), headers = req_header)
			
		content = None
		try :
			content = res.json()
		except :
			content = res.text
			
			
		return res.status_code, content

	def stack_list(self) :
		'''
		GET /v1/{tenant_id}/stacks
		'''
		(code, stacks) = self._heat_call('GET', '/stacks')
		return stacks
		

	def statck_detail(self, name, id) :
		'''
		GET /v1/{tenant_id}/stacks/{stack_name}/{stack_id}
		'''
		return self._heat_call('GET', '/stacks/%s/%s' %(name, id))
		

	def stack_template(self, name, id) :
		'''
		GET	/v1/{tenant_id}/stacks/{stack_name}/{stack_id}/template
		'''
		return self._heat_call('GET', '/stacks/%s/%s/template' %(name, id))

	def stack_update(self, name, id, data) :
		'''
		PUT	/v1/{tenant_id}/stacks/{stack_name}/{stack_id}
		'''

		return self._heat_call('PUT', '/stacks/%s/%s' %(name, id), data)

	def stack_resources(self, name,id):
		'''
		GET /v1/{tenant_id}/stacks/{stack_name}/{stack_id}/resources
		'''
		return self._heat_call('GET', '/stacks/%s/%s/resources'%(name, id))
	
	def stack_resource_data(self, stack_name, stack_id, resource_name):
		'''
		GET /v1/{tenant_id}/stacks/{stack_name}/{stack_id}/resources/{resource_name}
		'''		
		return self._heat_call('GET', '/stacks/%s/%s/resources/%s'%(stack_name, stack_id, resource_name))
	
	
	'''
	NOVA APIs
	#http://developer.openstack.org/api-ref-compute-v2.html
	'''
	def _nova_call(self, type, heat_api, d=None):

		req_header = {"Content-Type" : "application/json", "Accept" : "application/json"}
		
		req_data = { "auth": {"identity": {"methods": ["password"], "password": {"user": {"domain": {"name": self.domain},"name": self.user,"password": self.password}}}}}

		res = requests.post(self.os_url + "/v3/auth/tokens", data = json.dumps(req_data), headers = req_header)
		if res.status_code == 201:
			token = res.headers['x-subject-token']
			res_json = res.json()
			for service in res_json['token']['catalog']:
				if cmp(service['name'], 'nova') == 0 :
					nova_base_url = service['endpoints'][0]['url']

		#print token
		#print nova_base_url
		req_header = {"Content-Type" : "application/json", "X-Auth-Token" : token, "Accept" : "application/json"}
		url = nova_base_url + heat_api
		print url
		if type == 'GET' :
			res = requests.get(url, headers = req_header)
		if type == 'PUT' :
			print json.dumps(d)
			res = requests.put(url, data = json.dumps(d), headers = req_header)
		
		return res.status_code, res.json()
	
	def _nova_ips(self, server_id):
		'''
		GET /v2/{tenant_id}/servers/{server_id}/ips
		'''
		return self._nova_call('GET', '/servers/%s/ips'%(server_id))
		


	'''
	Scaling APIs
	'''
	def _remove_server(self, template, server_name):
		
		#1. remove server resource
		del( template['resources'][server_name])		
		#2. remove EIP resource
		del(template['resources'][server_name +'_EIP'])		
		#3. remove EIPAssoc resource
		del (template['resources'][server_name +'_EIPAssoc'])								
		return template
	
	def _clone_server1(self, template, server_name):
		#e.g. "WAS.11421306120484		
		server_resource = template['resources'][server_name]
		group_name =  template['resources'][server_name]['properties']['scheduler_hints']['group']['get_resource']
		new_server_name = group_name + '.' + str(time.time()).split('.')[0]
		print 'The new server name is ' , new_server_name
		
		#1. copy server resource
		server_resource_string = str(server_resource) 
		server_resource_string = server_resource_string.replace(server_name, new_server_name)
		new_server_resource = eval(server_resource_string)
		#print new_server_resource
		template['resources'][new_server_name] = new_server_resource
		
		
		#create EIP resource
		new_eip_resource_name = new_server_name +'_EIP'
		template['resources'][new_eip_resource_name]={ "type": "OS::Nova::FloatingIP"}
		
		#create EIPAssoc resource
		new_eipassoc_resource_name = new_server_name +'_EIPAssoc'
		properties = {"server_id": { "get_resource": new_server_name}, "floating_ip": {"get_resource": new_eip_resource_name}}
		new_eip_resource = { "type": "OS::Nova::FloatingIPAssociation","properties":properties}
		template['resources'][new_eipassoc_resource_name] = new_eip_resource
		
		return template, new_server_name
	
	def _clone_server(self, template, server_name):
		#e.g. "WAS.11421306120484		
		server_resource = template['resources'][server_name]
		group_name =  template['resources'][server_name]['properties']['scheduler_hints']['group']['get_resource']
		new_server_name = group_name + '.' + str(time.time()).split('.')[0]
		print 'The new server name is ' , new_server_name
		
		#1. copy server resource
		server_resource_string = str(server_resource) 
		server_resource_string = server_resource_string.replace(server_name, new_server_name)
		new_server_resource = eval(server_resource_string)
		#print new_server_resource
		template['resources'][new_server_name] = new_server_resource
		
		
		#create EIP resource
		new_eip_resource_name = new_server_name +'-Default_add_NIC_in_Openstack'
		template['resources'][new_eip_resource_name]={'type': 'OS::Neutron::Port','properties': {'fixed_ips': [{'subnet': 'net01-subnet01'}],'network': 'net01'}}
		
		new_eip_resource_name = new_server_name +'-Default_add_NIC_in_Openstack_1'
		template['resources'][new_eip_resource_name]={'type': 'OS::Neutron::Port','properties': {'fixed_ips': [{'subnet': 'net02-subnet01'}],'network': 'net02'}}
		
		#create EIPAssoc resource
		new_eipassoc_resource_name = new_server_name +'-floating_ip'
		new_eip_resource = {'type': 'OS::Neutron::FloatingIP','properties': {'floating_network': 'public','port_id': {'get_resource': new_server_name + '-Default_add_NIC_in_Openstack'}}}
		template['resources'][new_eipassoc_resource_name] = new_eip_resource
		
		new_output_ip_name =  new_server_name + '_IP'
		new_output_ip = {"description": "IP of " + new_server_name + " instance","value": {"get_attr": [new_server_name + "-Default_add_NIC_in_Openstack","fixed_ips",0,"ip_address"]}}
		template['outputs'][new_output_ip_name] = new_output_ip
		
		new_output_eip_name = new_server_name + 'EIP'
		new_output_eip =  {"description": "Floating IP of " + new_server_name + " instance","value": {"get_attr": [new_server_name + "-floating_ip","floating_ip_address"]}}
		template['outputs'][new_output_eip_name] = new_output_eip
		
		return template, new_server_name
	
	
	def scale_in(self, node = None):
		(code, template) = self.stack_template(self.topology['stack_name'], self.topology['stack_id'])
		new_template = self._remove_server(template, node)
		
		(code, details) = self.statck_detail(self.topology['stack_name'], self.topology['stack_id'])
		parameters = details['stack']['parameters']
		del(parameters['OS::stack_id'])
		del(parameters['OS::stack_name'])
		#print self.stack_update(self.topology['stack_name'], self.topology['stack_id'],{'template' : new_template, 'parameters': parameters})
		(code, content) = self.stack_update(self.topology['stack_name'], self.topology['stack_id'],{'template' : new_template, 'parameters' : parameters})
		
		print content	
		
		
	def scale_out(self):
		(code, template) = self.stack_template(self.topology['stack_name'], self.topology['stack_id'])
		
		#print '---------------------------------'
		#print str(template)
		# find candidate server OS::Nova::ServerGroup
		server_group = None
		server_name = None
		for k,v in template['resources'].items():
			#print v['type']
			if cmp(v['type'], 'OS::Nova::ServerGroup') == 0 :
				server_group = k
				print server_group
				break
		
		if server_group :
			for k,v in template['resources'].items():
				if cmp(v['type'], 'OS::Nova::Server') == 0 :
					if v['properties'].has_key('scheduler_hints') :
						if cmp (server_group, v['properties']['scheduler_hints']['group']['get_resource']) == 0 :
							server_name = k
							print server_name
							break
				
		if server_name : 
			(new_template, new_server_name) = self._clone_server(template, server_name)
			#print 'tttttttttttttttttttttt'
			#print json.dumps(new_template)
			(code, details) = self.statck_detail(self.topology['stack_name'], self.topology['stack_id'])
			parameters = details['stack']['parameters']
			del(parameters['OS::stack_id'])
			del(parameters['OS::stack_name'])
			#print self.stack_update(self.topology['stack_name'], self.topology['stack_id'],{'template' : new_template, 'parameters': parameters})
			(code, content) = self.stack_update(self.topology['stack_name'], self.topology['stack_id'],{'template' : new_template, 'parameters' : parameters})
			#print 'cccccccccccccccccccccccccccccccc'
			#print str(content)
			if code == 202 :
				print 'added new server : ', new_server_name
				return new_server_name	
		else :
			return None
'''
import os 

f = open('/root/monitoring/conf/scaling.cfg')
cfg = json.load(f)
topo = Topology(cfg['iaas']['config'])
topo.create()
topo.scale_out()
#topo.scale_in('WAS.1422948788')
'''
