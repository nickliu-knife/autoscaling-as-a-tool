class Cache() :
	cache = None
	def __init__(self) :
		self.cache = {}
	
	def put(self, node, component, data) :
		if not self.cache.has_key(node) :
			self.cache[node] = {}
		
		self.cache[node][component] = data
	
	def get(self, node, component) :
		if  self.cache.has_key(node) and self.cache[node].has_key(component) :
			return self.cache[node][component]
		
		return None
		
	def dump(self):
		print 'this is for debug, cache = ' ,str(self.cache)
		return self.cache