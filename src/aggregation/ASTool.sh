#!/usr/bin/env bash

LOCAL_IP=`LC_ALL=C ifconfig|grep "inet addr:"|grep -v "127.0.0.1"|cut -d: -f2|awk '{print $1}'`

case $1 in 
install)
	
	echo "Change file permission"
	chmod +x -R ./libs
	chmod 600 -R ./libs/provisioner/key	
	chmod +x -R ./dependencies
	
	echo  "Installing packages"
	cd ./dependencies/six/	
	python setup.py install
	cd ../../
	cd ./dependencies/kafka-python/
	python setup.py install
	cd ../../

	service iptables stop
	service ip6tables stop
	##advertised.host.name=<hostname routable by clients>
	#sed "s/.*CTIRA_SYSTEM_NAME.*/export CTIRA_SYSTEM_NAME="$HOSTNAME"/" $ITM_Q9_CONFIG >> $ITM_Q9_CONFIG_TMP
	sed "s/.*advertised.host.name.*/advertised.host.name="$LOCAL_IP"/" ./dependencies/kafka/config/server.properties >> ./dependencies/kafka/config/server.properties.new
	rm -f ./dependencies/kafka/config/server.properties
	mv ./dependencies/kafka/config/server.properties.new ./dependencies/kafka/config/server.properties
	
	;;
start)
	echo  "Starting zookeeper"
	cd dependencies/zookeeper/bin/
	./zkServer.sh start
	cd ../../..
	
	echo "Wait for zookeeper ready"
	sleep 10s
	echo  "Starting kafka"
	./dependencies/kafka/bin/kafka-server-start.sh ./dependencies/kafka/config/server.properties > logs/kafka.log &
	
	echo "Wait for kafka ready"
	sleep 30s
	
	echo "Starting aggregator"
	python ./libs/aggregator.py &
	;;
stop)
	echo  "Stop aggregator"
	ps -ef | grep aggregator.py | grep -v grep | awk '{print $2}' | xargs kill -9
	echo  "Stop kafka"
	ps -ef | grep kafka | grep -v grep | awk '{print $2}' | xargs kill -9
	echo  "Stop zookeeper"
	ps -ef | grep zookeeper | grep -v grep | awk '{print $2}' | xargs kill -9	
	;;
	
stopall)
	echo "Stop all including collectors"
	;;
stopagg)
	echo "Stop aggregator"
	ps -ef | grep aggregator.py | grep -v grep | awk '{print $2}' | xargs kill -9
	;;
startagg)
	echo "Start aggregator"
	python ./libs/aggregator.py &
	;;
*)
	echo "Usage: $0 {install|start|stop|restart|stopall}" >&2
esac
