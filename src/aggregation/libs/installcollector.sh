IP=$1
LOCAL_IP=`LC_ALL=C ifconfig|grep "inet addr:"|grep -v "127.0.0.1"|cut -d: -f2|awk '{print $1}'`
BASE=`pwd`
echo $BASE
RSA=$BASE/libs/provisioner/key/id_rsa
echo $RSA
DIST=$BASE/dist
echo $DIST
echo $IP

#ssh  -o "StrictHostKeyChecking no" -i id_rsa root@9.110.95.141 "ps -ef | grep collector.py | grep -v grep | awk '{print $2}' | xargs kill -9"
ssh  -o "StrictHostKeyChecking no" -i $RSA root@$IP "ps -ef | grep collector.py | grep -v grep | awk '{print $2}' | xargs kill -9"
ssh  -o "StrictHostKeyChecking no" -i $RSA root@$IP "rm -rf  /root/collector"
ssh  -o "StrictHostKeyChecking no" -i $RSA root@$IP "mkdir /root/collector" 
scp  -o "StrictHostKeyChecking no" -i $RSA $DIST/collector.tgz root@$IP:/root/collector/collector.tgz 
ssh  -o "StrictHostKeyChecking no" -i $RSA root@$IP "cd /root/collector/; tar zxvf /root/collector/collector.tgz"
ssh  -o "StrictHostKeyChecking no" -i $RSA root@$IP "cd /root/collector/six; python setup.py install" 
ssh  -o "StrictHostKeyChecking no" -i $RSA root@$IP "cd /root/collector/kafka-python; python setup.py install"
ssh  -o "StrictHostKeyChecking no" -i $RSA root@$IP "service iptables stop"
ssh  -o "StrictHostKeyChecking no" -i $RSA root@$IP "cd /root/collector/;python collector.py $LOCAL_IP:9092 > /root/collector/collector.log &" 
