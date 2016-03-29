#coding=utf-8
import time
import requests
import re
import json
import HTMLParser
import threading
import functools
import signal
class data:
    login_url = ''
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
    content_json = json.loads(requests.get(data.tbs_url, headers = headers).content)
    data.tbs = content_json['tbs']
    return content_json['tbs']

def get_fid():
    headers = {'Cookie':data.cookie,'User-Agent':data.UA}
    content = requests.get('http://tieba.baidu.com/'+data.aim_tieba, headers = headers).content
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
    print r.text
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
    print r.text
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
    print r.text
    return status

def get_thread_list(pn=0):
    threads = []
    regular_expression = '{&quot;author_name&quot;.*?</a>'
    payload = {'pn':pn, 'ie':'utf-8'}
    headers = {'Cookie':data.cookie,'User-Agent':data.UA}
    content = requests.get('http://tieba.baidu.com/f?kw='+data.aim_tieba,params=payload, headers=headers).content
    first_match = re.findall(regular_expression, content)
    for i in first_match:
        thread = {}
        tid = re.search('href="/p/(.*?)"', i).group(1)
        thread["tid"] = tid
        pid = re.search('&quot;first_post_id&quot;:(.*?),', i)
        if pid:
            pid = pid.group(1)
            thread["pid"] = pid
        else:
            thread["pid"] = '0'
        topic = re.search('" title="(.*?)" target', i)
        if topic:
            thread["topic"] = topic.group(1)
        author = re.search('&quot;author_name&quot;:&quot;(.*?)&quot;', i)
        if author:
            thread["author"] = author.group(1).decode('unicode_escape')
        reply_num = re.search('&quot;reply_num&quot;:(.*?),',i)
        if reply_num:
            thread["reply_num"] = reply_num.group(1)
        threads.append(thread)
    return threads

def get_page_content(thread, pn):
    url = 'http://tieba.baidu.com/p/'+thread
    payload = {'pn':pn}
    headers = {'Cookie':data.cookie,'User-Agent':data.UA}
    content = requests.get(url, params=payload, headers=headers).content
    return content
def process_html(content,tid):
    html_parser = HTMLParser.HTMLParser()
    processed = []
    for post_info in content:
        dic = {}
        t = json.loads(html_parser.unescape(post_info[0]))
        dic["text"] = post_info[1].strip()#去除开头空格
        dic["tid"] = tid
        dic["author"] = t["author"]["user_name"]
        dic["pid"] = t["content"]["post_id"]
        dic["date"] = t["content"]["date"]
        dic["floor"] = t["content"]["post_no"]
        dic["comment_num"] = t["content"]["comment_num"]
        processed.append(dic)
    return processed
def get_thread_content(thread):
    t2 = time.time()
    post_list = []
    all_page_number = '1'
    content_page_1 = get_page_content(thread,'1')#读取第一页
    search_pn = re.search('pn=(.*?)">尾页</a>', content_page_1)
    if search_pn:
        all_page_number = search_pn.group(1)#获取页数
    for pn in range(1,int(all_page_number)+1):
        content = get_page_content(thread, pn)
        separate = re.findall('l_post j_l_post l_post_bright[\s\S]*?\'({[\s\S]*?})\'[\s\S]*?d_post_content j_d_post_content  clearfix">(.*?)</div>', content)
        post_info = process_html(separate, thread)
        post_list += post_info
    return post_list

def get_thread_last_content(thread):
    t2 = time.time()
    post_list = []
    content = get_page_content(thread,'9999999')
    topic = ''
    if re.search('core_title_txt(.*?)title="(.*?)"', content):
        topic = re.search('core_title_txt(.*?)title="(.*?)"', content).group(2)
    separate = re.findall('l_post j_l_post l_post_bright[\s\S]*?\'({[\s\S]*?})\'[\s\S]*?d_post_content j_d_post_content  clearfix">(.*?)</div>', content)
    if not separate:#偶见最后一页无内容
        return
    separate = [separate[-1],]
    post_info = process_html(separate, thread)
    for i in post_info:
        i["topic"] = topic
    post_list += post_info
    return post_list

def image_check(keyword,url):
    url = 'http://image.baidu.com/n/pc_search?queryImageUrl='+url
    r = requests.get(url)   
    if re.search(keyword, r.content):
        return 1
    return 0
def image_filter(text):
    url = re.findall('http://imgsrc.baidu.com/forum/w%3D580/sign.*?\.jpg', text)
    return url
