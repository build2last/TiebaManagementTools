#coding=utf-8
from tiebalib import *
import gevent
from gevent import monkey
from gevent.pool import Pool as GPool
from gevent import Greenlet
import threading
import json
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from keywords import *
from author_keywords import *
import os
import sys
def restart_program(signum,stack):
    with open('./error_log', 'a') as file:
        file.write('timeout '+str(time.strftime("%b %d %Y %H:%M:%S %Z"))+'\n')
    python = sys.executable
    os.execl(python, python, * sys.argv)

def write_log(post,kind,reason):
    with open('./'+kind,'a') as file:
        file.write(str(time.strftime("%b %d %Y %H:%M:%S %Z"))+' ')
        file.write(reason+' '+str(post)+'\n')

def handle_post(post):
#    if post["level"]<=2 and post["imgs"]:
#        delete_post(post["tid"],post["pid"])
#        with open('./delete_log', 'a') as file:
#            file.write(str(time.strftime("%b %d %Y %H:%M:%S %Z"))+' ')
#            file.write('未关注小号 带图'+str(post)+'\n')
    global new_post
    new_post += 1
    for dic in keywords:
        if re.search(dic["keyword"],post["text"]) and dic["post"]:
            if dic["delete"]:
                delete_post(post["tid"],post["pid"])
                write_log(post,'delete_log',dic["keyword"])
            if dic["block"]:
                blockid(post["tid"],post["pid"],post["author"])
                write_log(post,'block_log',dic["keyword"])
    for dic in author_keywords:
        if re.search(dic["author"],post["author"]):
            if dic["delete"]:
                delete_post(post["tid"],post["pid"])
                write_log(post,'delete_log',dic["author"])
            if dic["block"]:
                blockid(post["tid"],post["pid"],post["author"])
                write_log(post,'block_log',dic["auhtor"])
#    if post["sign"] and post["level"]==1 and level_sign_block:
#        if post["floor"] != 1:
#            delete_post(post["tid"],post["pid"])
#            blockid(post["tid"],post["pid"],post["author"])
#            with open('./block_log', 'a') as file:
#                file.write(str(time.strftime("%b %d %Y %H:%M:%S %Z"))+' ')
#                file.write('一级带签名'+str(post)+'\n')
#            with open('./delete_log', 'a') as file:
#                file.write(str(time.strftime("%b %d %Y %H:%M:%S %Z"))+' ')
#                file.write('一级带签名'+str(post)+'\n')
#            with open('./sign_log', 'a') as file:
#                file.write(post["sign"]+'\n')

def handle_topic(thread):
    if thread["tid"] in thread_cache:
        return
    global new_thread
    new_thread += 1
    if thread == {}:
        return

    for dic in keywords:
        if re.search(dic["keyword"],thread["topic"]) and dic["topic"]:
            if dic["delete"]:
                delete_thread(thread["tid"])
                write_log(thread,'delete_log',dic["keyword"])
            if dic["block"]:
                blockid(thread["tid"],thread["pid"],thread["author"])
                write_log(thread,'block_log',dic["keyword"])

    for dic in author_keywords:
        if re.search(dic["author"],thread["author"]):
            if dic["delete"]:
                delete_thread(thread["tid"])
                write_log(thread,'delete_log',dic["author"])
            if dic["block"]:
                blockid(thread["tid"],thread["pid"],thread["author"])
                write_log(thread,'block_log',dic["author"])
    thread_cache.append(thread["tid"])
def check_last_content(tid):
    t = get_thread_last_content(tid)
    if t:
        for post in t:
            if post["pid"] not in post_cache:
                handle_post(post)
                post_cache.append(post["pid"])
    if type(t) != type(0) and len(t)>=2:
        time1 = time.mktime(time.strptime(t[-1]["date"],'%Y-%m-%d %H:%M'))
        time2 = time.mktime(time.strptime(t[-2]["date"],'%Y-%m-%d %H:%M'))
        if (time1 - time2) >= 2592000:
            if (abs(time1-time.time())<=86400):
                data.is_tomb+=1
                if block_dig_tomb:
                    blockid(t[-1]["tid"],t[-1]["pid"],t[-1]['author'],reason='挖坟')
                    write_log(t[-1],'block_log','挖坟')
                    delete_post(t[-1]["tid"],t[-1]["pid"])
                    write_log(t[-1],'delete_log','挖坟')

config(,)
post_cache = []
thread_cache = []
new_post = new_thread = 0
error = 0
loop_times = 0
level_sign_block = 1
block_dig_tomb = 0
is_same_author = 1
intel_delete = 1
block_loops = 0
pool_size = 2
monkey.patch_all()
punct = set(u''':!),.:;?]}¢'"、。〉》」』】〕〗〞︰︱︳﹐､﹒
﹔﹕﹖﹗﹚﹜﹞！），．：；？｜｝︴︶︸︺︼︾﹀﹂﹄﹏､～￠
々‖•·ˇˉ―--′’”([{£¥'"‵〈《「『【〔〖（［｛￡￥〝︵︷︹︻
︽︿﹁﹃﹙﹛﹝（｛“‘-—_… ''')

filterpunt = lambda s: ''.join(filter(lambda x: x not in punct, s))
while True:
    new_post = new_thread = 0
    data.is_tomb = 0
    #data.is_tomb = 4#镇压mode
    deleted = data.deleted+data.deleted_post
    t1 = time.time()
    signal.signal(signal.SIGALRM,restart_program)
    signal.alarm(30)
    try:
        thread_list = get_thread_list()
        [handle_topic(i) for i in thread_list]
        repetition_list = check_same_author(thread_list)
        if is_same_author:
            for i in repetition_list:
                if len(i)>=4:
                    tid =[]
                    pid =[]
                    print(len(i))
                    print(i)
                    for post in i[:-1]:
                        if (int(post["tid"]) >= int(thread_list[-1]["tid"])):
                            tid.append(post["tid"])
                            pid.append(post["pid"])
                    delete_post(tid,pid)
                    write_log(i,'delete_log','超过四贴')
                                    #raise Exception('find same author!')


        pool = GPool(pool_size)
        [pool.spawn(check_last_content, i["tid"]) for i in thread_list[0:15]]
        pool.join()

        if data.is_tomb >= 3:
            block_dig_tomb =1
            pool_size = 15
            is_same_author = 0
            intel_delete = 0
            if block_loops != 1:
                block_loops = 1
        if block_loops >= 1:
            block_loops += 1
        if block_loops>=300:
            block_dig_tomb = 0
            pool_size = 2
            is_sanme_author = 1
            intel_delete = 0

        if intel_delete:
            pthreads = thread_list[:]
            i = 0
            delete_num = 0
            while i<len(pthreads):
                for t in pthreads[i+1:]:
                    text1 = filterpunt(t["topic"])
                    text2 = filterpunt(pthreads[i]["topic"])
                    simi = check_similarity(text1,text2)
#                    if simi >= 0.43 and simi <0.6:
#                        if int(t["reply_num"])>int(pthreads[i]["reply_num"]):
#                            if (int(t["tid"]) >= int(thread_list[-1]["tid"])):
#                                delete_post(t["tid"],t["pid"])
#                                delete_num +=1
#                                write_log(t,'delete_log','相似度介于0.4-0.6')
#
#                        if int(t["reply_num"])<int(pthreads[i]["reply_num"]):
#                            if (int(pthreads[i]["tid"]) >= int(thread_list[-1]["tid"])):
#                                delete_post(pthreads[i]["tid"],pthreads[i]["pid"])
#                                delete_num +=1
#                                write_log(t,'delete_log','相似度介于0.4-0.6')
#                        print(t,'\n',pthreads[i])
#                        print('similaity rate:',simi)
                    if simi >= 0.6:
                        if int(t["reply_num"])>int(pthreads[i]["reply_num"]):
                            delete_post(t["tid"],t["pid"])
                            delete_num +=1
                        else:
                            delete_post(pthreads[i]["tid"],pthreads[i]["pid"])
                            delete_num +=1
                            write_log(t,'delete_log','相似度超过0.6')
                        print(t,'\n',pthreads[i])
                        print('similaity rate:',simi)
                i = i + 1
            if delete_num>=8:
                break


    except KeyboardInterrupt as e:break
#    except Exception as e:
#        with open('./error_log','a') as file:
#            file.write(str(e)+' '+str(time.strftime("%b %d %Y %H:%M:%S %Z")) + '\n')
#        error += 1
#        time.sleep(10)
    finally:
        pass
    loop_times += 1
    if data.deleted+data.deleted_post - deleted >=20:
        break
    print('完成{0}次循环'.format(loop_times))
    print('已删{0}贴'.format(data.deleted+data.deleted_post))
    print('已封{0}贴'.format(data.blocked))
    print('失败{0}贴'.format(data.error_times))
    print('错误{0}个'.format(error))
    print('用时:{0}s'.format(time.time()-t1))
    print('新贴{0}个,新回复{1}个'.format(new_thread,new_post-new_thread))
