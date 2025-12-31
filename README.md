# Astrbot_Plugins_JMPlugins
## 简介
你是否有经历发现神秘id兴冲冲点进去发现是地雷的情景？你是否经历过在外面水群看到一堆神秘id，却不敢点开查看的情景？
别担心！这款插件正是为你解决这些难题而生！只需提供JMid，它能帮你快速查询神秘作品的详细信息，甚至还能选择是否发送封面图，

## 依赖
运行本插件需要安装以下包：  
[jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python)  
[PicImageSearch](https://github.com/kitUIN/PicImageSearch)  
apscheduler(定时任务需要使用)  
十分感谢以上作者提供的API。

根据项目里面的requirements.txt安装依赖包。

**此外，本插件依赖于Aiocqhttp，仅测试过NapCat可以正常使用，请窒息。**

## 注意（25/6/9添加）
qq疑似会检测转发的聊天记录里面的图片，有时候被检测到了会导致聊天记录发不出去而导致插件报错。  
尝试了嵌套转发，但是还是会被检测到。  
目前的解决办法是：古法防gank：  
在图片的上面添加一长条白色的图，来隐藏图片的真实信息。这样被检测到的记录就会变小。  


## 定时任务（自动发送指定key下前一段时间内更新的本）
插件会定时用配置好的key去查询，并且过滤到上一次查询的时间段内更新的本。    
该功能默认不开启，建议完全懂得如何使用的用户才考虑开启。  
开启方式：在插件控制台里面，修改**定时任务 (schdule_task)**为1，然后保存。  
之后，在想要定时发送的群/私人聊天里面输入/JM addlist添加到列表中。之后，定时任务就会自动执行。  
目前默认的参数为：定时任务执行时间：8:00 20:00 如有需要修改，请自行到源文件中找到以下代码，并且根据提示修改。  
```angular2html
# 设置定时任务
        # 初始化 APScheduler
        if schdule_task != 0:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.add_job(
                self.send_daily_comics_task,
                CronTrigger(hour='8,20', minute=0), #修改为你需要的时间
                # IntervalTrigger(minutes=5),
                id='daily_comic_send'
            )
            self.scheduler.start()
            print("APScheduler 定时任务已启动")

```

查询key：找到module.json这个文件，找到以下内容，修改key为你自己的key。当前默认key为blue archive。  
```angular2html
{
  "static_config": {
    "query_key": "ブルーアーカイブ", #修改为你自己想要查询的key
    "unified_msg": [
    ]
  },
  "dynamic_config": {
    "last_album_id": "1230010"
  }
}
```

由于当前没找到好的方法，当前定时任务发送的聊天记录当中的botid是空的，如要使用请自行修改。  
找到以下代码，根据提示修改:  
```angular2html
 async def send_daily_comics_task(self):
        """每日推送任务"""
        try:
            print(f"开始执行每日任务: {datetime.now()}")
            await send_daily_message(self.context, "修改为你的botid")
            print(f"每日任务执行完成: {datetime.now()}")
        except Exception as e:
            print(f"定时任务执行失败: {e}")
            import traceback
            traceback.print_exc()
```



## 功能
1 .根据id查询作品  
指令格式： /JM id id/包含神秘id的句子 (f)  
   比如: /JM id 114514 f 加上f/F会发送后面的图片，否则默认只发送封面。    
        /JM id 114抽出了51个彩，其中只有4个new F **(句子>10个字并且当中不能有换行)**

输出：若选择开启发送图片，则会返回作品的名字，作者，以及该章节当中的前img_count张图片。若选择关闭发送图片，则会返回作品的名字，作者。  
**请根据自己具体使用情况选择开启或者关闭发送图片的功能**  
**img_count默认为8张，可以在插件控制台修改**  

2.根据key查询作品   
指令格式:/JM key keyword (albumid，不输的话默认为0) (Y/y，不输入的话默认不发送)  
eg: /JM key 碧蓝档案 1230000 Y
    /JM key 碧蓝档案 1230000 
输出：搜索到的相关作品的名字以及id，并且过滤掉比albumid参数小的作品（不输入albumid默认不过滤）  
如果参数二输入为Y或者y，就会自动下载查询到的比albumid大的作品封面，最大发送**cover_count**个封面。不输入的话默认不发送.  
**cover_count默认为15张，可以在插件控制台修改**  


3.Rand随机功能  
指令格式： /JM rand  
输出：随机返回一个神秘作品的名字，作者和id。  
在每次调用前会用关键词查询"**blue archive**"获取最先(?)的代码作为最大值，然后再执行randint获取id。  

4.搜索功能（使用的ASCii2d）  
指令格式： 回复指定图片，输入/search,即可开始搜索。  
输出：搜索到类似图片的url。  

*搜索的结果不是特别准确，请谨慎使用.*

5 .查询月/周/日排行榜  
指令格式： /JM rank m/w/d/a
输出：按照浏览次数排序的月/周/日/总排行榜。

6.权限管理  
指令格式： /JM promote/demote group/user groupid/userid    
例如：/JM promote group 123456789 

**注意：该指令仅限管理员使用，需要在Astrbot控制台给对应账号添加为管理员才能使用。**

此外，权限管理也包括定时任务的管理。  
添加到队列当中： /JM addlist    
从队列中删除： /JM removelist  

7 .黑名单功能
指令格式： /JM block add/remove albumid  
例如:  /JM block add 350234

8.查看历史记录  
指令格式： /JM history  
输出：包含所有查询过的神秘作品的id和名字，以json格式输出。  

## 版本问题：
若您的astrbot版本比较早，可能没有此函数：
```
datadir = StarTools.get_data_dir("astrbot_plugins_JMPlugins")
```
如果遇到这种情况，请根据以下方法进行修改：
把这段代码
```
#导入包
from astrbot.api.star import StarTools
# 加载白名单
global datadir, white_list_path, history_json_path,blocklist_path,block_list,favorite_path
datadir = StarTools.get_data_dir("astrbot_plugins_JMPlugins")
print(datadir)
white_list_path = os.path.join(datadir, "white_list.json")
history_json_path = os.path.join(datadir, "history.json")
blocklist_path = os.path.join(datadir, "block_list.json")
favorite_path=os.path.join(datadir, "favorite.json")
```
当中的导入删除，以及下面的加载白名单代码修改为
```
global white_list_path, history_json_path,blocklist_path,favorite_path
white_list_path="./data/plugins/astrbot_plugins_JMPlugins/white_list.json"
history_json_path="./data/plugins/astrbot_plugins_JMPlugins/history.json"  
blocklist_path="./data/plugins/astrbot_plugins_JMPlugins/block_list.json"
favorite_path="./data/plugins/astrbot_plugins_JMPlugins/favorite.json"
```

## 使用
1. 下载本插件，将本插件放入plugins文件夹下。

2. 如果是大陆地区使用，需要修改一下代理的设置：    
找到文件夹里面的option.yml，找到下面这一行选项
``` 
proxies: {
       https: 127.0.0.1:12334 //修改为自己设置好的代理
      }
```
将代理设置替换为自己已经开启的代理设置。

3.安装[jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python)和[PicImageSearch](https://github.com/kitUIN/PicImageSearch)两个包。

4.设置是否发送封面以及cd时间。
目前插件默认是关闭发送封面，以及cd为15秒。若需要更改，在插件控制台里面修改即可。

*注意:cd是全局共享的，我懒得分群写:)*

5.为开用的私聊qq号或者群聊添加权限。
指令： /JM promote/demote group/user groupid/userid  
    例如：/JM promote group 123456789   
    例如：/JM demote user 123456789  

*为了预防内鬼写的白名单:(*

## 插件示例
不带封面查询id：
![1.jpg](1.jpg)
带封面查询id：
![2.jpg](2.jpg)
搜索功能：
![3.jpg](3.jpg)

## 声明
**使用本插件可能导致qq被击毙，请谨慎使用或者查询是否有内鬼再使用。**  
**使用本插件可能导致qq被击毙，请谨慎使用或者查询是否有内鬼再使用。**  
**使用本插件可能导致qq被击毙，请谨慎使用或者查询是否有内鬼再使用。**  


## 更新：
2025/5/10
添加了控制台修改配置的功能。  
修复了无法正常发送历史记录json的问题。

2025/5/25
添加了黑名单功能，防止有人查出董卓恶心大伙

2025/6/4
添加搜索具体本子的时候显示tags

2025/6/9
添加古法防gank法:  
在图片的上面添加一长条白色的图，来隐藏图片的真实信息。这样被检测到的记录就会变小。  

2025/8/9
添加了收藏功能，主要是给我自己用的:)
使用方法：
/JM f add/remove id
/JM f show a(后面随便输入个什么，我懒得分成多个指令组了，就写在一起了，所以也需要两个参数)

2025/8/17
修改了查询本子的指令关键词，由name->id  
修改原因：一开始本插件只是通过jmid查询名字，但是后续加上了tag和封面显示，name关键词显得不合适，所以修改为id。  

修改了原本只发送封面图的功能，现在会发送前img_count张图片。  
修改原因：防止封面欺诈，添加了个类似预览的功能。 

2025/8/30
为搜索key的指令添加了参数，默认为0，即不进行过滤。如果添加了参数，就过滤掉id比参数小的作品名。  

2025/9/9
为搜索key的指令添加了第二个参数，默认不发送，填入Y/y就会一次性把搜索到的符合条件的作品的封面也发送出来，默认最大发送15个封面。  

2025/9/12
添加了定时任务功能，自动查询key并且发送前一次查询之间更新的作品。  

2025/9/28
修改了定时任务的部分逻辑，上次查询到的id最前面的一个本子在下一次不会再出现，如果没有更新新的本子，会有独特的回复语句。    
原因： 疑似tx在一次发送定时任务中检测到咸湿给夹了之后，下一次发送如果还有那个图会增大再次被夹的几率。同时，如果一段时间没有更新新的本子，然后最后更新的那个本子有点恶心人，定时任务会一直发送这个本子，一直恶心你，因此修改为不再出现。  


2025/10/9
为定时任务添加了过滤tag功能，当检测到含有指定tag时候，该作品的图片不会发送，转而使用一张已经制作好的图片来替换。  
若想要替换过滤的tag，请自行修改main当中的该数组：  
```angular2html
#判断tag里面是否有需要过滤的内容：  
filter_tag = ['NTR','猎奇','寝取']

#该代码段在整个py文件的几乎最下方
```

2025/12/31
修改了定时任务的执行逻辑，在一个时间段内本子更新大于max_count的时候，前max——count个本子会下载封面并且发送，而后面的只会发送id跟标题，如果全部都下载封面跟tag的话，查询时间就会太久了，故修改成这样。  
此外，填在了在定时任务发送失败的时候，会额外发送一版不带图片的纯文字的记录，这样应该不会再给tx给夹了。  
**定时任务里面过滤的tag内容后续有时间再修改一下逻辑。**  

