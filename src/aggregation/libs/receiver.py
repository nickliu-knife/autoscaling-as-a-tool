import threading
import json

from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer

class Receiver (threading.Thread):
	kafka = None
	consumer = None
	kafkaHost = "localhost:9092"
	
	cache = None
	
	def __init__(self, cache) :
	
		threading.Thread.__init__(self)

		self.kafka = KafkaClient(self.kafkaHost)
		self.consumer = SimpleConsumer(self.kafka, "test-group", "collector")
		
		self.cache = cache
		
	def run(self) :
		for q,m in self.consumer:
			message =  m.value
		
			try :
				object = json.loads(message)
				if object.has_key('node') :
					node = object['node']
					for component, data in object.items():
						#print 'message object-->',component, str(data)
						if cmp(component, node) == 0 :
							continue
							
						self.cache.put(node, component, data)
						
			except Exception, e:
				print str(e)