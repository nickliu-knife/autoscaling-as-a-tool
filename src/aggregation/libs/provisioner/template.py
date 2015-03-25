
'''
This class is not for use, just demo what methods need to be provide by provison Topology
'''
class Topology():
	
	'''
	Information APIs
	'''
	def create(self) :
		pass

	def list_nodes(self):
		pass

	def get_node_info(self, node):
		pass
	
	def get_node_ipaddress(self, node):
		pass

	def get_topology(self):
		pass
	
	
	'''
	Scaling APIs
	'''
	def scale_out(self):
		pass
	
	def scale_in(self, node = None):
		pass		
