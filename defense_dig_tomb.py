#coding=utf-8
from tiebalib import *

@timeout(2)
def get_thread_list():
    threads = []
    regular_expression = '{&quot;author_name&quot;.*?</a>'
    content = requests.get('http://tieba.baidu.com/f?kw='+data.aim_tieba+'&ie=utf-8').content
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
@timeout(2)
def get_and_block_thread_last_content(thread):
    t2 = time.time()
    post_list = []
    content = get_page_content(thread,'9999999')
    topic = ''
    if re.search('core_title_txt(.*?)title="(.*?)"', content):
        topic = re.search('core_title_txt(.*?)title="(.*?)"', content).group(2)
    separate = re.findall('l_post j_l_post l_post_bright[\s\S]*?\'({[\s\S]*?})\'[\s\S]*?d_post_content j_d_post_content  clearfix">(.*?)</div>', content)
    if not separate:#偶见最后一页无内容
        return
    separate = separate[-2:]
    post_info = process_html(separate, thread)
    for i in post_info:
        i["topic"] = topic
        print i["date"]
    post_list += post_info
    if len(post_list) >= 2:
        time1 = time.mktime(time.strptime(post_list[0]["date"],'%Y-%m-%d %H:%M'))
        time2 = time.mktime(time.strptime(post_list[1]["date"],'%Y-%m-%d %H:%M'))
        if (time2 - time1) >2592000:#最后回复相差秒数
            blockid(post_list[1]["tid"],post_list[1]["pid"],post_list[1]["author"],reason="挖坟")
            delete_post(post_list[1]["tid"],post_list[1]["pid"])

config('','')
while True:
    threads = get_thread_list()
    threads = threads[3:25]
    for i in threads:
        try:
            get_and_block_thread_last_content(i["tid"])
        finally:
            pass
    time.sleep(2)
