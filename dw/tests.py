#coding:utf-8
import re,os
from datetime import datetime
import time
import uuid
import base64
from django.shortcuts import render_to_response
from common_function import mac_computer_name_get


# Create your tests here.

def test(request):
    mymac, myname = mac_computer_name_get()

    #转换成时间戳
    a = '2018-11-7 10:30:30'  #该管理系统可用时限
    cdkey_time = int(time.mktime(time.strptime(a,'%Y-%m-%d %H:%M:%S')))

    nameMacTime = myname + mymac + str(cdkey_time)
    CDKEY= base64.encodestring(nameMacTime)  #生成加码字符串（激活码）


    return render_to_response('test.html',locals())
