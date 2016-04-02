#coding=utf-8
import gevent
from gevent import monkey
from tiebalib import *
import threading
import json
from keywords import *
from author_keywords import *
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')
def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)
def handle_post(post):
    for dic in keywords:
        if re.search(dic["keyword"],post["text"]) and dic["post"]:
            if dic["delete"]:
                delete_post(post["tid"],post["pid"])
                with open('./delete_log', 'a') as file:
                    file.write(str(dic)+str(post)+'\n')
            if dic["block"]:
                blockid(post["tid"],post["pid"],post["author"])
                with open('./block_log', 'a') as file:
                    file.write(str(dic)+str(post)+'\n')
    for dic in author_keywords:
        if re.search(dic["author"],post["author"]):
            if dic["delete"]:
                delete_post(post["tid"],post["pid"])
                with open('./delete_log', 'a') as file:
                    file.write(str(dic)+str(post)+'\n')
            if dic["block"]:
                blockid(post["tid"],post["pid"],post["author"])
                with open('./block_log', 'a') as file:
                    file.write(str(dic)+str(post)+'\n')

def handle_topic(thread):
    for dic in keywords:
        if re.search(dic["keyword"],thread["topic"]) and dic["topic"]:
            if dic["delete"]:
                delete_thread(thread["tid"])
                with open('./delete_log', 'a') as file:
                    file.write(str(dic)+str(thread)+'\n')
            if dic["block"]:
                blockid(thread["tid"],thread["pid"],thread["author"])
                with open('./block_log', 'a') as file:
                    file.write(str(dic)+str(thread)+'\n')

    for dic in author_keywords:
        if re.search(dic["author"],thread["author"]):
            if thread["delete"]:
                delete_thread(thread["tid"])
                with open('./delete_log', 'a') as file:
                    file.write(str(dic)+str(thread)+'\n')
            if thread["block"]:
                blockid(thread["tid"],thread["pid"])
                with open('./block_log', 'a') as file:
                    file.write(str(dic)+str(thread)+'\n')
def check_last_content(tid):
    t = get_thread_last_content(tid)
    if t:
        for i in t:
            handle_post(i)


config('','')
loop_times = 0
while True:
    post_list = []
    t1 = time.time()
    try:
        thread_list = get_thread_list()
        pool = ThreadPool(15)
        pool.map(handle_topic,thread_list[0:15])
        pool.close()
        pool.join()
        for i in thread_list[0:15]:
            post_list.append(i["tid"])
        jobs = [gevent.spawn(check_last_content, tid) for tid in post_list]
        gevent.joinall(jobs)
    except KeyboardInterrupt as e:break
    except:pass
    finally:
        pass
    loop_times += 1

    print u'完成{0}次循环'.format(loop_times)
    print u'已删{0}贴'.format(data.deleted+data.deleted_post)
    print u'已封{0}贴'.format(data.blocked)
    print u'失败{0}贴'.format(data.error_times)
    print u'用时:{0}s'.format(time.time()-t1)

