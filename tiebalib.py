#coding=utf-8
import time
import requests
import re
import json
import threading
import functools
import signal
from bs4 import BeautifulSoup
from html.parser import HTMLParser
import jieba
import math
class data:
    login_url = ''
    is_tomb = 0
    delete_thread_url = 'http://tieba.baidu.com/f/commit/thread/delete'
    delete_post_url_1 = 'http://tieba.baidu.com/f/commit/post/delete'
    delete_post_url_2 = 'http://tieba.baidu.com/bawu2/postaudit/audit'
    aim_tieba = ''
    block_id = 'http://tieba.baidu.com/pmc/blockid'
    tbs_url = "http://tieba.baidu.com/dc/common/tbs"
    cookie = ''
    tbs = ''
    UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'
    fid = ''
    threads = []
    post = []
    deleted = 0
    deleted_post = 0
    error_times = 0
    blocked = 0
def check_similarity(text1,text2):
    raw1 = jieba.cut(text1)
    raw2 = jieba.cut(text2)
    dict1 ={}
    dict2 ={}
    for i in raw1:
        if i not in dict1:
            dict1[i] = 1
        else:
            dict1[i] +=1
    for i in raw2:
        if i not in dict2:
            dict2[i] = 1
        else:
            dict2[i] +=1
    for i in dict1:
        if i not in dict2:
            dict2[i] = 0
    for i in dict2:
        if i not in dict1:
            dict1[i] = 0
    mod1 = mod2 = 0
    for i in dict1:
        mod1 += dict1[i]*dict1[i]
    for i in dict2:
        mod2 += dict2[i]*dict2[i]
    dot_product = 0
    for i in dict1:
        dot_product += dict1[i]*dict2[i]
    if mod1*mod2 != 0:
        return dot_product/(math.sqrt(mod1*mod2))
    else:return 0

def timeout(seconds, error_message = 'Function call timed out'):
   def decorated(func):
       def _handle_timeout(signum, frame):
          # raise TimeoutError(error_message)
          pass
       def wrapper(*args, **kwargs):
           signal.signal(signal.SIGALRM, _handle_timeout)
           signal.alarm(seconds)
           try:
               result = func(*args, **kwargs)
           finally:
               signal.alarm(0)
           return result
       return functools.wraps(func)(wrapper)
   return decorated

def config(aim_tieba,cookie):#读配置函数
    data.cookie = cookie
    data.aim_tieba = aim_tieba
    data.fid = get_fid()
    data.tbs = get_tbs()

def get_tbs():
    headers = {'Cookie':data.cookie,'User-Agent':data.UA}
    content_json = json.loads(requests.get(data.tbs_url, headers = headers).text)
    data.tbs = content_json['tbs']
    return content_json['tbs']
def get_fid():
    headers = {'Cookie':data.cookie,'User-Agent':data.UA}
    content = requests.get('http://tieba.baidu.com/'+data.aim_tieba, headers = headers).text
    fid = re.search('"forum_id":(.*?),', content).group(1)
    return fid

def delete_thread(tid):#管理工具删整贴接口
    url = data.delete_post_url_2
    headers = {'Cookie':data.cookie,'User-Agent':data.UA}
    payload = {'ie':'utf8','kw':data.aim_tieba,'tids[]':tid,'flag':2,'type':0}
    r = requests.post(url, data = payload, headers = headers)
    status = json.loads(r.text)
    if status['no'] == 0:
        data.deleted += 1
    else:
        data.error_times +=1
    print(r.text)
    return status

def delete_post(tid, pid):#批量删帖接口
    url = data.delete_post_url_2
    headers = {'Cookie':data.cookie,'User-Agent':data.UA}
    payload = {'ie':'utf8','kw':data.aim_tieba,'tids[]':tid,'pids[]':pid,'flag':2,'type':1}
    r = requests.post(url, data = payload, headers = headers)
    status = json.loads(r.text)
    if status['no'] == 0:
        data.deleted_post += 1
    else:
        data.error_times += 1
    print(r.text)
    return status

def blockid(tid, pid, username,reason="恶意刷屏、挖坟、水贴、抢楼、带节奏等，给予封禁处罚"):#封禁
    url = data.block_id
    headers = {'Cookie':data.cookie,'User-Agent':data.UA}
    payload = {'day':1,'ie':'utf8','fid':data.fid,'tbs':data.tbs, 'user_name[]':username,'pid[]':pid,'reason':reason}
    r = requests.post(url, data = payload, headers = headers)
    status = json.loads(r.text)
    if status['errno'] == 0:
        data.blocked += 1
    else:
        data.error_times += 1
    print(r.text)
    return status

def get_thread_list(pn=0):
    threads = []
    payload = {'pn':pn, 'ie':'utf-8'}
    headers = {'Cookie':data.cookie,'User-Agent':data.UA}
    content = requests.get('http://tieba.baidu.com/f?kw='+data.aim_tieba,params=payload, headers=headers).text
    raws = re.findall('thread_list clearfix([\s\S]*?)创建时间"',content)
    for raw in raws:
        tid = re.findall('href="/p/(.*?)"', raw)
        pid = re.findall('&quot;first_post_id&quot;:(.*?),', raw)
        topic = re.findall('href="/p/.*?" title="([\s\S]*?)"', raw)
        author = re.findall('title="主题作者: (.*?)"', raw)
        reply_num = re.findall('&quot;reply_num&quot;:(.*?),',raw)
        #print(len(tid),len(pid),len(topic),len(author),len(reply_num))
        if len(tid)==len(pid)==len(topic)==len(author)==len(reply_num):
            dic = {"tid":tid[0],"pid":pid[0],"topic":topic[0],"author":author[0],"reply_num":reply_num[0]}
            threads.append(dic)
        else:
            print('error')
            print(raw)
    return threads
def get_page_content(thread, pn):
    url = 'http://tieba.baidu.com/p/'+thread
    payload = {'pn':pn}
    headers = {'Cookie':data.cookie,'User-Agent':data.UA}
    return requests.get(url, params=payload, headers=headers).text
def process_html(post_info,tid):
    dic = {}
    t = json.loads(post_info[0])
    dic["text"] = post_info[1].strip()#去除开头空格
    dic["tid"] = tid
    dic["author"] = t["author"]["user_name"]
    dic["uid"] = t["author"]["user_id"]
    dic["sex"] = t["author"]["user_sex"]
    dic["exp"] = t["author"]["cur_score"]
    dic["level"] = t["author"]["level_id"]
    dic["pid"] = t["content"]["post_id"]
    dic["date"] = t["content"]["date"]
    dic["voice"] = t["content"]["ptype"]
    dic["floor"] = t["content"]["post_no"]
    dic["device"] = t["content"]["open_type"]
    dic["comment_num"] = t["content"]["comment_num"]
    dic["sign"] = post_info[2]
    dic["imgs"] = post_info[3]
    dic["smiley"] = post_info[4]
    return dic
def get_thread_last_content(thread,pn=9999999):
    t2 = time.time()
    last_page = []
    content =BeautifulSoup(get_page_content(thread,pn),'lxml')
    author_info = content.find_all("div",class_=re.compile("l_post"))
    texts = content.find_all("div",class_=re.compile("j_d_post_content"))
    if not texts:
        return 0
    if len(author_info) == len(texts):
        posts = zip(texts,author_info)
    else:return 0
    for post_raw in posts:
        text = ''
        for i in post_raw[0].strings:
            text = text+i
        user_sign = post_raw[0].parent.parent.parent.find_all(class_='j_user_sign')
        if user_sign:
            user_sign = user_sign[0]["src"]
        imgs = post_raw[0].find_all("img",class_="BDE_Image")
        img = []
        if imgs:
            for i in imgs:
                img.append(i["src"])
        smileys = post_raw[0].find_all('img',class_='BDE_Smiley')
        smiley = []
        if smileys:
            for i in smileys:
                smiley.append(i["src"])
        post_info = [post_raw[1]["data-field"],text,user_sign,img,smiley]
        post = process_html(post_info, thread)
        last_page.append(post)
    return last_page

def check_same_author(threads):
    pthreads = threads[:]
    handled = []
    temp =[]
    while len(pthreads)>=1:
        i = 0
        author = pthreads[0]["author"]
        temp.append(pthreads[0])
        pthreads.pop(0)
        while i<len(pthreads):
            if pthreads[i]["author"]==author:
                temp.append(pthreads[i])
                pthreads.pop(0)
            i = i + 1
            temp.sort(key=lambda x:int(x["reply_num"]))
        if temp[0]["author"] != '----':
            handled.append(temp)
        temp=[]
    return handled
