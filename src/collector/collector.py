import threading
import json
import subprocess
import time
import re
import sys

from kafka.client import KafkaClient
from kafka.producer import SimpleProducer

class OSCollector(threading.Thread):  
    path = None
    kafka = None
    producer = None
    kafkaHost = None #'9.110.95.141:9092'
    hostname = None

    def __init__(self, kafkaHost) :     

        if kafkaHost is None :
            raise SyntaxError('Unknown kafka server')

        self.kafkaHost = kafkaHost

        threading.Thread.__init__(self)

        p = subprocess.Popen('hostname -f', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	for line in p.stdout.readlines() :
            self.hostname = line.lstrip().rstrip()
            break
        
        self.path = '/root/x.json'        

        
        self.kafka = KafkaClient(self.kafkaHost)
        self.producer = SimpleProducer(self.kafka)
        
    def run(self) :
        while True :
            cpu = self.get_cpu_usage()
            memory = self.get_mem_usage()
            
            message = {}
            message["node"] = self.hostname
            systemObject = {}
            systemObject["cpu"] = cpu
            systemObject["memory"] = memory
            message["system"] = systemObject

            try :
                print str(message)
                self.producer.send_messages( "collector",str(json.dumps(message)))
            except Exception, e:
                print str(e)
        
            time.sleep(10)
	
    def _read_cpu_usage(self):  
        """Read the current system cpu usage from /proc/stat.""" 
        try:  
            fd = open("/proc/stat", 'r')  
            lines = fd.readlines()  
        finally:  
            if fd:  
                fd.close()  
                            
        for line in lines:  
            l = line.split()  
            if len(l) < 5:  
                continue 
            if l[0].startswith('cpu'):  
                return l  
        return []  
   
    def get_cpu_usage(self):  
        """ 
        get cpu avg used by percent 
        """ 
        cpustr=self._read_cpu_usage()  
        if not cpustr:  
                return 0 
        #cpu usage=[(user_2 +sys_2+nice_2) - (user_1 + sys_1+nice_1)]/(total_2 - total_1)*100  
        usni1=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])+long(cpustr[5])+long(cpustr[6])+long(cpustr[7])+long(cpustr[4])  
        usn1=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])  
        #usni1=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])+long(cpustr[4])  
        # self.sleep=2  
        time.sleep(2)  
        cpustr=self._read_cpu_usage()  
        if not cpustr:  
                return 0 
        usni2=long(cpustr[1])+long(cpustr[2])+float(cpustr[3])+long(cpustr[5])+long(cpustr[6])+long(cpustr[7])+long(cpustr[4])  
        usn2=long(cpustr[1])+long(cpustr[2])+long(cpustr[3])  
        cpuper=(usn2-usn1)/(usni2-usni1)  
        return 100*cpuper

    re_meminfo_parser = re.compile(r'^(?P<key>\S*):\s*(?P<value>\d*)\s*kB')  
    def get_mem_usage(self):  
        """ 
        get mem used by percent 
        self.result = falot 
        """  
        result={}  
        try:  
            fd=open('/proc/meminfo', 'r')  
            lines=fd.readlines()  
        finally:  
            if fd:  
                fd.close()  
        for line in lines:  
            match = self.re_meminfo_parser.match(line)  
            if not match:  
                continue # skip lines that don't parse  
            key, value = match.groups(['key', 'value'])  
            result[key] = int(value)  
        #print "mem :", 100*(result["MemTotal"]-result["MemFree"])/result["MemTotal"]  
        return 100.0*(result["MemTotal"]-result["MemFree"])/result["MemTotal"]  

if __name__ == "__main__":
    if len(sys.argv) < 2 :
        print 'Wrong argument.'
        print 'Usage :'
        print 'python collector.py <server:port>'
        exit(0) 
    #9.110.95.141:9092
    server = sys.argv[1]
    collector = OSCollector(server)
    collector.start()
	
