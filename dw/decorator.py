#coding:utf8
from django.shortcuts import render,render_to_response,HttpResponse,HttpResponseRedirect
from models import *
import os,time,sys,base64,uuid,socket
from common_function import mac_computer_name_get


def views_permission(fun):
    def wrap(request,*args,**kwargs):

        user = request.session.get('USERNAME',False)
        try:
            staff_user = User.objects.get(username=user)
        except:
            return HttpResponseRedirect('/login')
        ############################################################             参数
        hase_per = kwargs.get('views_permission',None)
        #print hase_per
        project_id = kwargs.get('project_id',None)
        ticket_id = kwargs.get('ticket_id',None)
        wiki_id = kwargs.get('wiki_id',None)
        roadmap_name = kwargs.get('roadmap_name',None)
        group_id = kwargs.get('group_id',None)
        user_id = kwargs.get('user_id',None)
        application_people = kwargs.get('application_people',None)
        task_team_id = kwargs.get('task_team_id',None)
        ###############################################################            检查项目是否存在
        if project_id is not None :
            if Project.objects.filter(id=project_id).exists() :
                kwargs.setdefault('project',Project.objects.get(id=project_id))
                if group_id is not None:
                    #print type(Group.objects.get(id=group_id).owner_project)
                    if Group.objects.filter(id=group_id).exists() and project_id==str(Group.objects.get(id=group_id).owner_project_id):
                        kwargs.setdefault('group_id',group_id)
                    else:
                        error = '您没有该小组的编辑权限！'
                        return render_to_response('permission_notice.html',locals())
                else:
                    pass
            else:
                error = '未找到该项目!'
                return render_to_response('permission_notice.html',locals())
                ###################################################################







            #########################################################################
        staff_permission = staff_user.user_permission.all()                    #用户个人所有权限
        groups = staff_user.group.all()                                   #用户所有所属组
        group_permission_all = []                                         #用户所有所属组的全部权限
        for i in groups:
            for j in i.group_permission.all():
                group_permission_all.append(j)
        staff_all_per = list(set(list(staff_permission)+group_permission_all))    #用户所有权限

        active = staff_user.is_active                                         #用户账户是否激活
        super_user = staff_user.is_superuser                                 #是否是超级用户
        super_permission = Permission.objects.all()                        #权限列表所有权限

        label_control_per_dict = {}                                        #按钮控制权限   暂未启用
        all_views_per_list = []                                            #views权限列表  用于判断用户项目之外的权限
        per_project_id_list = []                                           #项目id列表     用于判断与项目相关的权限
        for i in staff_all_per:
            all_views_per_list.append(i.view_name)
            per_project_id_list.append(i.project_id)

        views_per_list = []                                                 #用户与项目相关的views权限列表
        for i in  staff_all_per:
            if i.project_id == project_id:
                views_per_list.append(i.view_name)





        if active is False:              #账户冻结
            error = '此用户的账户已被冻结，所有权限均已失效,如有问题请联系管理员！'
            return render_to_response('permission_notice.html',locals())

        if super_user is True:           #超级用户
            for i in super_permission:
                label_control_per_dict.setdefault(i.label_control,i.id)
            kwargs.setdefault('label_control_per_dict',label_control_per_dict)

        if hase_per is None :                  #实现传参 但不检查权限
            pass
            #return HttpResponse('hase_per is None!')

        try:
            is_check_permission = kwargs['project'].is_check_permission
        except:
            is_check_permission = True
        if hase_per is not None and is_check_permission or hase_per=='manage':               #检查权限
            if super_user is False:          #不是超级用户
                ##################################      判断用户是否能进入管理网站
                is_active_proejct = []
                for i in staff_all_per:
                    is_active_proejct.append(i.view_name)
                project_creators = []                                                 #所有项目创建人（项目主管）列表
                for i in Project.objects.all():
                    project_creators.append(i.creator)

                if 'project_index' not in is_active_proejct \
                        and 'create_project' not in is_active_proejct \
                        and staff_user not in project_creators :
                    error = '您属于新注册用户，此账户暂时未被激活，如有问题请联系项目主管或管理员！'
                    return render_to_response('permission_notice.html',locals())
                    ##################################

                if project_id is None:       #判断项目之外的权限
                    if hase_per not in all_views_per_list:
                        error = '您没有该权限，如有问题请联系管理员！'
                        return render_to_response('permission_notice.html',locals())
                if project_id is not None :   #判断与项目相关的权限
                    project_creator = Project.objects.get(id = project_id).creator        #该项目创建人（项目主管）
                    if staff_user!=project_creator:
                        if project_id not in per_project_id_list :
                            error = '您没有进入该项目的权限，如有问题请联系项目主管或管理员！'
                            return render_to_response('permission_notice.html',locals())

                        if project_id in per_project_id_list:
                            if 'project_index' not in views_per_list :
                                error = '您在该项目中的权限尚未激活，如有问题请联系项目主管或管理员！'
                                return render_to_response('permission_notice.html',locals())

                            if hase_per not in views_per_list and 'project_index' in views_per_list:
                                if wiki_id is not None:                                                #6/12
                                    #pass
                                    if not Wiki.objects.filter(owner = project_id,id=wiki_id).exists() or  staff_user !=Wiki.objects.get(owner = project_id,id=wiki_id).creator:
                                        error = '您没有该维基的操作权限！'
                                        return render_to_response('permission_notice.html',locals())
                                else:
                                    error = '您没有该项目中的本操作权限，如有问题请联系项目主管或管理员！'
                                    return render_to_response('permission_notice.html',locals())

                            if hase_per in views_per_list and 'project_index' in views_per_list:
                                for i in staff_all_per:
                                    if i.project_id ==  project_id :
                                        label_control_per_dict.setdefault(i.label_control,i.id)
                                kwargs.setdefault('label_control_per_dict',label_control_per_dict)
                                #print label_control_per_dict
                    else:                                                                               #6/13
                        for i in Permission.objects.filter(project_id = project_id):
                            label_control_per_dict.setdefault(i.label_control,i.id)
                        kwargs.setdefault('label_control_per_dict',label_control_per_dict)
                        #print label_control_per_dict



        kwargs.setdefault('staff_user',staff_user)
        kwargs.setdefault('project_id',project_id)
        kwargs.setdefault('ticket_id',ticket_id)
        kwargs.setdefault('wiki_id',wiki_id)
        kwargs.setdefault('roadmap_name',roadmap_name)
        kwargs.setdefault('user',user)
        kwargs.setdefault('staff_all_per',staff_all_per)
        kwargs.setdefault('staff_permission',staff_permission)
        kwargs.setdefault('groups',groups)
        #kwargs.setdefault('group_id',group_id)
        kwargs.setdefault('user_id',user_id)
        kwargs.setdefault('application_people',application_people)
        kwargs.setdefault('task_team_id',task_team_id)
        return fun(request,*args,**kwargs)
    return wrap

def is_login(f):
    def check_login(request,*arg,**kwarg):
        login_status = request.session.get('IS_LOGIN',False)
        if login_status != True:

            return HttpResponseRedirect('/login')

        return f(request,*arg,**kwarg)

    return check_login


def login_required(function):
    def wrapped_view(request,*args,**kwargs):
        login_status =request.session.get('IS_LOGIN',False)
        if login_status == False:
            return HttpResponseRedirect('/login?next='+request.path)
        return function(request,*args,**kwargs)
    return wrapped_view

def is_superuser(function):
    def wrapped_view(request,*args,**kwargs):
        user_now = request.session.get('USERNAME', False)
        if User.objects.get(username=user_now).is_superuser == False:
            return HttpResponseRedirect('/403/')
        return function(request,*args,**kwargs)
    return wrapped_view

def checkCdkey(function):
    def wrapped_view(request,*args,**kwargs):

        mymac, myname = mac_computer_name_get()

        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        ss = open(path+os.sep+"cdkey.txt").read()
        CDKEYDECODE = base64.decodestring(ss)

        checkMac = CDKEYDECODE.find(mymac)
        checkHostname = CDKEYDECODE.find(myname)

        if checkMac < 0 or checkHostname <0:
            return HttpResponseRedirect('/usecdkey/')

        useTime = CDKEYDECODE[len(CDKEYDECODE)-10:]
        if int(useTime) < int(time.time()):
            return HttpResponseRedirect('/cdkey_past_dut/')

        return function(request,*args,**kwargs)
    return wrapped_view
