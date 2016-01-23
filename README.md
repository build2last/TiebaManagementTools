# TiebaManagementTools
### 贴吧管理常用接口的整理和管理工具的实现

##tiebalib的使用方法
* 初始化:
```
from tiebalib import *  
config('目标贴吧','cookie')   
```
* 返回一个tbs值:
```
get_tbs()
```
* 返回目标贴吧的fid:
```
get_fid()
```
* 通过tid删帖:
```
delete_thread(tid) 
```
* 删除回复(需要对应回复的tid和pid)
```
delete_post(tid, pid)
```
* 封禁
```
blockid(tid, pid, username)
```
* #获取当前首页的贴子列表
```
get_thread_list()
```
返回一个list list内为50个dict 记录每个贴的作者名 发布时间 回复数 标题以及pid tid 
* 获取某一主题全部回复列表(不包括楼中楼) 返回list 每个回复以dict形式记录
```
get_thread_content(tid)
```
* 获取主题帖最后一个回复
```
get_thread_last_content(tid)
```
* 送入一个关键词和图片链接 通过百度识图判断是否符合关键字内容 
```
image_check(keyword,url)
```
* 贴吧图片链接过滤器 送入贴子内容 返回所有不包括表情图片链接  
```
image_filter(text)
```
