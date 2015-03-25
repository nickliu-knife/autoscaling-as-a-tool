import logging
import subprocess
import os

log_dir =  os.path.join(os.getcwd(),'logs')
print log_dir
if not os.path.exists(log_dir) :
	os.mkdir(log_dir)
log_file = os.path.join(log_dir, 'installer.log')

logger = logging.getLogger('installer')
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

class Installer ():
	
	installer = None
	node_config = None
	def __init__(self, node_config) :	
		self.installer = os.path.join(os.getcwd(),'libs', 'installcollector.sh')
		self.node_config = node_config
		
	def set_trust(self, dest):
		logger.info('Set trust on ' + dest)
		if cmp(self.node_config['auth']['method'], 'password') == 0:
			script  = os.path.join(os.getcwd(),'libs', 'ssh-no-log-on.sh')
			cmd = script + ' ' +  dest + ' ' + self.node_config['auth']['password']['user'] + ' ' +  self.node_config['auth']['password']['password']
			#print cmd
			logger.debug('cmd = ' + cmd)
			p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			p.wait()
			output = p.stdout.readlines()
			logger.debug('output = ' + str(output))
		elif cmp(self.node_config['auth']['method'], 'password') :
			#assume the id_rsa is already in \libs\provisioner\key
			pass
		
	def install(self, dest) :
		logger.info('Install collector on ' + dest)
		#cmd = '/root/monitoring/installcollector.sh %s' %(node)
		cmd = self.installer + ' ' +  dest
		#print cmd
		logger.debug('cmd = ' + cmd)
		p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		p.wait()
		output = p.stdout.readlines()
		#print output
		logger.debug('output = ' + str(output))