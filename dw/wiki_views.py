#coding:utf-8
from django.shortcuts import render,render_to_response,HttpResponseRedirect,HttpResponse
from models import *
import re,os
from darkwarrior.settings import MEDIA_ROOT
from decorator import checkCdkey, is_login, login_required, views_permission


@checkCdkey
@is_login
@views_permission
def create_wiki(request,*args,**kwargs):     #创建维基
    project_archive = kwargs['project']  #项目归档判断

    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    url = project_id
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait


    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    #project_name = Project.objects.get(project_url = url).project_name
    if request.method == 'POST':
        title = request.POST.get('title',None)
        content = request.POST.get('content',None)
        if content is not None and title is not None and len(title.strip())>0 and len(content.strip())>0:
            wiki = Wiki(creator=staff_user,content=content,title=title,owner=project)
            wiki.save()
            return HttpResponseRedirect('/'+project_id+'/wiki_index',locals())
        else:

            error = '标题跟内容都为必填项！'
            return render_to_response('wiki/create_wiki.html',locals())
    return render_to_response('wiki/create_wiki.html',locals())

@checkCdkey
@is_login
@views_permission
def wiki(request,*args,**kwargs):      #维基首页
    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    url = project_id
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    #project_name = Project.objects.get(owner_proejct = project_id).project_name
    try:
        content = Wiki.objects.filter(owner = project).order_by('-id')[0]

        return render_to_response('wiki/wiki.html',locals())

    except:
       # wiki = Wiki.objects.filter(owner = project)
       # if len(wiki)>0:
       #     notice = '还没有设置wiki/项目首页！'
       # else:
            notice_no = '还没有创建维基！'


    return render_to_response('wiki/wiki.html',locals())

@checkCdkey
@is_login
@views_permission
def wiki_index(request,*args,**kwargs):  #维基索引
    project_archive = kwargs['project']  #项目归档判断

    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    wiki_id = kwargs['wiki_id']
    url = project_id
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait
  
    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None
    
    wikis = Wiki.objects.filter(owner=project).order_by('-id')
    return render_to_response('wiki/wiki_index.html',locals())



@checkCdkey
@is_login
@views_permission
def wiki_content(request,*args,**kwargs):  #维基内容
    project_archive = kwargs['project']  #项目归档判断

    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    wiki_id = kwargs['wiki_id']
    url = project_id
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None
    #print type(wiki_id)

    try:
      content = Wiki.objects.get(owner=project,id=wiki_id)
      attachment_images = Wiki_attachment_image.objects.filter(owner=Wiki.objects.get(id=wiki_id),owner_project=project).order_by('-id')
      attachment_files = Wiki_attachment_file.objects.filter(owner=Wiki.objects.get(id=wiki_id),owner_project=project).order_by('-id')
      attachment_videos = Wiki_attachment_video.objects.filter(owner=Wiki.objects.get(id=wiki_id),owner_project=project).order_by('-id')
      file_num = attachment_images.count()+attachment_files.count()+attachment_videos.count()
      if request.method == 'POST':
        judge = request.POST.get('judge')
        if judge == 'attachment_remove':#附件维基删除
            image_url_delete = request.POST.get('img_url_delete')
            file_url_delete = request.POST.get('file_url_delete')
            video_url_delete = request.POST.get('video_url_delete')

            if image_url_delete is not None and len(image_url_delete)>0:
                Wiki_attachment_image.objects.filter(url=image_url_delete).delete()
                image_delete_url = os.path.join(MEDIA_ROOT,image_url_delete).replace('\\','/')
                if os.path.isfile(image_delete_url):
                    os.remove(image_delete_url)
                return HttpResponseRedirect('/'+project_id+'/wiki_index/'+wiki_id+'/')
            elif video_url_delete is not None and len(video_url_delete)>0:
                Wiki_attachment_video.objects.filter(url=video_url_delete).delete()
                video_delete_url = os.path.join(MEDIA_ROOT,video_url_delete).replace('\\','/')
                if os.path.isfile(video_delete_url):
                    os.remove(video_delete_url)
                return HttpResponseRedirect('/'+project_id+'/wiki_index/'+wiki_id+'/')
            elif file_url_delete is not None and len(file_url_delete)>0:
                Wiki_attachment_file.objects.filter(url=file_url_delete).delete()
                file_delete_url = os.path.join(MEDIA_ROOT,file_url_delete).replace('\\','/')
                if os.path.isfile(file_delete_url):
                    os.remove(file_delete_url)
                return HttpResponseRedirect('/'+project_id+'/wiki_index/'+wiki_id+'/')  
             

      return render_to_response('wiki/wiki_content.html',locals())
    except:
        error = '您所找的wiki不存在！'

  
        return render_to_response('permission_notice.html',locals())

@checkCdkey
@is_login
@views_permission
def wiki_edit(request,*args,**kwargs):                 #编辑维基
    project_archive = kwargs['project']  #项目归档判断

    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    wiki_id = kwargs['wiki_id']
    url = project_id
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None


    try:
        wiki_title = Wiki.objects.get(owner=project,id=wiki_id).title
        wiki_content = Wiki.objects.get(owner=project,id=wiki_id).content
    except:
        error = '您要编辑的维基不存在！'
        return render_to_response('permission_notice.html',locals())

    #if staff_user !=Wiki.objects.get(id=wiki_id).creator:
         #error = '您没有编辑权限！'
         #return render_to_response('words/permission_notice.html',locals())



    if request.method == 'POST':
        title = request.POST.get('title',None)
        content = request.POST.get('content',None)
        if content is not None and title is not None and len(title.strip())>0 and len(content.strip())>0:
            Wiki.objects.filter(id=wiki_id).update(content=content,title=title)
            #wiki.save()
            #if True ==Wiki.objects.get(id=wiki_id).is_wiki_home:
            #return HttpResponseRedirect('/'+project_id)
            #else:
            return HttpResponseRedirect('/'+project_id+'/wiki_index/'+wiki_id,locals())
        else:

            error = '标题跟内容都为必填项！'
            return render_to_response('wiki/wiki_edit.html',locals())




    return render_to_response('wiki/wiki_edit.html',locals())


@checkCdkey
@is_login
@views_permission
def wiki_delete(request,*args,**kwargs):                 #删除维基
    project_archive = kwargs['project']  #项目归档判断

    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    wiki_id = kwargs['wiki_id']
    url = project_id
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    try:
        wiki = Wiki.objects.get(owner=project,id=wiki_id)
        #if wiki.is_wiki_home:
        #    notice = '您现在删除的维基是项目首页！'
    except:
        error = '您要删除的维基不存在！'
        return render_to_response('permission_notice.html',locals())

    if request.method =="POST":
        Wiki.objects.get(owner=project,id=wiki_id).delete()
        return HttpResponseRedirect('/'+project_id+'/wiki_index/')





    return render_to_response('wiki/wiki_delete.html',locals())


@checkCdkey
@is_login
@views_permission
def wiki_attachment_upload(request,*args,**kwargs):                            #liuluyang 2016/08/09
    user = kwargs['user']
    staff_user = kwargs['staff_user']
    project_id = kwargs['project_id']
    project = kwargs['project']
    wiki_id = kwargs['wiki_id']
    url = project_id
    user_now = request.session.get('USERNAME',False)
    user_head_portrait = User.objects.get(username=user_now).head_portrait

    try:
        template = Template.objects.get(owner_project=url)
    except:
        template = None

    owner_project = Project.objects.get(id=url)
    author = User.objects.get(username=user_now)
    owner = Wiki.objects.get(id=wiki_id)
    if request.method == 'POST':
        file_url = request.FILES.get('file_url')
        #print file_url
        if file_url is not None:     #附件上传
                file_type = file_url.name.split('.')[-1]
                #print file_type
                image_format = ['bmp','pcx','gif','jpeg','jpg','tga','exif','fpx','svg','psd','cdr','pcd','dxf','ufo','eps','ai','png','hdri','raw','ico']
                video_format = ['rm','rmvb','mp4','mov','mtv','dat','wmv','avi','3gp','amv','dmv']
                file_format = ['doc','txt','html','bmp','rar','zip','exe','pdf','xls']
                if file_type in image_format:
                    if Wiki_attachment_image.objects.filter(name=file_url.name,author=author,owner=owner,owner_project=owner_project).exists():
                        return HttpResponseRedirect('/')  #lly 2016/10/14
                    wiki_image = Wiki_attachment_image.objects.create(url=file_url,name=file_url.name,author=staff_user,
                                                                      owner=Wiki.objects.get(id=wiki_id),owner_project=project)
                    return HttpResponseRedirect('/'+project_id+'/wiki_index/'+wiki_id+'/')
                elif file_type in video_format:
                    if Wiki_attachment_video.objects.filter(name=file_url.name,author=author,owner=owner,owner_project=owner_project).exists():
                        return HttpResponseRedirect('/')  #lly 2016/10/14
                    wiki_video = Wiki_attachment_video.objects.create(url=file_url,name=file_url.name,author=staff_user,
                                                                      owner=Wiki.objects.get(id=wiki_id),owner_project=project)
                    return HttpResponseRedirect('/'+project_id+'/wiki_index/'+wiki_id+'/')
                elif file_type in file_format:
                    if Wiki_attachment_file.objects.filter(name=file_url.name,author=author,owner=owner,owner_project=owner_project).exists():
                        return HttpResponseRedirect('/')  #lly 2016/10/14
                    wiki_file = Wiki_attachment_file.objects.create(url=file_url,name=file_url.name,author=staff_user,
                                                                      owner=Wiki.objects.get(id=wiki_id),owner_project=project)
                    return HttpResponseRedirect('/'+project_id+'/wiki_index/'+wiki_id+'/')
                else:
                    pass

    return render_to_response('wiki/attachment_upload.html',locals())
