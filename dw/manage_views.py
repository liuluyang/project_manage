#coding:utf8
from django.shortcuts import render,render_to_response,HttpResponseRedirect,HttpResponse
from models import *
import re,os
from datetime import datetime
import time
from darkwarrior.settings import MEDIA_ROOT,EMAIL_HOST_USER
from django.contrib.auth.hashers import make_password,check_password
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from decorator import *
import subprocess
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
from itertools import chain
import pytz
import xlrd
from HR_views import project_staff



@checkCdkey
@login_required
@views_permission
def department(request,*args,**kwargs):
    project_archive = kwargs['project']  # 项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME', False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    department_personnels = project_staff(url)

    company_departments = CompanyDepartment.objects.filter(owner_project=url)

    if request.method == 'POST':
        judge= request.POST.get('judge')
        company_name = request.POST.get('company_name')
        department_name = request.POST.get('department_name')
        department_members = request.POST.getlist('department_members')
        company_department_id = request.POST.get('company_department_id')
        if judge == 'add_department':
            if len(company_name)>0 and len(department_name)>0 and len(department_members)>0:
                company_deparment = CompanyDepartment.objects.create(company=company_name,name=department_name,owner_project=url)
                for user in User.objects.filter(id__in=department_members):
                    company_deparment.personnel.add(user)
                return HttpResponseRedirect('/%s/manage/department/'%url)
            else:
                errors = '全部为必填项,不可为空'
        if judge == 'change_department':
            if len(company_name)>0 and len(department_name)>0 and len(department_members)>0 and company_department_id:
                CompanyDepartment.objects.filter(id=company_department_id).update(company=company_name,name=department_name)
                now_department = CompanyDepartment.objects.get(id=company_department_id)
                for personnel in now_department.personnel.all():
                    now_department.personnel.remove(personnel)
                for user in User.objects.filter(id__in=department_members):
                    now_department.personnel.add(user)
                return HttpResponseRedirect('/%s/manage/department/'%url)
            else:
                errors = '全部为必填项,不可为空'
    return render_to_response('manage/department.html',locals())





@checkCdkey
@login_required
@views_permission
def project_type_import(request,*args,**kwargs):
    url = kwargs['project_id']
    project_archive = kwargs['project']  # 项目归档判断
    user_now = request.session.get('USERNAME', False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    user = User.objects.get(username=user_now)

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    try:
        example_xls = Project_type_import.objects.get(example=True)
    except:
        example_xls = None

    if request.method == 'POST':
        import_file = request.FILES.get('import_file')
        if import_file is not None and import_file.name.split('.')[1] == 'xls':
            project_type_import = Project_type_import.objects.create(url=import_file,name=import_file.name,author=user_now)

            file_url = os.path.join(MEDIA_ROOT, str(project_type_import.url)).replace('\\', '/')
            data = xlrd.open_workbook(file_url, 'r')
            table = data.sheets()[0]
            ncols = table.ncols
            nrows = table.nrows

            if ncols == 7 and nrows > 2:
                if '' not in table.row_values(1):
                    project_type_name = table.cell(1,0).value
                    project_type_names= []
                    for project in Project.objects.all():
                        for create_type in Project_type.objects.filter(owner=project.id).exclude(id=project.project_type.id):
                            project_type_names.append(create_type.name)
                    for base_type in Project_type.objects.filter(owner=0):
                        project_type_names.append(base_type.name)
                    if project_type_name in project_type_names:
                        error = '项目类型名称已存在，请进行修改!'
                        return render_to_response('manage/project_type_import.html', locals())

                    now_project_type = Project_type.objects.create(name=project_type_name,owner=url,creator=user_now)

                    type_value = 1
                    for content in table.col_values(1)[1:]:
                        if len(content)>0:
                            type = Type.objects.create(name=content,value=type_value,owner_project=url)
                            type_value +=1
                            now_project_type.task_type.add(type)

                    priority_value = 1
                    for content in table.col_values(2)[1:]:
                        if len(content) > 0:
                            priority = Priority.objects.create(name=content, value=priority_value,owner_project=url)
                            priority_value += 1
                            now_project_type.task_priority.add(priority)

                    status_value = 1
                    for content in table.col_values(3)[1:]:
                        if len(content) > 0:
                            status = Status.objects.create(name=content, value=status_value,owner_project=url)
                            status_value += 1
                            now_project_type.task_status.add(status)


                    for content in table.col_values(4)[1:]:
                        if len(content) > 0:
                            milestone = Milestone.objects.create(name=content,owner_project=url)
                            now_project_type.milestone.add(milestone)


                    for content in table.col_values(5)[1:]:
                        if len(str(content)) > 0:
                            version = Versions.objects.create(name=content,owner_project=url)
                            now_project_type.task_version.add(version)


                    for content in table.col_values(6)[1:]:
                        if len(content) > 0:
                            component = Component.objects.create(name=content,owner_project=url)
                            now_project_type.task_component.add(component)


                    milestones = now_project_type.milestone.all()  #设置初始默认属性
                    prioritys = now_project_type.task_priority.all()
                    components = now_project_type.task_component.all()
                    types = now_project_type.task_type.all()
                    versions = now_project_type.task_version.all()

                    Milestone.objects.filter(owner_project=url,id=milestones[0].id).update(default=True)
                    Priority.objects.filter(owner_project=url,id=prioritys[2].id).update(default=True)
                    Component.objects.filter(owner_project=url,id=components[0].id).update(default=True)
                    Type.objects.filter(owner_project=url,id=types[0].id).update(default=True)
                    Versions.objects.filter(owner_project=url,id=versions[0].id).update(default=True)
                    return HttpResponseRedirect('/%s/manage/project_type/'%url)
                else:
                    error = '文件不符合规定请按规定格式编写文件'
            else:
                error = '文件不符合规定请按规定格式编写文件'
        else:
            error = '必须是xls文件'


    return render_to_response('manage/project_type_import.html',locals())


@checkCdkey
@login_required
@views_permission
def login_title(request,*args,**kwargs): #登陆页面标题
    project_archive = kwargs['project']  # 项目归档判断
    user_now = request.session.get('USERNAME', False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    user = User.objects.get(username=user_now)
    url = kwargs['project_id']

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    if Login_title.objects.filter(owner_project=0).exists():
        login_title = Login_title.objects.filter(owner_project=0)[0]
    else:
        login_title = "动量影视"
    if request.method == 'POST':
        login_title = request.POST.get('login_title')
        if login_title is not None and len(login_title)>0:
            if Login_title.objects.filter(owner_project=0).exists():
                Login_title.objects.filter(owner_project=0).update(update_user=user,title=login_title,time=datetime.now())
                return HttpResponseRedirect('/%s/manage/' % url, locals())
            else:
                Login_title.objects.create(update_user=user,title=login_title)
                return HttpResponseRedirect('/%s/manage/' % url, locals())
    return render_to_response('manage/login_title.html',locals())

@checkCdkey
@login_required
@views_permission
def manage(request,*args,**kwargs):   #管理页面
    project_archive = kwargs['project']  #项目归档判断
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    url = kwargs['project_id']

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    try:
        project_index = Project_index.objects.get(owner=Project.objects.get(id=url)).content
    except:
        pass

    if request.method == 'POST':
        content = request.POST.get('content')

        if Project_index.objects.filter(owner=Project.objects.get(id=url)):
            Project_index.objects.filter(owner=Project.objects.get(id=url)).update(content=content)
            return HttpResponseRedirect('/%s/manage/'%url)

        else:
            Project_index.objects.create(creator=User.objects.get(username=user_now),content=content,owner=Project.objects.get(id=url))
            return HttpResponseRedirect('/%s/manage/'%url)

    return render_to_response('manage/manage.html',locals())

@checkCdkey
@login_required
@views_permission
def user(request,*args,**kwargs): #用户
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    users = User.objects.all()

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    if User.objects.get(username=user_now).is_superuser!=True:
        error = '无权操作！'
        return render_to_response('permission_notice.html',locals())

    paginator = Paginator(users,10)
    page = request.GET.get('page')

    return render_to_response('manage/user.html',locals())


@checkCdkey
@login_required
@views_permission
def permission(request,*args,**kwargs): #授权
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    users = User.objects.all()
    groups = Group.objects.filter(owner_project_id=url)
    permissions = Permission.objects.filter(project_id=url)

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    if request.method == 'POST':
        user_all = request.POST.getlist('users')
        group_all = request.POST.getlist('groups')
        permission_all = request.POST.getlist('permissions')
        errors = []
        for user in user_all:
            if user is not None and len(user)>0:
                for permission in permission_all:
                    if permission is not None and len(permission)>0:
                        User.objects.get(username=user).user_permission.add(Permission.objects.get(id=permission))


        for group in group_all:
            if group is not None and len(group)>0:
                for permission in permission_all:
                    if permission is not None and len(permission)>0:
                        Group.objects.get(name=group).group_permission.add(Permission.objects.get(id=permission))


        return HttpResponseRedirect('/%s/manage/permission/'%(url),locals())


    return render_to_response('manage/permission.html',locals())



@checkCdkey
@login_required
@views_permission
def group(request,*args,**kwargs):  #组
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    groups = Group.objects.filter(owner_project_id=url)
    return render_to_response('manage/group.html',locals())


@checkCdkey
@login_required
@views_permission
def user_content(request,*args,**kwargs): #用户修改
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_id = kwargs['user_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    groups = Group.objects.filter(owner_project_id=url)
    permissions = Permission.objects.filter(project_id=url)
    user = User.objects.get(id=user_id)

    entry_time = user.entry_time
    entry_time_Array = time.strptime(str(entry_time).split('+')[0].split('.')[0], '%Y-%m-%d')
    entry_time_date = time.strftime("%Y/%m/%d %H:%M", entry_time_Array)
    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    user_group = user.group.filter(owner_project_id=url)
    user_permissions = user.user_permission.filter(project_id=url)

    if request.method == 'POST':
        user_permission_all = request.POST.getlist('user_permission')
        user_group_all = request.POST.getlist('user_group')
        user_entry_time = request.POST.get('user_entry_time')

        if user_entry_time is not None and len(user_entry_time)>0:
            user_entry_time = datetime.strptime(user_entry_time, '%Y/%m/%d %H:%M')
            User.objects.filter(id=user_id).update(entry_time=user_entry_time)
        if user_group is not None and len(user_group)>0:
            for group in user_group:
                user.group.remove(group)

        for group_id in user_group_all:
            if group_id is not None and len(group_id)>0:
                user.group.add(Group.objects.get(id=group_id))

        if user_permissions is not None and len(user_permissions)>0:
            for permission in user_permissions:
                user.user_permission.remove(permission)

        for permission_id in user_permission_all:
            if permission_id is not None and len(permission_id)>0:
                user.user_permission.add(Permission.objects.get(id=permission_id))
        return HttpResponseRedirect('/%s/manage/project_members/'%url,locals())
    return render_to_response('manage/user_content.html',locals())


@checkCdkey
@login_required
@views_permission
def add_group(request,*args,**kwargs):  #添加组
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    users = User.objects.all()
    permissions = Permission.objects.filter(project_id=url)
    errors = []
    if request.method == 'POST':
        groupname = request.POST.get('groupname')
        permission_all = request.POST.getlist('permissions')
        if groupname is not None and len(groupname)>0:
            group = Group(name=groupname,owner_project_id=url)
            group.save()
            for permission in permission_all:
                if permission is not None and len(permission)>0:
                    Group.objects.get(name=groupname).group_permission.add(Permission.objects.get(id=permission))

            return HttpResponseRedirect('/%s/manage/group/'%(url),locals())
        else:
            errors.append('请输入组名称')
    return render_to_response('manage/add_group.html',locals())


@checkCdkey
@login_required
@views_permission
def add_group_user(request,*args,**kwargs): #添加组成员
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    group_id = kwargs['group_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    group = Group.objects.get(id=group_id)
    users = User.objects.all()
    group_user = Group.objects.get(id=group_id).user_set.all()
    #print group_user
    if request.method == 'POST':
        user_all = request.POST.getlist('users')
        if user_all is not None and len(user_all)>0:
            for user in group_user:
                if user is not None:
                    user.group.remove(group)

            for user_id in user_all:
                if user_id is not None and len(user_id)>0:
                    User.objects.get(id=user_id).group.add(group)
            return HttpResponseRedirect('/%s/manage/group'%url,locals())


    return render_to_response('manage/add_group_user.html',locals())


@checkCdkey
@login_required
@views_permission
def group_content(request,*args,**kwargs): #修改组
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    group_id = kwargs['group_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    group = Group.objects.get(id=group_id)

    permissions = Permission.objects.filter(project_id=url)

    group_permissions = group.group_permission.filter(project_id=url)

    if request.method == 'POST':
        group_permission_all = request.POST.getlist('group_permission')

        if group_permissions is not None and len(group_permissions)>0:
            for permission in group_permissions:
                group.group_permission.remove(permission)
        if group is not None:
            for group_permission_id in group_permission_all:
                if group_permission_id is not None and len(group_permission_id)>0:
                    group.group_permission.add(Permission.objects.get(id=group_permission_id))

        delete_group = request.POST.get('delete_group')
        if delete_group is not None and len(delete_group)>0:
            Group.objects.get(id=delete_group).delete()
        return HttpResponseRedirect('/%s/manage/group/'%(url),locals())

    return render_to_response('manage/group_content.html',locals())


@checkCdkey
@login_required
@views_permission
def task_grade(request,*args,**kwargs): #任务等级
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    task_grades = Taskgrade.objects.filter(owner_project=url)
    taskgrade_correlation = []
    for taskgrade in task_grades:
        if Taskorder.objects.filter(owner_project=project_archive,grade=taskgrade.name):
            taskgrade_correlation.append(taskgrade.name)
    if request.method == 'POST':
        judge = request.POST.get('judge')
        if judge == 'task_grade':
            task_grade_id = request.POST.get('task_grade_id')
            task_grade_name = request.POST.get('task_grade_name')
            task_grade_description = request.POST.get('task_grade_description')
            delete = request.POST.get('delete')
            save = request.POST.get('save')
            if save == 'save':
                if len(task_grade_name)>0 and len(task_grade_description)>0:
                    Taskgrade.objects.filter(id=task_grade_id).update(name=task_grade_name,description=task_grade_description)
                else:
                    grade_error = '任务等级 名称 说明不可为空'
                return HttpResponseRedirect('/%s/manage/task_grade/' % url)
            if delete == 'delete':
                Taskgrade.objects.get(id=task_grade_id).delete()
                return HttpResponseRedirect('/%s/manage/task_grade/' % url)
        if judge == 'add_task_grade':
            name = request.POST.get('name')
            description = request.POST.get('description')
            if len(name)>0 and len(description)>0:
                Taskgrade.objects.create(name=name,description=description,owner_project=url)
            else:
                grade_error = '任务等级 名称 说明不可为空'
            return HttpResponseRedirect('/%s/manage/task_grade/' % url)
    return render_to_response('manage/task_grade.html',locals())


@checkCdkey
@login_required
@views_permission
def delect_project(request,*args,**kwargs):    #删除项目
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    if User.objects.get(username=user_now).is_superuser!=True:    #权限判断 
        error = '无权操作！'
        return render_to_response('permission_notice.html',locals())

    delect_project_id = kwargs['delect_project_id']
    Project.objects.get(id=delect_project_id).delete()

    Permission.objects.filter(project_id=delect_project_id).delete()
    project_types = Project_type.objects.filter(owner=delect_project_id)

    for project_type in project_types:
        project_type.milestone.all().delete()
        project_type.task_priority.all().delete()
        project_type.task_status.all().delete()
        project_type.task_component.all().delete()
        project_type.task_type.all().delete()
        project_type.task_version.all().delete()
    project_types.delete()

    Template.objects.filter(owner_project=delect_project_id).delete()
    Taskgrade.objects.filter(owner_project=delect_project_id).delete()
    Gantt_type.objects.filter(owner_project=delect_project_id).delete()
    Task_team.objects.filter(owner_project=delect_project_id).delete()
    Taskorder.objects.filter(owner_project=delect_project_id).delete()
    Scheduler_type.objects.filter(owner_project=delect_project_id).delete()
    Attachment_file.objects.filter(owner_project=delect_project_id).delete()
    Attachment_video.objects.filter(owner_project=delect_project_id).delete()
    Attachment_image.objects.filter(owner_project=delect_project_id).delete()
    Comment.objects.filter(owner_project=delect_project_id).delete()
    Wiki.objects.filter(owner=delect_project_id).delete()
    Wiki_attachment_file.objects.filter(owner_project=delect_project_id).delete()
    Wiki_attachment_video.objects.filter(owner_project=delect_project_id).delete()
    Wiki_attachment_image.objects.filter(owner_project=delect_project_id).delete()
    Project_index.objects.filter(owner=delect_project_id).delete()
    Repository.objects.filter(project_id=delect_project_id).delete()
    RepositoryUser.objects.filter(project_id=delect_project_id).delete()
    Message.objects.filter(owner_project=delect_project_id).delete()


    return HttpResponseRedirect('/')

@checkCdkey
@login_required
@views_permission
def project_change(request,*args,**kwargs): #修改项目
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    if user_now !=Project.objects.get(id=url).creator.username and User.objects.get(username=user_now).is_superuser!=True:    #权限判断 
        error = '无权操作！'
        return render_to_response('permission_notice.html',locals())

    errors = []
    project = Project.objects.get(id=url)
    project_types = Project_type.objects.filter(owner=url)
    now_project_type = project.project_type
    start_date_Array = time.strptime(str(project.due_time.astimezone(pytz.timezone('Asia/Shanghai'))).split('+')[0].split('.')[0], '%Y-%m-%d %H:%M:%S')
    now_date = time.strftime("%Y/%m/%d %H:%M", start_date_Array)
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        project_type = request.POST.get('project_type')
        project_description = request.POST.get('project_description')
        project_due_time = request.POST.get('project_due_time')
        #project_complete_time = request.POST.get('project_complete_time')
        project_status = request.POST.get('project_status')
        is_archive=request.POST.get('is_archive')
        is_check_permission = request.POST.get('is_check_permission')
        #project_id = request.POST.get('project_id')
        project_logo=request.FILES.get('project_logo')

        if project_name is not None and len(project_name)>0:
            if project_due_time != project.due_time:
                project_due_time = datetime.strptime(project_due_time,'%Y/%m/%d %H:%M')
                Project.objects.filter(id=url).update(due_time=project_due_time)

                #if project_complete_time is not None and len(project_complete_time)>0:
                #Project.objects.filter(id=url).update(complete_time=project_complete_time)
            if project_logo is not None and len(project_logo)>0:
                re_img=re.search(r'[\w+]\.(?:png|jpg|jpeg|ico|gif|bmp|pic|tiff)',str(project_logo),re.I)
                if not re_img:
                    errors.append('图片格式不支持')
                    return render_to_response('manage/project_change.html',locals())
                else:
                    project=Project.objects.get(id=url)
                    old_logo = project.project_logo
                    project.project_logo=project_logo
                    project.save()
                    try:
                        old_logo = os.path.join(MEDIA_ROOT, str(old_logo)).replace('\\', '/')
                        os.remove(old_logo)  # 删除之前的logo
                    except:
                        pass
            Project.objects.filter(id=url).update(project_name=project_name,
                                                  project_description=project_description,project_status=project_status,is_archive=int(is_archive),
                                                  is_check_permission=int(is_check_permission))

            return HttpResponseRedirect('/%s/manage/project_change/'%url)

            #elif project_id is not None and len(project_id)>0:
            #Project.objects.get(id=project_id).delete()
            #return HttpResponseRedirect('/')
    return render_to_response('manage/project_change.html',locals())


@checkCdkey
@login_required
@views_permission
def application_record(request,*args,**kwargs):         #申请历史记录     liuluyang20160726
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    application_records = Message.objects.filter(classify='application_record',owner_project=project).order_by('-time')

    return render_to_response('manage/application_record.html',locals())

@checkCdkey
@login_required
@views_permission
def task_team(request,*args,**kwargs):  #团队                     #liuluyang 2016/07/29
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    task_teams = Task_team.objects.filter(owner_project = url)

    return render_to_response('manage/task_team.html',locals())

@checkCdkey
@login_required
@views_permission
def add_task_team(request,*args,**kwargs):  #新建团队              #liuluyang 2016/07/29
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    users = User.objects.all()
    if request.method=="POST":
        team_name = request.POST.get('team_name')
        team_introduction = request.POST.get('team_introduction')
        team_members= request.POST.getlist('team_members')
        team_logo = request.FILES.get('team_logo')
        if team_name.strip()=='' or Task_team.objects.filter(owner_project=url,name=team_name).exists():
            error = '团队名称有误或已存在，请重新输入！'
            return render_to_response('manage/add_task_team.html', locals())
        elif team_logo:
            file_last = team_logo.name.split('.')[-1]
            image_format = ['bmp', 'pcx', 'gif', 'jpeg', 'jpg', 'tga', 'exif', 'fpx', 'svg', 'psd', 'cdr', 'pcd',
                            'dxf', 'ufo', 'eps', 'ai', 'png', 'hdri', 'raw', 'ico']
            if file_last not in image_format:
                error = '文件格式不对！'
                return render_to_response('manage/add_task_team.html', locals())
            else:
                new_team = Task_team.objects.create(name=team_name, introduction=team_introduction,
                                                    owner_project=url)
                if len(team_members) > 0:
                    for user_id in team_members:
                        new_team.member.add(User.objects.get(id=user_id))
                new_team.team_logo = team_logo
                new_team.save()
                return HttpResponseRedirect('/' + url + '/manage/task_team/')

        else:
            new_team = Task_team.objects.create(name=team_name, introduction=team_introduction,
                                                owner_project=url)
            if len(team_members) > 0:
                for user_id in team_members:
                    new_team.member.add(User.objects.get(id=user_id))
            return HttpResponseRedirect('/' + url + '/manage/task_team/')



    return render_to_response('manage/add_task_team.html',locals())

@checkCdkey
@login_required
@views_permission
def task_team_change(request,*args,**kwargs):  #编辑团队                #liuluyang 2016/07/29
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    task_team_id = kwargs['task_team_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    try:
        users = User.objects.all()
        unselected_users = list(users)
        team = Task_team.objects.get(id=task_team_id,owner_project=url)
        for user in team.member.all():
            if user in unselected_users:
                unselected_users.remove(user)
    except:
        error = '该团队不存在！'
        return render_to_response('permission_notice.html',locals())


    if request.method=="POST":
        team_name = request.POST.get('team_name')
        team_introduction = request.POST.get('team_introduction')
        team_members= request.POST.getlist('team_members')
        team_logo = request.FILES.get('team_logo')

        submit = request.POST.get('submit')
        delete_team = request.POST.get('delete_team')
        #print team_name,team_introduction,team_members

        if submit is not None:
            if team_name.strip()=='':
                error = '团队名称不能为空！'
                return render_to_response('manage/task_team_change.html',locals())
            elif Task_team.objects.filter(owner_project=url,name=team_name).exists() and team_name!=team.name:
                error = '团队名称已存在，请重新输入！'
                return render_to_response('manage/task_team_change.html',locals())
            else:
                for user in team.member.all():
                    team.member.remove(user)
                for user_id in team_members:
                    team.member.add(User.objects.get(id=user_id))
                team.name= team_name
                team.introduction = team_introduction
                team.save()
                if team_logo:
                    file_last = team_logo.name.split('.')[-1]
                    image_format = ['bmp', 'pcx', 'gif', 'jpeg', 'jpg', 'tga', 'exif', 'fpx', 'svg', 'psd', 'cdr', 'pcd',
                                    'dxf', 'ufo', 'eps', 'ai', 'png', 'hdri', 'raw', 'ico']
                    if file_last not in image_format:
                        error = '文件格式不对！'
                        return render_to_response('manage/task_team_change.html', locals())
                    else:
                        try:
                            old_team_logo = os.path.join(MEDIA_ROOT, str(team.team_logo)).replace('\\', '/')
                            os.remove(old_team_logo)  # 删除团队之前的logo
                        except:
                            pass
                        team.team_logo=team_logo
                        team.save()
                return HttpResponseRedirect('/'+url+'/manage/task_team/')
        if delete_team is not None:
            try:
                old_team_logo = os.path.join(MEDIA_ROOT, str(team.team_logo)).replace('\\', '/')
                os.remove(old_team_logo)  # 删除团队之前的logo
            except:
                pass
            team.delete()
            return HttpResponseRedirect('/'+url+'/manage/task_team/')


    return render_to_response('manage/task_team_change.html',locals())


@checkCdkey
@login_required
@views_permission
def manage_logo(request,*args,**kwargs):
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    user=User.objects.get(username=user_now)
    superuser=user.is_superuser
    logos=Logo.objects.order_by('-id')
    errors=[]
    if superuser!=True:    #权限判断
        error = '无权操作！'
        return render_to_response('permission_notice.html',locals())
    if request.method == "POST":
        logo=request.FILES.get('logo')
        if logo is not None and len(logo)>0:
            re_img=re.search(r'[\w+]\.(?:png|jpg|jpeg|ico|gif|bmp|pic|tiff)',str(logo),re.I)
            if not re_img:
                errors.append('图片格式不支持')
                return render_to_response('manage/manage_logo.html',locals())
            else:
                try:
                    old_logo_obj = Logo.objects.order_by('-id')[0]
                    old_logo = old_logo_obj.logo
                    old_logo_obj.logo = logo
                    old_logo_obj.creator = user
                    old_logo_obj.save()
                except:
                    Logo.objects.create(logo=logo,creator=user)
                try:
                    old_logo = os.path.join(MEDIA_ROOT, str(old_logo)).replace('\\', '/')
                    os.remove(old_logo)  # 删除之前的logo
                except:
                    pass
    return  render_to_response('manage/manage_logo.html',locals())

@checkCdkey
@login_required
@views_permission
def project_member(request,*args,**kwargs):       #项目成员
    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    #project_home_permission = Permission.objects.get(project_id = project_id,view_name = 'project_index')  #项目首页权限


    ##########################   检索跟本项目相关的所有人员
    permission_project = Permission.objects.filter(project_id = project_id)
    project_staff_list = []
    for permission in permission_project:
        staff_list = permission.user_set.all()
        project_staff_list = list(set(list(staff_list)+project_staff_list))

    for permission in permission_project:
        for group in permission.group_set.all():
            project_staff_list = list(set(list(group.user_set.all())+project_staff_list))

    project_groups = Group.objects.filter(owner_project_id = project_id)
    for group in project_groups:
        project_staff_list = list(set(list(group.user_set.all())+project_staff_list))
    project_staff_list.append(Project.objects.get(id=project_id).creator)
    project_staff_list = list(set(project_staff_list))
    all_num = len(project_staff_list)
    #############################


    users = []
    for user in project_staff_list:
        id = user.id
        username = user.username
        last_login = user.last_login
        is_superuser = user.is_superuser
        is_staff = user.is_staff
        is_active = user.is_active
        name = user.name
        email = user.email
        date_joined = user.date_joined
        gender = user.gender
        position = user.position
        address = user.address
        phone = user.phone

        staff_permission = user.user_permission.all()                   #用户个人所有权限
        ############
        project_staff_group_list = []                           #用户跟该项目相关的所属小组
        staff_group = user.group.all()                             #用户所属的所有小组
        group_permission_all = []
        for group in staff_group:
            if len(group.group_permission.filter(project_id = project_id))>0:
                project_staff_group_list.append(group)

                for permission in group.group_permission.all():
                    group_permission_all.append(permission)
        #print project_staff_group_list,'用户跟该项目相关的所属小组'
        staff_all_per = list(set(list(staff_permission)+group_permission_all))     #用户跟该项目相关的所有权限
        ##############

        staff_permission_list=[]                                 #用户跟该项目相关的个人所有权限
        for s in staff_permission:
            if s.project_id == project_id:
                staff_permission_list.append(s)

        users.append({'id':id,'username':username,'email':email,'position':position,'last_login':last_login,'date_joined':date_joined,
                      'phone':phone,'is_active':is_active,'is_superuser':is_superuser,'is_staff':is_staff,'name':name,'gender':gender,
                      'user_permission':staff_permission_list,'group':project_staff_group_list,'address':address })


    return render_to_response('manage/project_member.html',locals())


@checkCdkey
@login_required
@views_permission
def change_company_name(request,*args,**kwargs):       #lly 2016/09/08 修改公司名称
    project_archive = kwargs['project']  #项目归档判断
    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    if User.objects.get(username=user_now).is_superuser!=True:
        error = '无权操作！'
        return render_to_response('permission_notice.html',locals())

    try:
        name = Company_name.objects.filter(owner_project=0)[0]
    except:
        name = False

    if request.method == "POST":
        company_name = request.POST.get('company_name')
        if len(company_name.strip())>0:
            if Company_name.objects.filter(owner_project=0).exists():
                Company_name.objects.filter(owner_project=0).update(update_user=staff_user,name=company_name,time=datetime.now())
            else:
                Company_name.objects.create(update_user=staff_user,name=company_name)
            return HttpResponseRedirect('/'+url+'/manage/change_company_name/')
        else:
            error = '名称不能为空！'
            return render_to_response('manage/company_name.html',locals())

    return render_to_response('manage/company_name.html',locals())


@checkCdkey
@login_required
@views_permission
def project_type(request,*args,**kwargs): #项目类型
    project_archive = kwargs['project']  #项目归档判断
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        base = kwargs['base']
    except:
        base = False
    if base == '0':
        if User.objects.get(username=user_now).is_superuser != True:
            error = '无权操作！'
            return render_to_response('permission_notice.html', locals())
        project_types = chain(Project_type.objects.filter(owner=0))  # 0为默认类型
    else:
        project_types = chain(Project_type.objects.filter(owner=url))    #0为默认类型
    return render_to_response('manage/project_type.html',locals())

@checkCdkey
@login_required
@views_permission
def add_project_type(request,*args,**kwargs): #添加项目类型
    project_archive = kwargs['project']  #项目归档判断
    project_id = kwargs['project_id']
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    task_types = chain(Type.objects.filter(owner_project=0)) #0为默认
    task_prioritys = chain(Priority.objects.filter(owner_project=0))

    versions = chain(Versions.objects.filter(owner_project=0))
    task_components = chain(Component.objects.filter(owner_project=0))
    task_statuss = chain(Status.objects.filter(owner_project=0))
    milestones = chain(Milestone.objects.filter(owner_project=0))


    try:
        base = kwargs['base']
        if base == '0':
            project_id = 0
            if User.objects.get(username=user_now).is_superuser != True:
                error = '无权操作！'
                return render_to_response('permission_notice.html', locals())
    except:
        base = False

    errors = []
    if request.method == 'POST':
        project_type_name = request.POST.get('project_type_name')
        task_type = request.POST.getlist('task_type')
        task_priority = request.POST.getlist('task_priority')
        task_component = request.POST.getlist('task_component')
        version_all = request.POST.getlist('version')
        task_status = request.POST.getlist('task_status')
        milestone_all = request.POST.getlist('milestone')

        project_type_names = []
        for project in Project.objects.all():
            for create_type in Project_type.objects.filter(owner=project.id).exclude(id=project.project_type.id):
                project_type_names.append(create_type.name)
        for base_type in Project_type.objects.filter(owner=0):
            project_type_names.append(base_type.name)
        if len(project_type_name.strip())>0 and project_type_name in project_type_names:
            errors.append('名称不能重名')
            return render_to_response('manage/add_project_type.html', locals())

        if project_type_name is not None and len(project_type_name.strip())>0:
            now_project_type = Project_type.objects.create(name=project_type_name,owner=project_id,creator=user_now)

            value = 0
            for type_id in task_type:
                if type_id is not None and len(type_id)>0:
                    value += 1
                    type = Type.objects.get(id=type_id)
                    default = False
                    if value == 1:
                        default = True
                    new_type = Type.objects.create(name=type.name,value=value,owner_project=project_id,default =default)
                    now_project_type.task_type.add(new_type)


            value = 0
            for priority_id in task_priority:
                if priority_id is not None and len(priority_id)>0:
                    value += 1
                    priority = Priority.objects.get(id=priority_id)
                    default = False
                    if value == 1:
                        default = True
                    new_priority = Priority.objects.create(name=priority.name,value=value,owner_project=project_id,default =default)
                    now_project_type.task_priority.add(new_priority)


            value = 0
            for component_id in task_component:
                if component_id is not None and len(component_id)>0:
                    value += 1
                    component = Component.objects.get(id=component_id)
                    default = False
                    if value == 1:
                        default = True
                    new_component = Component.objects.create(name=component.name,description=component.description,owner_project = project_id,default =default)
                    now_project_type.task_component.add(new_component)

            value = 0
            for version_id in version_all:
                if version_id is not None and len(version_id)>0:
                    value += 1
                    version = Versions.objects.get(id=version_id)
                    default = False
                    if value == 1:
                        default = True
                    new_version = Versions.objects.create(name=version.name,description=version.description,owner_project=project_id,default =default)
                    now_project_type.task_version.add(new_version)


            value = 0
            for status_id in task_status:
                if status_id is not None and len(status_id)>0:
                    value += 1
                    status = Status.objects.get(id=status_id)
                    new_status = Status.objects.create(name=status.name,value=value,owner_project=project_id)
                    now_project_type.task_status.add(new_status)


            value = 0
            for milestone_id in milestone_all:
                if milestone_id is not None and len(milestone_id)>0:
                    value += 1
                    milestone = Milestone.objects.get(id=milestone_id)
                    default = False
                    if value == 1:
                        default = True
                    new_milestone = Milestone.objects.create(name=milestone.name,description=milestone.description,owner_project=project_id,default =default)
                    now_project_type.milestone.add(new_milestone)

            if base == '0':
                return HttpResponseRedirect('/%s/manage/project_type/0' % url, locals())
            else:
                return HttpResponseRedirect('/%s/manage/project_type/'%url,locals())
        else:
            errors.append('请输入项目类型名称')



    return render_to_response('manage/add_project_type.html',locals())

@checkCdkey
@login_required
@views_permission
def project_type_edit(request,*args,**kwargs): #项目类型修改       lly 2016/10/25
    project_archive = kwargs['project']  #项目归档判断
    project_id = kwargs['project_id']
    url = kwargs['project_id']
    project_type_id = kwargs['project_type_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait


    #项目类型
    project_filter = Project_type.objects.filter(id=project_type_id)
    if project_filter.exists():
        if project_filter[0].owner == project_id:
            if int(project_archive.project_type.id) == int(project_type_id):
                present_project_type = True
            else:
                create_project_type = True
        elif project_filter[0].owner == '0':
            project_id = 0
            base_project_type = True
            if User.objects.get(username=user_now).is_superuser != True:
                error = '无权操作！'
                return render_to_response('permission_notice.html', locals())
        else:
            error = '非法操作！'
            return render_to_response('permission_notice.html', locals())
    else:
        error = '项目类型不存在！'
        return render_to_response('permission_notice.html', locals())

    project_type = Project_type.objects.get(id=project_type_id)
    task_types = project_type.task_type.all().order_by('value')
    task_prioritys = project_type.task_priority.all().order_by('value')
    task_versions = project_type.task_version.all()
    task_components = project_type.task_component.all()
    task_statuss = project_type.task_status.all().order_by('value')
    task_milestones = project_type.milestone.all()
    milestone_due_list = []
    for milestone in task_milestones:
        time_zone = milestone.due.astimezone(pytz.timezone('Asia/Shanghai'))
        list = str(time_zone).split('+')[0].replace('-','/').split(':')
        due_time = list[0]+':'+list[1]
        milestone_due_list.append({'due':due_time,'id':milestone.id})



    if request.method == 'POST':
        judge = request.POST.get('judge')
        default = request.POST.get('default')
        save = request.POST.get('save')
        delete = request.POST.get('delete')
        create = request.POST.get('create')

        id = request.POST.get('id')
        name = request.POST.get('name')
        if name:
            name = name.strip()
        value = request.POST.get('value')
        description = request.POST.get('description')
        due_time = request.POST.get('time')
        milestone_status = request.POST.get('milestone_status')

        if save or create:
            if len(name)<=0:
                return render_to_response('manage/project_type_edit.html', locals())

        if judge=='projectType':
            if save:
                if int(project_archive.project_type.id) != int(project_type_id):
                    project_type_names = []
                    for project in Project.objects.all():
                        for create_type in Project_type.objects.filter(owner=project.id).exclude(id=project.project_type.id):
                            project_type_names.append(create_type.name)
                    for base_type in Project_type.objects.filter(owner=0).exclude(id=project_type_id):
                        project_type_names.append(base_type.name)
                    if name!=Project_type.objects.get(id=project_type_id).name and name in project_type_names:
                        name_error = '名称不能重名!'
                    else:
                        project_type.name=name
                        project_type.save()
                        return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                else:
                    project_type.name = name
                    project_type.save()
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
            if delete:
                if int(project_archive.project_type.id) != int(project_type_id):
                    task_types.delete()
                    task_prioritys.delete()
                    task_versions.delete()
                    task_components.delete()
                    task_statuss.delete()
                    task_milestones.delete()
                    project_type.delete()
                    if project_id == 0:
                        return HttpResponseRedirect('/' + url + '/manage/project_type/0')
                    else:
                        return HttpResponseRedirect('/' + url + '/manage/project_type/')
                else:
                    pass


        if judge=='type':
            if save:
                if project_type.task_type.filter(name=name).exists() and Type.objects.get(id=id).name!=name:
                    type_error = '修改的类型名称不能重名！'
                else:
                    others = project_type.task_type.filter(value=value).exclude(id=id)
                    if others.exists():
                        for type in project_type.task_type.all().exclude(id=id):
                            if type.value >= int(value):
                                type.value = type.value+1
                                type.save()
                    Type.objects.filter(id=id).update(name=name, value=value)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
            if delete:
                try:
                    type = Type.objects.get(id=id)
                    if not type.taskorder_set.all():
                        try:
                            if type.default == True:
                                new = project_type.task_type.all().order_by('id').exclude(id=id)[0]
                                new.default = True
                                new.save()
                        except:
                            pass
                        type.delete()
                        return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                except:
                    pass
            if create:
                if not project_type.task_type.filter(name=name).exists():
                    try:
                        next_value = project_type.task_type.all().order_by('-value')[0].value+1
                    except:
                        next_value = 1
                    if project_type.task_type.all().exists():
                        new = Type.objects.create(name=name, value=next_value, owner_project=project_id)
                        project_type.task_type.add(new)
                    else:
                        new = Type.objects.create(name=name, value=next_value, owner_project=project_id, default=True)
                        project_type.task_type.add(new)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                else:
                    type_error = '新建的类型名称不能重名！'
            if default:
                task_types.update(default=False)
                Type.objects.filter(id=id).update(default=True)
                return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)

        if judge=='priority':
            if save:
                if project_type.task_priority.filter(name=name).exists() and Priority.objects.get(id=id).name!=name:
                    priority_error = '修改的优先级名称不能重名！'
                else:
                    others = project_type.task_priority.filter(value=value).exclude(id=id)
                    if others.exists():
                        for priority in project_type.task_priority.all().exclude(id=id):
                            if priority.value >= int(value):
                                priority.value = priority.value + 1
                                priority.save()
                    Priority.objects.filter(id=id).update(name=name, value=value)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
            if delete:
                try:
                    priority = Priority.objects.get(id=id)
                    if not priority.taskorder_set.all():
                        try:
                            if priority.default == True:
                                new = project_type.task_priority.all().order_by('id').exclude(id=id)[0]
                                new.default = True
                                new.save()
                        except:
                            pass
                        priority.delete()
                        return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                except:
                    pass
            if create:
                if not project_type.task_priority.filter(name=name).exists():
                    try:
                        next_value = project_type.task_priority.all().order_by('-value')[0].value+1
                    except:
                        next_value = 1
                    if project_type.task_priority.all().exists():
                        new = Priority.objects.create(name=name, value=next_value, owner_project=project_id)
                        project_type.task_priority.add(new)
                    else:
                        new = Priority.objects.create(name=name, value=next_value, owner_project=project_id, default=True)
                        project_type.task_priority.add(new)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                else:
                    priority_error = '新建的优先级名称不能重名！'
            if default:
                task_prioritys.update(default=False)
                Priority.objects.filter(id=id).update(default=True)
                return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)

        if judge=='status':
            if save:
                if project_type.task_status.filter(name=name).exists() and Status.objects.get(id=id).name!=name:
                    status_error = '修改的状态名称不能重名！'
                else:
                    others = project_type.task_status.filter(value=value).exclude(id=id)
                    if others.exists():
                        for status in project_type.task_status.all().exclude(id=id):
                            if status.value >= int(value):
                                status.value = status.value + 1
                                status.save()
                    Status.objects.filter(id=id).update(name=name, value=value)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
            if delete:
                try:
                    status = Status.objects.get(id=id)
                    if not status.taskorder_set.all():
                        status.delete()
                        return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                except:
                    pass
            if create:
                if not project_type.task_status.filter(name=name).exists():
                    try:
                        next_value = project_type.task_status.all().order_by('-value')[0].value+1
                    except:
                        next_value = 1
                    new = Status.objects.create(name=name, value=next_value, owner_project=project_id)
                    project_type.task_status.add(new)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                else:
                    status_error = '新建的状态名称不能重名！'

        if judge=='component':
            if save:
                if project_type.task_component.filter(name=name).exists() and Component.objects.get(id=id).name!=name:
                    component_error = '修改的组件名称不能重名！'
                else:
                    Component.objects.filter(id=id).update(name=name, description=description)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
            if delete:
                try:
                    component = Component.objects.get(id=id)
                    if not component.taskorder_set.all():
                        try:
                            if component.default == True:
                                new = project_type.task_component.all().order_by('id').exclude(id=id)[0]
                                new.default = True
                                new.save()
                        except:
                            pass
                        component.delete()
                        return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                except:
                    pass
            if create:
                if not project_type.task_component.filter(name=name).exists():
                    if project_type.task_component.all().exists():
                        new = Component.objects.create(name=name, description=description, owner_project=project_id)
                        project_type.task_component.add(new)
                    else:
                        new = Component.objects.create(name=name, description=description, owner_project=project_id,default=True)
                        project_type.task_component.add(new)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                else:
                    component_error = '新建的组件名称不能重名！'
            if default:
                task_components.update(default=False)
                Component.objects.filter(id=id).update(default=True)
                return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)

        if judge=='version':
            if save:
                if project_type.task_version.filter(name=name).exists() and Versions.objects.get(id=id).name!=name:
                    version_error = '修改的版本名称不能重名！'
                else:
                    Versions.objects.filter(id=id).update(name=name, description=description)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
            if delete:
                try:
                    version = Versions.objects.get(id=id)
                    if not version.taskorder_set.all():
                        try:
                            if version.default == True:
                                new = project_type.task_version.all().order_by('id').exclude(id=id)[0]
                                new.default = True
                                new.save()
                        except:
                            pass
                        version.delete()
                        return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                except:
                    pass
            if create:
                if not project_type.task_version.filter(name=name).exists():
                    if project_type.task_version.all().exists():
                        new = Versions.objects.create(name=name, description=description, owner_project=project_id,)
                        project_type.task_version.add(new)
                    else:
                        new = Versions.objects.create(name=name, description=description, owner_project=project_id,default=True)
                        project_type.task_version.add(new)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                else:
                    version_error = '新建的版本名称不能重名！'
            if default:
                task_versions.update(default=False)
                Versions.objects.filter(id=id).update(default=True)
                return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)

        if judge=='milestone':
            if save:
                if project_type.milestone.filter(name=name).exists() and Milestone.objects.get(id=id).name!=name:
                    milestone_error = '修改的里程碑名称不能重名！'
                else:
                    try:
                        time = datetime.strptime(due_time, '%Y/%m/%d %H:%M')
                        Milestone.objects.filter(id=id).update(name=name, description=description,due=time,milestone_status=milestone_status)
                        return HttpResponseRedirect('/' + url + '/manage/project_type_edit/'+project_type_id)
                    except:
                        Milestone.objects.filter(id=id).update(name=name, description=description,milestone_status=milestone_status)
                        return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
            if delete:
                try:
                    milestone= Milestone.objects.get(id=id)
                    if not milestone.taskorder_set.all():
                        try:
                            if milestone.default == True:
                                new = project_type.milestone.all().order_by('id').exclude(id=id)[0]
                                new.default = True
                                new.save()
                        except:
                            pass
                        milestone.delete()
                        return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                except:
                    pass
            if create:
                try:
                    time = datetime.strptime(due_time, '%Y/%m/%d %H:%M')
                except:
                    time = datetime.now()
                if not project_type.milestone.filter(name=name).exists():
                    if project_type.milestone.all().exists():
                        new = Milestone.objects.create(name=name, description=description, due=time,owner_project=project_id,)
                        new.due = time
                        new.save()
                        project_type.milestone.add(new)
                    else:
                        new = Milestone.objects.create(name=name, description=description, due=time, owner_project=project_id,default=True)
                        new.due = time
                        new.save()
                        project_type.milestone.add(new)
                    return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)
                else:
                    milestone_error = '新建的里程碑名称不能重名！'
            if default:
                task_milestones.update(default=False)
                Milestone.objects.filter(id=id).update(default=True)
                return HttpResponseRedirect('/' + url + '/manage/project_type_edit/' + project_type_id)



    return render_to_response('manage/project_type_edit.html',locals())

@checkCdkey
@login_required
@views_permission
def project_interface_edit(request,*args,**kwargs): #项目界面修改       lly 2016/11/02
    project_archive = kwargs['project']  #项目归档判断
    project_id = kwargs['project_id']
    url = kwargs['project_id']
    project_type_id = kwargs['project_type_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    project_filter = Project_type.objects.filter(id=project_type_id)
    project_type = project_filter
    if project_filter.exists():
        if project_filter[0].owner == project_id:
            if int(project_archive.project_type.id) == int(project_type_id):
                present_project_type = True
            else:
                create_project_type = True
        elif project_filter[0].owner == '0':
            project_id = 0
            base_project_type = True
            if User.objects.get(username=user_now).is_superuser != True:
                error = '无权操作！'
                return render_to_response('permission_notice.html', locals())
        else:
            error = '非法操作！'
            return render_to_response('permission_notice.html', locals())
    else:
        error = '项目类型不存在！'
        return render_to_response('permission_notice.html', locals())

    project_name = project_type[0].name
    task_types = project_type[0].task_type.all().order_by('value')
    task_prioritys = project_type[0].task_priority.all().order_by('value')

    gantt_css = project_type[0].gantt_skin
    gantt_task_height = project_type[0].gantt_task_height
    gantt_row_height =  project_type[0].gantt_row_height
    scheduler_css = project_type[0].scheduler_skin


    if request.method == 'POST':
        change = request.POST.get('change')
        type_id = request.POST.get('type_id')
        color = request.POST.get('color')
        textColor = request.POST.get('textColor')
        progressColor = request.POST.get('progressColor')
        gantt_skin = request.POST.get('gantt_skin')
        gantt_task_height = request.POST.get('gantt_task_height')
        gantt_row_height = request.POST.get('gantt_row_height')
        scheduler_skin = request.POST.get('scheduler_skin')
        judge = request.POST.get('judge')

        if judge == 'gantt_color':
            if change:
                Type.objects.filter(id=type_id).update(color=color,textColor=textColor, progressColor=progressColor)
                return HttpResponseRedirect('/' + url + '/manage/project_interface_edit/'+project_type_id)

        if judge=="priority":  #修改优先级颜色
            if change :
                Priority.objects.filter(id=type_id).update(color=color,textColor=textColor)
                return HttpResponseRedirect('/' + url + '/manage/project_interface_edit/' + project_type_id)
        if judge == 'gantt_skin':
            project_type.update(gantt_skin=gantt_skin)
            return HttpResponseRedirect('/' + url + '/manage/project_interface_edit/'+project_type_id)

        if judge == 'gantt_height':
            if change:
                if len(gantt_task_height.strip()) !=0 and len(gantt_row_height.strip()) !=0:
                    project_type.update(gantt_task_height=gantt_task_height,gantt_row_height=gantt_row_height)
                    return HttpResponseRedirect('/' + url + '/manage/project_interface_edit/'+project_type_id)
                else:
                    error = '高度不能为空！'
                    return render_to_response('manage/project_interface_edit.html', locals())

        if judge=='scheduler_skin':
            project_type.update(scheduler_skin=scheduler_skin)
            return HttpResponseRedirect('/' + url + '/manage/project_interface_edit/' + project_type_id)

    return render_to_response('manage/project_interface_edit.html', locals())

from createtree import mkdir

@checkCdkey
@login_required
@views_permission
def createtree(request,*args,**kwargs):
    project_archive = kwargs['project']  #项目归档判断
    project_id = kwargs['project_id']
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    if request.method == 'POST':
        paths = request.POST.get('all_path')
        root = '/var/centralStorage'
        for path in paths.split('|'):
            mkdir(root + path)

        return HttpResponseRedirect('/' + url + '/manage/createtree/')

    return render_to_response('manage/make_tree.html', locals())