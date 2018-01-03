#coding:utf-8
from django.shortcuts import render,render_to_response,HttpResponseRedirect,HttpResponse
from models import *
import re,os
from datetime import datetime
from datetime import timedelta
import time
from darkwarrior.settings import MEDIA_ROOT,EMAIL_HOST_USER
from django.contrib.auth.hashers import make_password,check_password
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from decorator import checkCdkey, login_required, views_permission
import subprocess
import uuid
from task_content_views import create_task,movetask
import calendar
from permissions import user_permissions
import base64

@checkCdkey
@login_required
@views_permission
def project_members_report(request,*args,**kwargs): #项目成员个人报表
    member_id = kwargs['member_id']
    url = kwargs['project_id']
    project_archive = kwargs['project']  # 项目归档判断
    user_now = request.session.get('USERNAME', False)
    member_name = User.objects.get(id=member_id).username
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    import time
    start_date_Array = time.strptime(str(datetime.now()).split('.')[0], '%Y-%m-%d %H:%M:%S')
    now_date = time.strftime("%m/%d/%Y", start_date_Array)

    time = now_date.split('/')

    monthRange = calendar.monthrange(int(time[2]),int(time[0]))

    start_date = '%s/%s/%s'%(time[0],1,time[2])

    end_date = '%s/%s/%s' % (time[0], monthRange[1], time[2])

    tasks = Taskorder.objects.filter(owner_project=url,owner__contains=member_name)

    if request.method == "POST":
        judge = request.POST.get('judge')
        if judge == "task_select":
            start = request.POST.get('start')
            end = request.POST.get('end')
            if len(start)>0 and len(end)>0:
                starts = start.split('/')
                start = datetime(int(starts[2]), int(starts[0]), int(starts[1]), 0, 0)
                ens = end.split('/')
                end = datetime(int(ens[2]), int(ens[0]), int(ens[1])) + timedelta(days=1)
                tasks = Taskorder.objects.filter(owner_project=url,owner__contains=member_name,start_date__range=(start, end)).order_by('priority')

    return render_to_response('project_members_report.html',locals())

@checkCdkey
@login_required
@views_permission
def wpaint(request,*args,**kwargs): #图片编辑
    url = kwargs['project_id']
    id = kwargs['id']
    wpaint_image = kwargs['wpaint_image']

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None
    try:
        name = Company_name.objects.filter(owner_project=0)[0]
    except:
        name = ''
    try:
        icon = logos = Logo.objects.order_by('-id')[0]
        icon = str(icon.logo)
    except:
        icon = ''
    return render_to_response('wpaint.html',locals())

@checkCdkey
@login_required
@views_permission
def update_image(request,*args,**kwargs): #图片编辑axaj
    url = kwargs['project_id']
    id = kwargs['id']
    user_now = request.session.get('USERNAME', False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    owner_project = Project.objects.get(id=url)
    author = User.objects.get(username=user_now)
    owner = Taskorder.objects.get(id=id)
    if request.method == 'POST':
        image_base64 = request.POST.get('image')
        image_base64 = image_base64.split(',')[1]

        image_name = uuid.uuid1()

        imgData = base64.b64decode(image_base64)
        image = open('E:/xunlei/local-repositories/project_manage/static/attachment/wpaint/%s.png'%image_name,'wb')
        image.write(imgData)
        image.close()

        submit_attachment = Attachment_image(url='attachment/wpaint/%s.png'%image_name, name=image_name, owner_comment=0, author=author,
                                             owner=owner, owner_project=owner_project)
        submit_attachment.save()

        return HttpResponse('ok')
        #return HttpResponseRedirect('%s/task/%s'%(url,id),locals())
    #return render_to_response('task_content.html',locals())


def welcome(request):      #起始页
    logos=Logo.objects.order_by('-id')
    user_now = request.session.get('USERNAME',False)
    return render_to_response('welcome.html',locals())

def registration(request):            #注册
    try:
        name = Company_name.objects.filter(owner_project=0)[0]
    except:
        name = ''

    if Login_title.objects.filter(owner_project=0).exists():
        login_title = Login_title.objects.filter(owner_project=0)[0].title
        login_left_title = login_title[0:int(len(login_title)/2)]
        login_right_title = login_title[int(len(login_title)/2):len(login_title)]
    else:
        login_left_title = "Dark Warrior |"
        login_right_title = '玄武 '
    try:
        icon = logos = Logo.objects.order_by('-id')[0]
        icon = str(icon.logo)
    except:
        icon = ''

    if request.method == 'POST':
        username = request.POST.get('name','')
        password1 = request.POST.get('password1','')
        password2 = request.POST.get('password2','')
        email = request.POST.get('email','')
        usernames = username.encode('utf8')

        chat_password = password1
        errors = []
        user= re.search(r'\S[0-9a-zA-Z\u4e00-\u9fa5]*$',str(usernames),re.I)
        pas = re.search(r'^[a-zA-Z]\w{5,17}$',str(password1),re.I)
        emai = re.search(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$',str(email),re.I)
        if not user:
            errors.append("您输入的用户名格式不正确，允许中文字母数字下划线")
            return render_to_response('page-register.html',locals())
        if not pas:
            errors.append("您输入的密码格式不正确，密码以字母开头，长度在6~18之间，只能包含字符、数字和下划线")
            return render_to_response('page-register.html',locals())
        if not emai:
            errors.append("您输入的邮箱格式不正确")
            return render_to_response('page-register.html',locals())
        if password1 != password2:
            errors.append("两次输入的密码不一致!")
            return render_to_response('page-register.html',locals())
        if User.objects.filter(email=email).count() >0:
            errors.append("邮箱已被使用!")
            return render_to_response('page-register.html', locals())
        is_user = User.objects.filter(username=username)
        if len(is_user)>0:
            errors.append("用户名已存在!")
            return render_to_response('page-register.html',locals())
        else:
            password = make_password(password1,None,'pbkdf2_sha256')
            register_user = User.objects.create(username=username,password=password,email=email)

            register_user.user_permission.add(Permission.objects.get(view_name = 'create_project'))
            request.session['IS_LOGIN'] = True
            request.session['USERNAME'] = username
            xmpp_server = '59.110.45.134'

            try:
                cmd = "prosodyctl register %s %s %s" % (username, xmpp_server, chat_password)
                sub = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                ss = sub.wait()
            except:
                errors.append('注册失败')
            chat_password2 = base64.encodestring(chat_password)
            ChatUser.objects.create(username=username, password=chat_password2, creator=username)
            errors.append('注册成功')
        return HttpResponseRedirect('/',locals())
    return render_to_response('page-register.html',locals())

def permission_403(request):
    return render_to_response('page-403.html')

def userlogout(request):       #登出
    del request.session['IS_LOGIN']
    del request.session['USERNAME']
    return HttpResponseRedirect('/login')


def password_reset(request,*args,**kwargs):
    ip = request.get_host()
    logos=Logo.objects.order_by('-id')
    if Login_title.objects.filter(owner_project=0).exists():
        login_title = Login_title.objects.filter(owner_project=0)[0].title
        login_left_title = login_title[0:int(len(login_title)/2)]
        login_right_title = login_title[int(len(login_title)/2):len(login_title)]
    else:
        login_left_title = "Dark Warrior |"
        login_right_title = '玄武 '
    try:
        if request.method == 'POST':
            email = request.POST.get('email',None)
            try:
                mail = User.objects.get(email = email)
            except:
                error = '您填写的邮箱不正确'
                return render_to_response('password_reset_form.html',locals())
            subject = '重置%s密码'%request.get_host()
            username_id = User.objects.get(email=email).id
            uidb64 = urlsafe_base64_encode(str(username_id))
            user = User.objects.get(id =username_id)
            token = default_token_generator.make_token(user)

            html_content = u'激活链接：http://%s/reset/%s/%s/'%(ip,uidb64,token)
            send_mail(subject,html_content,EMAIL_HOST_USER,[email])
            return HttpResponseRedirect('/',locals())
        return render_to_response('password_reset_form.html',locals())
    except Exception as e:
        error=e
        return render_to_response('password_reset_form.html',locals())


def password_reset_confirm(request,uidb64,token):
    logos=Logo.objects.order_by('-id')
    uidb64 =uidb64
    token =token
    user_id = urlsafe_base64_decode(uidb64)
    user = User.objects.get(id=user_id)

    if Login_title.objects.filter(owner_project=0).exists():
        login_title = Login_title.objects.filter(owner_project=0)[0].title
        login_left_title = login_title[0:int(len(login_title)/2)]
        login_right_title = login_title[int(len(login_title)/2):len(login_title)]
    else:
        login_left_title = "Dark Warrior |"
        login_right_title = '玄武 '
    errors = []
    if default_token_generator.check_token(user,token):
        print 'ok'
        if request.method == 'POST':
            new_password1 = request.POST.get('new_password1','')
            new_password2 = request.POST.get('new_password2','')
            chat_password = new_password1
            if new_password1 != new_password2:
                errors.append('新密码两次输入不一致')
            else:
                new_password = make_password(new_password1,None,'pbkdf2_sha256')
                User.objects.filter(username=user.username).update(password=new_password)
                xmpp_server = '59.110.45.134'

                try:
                    cmd = "prosodyctl register %s %s %s" %(user.username, xmpp_server, chat_password)
                    sub = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    ss = sub.wait()

                except:
                    errors.append('修改失败')
                chat_password2 = base64.encodestring(chat_password)

                ChatUser.objects.filter(username=user.username).update(password=chat_password2)
                errors.append('修改成功')
                return HttpResponseRedirect('/login')

    return render_to_response('password_reset_confirm.html',locals())




def login(request):        #登录
    try:
        name = Company_name.objects.filter(owner_project=0)[0]
    except:
        name = ''
    if Login_title.objects.filter(owner_project=0).exists():
        login_title = Login_title.objects.filter(owner_project=0)[0].title
        login_left_title = login_title[0:int(len(login_title)/2)]
        login_right_title = login_title[int(len(login_title)/2):len(login_title)]
    else:
        login_left_title = "Dark Warrior |"
        login_right_title = '玄武 '


    try:
        icon = logos = Logo.objects.order_by('-id')[0]
        icon = str(icon.logo)
    except:
        icon = ''


    if request.method == 'POST':
        try:
            nexts = request.GET['next']
        except:
            nexts = '/'
        username = request.POST.get('username','')
        password = request.POST.get('password','')
        errors=[]
        try:
            password2 = User.objects.get(username=username).password
            if check_password(password,password2):
                request.session['IS_LOGIN'] = True
                request.session['USERNAME'] = username
                User.objects.filter(username=username).update(last_login=datetime.now())
                return HttpResponseRedirect(str(nexts),locals())
            else:
                errors.append("您输入的用户名或密码不正确")
                request.session['username']=username
                return render_to_response('page-login.html',locals())
        except:
            errors.append("您输入的用户名或密码不正确")
    return render_to_response("page-login.html",locals())


@checkCdkey
@login_required
@views_permission
def create_project(request,*args,**kwargs):                  #创建项目
    logos=Logo.objects.order_by('-id')
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    project_types = Project_type.objects.filter(owner=0)|Project_type.objects.filter(creator=user_now)

    import time
    start_date_Array = time.strptime(str(datetime.now()).split('.')[0], '%Y-%m-%d %H:%M:%S')
    now_date = time.strftime("%Y/%m/%d %H:%M", start_date_Array)
    templates = Template.objects.filter(owner_project=0)
    if request.method == 'POST':
        name = request.POST.get('project_name')
        type = request.POST.get('project_type')
        selected_type = type
        description = request.POST.get('description')
        due_time = request.POST.get('time')
        template = request.POST.get('template')
        error=[]

        if len(Project.objects.filter(project_name=name))>0:
            error.append('您输入的项目名称已经存在')
            return render_to_response('create_project.html',locals())
        if not name:
            error.append('请输入项目名')
            request.session['project_name'] = name
            return render_to_response('create_project.html',locals())

        if not due_time:
            error.append('您输入项目预计完成时间格式不正确')
            return render_to_response('create_project.html',locals())

        else:
            time = datetime.strptime(due_time, '%Y/%m/%d %H:%M')
            creator = User.objects.get(username = user_now)

            project_type = Project_type.objects.get(id=type)
            create_project = Project.objects.create(project_name = name,project_type=project_type,project_description=description,due_time=time,creator=creator)

            now_project_id = create_project.id

            for taskgrade in Taskgrade.objects.filter(owner_project=0):
                Taskgrade.objects.create(name=taskgrade.name,description=taskgrade.description,owner_project=now_project_id)

            project_type = Project.objects.get(id=now_project_id).project_type.id
            milestones = Project_type.objects.get(id=project_type).milestone.all()
            prioritys = Project_type.objects.get(id=project_type).task_priority.all()
            statuss = Project_type.objects.get(id=project_type).task_status.all()
            components = Project_type.objects.get(id=project_type).task_component.all()
            types = Project_type.objects.get(id=project_type).task_type.all()
            versions = Project_type.objects.get(id=project_type).task_version.all()

            value = 0
            for milestone in milestones:
                value +=1
                default = False
                if milestone.default == True:
                    default = True
                Milestone.objects.create(name=milestone.name,description=milestone.description,owner_project=now_project_id,default=default)

            value = 0
            for priority in prioritys:
                value +=1
                default = False
                if priority.default == True:
                    default = True
                Priority.objects.create(name=priority.name,value=value,owner_project=now_project_id,default=default,
                                        color=priority.color, textColor=priority.textColor)

            value = 0
            for status in statuss:
                value +=1
                Status.objects.create(name=status.name,value=value,owner_project=now_project_id)

            for component in components:
                default = False
                if component.default == True:
                    default = True
                Component.objects.create(name=component.name,description=component.description,owner_project = now_project_id,default=default)

            value = 0
            for type in types:
                value +=1
                default = False
                if type.default == True:
                    default = True
                Type.objects.create(name=type.name,value=value,owner_project=now_project_id,default=default,
                                    color=type.color,textColor=type.textColor,progressColor=type.progressColor)

            for version in versions:
                default = False
                if version.default == True:
                    default = True
                Versions.objects.create(name=version.name,description=version.description,owner_project=now_project_id,default=default)


            #创建自己的项目专属项目类型
            selected_type = Project_type.objects.get(id=int(selected_type))
            project_types = Project_type.objects.create(name=Project_type.objects.get(id=project_type).name,owner=now_project_id,creator=user_now,
                                                        gantt_skin = selected_type.gantt_skin,scheduler_skin = selected_type.scheduler_skin,
                                                        gantt_task_height = selected_type.gantt_task_height,gantt_row_height = selected_type.gantt_row_height)


            now_project_type = project_types
            for type in Type.objects.filter(owner_project=now_project_id):
                now_project_type.task_type.add(type)

            for priority in Priority.objects.filter(owner_project=now_project_id):
                now_project_type.task_priority.add(priority)

            for component in Component.objects.filter(owner_project=now_project_id):
                now_project_type.task_component.add(component)

            for version in Versions.objects.filter(owner_project =now_project_id):
                now_project_type.task_version.add(version)

            for status in Status.objects.filter(owner_project=now_project_id):
                now_project_type.task_status.add(status)


            for milestone in Milestone.objects.filter(owner_project=now_project_id):
                now_project_type.milestone.add(milestone)

            Project.objects.filter(id=now_project_id).update(project_type=now_project_type) #项目类型修改到专属类型


            #milestones = Milestone.objects.filter(owner_project=now_project_id)  #设置初始默认属性
            #prioritys = Priority.objects.filter(owner_project=now_project_id)
            #components = Component.objects.filter(owner_project=now_project_id)
            #types = Type.objects.filter(owner_project=now_project_id)
            #versions = Versions.objects.filter(owner_project=now_project_id)

            #Milestone.objects.filter(owner_project=now_project_id,id=milestones[0].id).update(default=True)
            #Priority.objects.filter(owner_project=now_project_id,id=prioritys[2].id).update(default=True)
            #Component.objects.filter(owner_project=now_project_id,id=components[0].id).update(default=True)
            #Type.objects.filter(owner_project=now_project_id,id=types[0].id).update(default=True)
            #Versions.objects.filter(owner_project=now_project_id,id=versions[0].id).update(default=True)


            #选择模版
            select_template = Template.objects.get(id=template)
            Template.objects.create(name=select_template.name, display=select_template.display,
                                    description=select_template.description, owner_project=now_project_id)

            #创建项目权限
            base_permission = Base_permission.objects.all()
            project_id = now_project_id
            for i in base_permission:

                permission = Permission(project_id=project_id,view_name=i.view_name,description=name+' | '+i.description)
                permission.save()
            for user_permission in Permission.objects.filter(project_id=project_id):
                User.objects.get(username=user_now).user_permission.add(user_permission)
            return HttpResponseRedirect('/',locals())
    else:
        return render_to_response('create_project.html',locals())

@checkCdkey
@login_required
@views_permission
def index(request,*args,**kwargs):  #首页
    staff_user = kwargs['staff_user']
    staff_all_per = kwargs['staff_all_per']
    user_now =request.session.get('USERNAME',False)
    user_permission = User.objects.get(username=user_now).user_permission.all()
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    global_manage = True

    request.session.set_expiry(0) #浏览器关闭注销会话

    projects=Project.objects.filter(is_archive=False)
    createproject=True
    logos=Logo.objects.order_by('-id')
    #添加时间6/17
    projects_list = []
    other_projects_list = []
    for project in projects:
        project_groups = Group.objects.filter(owner_project_id = str(project.id))

        project_id = project.id
        project_name = project.project_name
        project_type = project.project_type
        project_status =project.project_status
        project_creator = project.creator
        project_description = project.project_description
        create_time = project.create_time


        project_type = project.project_type
        milestones = project_type.milestone.all()
        prioritys = project_type.task_priority.all()
        statuss = project_type.task_status.all()
        components = project_type.task_component.all()
        types = project_type.task_type.all()
        versions = project_type.task_version.all()

        try:
            template = Template.objects.get(owner_project=project_id)
        except:
            template = None

        is_archive=project.is_archive

        if Taskorder.objects.filter(owner_project=project).count() == 0:
            percent = 0
        else:
            percent = int(float(Taskorder.objects.filter(owner_project=project,status=statuss.order_by('-value')[0]).count())/Taskorder.objects.filter(owner_project=project).count()*100)

        project_home_permission = Permission.objects.get(project_id = project_id,view_name = 'project_index')  #项目首页权限  lly 2016/08/23
        if project_home_permission in staff_all_per or staff_user.is_superuser==True or staff_user==project_creator or project.is_check_permission==False:
            projects_list.append({'project_id':project_id,'project_name':project_name,'project_type':project_type,'project_status':project_status,
                                  'project_creator':project_creator,'project_description':project_description,'create_time':create_time,
                                  'project_groups':project_groups,'percent':percent,'is_archive':is_archive,'template':template})
        else:
            other_projects_list.append({'project_id':project_id,'project_name':project_name,'project_type':project_type,'project_status':project_status,
                                        'project_creator':project_creator,'project_description':project_description,'create_time':create_time,
                                        'project_groups':project_groups,'percent':percent,'is_archive':is_archive,'template':template})



    return render_to_response('index.html',locals())


@checkCdkey
@login_required
@views_permission
def archive_page(request,*args,**kwargs):  #项目归档页
    staff_user = kwargs['staff_user']
    staff_all_per = kwargs['staff_all_per']
    user_now =request.session.get('USERNAME',False)
    user_permission = User.objects.get(username=user_now).user_permission.all()
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    global_manage = True
    archive_projects = []
    if staff_user.is_superuser == True:
        archive_projects = Project.objects.filter(is_archive=True)
    else:
        for project in Project.objects.filter(is_archive=True):
            if Permission.objects.get(project_id=project.id,view_name='manage') in staff_all_per or project.creator==staff_user:
                archive_projects.append(project)
    projects_list= []
    for project in archive_projects:
        project_groups = Group.objects.filter(owner_project_id = str(project.id))

        project_id = project.id
        project_name = project.project_name
        project_type = project.project_type
        project_status =project.project_status
        project_creator = project.creator
        project_description = project.project_description
        create_time = project.create_time

        project_type = project.project_type
        milestones = project_type.milestone.all()
        prioritys = project_type.task_priority.all()
        statuss = project_type.task_status.all()
        components = project_type.task_component.all()
        types = project_type.task_type.all()
        versions = project_type.task_version.all()

        try:
            template = Template.objects.get(owner_project=project_id)
        except:
            template = None

        percent = 100
        projects_list.append({'project_id':project_id,'project_name':project_name,'project_type':project_type,'project_status':project_status,
                              'project_creator':project_creator,'project_description':project_description,'create_time':create_time,
                              'project_groups':project_groups,'percent':percent,'is_archive':True,'template':template})






    return render_to_response('archive_page.html', locals())

@checkCdkey
@login_required
@views_permission
def password_change(request,*args,**kwargs):     #密码修改

    if Login_title.objects.filter(owner_project=0).exists():
        login_title = Login_title.objects.filter(owner_project=0)[0].title
        login_left_title = login_title[0:int(len(login_title)/2)]
        login_right_title = login_title[int(len(login_title)/2):len(login_title)]
    else:
        login_left_title = "Dark Warrior |"
        login_right_title = '玄武 '
    errors = []
    if request.method == 'POST':
        username = request.session.get('USERNAME',False)
        old_password = request.POST.get('old_password','')
        new_password1 = request.POST.get('new_password1','')
        new_password2 = request.POST.get('new_password2','')
        password = User.objects.get(username=username).password
        if not check_password(old_password,password):
            errors.append('您输入的旧密码有误')
        elif new_password1 != new_password2:
            errors.append('新密码两次输入不一致')
        else:
            new_password = make_password(new_password1,None,'pbkdf2_sha256')
            User.objects.filter(username=username).update(password=new_password)
            return HttpResponseRedirect('/login')

    return render_to_response('password_change.html',locals())


@checkCdkey
@login_required
@views_permission
def query(request,*args,**kwargs):         #定制查询
    project_archive = kwargs['project']  #项目归档判断

    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    project_type = project_archive.project_type
    milestones = project_type.milestone.all()
    prioritys = project_type.task_priority.all()
    statuss = project_type.task_status.all()
    components = project_type.task_component.all()
    types = project_type.task_type.all()
    versions = project_type.task_version.all()

    user = User.objects.get(username=user_now)
    user_all_permissions = user_permissions(user)
    project_manage_permissions = Permission.objects.get(view_name='manage', project_id=url)

    manage_status = statuss.order_by('-value')[0]
    all_status = list(statuss)
    all_status.pop()
    all_statuss = all_status

    if user.is_superuser:
        manage = True
    else:
        if project_manage_permissions in user_all_permissions:
            manage = True

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    condition = Taskorder.objects.filter(owner_project=Project.objects.get(id=url)).order_by('priority')
    if request.method == 'POST':
        select_owner = request.POST.get('owner_select')
        select_condition = request.POST.getlist('select_status')
        judge = request.POST.get('judge')

        if judge == 'task_select':
            select_conditions = []
            for status_id in select_condition:
                select_conditions.append(int(status_id))

            if len(select_condition)>0 and len(select_owner)>0:
                condition = Taskorder.objects.filter(owner_project=url,status__in=select_condition,owner__contains=select_owner).order_by('priority')
                return render_to_response('query.html',locals())
            elif len(select_condition)>0:
                condition =Taskorder.objects.filter(owner_project=url,status__in=select_condition).order_by('priority')
                return render_to_response('query.html',locals())
            elif select_owner is not None and len(select_owner)>0:
                condition = Taskorder.objects.filter(owner_project=url,owner__contains=select_owner).order_by('priority')
                return render_to_response('query.html',locals())
            else:
                condition = Taskorder.objects.filter(owner_project=url).order_by('priority')



    if request.method == 'POST':
        judge = request.POST.get('judge')
        task_id = request.POST.get('task_id')
        task_summary = request.POST.get('task_summary')
        task_status = request.POST.get('task_status')
        task_owner = request.POST.get('task_owner')
        task_reporter = request.POST.get('task_reporter')
        task_type = request.POST.get('task_type')
        task_priority = request.POST.get('task_priority')
        task_milestone = request.POST.get('task_milestone')
        task_component =request.POST.get('task_component')
        task_version = request.POST.get('task_version')
        task_story_point = request.POST.get('task_story_point')


        if judge == 'task_change':
            #根据状态修改开始结束时间
            start_date_Array = datetime.strptime(str(datetime.now()).split('.')[0], '%Y-%m-%d %H:%M:%S')

            if statuss[1].id == task_status:
                Taskorder.objects.filter(id=task_id).update(start_date=start_date_Array)
            if statuss.order_by('-value')[0].id == task_status:
                Taskorder.objects.filter(id=task_id).update(end_date=start_date_Array)

            #更新甘特图持续时间
            now_end_time = time.mktime(time.strptime(str(Taskorder.objects.get(id=task_id).end_date).split('+')[0].split('.')[0],"%Y-%m-%d %H:%M:%S"))
            now_start_time = time.mktime(time.strptime(str(Taskorder.objects.get(id=task_id).start_date).split('+')[0].split('.')[0],"%Y-%m-%d %H:%M:%S"))
            duration_timestamip= int(now_end_time) - int(now_start_time)
            duration = duration_timestamip / 86400

            if duration == 0:
                duration = 1

            Taskorder.objects.filter(id=task_id).update(duration=duration)

            if task_owner.split(',') is not None and len(task_owner)>0:
                task_owners = ''
                for task_owner in task_owner.split(','):
                    if User.objects.filter(username=task_owner):
                        task_owners = task_owners + task_owner + ','
                    owner_list=list(task_owners)
                    if len(owner_list)>0:
                        owner_list.pop()
                    owner = "".join(owner_list)
            if task_owner == '':
                owner = ''
            if task_id is not None and len(task_id)>0:
                Taskorder.objects.filter(id=task_id).update(summary=task_summary,status=Status.objects.get(id=task_status),owner=owner,reporter=task_reporter,storypoint=task_story_point,
                                                            type=Type.objects.get(id=task_type),priority=Priority.objects.get(id=task_priority),milestone=Milestone.objects.get(id=task_milestone),
                                                            component=Component.objects.get(id=task_component),version=Versions.objects.get(id=task_version))
    return render_to_response('query.html',locals())



@checkCdkey
@login_required
@views_permission
def many_change(request,*args,**kwargs):         #批量修改
    project_archive = kwargs['project']  #项目归档判断

    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    project_type = project_archive.project_type
    milestones = project_type.milestone.all()
    prioritys = project_type.task_priority.all()
    statuss = project_type.task_status.all()
    components = project_type.task_component.all()
    types = project_type.task_type.all()
    versions = project_type.task_version.all()

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    condition = Taskorder.objects.filter(owner_project=Project.objects.get(id=url)).order_by('priority')
    if request.method == 'POST':
        select_owner = request.POST.get('owner_select')
        select_condition = request.POST.getlist('select_status')

        select_conditions = []
        for status_id in select_condition:
            select_conditions.append(int(status_id))

        if len(select_condition)>0 and len(select_owner)>0:
            condition = Taskorder.objects.filter(owner_project=url,status__in=select_condition,owner__contains=select_owner).order_by('priority')
            return render_to_response('many_change.html',locals())
        elif len(select_condition)>0:
            condition =Taskorder.objects.filter(owner_project=url,status__in=select_condition).order_by('priority')
            return render_to_response('many_change.html',locals())
        elif select_owner is not None and len(select_owner)>0:
            condition = Taskorder.objects.filter(owner_project=url,owner__contains=select_owner).order_by('priority')
            return render_to_response('many_change.html',locals())
        else:
            condition = Taskorder.objects.filter(owner_project=url).order_by('priority')
            #return render_to_response('many_change.html',locals())




    if request.method == 'POST':  #批量修改
        id = request.POST.getlist('id')

        change_owner = request.POST.get('change_owner')
        task_owner = request.POST.get('task_owner')
        if change_owner == 'task_owner':
            if task_owner.split(',') is not None and len(task_owner)>0:
                task_owners = ''
                for task_owner in task_owner.split(','):
                    if User.objects.filter(username=task_owner):
                        task_owners = task_owners + task_owner + ','
                owner_list=list(task_owners)
                if len(owner_list)>0:
                    owner_list.pop()
                owner = "".join(owner_list)
            if task_owner == '':
                owner = ''
            Taskorder.objects.filter(id__in=id).update(owner=owner)

        change_reporter = request.POST.get('change_reporter')
        task_reporter = request.POST.get('task_reporter')
        if change_reporter == 'task_reporter':
            if task_reporter is not None and len(task_reporter)>0:
                Taskorder.objects.filter(id__in=id).update(reporter=str(task_reporter).strip())

        change_status = request.POST.get('change_status')
        task_status = request.POST.get('task_status')
        if change_status == 'task_status':
            if task_status is not  None and len(task_status)>0:

                #根据状态修改开始结束时间
                #################################################################################################
                start_date_Array = datetime.strptime(str(datetime.now()).split('.')[0], '%Y-%m-%d %H:%M:%S')

                if statuss[1].id == task_status:
                    Taskorder.objects.filter(id__in=id).update(start_date=start_date_Array)
                if statuss.order_by('-value')[0].id == task_status:
                    Taskorder.objects.filter(id__in=id).update(end_date=start_date_Array)
                Taskorder.objects.filter(id__in=id).update(status=Status.objects.get(id=task_status))

                #更新甘特图持续时间
                for task in Taskorder.objects.filter(id__in=id):
                    now_end_time = time.mktime(time.strptime(str(task.end_date).split('+')[0].split('.')[0],"%Y-%m-%d %H:%M:%S"))
                    now_start_time = time.mktime(time.strptime(str(task.start_date).split('+')[0].split('.')[0],"%Y-%m-%d %H:%M:%S"))
                    duration_timestamip= int(now_end_time) - int(now_start_time)
                    duration = duration_timestamip / 86400

                    if duration == 0:
                        duration = 1
                    Taskorder.objects.filter(id=task.id).update(duration=duration)

        change_type = request.POST.get('change_type')
        task_type = request.POST.get('task_type')
        if change_type == 'task_type':
            if task_type is not None and len(task_type)>0:
                Taskorder.objects.filter(id__in=id).update(type=Type.objects.get(id=task_type))

        change_priority = request.POST.get('change_priority')
        task_priority = request.POST.get('task_priority')
        if change_priority == 'task_priority':
            if task_priority is not None and len(task_priority)>0:
                Taskorder.objects.filter(id__in=id).update(priority=Priority.objects.get(id=task_priority))

        change_milestone = request.POST.get('change_milestone')
        task_milestone = request.POST.get('task_milestone')
        if change_milestone == 'task_milestone':
            if task_milestone is not None and len(task_milestone)>0:
                Taskorder.objects.filter(id__in=id).update(milestone=Milestone.objects.get(id=task_milestone))

        change_component = request.POST.get('change_component')
        task_component = request.POST.get('task_component')
        if change_component == 'task_component':
            if task_component is not None and len(task_component)>0:
                Taskorder.objects.filter(id__in=id).update(component=Component.objects.get(id=task_component))

        change_version = request.POST.get('change_version')
        task_version = request.POST.get('task_version')
        if change_version == 'task_version':
            if task_version is not None and len(task_version)>0:
                Taskorder.objects.filter(id__in=id).update(version=Versions.objects.get(id=task_version))

        return HttpResponseRedirect('/%s/many_change'%url)



    return render_to_response('many_change.html',locals())


@checkCdkey
@login_required
@views_permission
def newtask(request,*args,**kwargs):    #创建任务单
    project_archive = kwargs['project']  #项目归档判断

    url = kwargs['project_id']

    project_type = project_archive.project_type
    milestones = project_type.milestone.all()
    prioritys = project_type.task_priority.all()
    statuss = project_type.task_status.all()
    components = project_type.task_component.all()
    types = project_type.task_type.all()
    versions = project_type.task_version.all()

    milestone_default = project_type.milestone.filter(owner_project=url,default=True)[0]
    priority_default = project_type.task_priority.filter(owner_project=url,default=True)[0]
    component_default = project_type.task_component.filter(owner_project=url,default=True)[0]
    type_default = project_type.task_type.filter(owner_project=url,default=True)[0]
    version_default = project_type.task_version.filter(owner_project=url,default=True)[0]

    #task_grades = Taskgrade.objects.filter(owner_project=project_archive)
    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    start_date_Array = time.strptime(str(datetime.now()).split('.')[0], '%Y-%m-%d %H:%M:%S')
    now_date = time.strftime("%Y/%m/%d %H:%M", start_date_Array)

    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    errors = []
    if request.method == 'POST':
        summary = request.POST.get('summary')
        description = request.POST.get('content')
        task_type = request.POST.get('type')
        milestone = request.POST.get('milestone')
        component = request.POST.get('component')
        priority = request.POST.get('priority')
        owner = request.POST.get('owner')
        version = request.POST.get('version')
        task_image = request.FILES.get('task_image')


        start_date = request.POST.get('start_date')
        text = request.POST.get('text')
        end_date = request.POST.get('end_date')
        story_point =request.POST.get('story_point')

        task_relevance = request.POST.get('relevance')
        task_id = request.POST.get('task_id')
        relevance_type = request.POST.get('relevance_type')

        task_grade = request.POST.get('task_grade')

        if end_date == '':
            end_date = now_date
        if start_date == '':
            start_date = now_date
        task_start_date = datetime.strptime(start_date,'%Y/%m/%d %H:%M')
        task_end_date = datetime.strptime(end_date,'%Y/%m/%d %H:%M')


        duration_timestamip= int(time.mktime(time.strptime(end_date,'%Y/%m/%d %H:%M'))) - int(time.mktime(time.strptime(start_date,'%Y/%m/%d %H:%M')))
        duration = duration_timestamip / 86400

        type = Type.objects.get(id=task_type)
        component = Component.objects.get(id=component)
        priority = Priority.objects.get(id=priority)
        version = Versions.objects.get(id=version)
        milestone = Milestone.objects.get(id=milestone)
        creator = User.objects.get(username=user_now)
        owner_project = Project.objects.get(id=url)
        if task_image is not None:
            image = task_image.name.split('.')[-1]
        else:
            image = None

        #检测属主是否存在，只添加存在的属主
        if owner.split(',') is not None and len(owner)>0:
            task_owners = ''
            for task_owner in owner.split(','):
                if User.objects.filter(username=task_owner):
                    task_owners = task_owners + task_owner + ','
            owner_list=list(task_owners)
            if len(owner_list)>0:
                owner_list.pop()
            owner = "".join(owner_list)

        #获取显示id
        task_num = Taskorder.objects.filter(owner_project=project_archive).count()

        if task_num == 0:
            display_id = 1
        else:
            display_id = int(Taskorder.objects.filter(owner_project=project_archive,parent=0).order_by('-id')[0].display_id) + 1

        if duration == 0:
            duration = 1

        if summary is not None and len(summary)>0:
            if image == 'tiff':
                errors.append('您上传的图片web不支持显示')
            elif start_date is not None and len(start_date)>0:
                create_task = Taskorder.objects.create(summary=summary, creator=creator, description=description, type=type,
                                        milestone=milestone, reporter=user_now,
                                        component=component, priority=priority, task_image=task_image, owner=owner,
                                        version=version, display_id=display_id,
                                        status=statuss[0], owner_project=owner_project, start_date=task_start_date,
                                        duration=duration, end_date=task_end_date, predict_start_date=task_start_date,
                                        predict_duration=duration, predict_end_date=task_end_date
                                        )

                if story_point is not None and len(story_point) > 0:
                    Taskorder.objects.filter(id=create_task.id).update(storypoint=story_point)

                #if task_grade is not None and len(task_grade) >0:
                    #Taskorder.objects.filter(id=create_task.id).update(grade=task_grade)


                id = Taskorder.objects.filter(creator=user_now).order_by('-id')[0].id

                #任务单关联
                if task_relevance == 'task_relevance':
                    if task_id is not None and len(task_id)>0:
                        Gantt_links.objects.create(source=id,target=task_id,type=relevance_type)
                return HttpResponseRedirect('/%s/task/%s'%(url,id),locals())
            else:
                errors.append('请输入任务起始时间')

        else:
            errors.append('请输入任务单概述')
    return render_to_response('create_task.html',locals())



@checkCdkey
@login_required
@views_permission
def gantt(request,*aegs,**kwargs):
    project_archive = kwargs['project']  #项目归档判断

    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    gantt_links = Gantt_links.objects.all()                                        #甘特图关联


    #实时更新甘特图任务进度数据
    project_type = project_archive.project_type
    milestones = project_type.milestone.all()
    prioritys = project_type.task_priority.all()
    statuss = project_type.task_status.all()
    components = project_type.task_component.all()
    types = project_type.task_type.all()
    versions = project_type.task_version.all()

    milestone_default = project_type.milestone.filter(owner_project=url, default=True)[0]
    priority_default = project_type.task_priority.filter(owner_project=url, default=True)[0]
    component_default = project_type.task_component.filter(owner_project=url, default=True)[0]
    type_default = project_type.task_type.filter(owner_project=url, default=True)[0]
    version_default = project_type.task_version.filter(owner_project=url, default=True)[0]

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    start_tasks = Taskorder.objects.filter(owner_project=url,status=statuss.order_by('value')[1])
    for start_task in start_tasks:
        now_start_time = time.mktime(time.strptime(str(Taskorder.objects.get(id=start_task.id).start_date).split('+')[0].split('.')[0],"%Y-%m-%d %H:%M:%S"))
        now_time = time.time()
        progress_timestamip = now_time - now_start_time
        use_time = progress_timestamip / 86400
        if start_task.duration == 0:
            start_task.duration = 1
        progress = use_time / start_task.duration
        Taskorder.objects.filter(id=start_task.id).update(progress=progress)


    gantt_css = project_type.gantt_skin
    gantt_css_url = 'codebase/skins/'+gantt_css
    gantt_task_height = project_type.gantt_task_height
    gantt_row_height = project_type.gantt_row_height

    #创建任务单



    start_date_Array = time.strptime(str(datetime.now()).split('.')[0], '%Y-%m-%d %H:%M:%S')
    now_date = time.strftime("%Y/%m/%d %H:%M", start_date_Array)

    if request.method=='GET':
        self = request.GET.get('self')
        if self=='self':
            get_form = """
             <form method="get" action=""   hidden='hidden'>
            <input type="submit" value="查看全部" id="all">
            </form>
            <a style='cursor:pointer;font-size:20px;' id='all_a' name='premise'><i class="fa fa-users" aria-hidden="true"></i></a>
            <script>
            document.getElementById('all_a').onclick = function(){
                document.getElementById('all').click();
             };
            </script>
             """

            gantt_tasks_creator = Taskorder.objects.filter(owner_project=url,creator=staff_user)
            gantt_tasks_owner = Taskorder.objects.filter(owner_project=url,owner__contains=user)
            gantt_tasks_reporter = Taskorder.objects.filter(owner_project=url,reporter=user)
            set_list = list(set(list(gantt_tasks_creator)+list(gantt_tasks_owner)+list(gantt_tasks_reporter)))
            for task_object in set_list:
                if task_object.parent!=0:
                    try:
                        task_parent = Taskorder.objects.get(id=task_object.parent_id)
                        if task_parent not in set_list:
                            set_list.append(task_parent)
                    except:
                        pass
            task_num = len(set_list)
            gantt_tasks = set_list
            if gantt_row_height:
                if task_num==0:
                    height_num = 100
                elif task_num < 5:
                    if gantt_row_height<=100:
                        height_num = task_num *100
                    else:
                        height_num = task_num * gantt_row_height
                elif 5 <= task_num <= 10:
                    if gantt_row_height<=60:
                        height_num = task_num *60
                    else:
                        height_num = task_num * gantt_row_height
                elif 10 < task_num <= 50:
                    if gantt_row_height<=50:
                        height_num = task_num *50
                    else:
                        height_num = task_num * gantt_row_height
                else:
                    if gantt_row_height<=40:
                        height_num = task_num * 40
                    else:
                        height_num = task_num * gantt_row_height
            else:
                if task_num==0:
                    height_num = 100
                elif task_num < 5:
                    height_num = task_num * 100
                elif 5 <= task_num <= 10:
                    height_num = task_num *60
                elif 10 < task_num <= 50:
                    height_num = task_num * 50
                else:
                    height_num = task_num * 40
            return render_to_response('gantt.html',locals())


        else:
            get_form = '''
              <form method="get" action=""  hidden='hidden' >
             <input type="text" value="self" name="self" >
             <input type="submit" value="查看属于的我" id='self'>
             </form>
               <a style='cursor:pointer;font-size:20px;"' id='self_a' name='premise'><i class="fa fa-user" aria-hidden="true"></i></a>
              <script>
            document.getElementById('self_a').onclick = function(){
                document.getElementById('self').click();
             };
            </script>
            '''
            gantt_tasks = Taskorder.objects.filter(owner_project=url).order_by('-start_date')
            task_num = Taskorder.objects.filter(owner_project=url).count()
            if gantt_row_height:
                if task_num==0:
                    height_num = 100
                elif 0<task_num < 5:
                    if gantt_row_height<=100:
                        height_num = task_num *100
                    else:
                        height_num = task_num * gantt_row_height
                elif 5 <= task_num <= 10:
                    if gantt_row_height<=60:
                        height_num = task_num *60
                    else:
                        height_num = task_num * gantt_row_height
                elif 10 < task_num <= 50:
                    if gantt_row_height<=50:
                        height_num = task_num *50
                    else:
                        height_num = task_num * gantt_row_height
                else:
                    if gantt_row_height<=40:
                        height_num = task_num * 40
                    else:
                        height_num = task_num * gantt_row_height
            else:
                if task_num==0:
                    height_num = 100
                elif 0< task_num < 5:
                    height_num = task_num * 100
                elif 5 <= task_num <= 10:
                    height_num = task_num *60
                elif 10 < task_num <= 50:
                    height_num = task_num * 50
                else:
                    height_num = task_num * 40
            return render_to_response('gantt.html',locals())

    errors = []
    if request.method == 'POST':
        summary = request.POST.get('summary')
        description = request.POST.get('content')
        task_type = request.POST.get('type')
        milestone = request.POST.get('milestone')
        component = request.POST.get('component')
        priority = request.POST.get('priority')
        owner = request.POST.get('owner')
        version = request.POST.get('version')
        task_image = request.FILES.get('task_image')

        start_date = request.POST.get('start_date')
        text = request.POST.get('text')
        end_date = request.POST.get('end_date')
        story_point =request.POST.get('story_point')

        task_parent_id =request.POST.get('parent_id')

        task_relevance = request.POST.get('relevance')
        task_id = request.POST.get('task_id')
        relevance_type = request.POST.get('relevance_type')

        if end_date == '':
            end_date = now_date
        if start_date == '':
            start_date = now_date

        task_start_date = datetime.strptime(start_date,'%Y/%m/%d %H:%M')
        task_end_date = datetime.strptime(end_date,'%Y/%m/%d %H:%M')

        duration_timestamip= int(time.mktime(time.strptime(end_date,'%Y/%m/%d %H:%M'))) - int(time.mktime(time.strptime(start_date,'%Y/%m/%d %H:%M')))
        duration = duration_timestamip / 86400

        type = Type.objects.get(id=task_type)
        component = Component.objects.get(id=component)
        priority = Priority.objects.get(id=priority)
        version = Versions.objects.get(id=version)
        milestone = Milestone.objects.get(id=milestone)

        creator = User.objects.get(username=user_now)
        owner_project = Project.objects.get(id=url)
        if task_image is not None:
            image = task_image.name.split('.')[-1]
        else:
            image = None

        #检测属主是否存在，只添加存在的属主
        if owner.split(',') is not None and len(owner)>0:
            task_owners = ''
            for task_owner in owner.split(','):
                if User.objects.filter(username=task_owner):
                    task_owners = task_owners + task_owner + ','
            owner_list=list(task_owners)
            if len(owner_list)>0:
                owner_list.pop()
            owner = "".join(owner_list)

        #获取最后一个显示id
        task_num = Taskorder.objects.filter(owner_project=project_archive).count()
        if task_num == 0:
            display_id = 1
        else:
            display_id = int(Taskorder.objects.filter(owner_project=project_archive,parent=0).order_by('-id')[0].display_id) + 1

        if duration == 0:
            duration = 1

        if summary is not None and len(summary)>0:

            if image == 'tiff':
                errors.append('您上传的图片web不支持显示')
            elif start_date is not None and len(start_date) > 0:
                create_task = Taskorder.objects.create(summary=summary, creator=creator, description=description,
                                                       type=type, milestone=milestone, reporter=user_now,
                                                       component=component, priority=priority, task_image=task_image,
                                                       owner=owner, version=version, parent=task_parent_id,
                                                       status=statuss[0], owner_project=owner_project,
                                                       start_date=task_start_date, end_date=task_end_date,duration=duration,
                                                       display_id=display_id, predict_start_date=task_start_date,
                                                       predict_duration=duration, predict_end_date=task_end_date)

                if story_point is not None and len(story_point) > 0:
                    Taskorder.objects.filter(id=create_task.id).update(storypoint=story_point)


                id = Taskorder.objects.filter(creator=user_now).order_by('-id')[0].id

                #任务单关联
                if task_relevance == 'task_relevance':
                    if task_id is not None and len(task_id)>0:
                        Gantt_links.objects.create(source=id,target=task_id,type=relevance_type)


                return HttpResponseRedirect('/%s/gantt'%url,locals())
            else:
                errors.append('请输入任务起始时间')
                return render_to_response('gantt.html',locals())
        else:
            errors.append('请输入任务概述')
            return render_to_response('gantt.html',locals())




    return render_to_response('gantt.html',locals())


def link(request):
    if request.method =="POST":
        source = request.POST.get('source')
        target = request.POST.get('target')
        type = request.POST.get('type')

        id = request.POST.get('id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        duration = request.POST.get('duration')
        progress = request.POST.get('progress')
        text = request.POST.get('text')

        judge = request.POST.get('judge')


        now_url = request.get_full_path() #当前路径

        delete_task_id = request.POST.get('task_id')
        delete_parent = request.POST.get('parent')

        if judge=='add_link':
            if Gantt_links.objects.filter(source=source,target=target,type=type).exists():
                pass
            else:
                Gantt_links.objects.create(source=source,target=target,type=type)
        if judge=='delete_link':
            Gantt_links.objects.filter(source=source,target=target,type=type).delete()
        if judge=='change_task':
            start_date= " ".join(start_date.split(' ')[1:5])
            time = datetime.strptime(start_date, '%b %d %Y %H:%M:%S')
            end_date = " ".join(end_date.split(' ')[1:5])
            time_end = datetime.strptime(end_date, '%b %d %Y %H:%M:%S')
            if duration == 0:
                duration = 1
            Taskorder.objects.filter(id=id).update(start_date=time,end_date=time_end,duration=duration,progress=progress,summary=text)
        if judge=='delete_task':
            if delete_parent == str(0):
                Taskorder.objects.filter(parent=delete_task_id).delete()
                Taskorder.objects.filter(id=delete_task_id).delete()
            else:
                Taskorder.objects.filter(id=delete_task_id).delete()
        return HttpResponseRedirect('%s'%now_url)


@checkCdkey
@login_required
@views_permission
def new_child_task(request,*args,**kwargs):    #创建子任务单
    project_archive = kwargs['project']  #项目归档判断

    url = kwargs['project_id']
    parent_id = kwargs['parent_task']

    project_type = project_archive.project_type
    milestones = project_type.milestone.all()
    prioritys = project_type.task_priority.all()
    statuss = project_type.task_status.all()
    components = project_type.task_component.all()
    types = project_type.task_type.all()
    versions = project_type.task_version.all()

    milestone_default = project_type.milestone.filter(owner_project=url, default=True)[0]
    priority_default = project_type.task_priority.filter(owner_project=url, default=True)[0]
    component_default = project_type.task_component.filter(owner_project=url, default=True)[0]
    type_default = project_type.task_type.filter(owner_project=url, default=True)[0]
    version_default = project_type.task_version.filter(owner_project=url, default=True)[0]

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    start_date_Array = time.strptime(str(datetime.now()).split('.')[0], '%Y-%m-%d %H:%M:%S')
    now_date = time.strftime("%Y/%m/%d %H:%M", start_date_Array)
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    errors = []
    if request.method == 'POST':
        summary = request.POST.get('summary')
        description = request.POST.get('content')
        task_type = request.POST.get('type')
        milestone = request.POST.get('milestone')
        component = request.POST.get('component')
        priority = request.POST.get('priority')
        owner = request.POST.get('owner')
        version = request.POST.get('version')
        task_image = request.FILES.get('task_image')
        due_time = request.POST.get('due_time')

        start_date = request.POST.get('start_date')
        text = request.POST.get('text')
        duration = request.POST.get('duration')
        end_date=request.POST.get('end_date')

        story_point =request.POST.get('story_point')

        task_relevance = request.POST.get('relevance')
        task_id = request.POST.get('task_id')
        relevance_type = request.POST.get('relevance_type')

        if end_date == '':
            end_date = now_date
        if start_date == '':
            start_date = now_date


        task_start_date = datetime.strptime(start_date,'%Y/%m/%d %H:%M')
        task_end_date = datetime.strptime(end_date,'%Y/%m/%d %H:%M')

        duration_timestamip= int(time.mktime(time.strptime(end_date,'%Y/%m/%d %H:%M'))) - int(time.mktime(time.strptime(start_date,'%Y/%m/%d %H:%M')))
        duration = duration_timestamip / 86400

        if duration == 0:
            duration = 1
        type = Type.objects.get(id=task_type)
        component = Component.objects.get(id=component)
        priority = Priority.objects.get(id=priority)
        version = Versions.objects.get(id=version)
        milestone = Milestone.objects.get(id=milestone)
        creator = User.objects.get(username=user_now)
        owner_project = Project.objects.get(id=url)
        if task_image is not None:
            image = task_image.name.split('.')[-1]
        else:
            image = None

        #检测属主是否存在，只添加存在的属主
        if owner.split(',') is not None and len(owner)>0:
            task_owners = ''
            for task_owner in owner.split(','):
                if User.objects.filter(username=task_owner):
                    task_owners = task_owners + task_owner + ','
            owner_list=list(task_owners)
            if len(owner_list)>0:
                owner_list.pop()
            owner = "".join(owner_list)

        #获取最后一个显示id
        task_num = Taskorder.objects.filter(owner_project=project_archive,parent=parent_id).count()
        if task_num == 0:
            display_id = '%s-%s'%(Taskorder.objects.get(id=parent_id).display_id,1)
        else:
            display_id = '%s-%s' % (Taskorder.objects.get(id=parent_id).display_id,task_num+1)

        if summary is not None and len(summary)>0:

            if image == 'tiff':
                errors.append('您上传的图片web不支持显示')
            elif start_date is not None and len(start_date)>0:
                if Taskorder.objects.get(id=parent_id).parent != 0:
                    parent = Taskorder.objects.get(id=parent_id).parent
                    task_num = Taskorder.objects.filter(owner_project=project_archive, parent=parent).count()
                    if task_num == 0:
                        display_id = '%s-%s' % (Taskorder.objects.get(id=parent).display_id, 1)
                    else:
                        display_id = '%s-%s' % (Taskorder.objects.get(id=parent).display_id, task_num + 1)

                    create_task = Taskorder.objects.create(summary=summary, creator=creator, description=description, type=type,
                                            milestone=milestone, reporter=user_now,
                                            component=component, priority=priority, task_image=task_image, owner=owner,
                                            version=version, display_id=display_id,
                                            status=statuss[0], end_date=task_end_date, owner_project=owner_project,
                                            start_date=task_start_date, duration=duration, parent=parent
                                            , predict_start_date=task_start_date, predict_duration=duration,
                                            predict_end_date=task_end_date)


                    if story_point is not None and len(story_point) > 0:
                        Taskorder.objects.filter(id=create_task.id).update(storypoint=story_point)


                else:
                    create_task = Taskorder.objects.create(summary=summary, creator=creator, description=description,
                                                           type=type, milestone=milestone, reporter=user_now,
                                                           component=component, priority=priority,
                                                           task_image=task_image, owner=owner, version=version,
                                                           display_id=display_id,
                                                           status=statuss[0], owner_project=owner_project,
                                                           end_date=task_end_date, start_date=task_start_date,
                                                           duration=duration, parent=parent_id
                                                           , predict_start_date=task_start_date,
                                                           predict_duration=duration,
                                                           predict_end_date=task_end_date)

                    if story_point is not None and len(story_point) > 0:
                        Taskorder.objects.filter(id=create_task.id).update(storypoint=story_point)


                id = Taskorder.objects.filter(creator=user_now).order_by('-id')[0].id

                #任务单关联
                if task_relevance == 'task_relevance':
                    if task_id is not None and len(task_id)>0:
                        Gantt_links.objects.create(source=id,target=task_id,type=relevance_type)


                return HttpResponseRedirect('/%s/task/%s'%(url,id),locals())
            else:
                errors.append('请输入任务起始时间')
        else:
            errors.append('请输入任务单概述')
    return render_to_response('create_task.html',locals())



@checkCdkey
@login_required
@views_permission
def roadmap(request,*args,**kwargs):              #里程碑
    project_archive = kwargs['project']  #项目归档判断

    url = kwargs['project_id']

    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    #if User.objects.get(username=user_now).is_superuser:
    #    admin = True

    milestone_id_all = []

    project_type = project_archive.project_type
    milestones = project_type.milestone.all()
    prioritys = project_type.task_priority.all()
    statuss = project_type.task_status.all()
    components = project_type.task_component.all()
    types = project_type.task_type.all()
    versions = project_type.task_version.all()

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    for milestone_name in milestones:
        milestone_id_all.append(milestone_name.id)

    all = []
    for milestone_id in milestone_id_all:
        milestone = Milestone.objects.get(id=milestone_id)
        allnum = len(Taskorder.objects.filter(owner_project=url,milestone=milestone))
        closenum = len(Taskorder.objects.filter(owner_project=url,status=statuss.order_by('-value')[0],milestone=milestone))
        description = milestone.description
        due_time = milestone.due
        status = milestone.milestone_status

        now_time = time.time()
        due_time_timestamp = time.mktime(due_time.timetuple())
        remaining_timestamp = int(due_time_timestamp - now_time)
        if remaining_timestamp >2419200:
            remaining_time = "%d月"%(remaining_timestamp / 2592000)
        elif remaining_timestamp < 2419200:
            remaining_time = "%d周"%(remaining_timestamp / 604800)
        elif remaining_timestamp < 604800:
            remaining_time = "%d天"%(remaining_timestamp / 86400)

        undone = allnum - closenum
        if allnum == 0:
            percent = 0
        else:
            percent = int(float(closenum) / allnum *100)
        all.append({'name':milestone.name,'percent':percent,'status':status,'allnum':allnum,'closenum':closenum,'undone':undone,'description':description,'due_time':due_time,'now_time':now_time,'remaining_time':remaining_time})
    return render_to_response('roadmap.html',locals())


@checkCdkey
@login_required
@views_permission
def personal_settings(request,*args,**kwargs): #个人设置
    url = kwargs['project_id']
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    personal_information = User.objects.get(username=user_now)

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    if request.method == 'POST':
        name = request.POST.get('personal_name')
        email = request.POST.get('email')
        head_portrait = request.FILES.get('head_portrait')
        gender = request.POST.get('gender')
        position = request.POST.get('position')
        address = request.POST.get('address')
        phone = request.POST.get('phone')



        if User.objects.filter(email = email).exclude(username=user_now).count() >= 1:
            error = '您输入的邮箱已经存在'
            return render_to_response('personal_settings.html', locals())
        elif email is not None and len(email)>0:
            if head_portrait is not None and len(head_portrait)>0:
                head_portrait_delete = os.path.join(MEDIA_ROOT,str(user_head_portrait)).replace('\\','/')

                try:
                    os.remove(head_portrait_delete)  #删除用户之前的头像
                except:
                    pass
                personal_information.head_portrait=head_portrait
                personal_information.save()

                User.objects.filter(username=user_now).update(name=name,email=email,
                                                              gender=gender,position=position,address=address,phone=phone)
                return HttpResponseRedirect('/personal_settings/')
            else:
                User.objects.filter(username=user_now).update(name=name,email=email,
                                                              gender=gender,position=position,address=address,phone=phone)
                return HttpResponseRedirect('/personal_settings/')
        else:
            error = '邮箱不可为空'
            return render_to_response('personal_settings.html', locals())

    return render_to_response('personal_settings.html',locals())


@checkCdkey
@login_required
@views_permission
def report(request,*args,**kwargs):
    url=kwargs['project_id']
    project_archive = kwargs['project']  #项目归档判断
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    project_type = project_archive.project_type
    milestones = project_type.milestone.all()
    prioritys = project_type.task_priority.all()
    statuss = project_type.task_status.all()
    components = project_type.task_component.all()
    types = project_type.task_type.all()
    versions = project_type.task_version.all()


    tasks=Taskorder.objects.filter(owner_project=project_archive)
    if request.method=="POST":
        judge=request.POST.get('judge')
        if judge=="task_select":
            owner_select=request.POST.get('owner_select')
            select_condition = request.POST.getlist('select_status')
            select_conditions = []
            for status_id in select_condition:
                select_conditions.append(int(status_id))
            if len(select_condition)>0 and len(owner_select)>0:
                tasks = Taskorder.objects.filter(owner_project=url,status__in=select_condition,owner__contains=owner_select).order_by('priority')
            elif len(select_condition)>0:
                tasks =Taskorder.objects.filter(owner_project=url,status__in=select_condition).order_by('priority')
            elif owner_select is not None and len(owner_select)>0:
                tasks = Taskorder.objects.filter(owner_project=url,owner__contains=owner_select).order_by('priority')
            else:
                tasks = Taskorder.objects.filter(owner_project=url).order_by('priority')
    return render_to_response('report.html',locals())

def dynamic_loading_kanban(task_list,present_tasks):            #2016/09/26
    '看板动态加载时去重操作'
    if present_tasks:
        for task_id in present_tasks:
            try:
                task_list.remove(Taskorder.objects.get(id=task_id))
            except:
                pass


def count_task_progress(task_object,sort_object,statuss):       #2016/09/26
    '计算任务单进度'
    child_complate_num = Taskorder.objects.filter(parent=task_object.id, status=statuss[len(statuss) - 1]).count()
    parent_num = Taskorder.objects.filter(parent=task_object.id).count()

    if parent_num > 0:
        if child_complate_num == 0:
            now_progress = 0
        else:
            now_progress = child_complate_num / float(parent_num) * 100

        if task_object.status == statuss[len(statuss) - 1]:
            now_progress = 100
    else:
        now_use_day_num = (time.time() - time.mktime(
            time.strptime(str(task_object.start_date).split('+')[0].split('.')[0],
                          '%Y-%m-%d %H:%M:%S'))) / 86400
        now_duration = task_object.duration
        if task_object.duration == 0:
            now_duration = 1
        now_progress = (now_use_day_num / now_duration) * 100
        if sort_object == statuss[0]:
            now_predict_duration = task_object.predict_duration
            if now_predict_duration == 0:
                now_predict_duration = 1
            now_progress = now_progress = (now_use_day_num / now_predict_duration) * 100
        if sort_object == statuss[len(statuss) - 1]:
            now_progress = 100

    return now_progress

def catch_kanban_Thumbnails(task_object,now_progress,task_list_new,project_archive):   #2016/09/26
    '抓取看板任务单缩略图'
    try:
        task_image = \
        Attachment_image.objects.filter(owner=task_object, owner_project=project_archive).order_by('-time')[0]
        task_list_new.append({'task': task_object, 'task_image': task_image.url, 'now_progress': now_progress})
    except:
        if task_object.task_image:
            task_list_new.append({'task': task_object, 'task_image': task_object.task_image, 'now_progress': now_progress})
        else:
            task_list_new.append({'task': task_object, 'task_image': False, 'now_progress': now_progress})
    return  task_list_new


def data_filter(search_content):
    search_content = search_content
    search_list = search_content.split(',',1)
    search_dict = {}
    if len(search_list)>=2:
        user_key = search_list[0]
        content_key = search_list[1]
        user_list = User.objects.filter(username__icontains=user_key)
        if user_list.exists():
            search_dict.setdefault('user_list',user_list)
            search_dict.setdefault('content', content_key)
            search_dict.setdefault('judge', 'two')
        else:
            search_dict.setdefault('user_list', False)
            search_dict.setdefault('content', False)
            search_dict.setdefault('judge', False)
    else:
        user_list = User.objects.filter(username__icontains=search_content)
        if user_list.exists():
            search_dict.setdefault('user_list',user_list)
            search_dict.setdefault('content', search_content)
            search_dict.setdefault('judge', 'one')
        else:
            search_dict.setdefault('user_list', False)
            search_dict.setdefault('content', search_content)
            search_dict.setdefault('judge', 'one')
    return search_dict


@checkCdkey
@login_required
@views_permission
def kanban(request, *args, **kwargs):  # 看版
    project_archive = kwargs['project']  # 项目归档判断
    url = kwargs['project_id']
    staff_user = kwargs['staff_user']
    staff_all_per = kwargs['staff_all_per']
    user_now = request.session.get('USERNAME', False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    loading_num = 5

    user = User.objects.get(username=user_now)  # 查询用户所在任务团队的项目  fanqi
    user_owner_team = user.task_team_set.all().order_by('-id')
    project_list = []
    for i in user_owner_team:
        project_name = Project.objects.get(id=i.owner_project)
        project_list.append(project_name)

    for project in Project.objects.all().order_by('-id'):
        project_home_permission = Permission.objects.get(project_id=project.id, view_name='project_index')  # 项目首页权限
        if project_home_permission in staff_all_per or staff_user.is_superuser == True or staff_user == project.creator:
            project_list.append(project)
    all_projects = list(set(project_list))
    project_del = Project.objects.get(id=url)
    try:
        all_projects.remove(project_del)
    except:
        pass

    project_type = project_archive.project_type
    milestones = project_type.milestone.all()
    prioritys = project_type.task_priority.all()
    statuss = project_type.task_status.all()
    components = project_type.task_component.all()
    types = project_type.task_type.all()
    versions = project_type.task_version.all()



    sort_dict = {'milestone':milestones,'priority':prioritys,'status':statuss,'component':components,'type':types,'versions':versions}
    sort_list = [{'name':'milestone','name_cn':'里程碑'},{'name':'priority','name_cn':'优先级'},{'name':'status','name_cn':'状态'},
                 {'name': 'component', 'name_cn': '组件'},{'name':'type','name_cn':'类型'},{'name':'versions','name_cn':'版本'},]

    try:
        present_tasks = kwargs['present_tasks']
        present_tasks = present_tasks.split(',')[0:-1]
    except:
        present_tasks = False

    if request.method == 'POST':
        judge = request.POST.get('judge')

        if judge=="copy_task":  #复制任务
            selected_project_id = request.POST.get('selected_project')
            if selected_project_id is None:
                return HttpResponseRedirect('/%s/kanban/' % url, locals())
            project = Project.objects.get(id=selected_project_id)
            task_id = request.POST.get('task_id')
            task = task = Taskorder.objects.get(id=task_id)

            project_type = project.project_type
            milestones = project_type.milestone.all()
            prioritys = project_type.task_priority.all()
            statuss = project_type.task_status.all()
            components = project_type.task_component.all()
            types = project_type.task_type.all()
            versions = project_type.task_version.all()

            milestone = project_type.milestone.filter(owner_project=selected_project_id, default=True)[0]
            priority = project_type.task_priority.filter(owner_project=selected_project_id, default=True)[0]
            component = project_type.task_component.filter(owner_project=selected_project_id, default=True)[0]
            type = project_type.task_type.filter(owner_project=selected_project_id, default=True)[0]
            version = project_type.task_version.filter(owner_project=selected_project_id, default=True)[0]


            status = statuss[0]


            task_num = Taskorder.objects.filter(owner_project=project_archive).count()
            if task_num == 0:
                display_id = 1
            else:
                display_id_list = []
                for task_objects in Taskorder.objects.filter(owner_project=project, parent=0):
                    display_id_list.append(int(task_objects.display_id))
                display_id_list.sort()
                display_id = display_id_list[-1] + 1

            if int(task.parent) != 0:
                parent_task_object = create_task(request,task=Taskorder.objects.get(id=task.parent), project=project, project_archive=project_archive,display_id=display_id,parent=0)
                task_number = 0

                for task_child in Taskorder.objects.filter(owner_project=project_archive,parent=Taskorder.objects.get(id=task.parent).id):

                    task_number += 1
                    child_display_id = '%s-%s' % (parent_task_object.display_id, task_number)
                    create_task(request,task=task_child, project=project, project_archive=project_archive,display_id=child_display_id,parent=parent_task_object.id)

            else:
                parent_task_object = create_task(request,task=task, project=project, project_archive=project_archive,display_id=display_id, parent=0)

                task_number = 0

                for task_child in Taskorder.objects.filter(owner_project=project_archive,parent=task.id):
                    task_number += 1
                    child_display_id = '%s-%s' % (parent_task_object.display_id, task_number)
                    create_task(request,task=task_child, project=project, project_archive=project_archive,display_id=child_display_id,parent=parent_task_object.id)

            #TaskList.objects.create(title=list_name,onwer_task=owner)
            return HttpResponseRedirect('/%s/kanban/'%project.id,locals())



        if judge == "move_task":  # 移动任务
            selected_project_id = request.POST.get('selected_project')
            if selected_project_id is None:
                return HttpResponseRedirect('/%s/kanban/' % url, locals())
            project = Project.objects.get(id=selected_project_id)
            task_id = request.POST.get('task_id')
            task = task = Taskorder.objects.get(id=task_id)

            project_type = project.project_type
            milestones = project_type.milestone.all()
            prioritys = project_type.task_priority.all()
            statuss = project_type.task_status.all()
            components = project_type.task_component.all()
            types = project_type.task_type.all()
            versions = project_type.task_version.all()

            milestone = project_type.milestone.filter(owner_project=selected_project_id, default=True)[0]

            priority = project_type.task_priority.filter(owner_project=selected_project_id, default=True)[0]
            component = project_type.task_component.filter(owner_project=selected_project_id, default=True)[0]
            type = project_type.task_type.filter(owner_project=selected_project_id, default=True)[0]
            version = project_type.task_version.filter(owner_project=selected_project_id, default=True)[0]


            status = statuss[0]


            task_num = Taskorder.objects.filter(owner_project=project).count()



            if task_num == 0:
                task_display_id = 1
            else:
                display_id_list = []
                for task_objects in Taskorder.objects.filter(owner_project=project, parent=0):
                    display_id_list.append(int(task_objects.display_id))
                display_id_list.sort()
                task_display_id = display_id_list[-1] + 1
                #task_display_id = int(Taskorder.objects.filter(owner_project=project, parent=0).order_by('-display_id')[0].display_id) + 1


            #print task_display_id

            if int(task.parent) != 0:
                parent_task = Taskorder.objects.get(owner_project=project_archive,id=task.parent)

                movetask(request,parenttask=parent_task,project_archive=project_archive,project=project)

            else:
                parent_task = Taskorder.objects.get(owner_project=project_archive, id=task.id)

                movetask(request,parenttask=parent_task,project_archive=project_archive,project=project)
            return HttpResponseRedirect('/%s/kanban/'%project.id,locals())

    if request.method == 'GET':
        #judge = request.GET.get('judge')
        #user_name = request.GET.get('user_name')
        search_content = request.GET.get('search_content')
        sort_name = request.GET.get('sort_name')


        try:
            member_id = kwargs['member_id']
            try:
                search_content = User.objects.get(id=member_id).username
            except:
                username_error = True
                return render_to_response('kanban_2.html', locals())
        except:
            pass

        if not sort_name:
            sort_name = 'status'
            status_id_names = []
            for status in statuss:
                status_id_names.append('drag-%s' % status.id)
        else:
            try:
                status_id_names = []
                for status in sort_dict[sort_name]:
                    status_id_names.append('drag-%s' % status.id)
            except:
                sortname_error = True
                return render_to_response('kanban_2.html', locals())




        if search_content:
            search_dict = data_filter(search_content)
            judge = search_dict['judge']
            user_list = search_dict['user_list']
            content = search_dict['content']

            kanbans = []
            more_data = 0
            for sort_object in sort_dict[sort_name]:
                if judge == 'one':
                    if user_list:
                        for user_name in user_list:
                            owner_kanban = sort_object.taskorder_set.filter(owner__contains=user_name).order_by('-id')
                            creator_kanban = sort_object.taskorder_set.filter(creator=User.objects.get(username=user_name)).order_by('-id')
                            reporter_kanban = sort_object.taskorder_set.filter(reporter=user_name).order_by('-id')
                            task_list_user = list(set(list(owner_kanban) + list(creator_kanban) + list(reporter_kanban)))
                            task_list_user += []
                    else:
                        task_list_user = []
                    summary = sort_object.taskorder_set.filter(summary__icontains=content).order_by('-id')
                    description = sort_object.taskorder_set.filter(description__icontains=content).order_by('-id')
                    task_list_content = list(set(list(summary) + list(description)))
                    task_list = list(set(task_list_user+task_list_content))
                elif judge == 'two':
                    for user_name in user_list:
                        s_owner_kanban = sort_object.taskorder_set.filter(owner__contains=user_name,summary__icontains=content).order_by('-id')
                        s_creator_kanban = sort_object.taskorder_set.filter(creator=User.objects.get(username=user_name), summary__icontains=content).order_by('-id')
                        s_reporter_kanban = sort_object.taskorder_set.filter(reporter=user_name,summary__icontains=content).order_by('-id')
                        d_owner_kanban = sort_object.taskorder_set.filter(owner__contains=user_name,description__icontains=content).order_by('-id')
                        d_creator_kanban = sort_object.taskorder_set.filter(creator=User.objects.get(username=user_name),description__icontains=content).order_by('-id')
                        d_reporter_kanban = sort_object.taskorder_set.filter(reporter=user_name,description__icontains=content).order_by('-id')
                        task_list = list(set(list(s_owner_kanban) + list(s_creator_kanban) + list(s_reporter_kanban) + list(d_owner_kanban) + list(d_creator_kanban) + list(d_reporter_kanban)))
                        task_list += []
                    task_list = list(set(task_list))
                else:
                    username_error=True
                    return render_to_response('kanban_2.html', locals())
                dynamic_loading_kanban(task_list, present_tasks)
                if len(task_list) > loading_num:
                    more_data += 1
                else:
                    pass

                task_list_new = []
                for task_object in task_list[0:loading_num]:
                    now_progress = count_task_progress(task_object, sort_object, statuss)
                    task_list_new = catch_kanban_Thumbnails(task_object, now_progress, task_list_new,
                                                            project_archive)
                if present_tasks:
                    if len(task_list[0:loading_num]) > 0:
                        kanbans.append({'status': sort_object, 'task': task_list_new})
                else:
                    kanbans.append({'status': sort_object, 'task': task_list_new})

            if present_tasks:
                if len(kanbans) == 0:
                    return HttpResponse('False')
                else:
                    return render_to_response('loading_kanban.html', locals())

            if more_data != 0:
                more_data = True
            else:
                more_data = False
            return render_to_response('kanban_2.html', locals())

        else:                                                          #sort_name

            kanbans = []
            more_data = 0
            for sort_object in sort_dict[sort_name]:
                try:
                    if list(statuss).index(sort_object) == 0:

                        task_list = sort_object.taskorder_set.all().order_by('priority')
                    else:

                        task_list = sort_object.taskorder_set.all().order_by('-id')
                except:

                    task_list = sort_object.taskorder_set.all().order_by('-id')

                if present_tasks:
                    try:
                        if list(statuss).index(sort_object) == 0:

                            task_list = sort_object.taskorder_set.all().order_by('priority')
                        else:
                            pass
                    except:
                        pass

                task_list = list(task_list)
                dynamic_loading_kanban(task_list, present_tasks)
                if len(task_list) > loading_num:
                    more_data += 1
                else:
                    pass

                task_list_new = []
                for task_object in task_list[0:loading_num]:
                    now_progress = count_task_progress(task_object,sort_object,statuss)
                    task_list_new = catch_kanban_Thumbnails(task_object, now_progress, task_list_new,project_archive)
                if present_tasks:
                    if len(task_list[0:loading_num]) > 0:
                        kanbans.append({'status': sort_object, 'task': task_list_new})
                else:
                    kanbans.append({'status': sort_object, 'task': task_list_new})

            if present_tasks:
                if len(kanbans) == 0 :
                    return HttpResponse('False')
                else:
                    return render_to_response('loading_kanban.html', locals())

            if more_data!=0:
                more_data = True
            else:
                more_data = False
            return render_to_response('kanban_2.html', locals())



@checkCdkey
@login_required
@views_permission
def updateTaskForProject(request,*args,**kwargs):
    project_archive = kwargs['project']  # 项目归档判断
    url = kwargs['project_id']
    staff_user = kwargs['staff_user']
    staff_all_per = kwargs['staff_all_per']

    user_now = request.session.get('USERNAME', False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
    if request.method=='POST':
        projectId=request.POST.get('projectId')
        taskId=request.POST.get('taskId')

        project=Project.objects.get(id=projectId)
        task = Taskorder.objects.get(id=taskId)

        milestone = Milestone.objects.get(owner_project=projectId, default=True)
        priority = Priority.objects.get(owner_project=projectId, default=True)
        status = Status.objects.filter(owner_project=projectId)[0]
        component = Component.objects.get(owner_project=projectId, default=True)
        type = Type.objects.get(owner_project=projectId, default=True)
        version = Versions.objects.get(owner_project=projectId, default=True)

        task1 = Taskorder.objects.filter(owner_project=project,parent=0)
        task_num = task1.count()
        global display_id
        if task_num == 0:
            display_id = 1
        else:
            if len(task1) > 0:
                display_id = int(task1.order_by('-display_id')[0].display_id) + 1
        #修改一级任务单/父级
        Taskorder.objects.filter(id=taskId,parent=0).update(owner_project=project, type=type, milestone=milestone,priority=priority, status=status, component=component,version=version,display_id=display_id)

        if len(Taskorder.objects.filter(parent=taskId))>0:
            Taskorder.objects.filter(parent=taskId).update(owner_project=project,type=type,milestone=milestone,priority=priority,status=status,component=component,version=version)#修改子任务单
            child_num = 1
            for task in Taskorder.objects.filter(parent=taskId):
                if len(Attachment_file.objects.filter(owner=task)) > 0:
                    Attachment_file.objects.filter(owner=task).update(owner_project=project)
                if len(Attachment_video.objects.filter(owner=task)) > 0:
                    Attachment_video.objects.filter(owner=task).update(owner_project=project)
                if len(Attachment_image.objects.filter(owner=task)) > 0:
                    Attachment_image.objects.filter(owner=task).update(owner_project=project)
                if len(Comment.objects.filter(owner_task=task)) > 0:
                    Comment.objects.filter(owner_task=task).update(owner_project=project)
                if len(Repository.objects.filter(owner_task=task)) > 0:
                    Repository.objects.filter(owner_task=task).update(project_id=project)
                if len(Message.objects.filter(owner_task=task)) > 0:
                    Message.objects.filter(owner_task=task).update(owner_project=project)

                child_id = str(display_id) + '-' + str(child_num)
                Taskorder.objects.filter(id=task.id).update(display_id=child_id)
                child_num = child_num + 1

            return HttpResponseRedirect('/%s/kanban/' % url, locals())
        if len(Attachment_file.objects.filter(owner=task))>0:
            Attachment_file.objects.filter(owner=task).update(owner_project=project)
        if len(Attachment_video.objects.filter(owner=task))>0:
            Attachment_video.objects.filter(owner=task).update(owner_project=project)
        if len(Attachment_image.objects.filter(owner=task))>0:
            Attachment_image.objects.filter(owner=task).update(owner_project=project)
        if len(Comment.objects.filter(owner_task=task))>0:
            Comment.objects.filter(owner_task=task).update(owner_project=project)
        if len(Repository.objects.filter(owner_task=task))>0:
            Repository.objects.filter(owner_task=task).update(project_id=project)
        if len(Message.objects.filter(owner_task=task))>0:
            Message.objects.filter(owner_task=task).update(owner_project=project)
    return HttpResponseRedirect('/%s/kanban/' % url, locals())


#模块导入太乱 尽量不要用*导入
#代码书写不规范