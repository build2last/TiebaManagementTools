#coding=utf-8
from tiebalib import *
import os
import sqlite3
def fill_thread_content(thread):
    post_list = get_thread_content(thread)
    all_post_list.append(post_list)

def get_all_post():
    threads = get_thread_list(pn=end_pn)
    threads_pool = []
    for thread in threads:
        t = threading.Thread(target=fill_thread_content, args=(thread["tid"],))
        threads_pool.append(t)
    for t in threads_pool:
        while threading.active_count() > 5:#同时开动线程数
            pass
        t.start()
    while threading.active_count() > 1:
        if (time.time() - t1) > 300:
            break
def write_database():
    for thread_post in all_post_list:
        for dic in thread_post:
            if dic["author"]:
                cursor.execute('insert into post (pid, tid, author, date, floor, text) values (?, ?, ?, ?, ?, ?)',(str(dic["pid"]) ,dic["tid"] ,dic["author"] ,dic["date"] ,str(dic["floor"]) ,dic["text"] ))


config('',"")
if not os.path.exists('tiebadatabase.db'):
    conn = sqlite3.connect('tiebadatabase.db')
    conn.text_factory = str
    cursor = conn.cursor()
    cursor.execute('create table post (pid, tid, author, date, floor, text)')
    cursor.close()
    conn.commit()
    conn.close()
end_pn = 50
loop_times = 0
while True:
    t1 = time.time()
    all_post_list = []
    get_tbs()
    get_all_post()
    conn = sqlite3.connect('tiebadatabase.db')
    conn.text_factory = str
    cursor = conn.cursor()
    write_database()
    cursor.close()
    conn.commit()
    conn.close()

    loop_times += 1 #循环加1
    print u'完成{0}次循环'.format(loop_times)
    print u'扫描到了pn={0}'.format(end_pn)
    end_pn += 50
    time.sleep(5)