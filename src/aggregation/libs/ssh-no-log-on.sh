#!/bin/bash
IP=$1
USER=$2
PASSWORD=$3
BASE=`pwd`
RSA=$BASE/libs/provisioner/key/

#ssh-keygen -t rsa -C "autoscaling" -f ./id_rsa -P ''
#scp id_rsa.pub $USER@@IP:/tmp
#cat id_rsa.pub >>  ~/.ssh/authorized_keys

auto_scp () {
    expect -c "set timeout -1;
                spawn scp -o StrictHostKeyChecking=no ${@:2};
                expect {
                    *assword:* {send -- $1\r;
                                 expect {
                                    *denied* {exit 1;}
                                    eof
                                 }
                    }
                    eof         {exit 1;}
                }
                "
    return $?
}

auto_smart_ssh () {
    expect -c "set timeout -1;
                spawn ssh -o StrictHostKeyChecking=no $2 ${@:3};
                expect {
                    *assword:* {send -- $1\r;
                                 expect {
                                    *denied* {exit 2;}
                                    eof
                                 }
                    }
                    eof         {exit 1;}
                }
                "
    return $?
}
 
rm $RSA/id_rsa*
ssh-keygen -t rsa -C "autoscaling" -f $RSA/id_rsa -P ''
chmod 600 $RSA/id_rsa
auto_scp $PASSWORD $RSA/id_rsa.pub $USER@$IP:/tmp
auto_smart_ssh $PASSWORD $USER@$IP "cat /tmp/id_rsa.pub >>  ~/.ssh/authorized_keys"

echo $?

