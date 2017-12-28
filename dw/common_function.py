#coding:utf8
import uuid
import os

def mac_computer_name_get():
    mymac=uuid.UUID(int = uuid.getnode()).hex[-12:]

    sys_type = os.name
    myname = None
    if sys_type == 'nt':
        myname = os.getenv('computername')
    elif sys_type == 'posix':
        try:
            host = os.popen('echo $HOSTNAME')
            myname = host.read()
        except:
            pass
    return mymac, myname