import os
import re
from datetime import datetime, timedelta
import random

from PicImageSearch import Ascii2D, Network, Google
from PicImageSearch.model import GoogleResponse
from apscheduler.triggers.interval import IntervalTrigger

from jmcomic import JmOption, JmAlbumDetail, JmHtmlClient, JmModuleConfig, JmApiClient, create_option_by_file, \
    JmSearchPage, JmPhotoDetail, JmImageDetail, JmCategoryPage, JmMagicConstants

import astrbot.api.event
from astrbot.api import event
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.core.message.components import Plain, Reply, File, Nodes
from astrbot.core.message.message_event_result import MessageChain

from astrbot.core.platform import MessageType
import json
import asyncio

from astrbot.core.star.filter.permission import PermissionType
from astrbot.api.star import StarTools

global last_Picture_time, Current_Picture_time, CoolDownTime, flag01, white_list_group, white_list_user, block_list,favor_list
global last_random_time, Current_random_time, flag02
global last_search_picture_time, Current_search_picture_time, flag03
global last_search_comic_time, Current_search_comic_time, flag04
global ispicture

global img_count
global cover_count

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger




# 定时任务需要的import
from .ScheduledTask import *


option_url = "./data/plugins/astrbot_plugins_JMPlugins/option.yml"

global white_list_path, history_json_path, datadir, blocklist_path,favorite_path


def check_is_6or7_digits(str):
    return bool(re.match(r'^\d{1,7}$', str))


def get_number_from_str(str):
    num_list = re.findall(r'\d+', str)
    result_number = ""
    for i in range(len(num_list)):
        result_number += num_list[i]

    return result_number


global option

@register("JMPlugins", "orchidsziyou", "查询本子名字插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        global option, last_Picture_time, white_list_group, white_list_user, last_random_time, Current_random_time, flag02, last_search_picture_time, flag03, last_search_comic_time, Current_search_comic_time, flag04
        option = create_option_by_file(option_url)
        last_search_picture_time = 0
        last_Picture_time = 0
        last_random_time = 0
        last_search_comic_time = 0

        # 加载设置
        global ispicture, CoolDownTime,img_count,cover_count
        self.config = config
        CoolDownTime = self.config["CD_Time"]
        img_count = self.config["img_count"]
        cover_count=self.config["cover_count"]
        schdule_task=self.config["schdule_task"]
        if self.config["IsPicture"] >= 1:
            ispicture = True
        else:
            ispicture = False
        print(ispicture, CoolDownTime)

        # 设置定时任务
        # 初始化 APScheduler
        if schdule_task != 0:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.add_job(
                self.send_daily_comics_task,
                CronTrigger(hour='8,20', minute=0),
                # IntervalTrigger(minutes=5),
                id='daily_comic_send',
                misfire_grace_time=120, # 允许120秒的延迟容
                coalesce=True, # 合并错过的任务
                max_instances=1
            )
            self.scheduler.start()
            print("APScheduler 定时任务已启动")

        # 加载白名单
        global datadir, white_list_path, history_json_path, blocklist_path, block_list,favorite_path,favor_list
        datadir = StarTools.get_data_dir("astrbot_plugins_JMPlugins")
        print(datadir)
        white_list_path = os.path.join(datadir, "white_list.json")
        history_json_path = os.path.join(datadir, "history.json")
        blocklist_path = os.path.join(datadir, "block_list.json")
        favorite_path=os.path.join(datadir, "favorite.json")

        if not os.path.exists(white_list_path):
            with open(white_list_path, 'w') as file:
                json.dump({"groupIDs": [], "userIDs": []}, file)
        else:
            with open(white_list_path, 'r') as file:
                data = json.load(file)
                white_list_group = data["groupIDs"]
                white_list_user = data["userIDs"]

        if not os.path.exists(history_json_path):
            with open(history_json_path, 'w') as file:
                json.dump([], file)

        if not os.path.exists(blocklist_path):
            with open(blocklist_path, 'w') as file:
                json.dump({"albumID": []}, file)
        else:
            with open(blocklist_path, 'r') as file:
                data = json.load(file)
                block_list = data["albumID"]

        if not os.path.exists(favorite_path):
            with open(favorite_path, 'w') as file:
                json.dump({"albumID": []}, file)
        else:
            with open(favorite_path, 'r') as file:
                data = json.load(file)
                favor_list = data["albumID"]

    async def send_daily_comics_task(self):
        """每日推送任务"""
        try:
            print(f"开始执行每日任务: {datetime.now()}")
            await send_daily_message(self.context, "123321123")
            print(f"每日任务执行完成: {datetime.now()}")
        except Exception as e:
            print(f"定时任务执行失败: {e}")
            import traceback
            traceback.print_exc()

    @filter.command_group("JM")
    async def jm_command_group(self, event: AstrMessageEvent):
        ...

    @jm_command_group.command("id")
    async def jm_name_command(self, event: AstrMessageEvent, name: str,type:str="s"):
        global last_Picture_time, Current_Picture_time, flag01, Cover_tag, flag02,img_count
        Cover_tag = 0
        '''这是一个 搜索本子 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return
            Current_Picture_time = int(datetime.now().timestamp())
            time_diff_in_seconds = Current_Picture_time - last_Picture_time
            last_Picture_time = Current_Picture_time
            if time_diff_in_seconds < CoolDownTime:
                cd_time = CoolDownTime - time_diff_in_seconds
                if flag01 == 0:
                    flag01 += 1
                    yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
                else:
                    flag01 += 1
                return

            flag01 = 0

        if not check_is_6or7_digits(name):
            if len(name) < 10:
                yield event.plain_result("请输入正确的编号")
                return
            else:
                name = get_number_from_str(name)
                Cover_tag = 1
                if not check_is_6or7_digits(name):
                    yield event.plain_result("未检测到正确的编号")
                    return


        # 检测是否在黑名单中
        if name in block_list:
            yield event.plain_result("该本子已被屏蔽,请窒息")
            return

        yield event.plain_result("正在搜索中，请稍后")

        album = ''
        try:
            client = JmOption.copy_option(option).new_jm_client()
            page = client.search_site(search_query=name)
            album: JmAlbumDetail = page.single_album
        except:
            yield event.plain_result("未找到该本子")
            return

        # 检查tag里面是否有非H的tag
        nonH_tags = False
        if "非H" in album.tags:
            nonH_tags = True

        # 放入json当中
        data = []
        try:
            with open(history_json_path, "r") as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = []  # 如果文件不存在，创建一个空列表

        existing_ids = [item["id"] for item in data]

        if str(album.id) not in existing_ids:
            newdata = {
                "id": str(album.id),
                "data": {
                    "times": 1,
                    "names": album.name
                }
            }
            data.append(newdata)
            with open(history_json_path, "w") as json_file:
                json.dump(data, json_file)
        else:
            for item in data:
                if item["id"] == str(album.id):
                    item["data"]["times"] += 1
                    break
            with open(history_json_path, "w") as json_file:
                json.dump(data, json_file)

        # 判断是否发送图片还是只发送名字
        botid = event.get_self_id()
        from astrbot.api.message_components import Node, Plain, Image

        folder_path = './data/plugins/astrbot_plugins_JMPlugins/pic/'

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if ispicture:
            # 下载封面
            try:
                photo: JmPhotoDetail = album.getindex(0)
                photo01 = client.get_photo_detail(photo.photo_id, False)

                #下载封面和后面的几张图片
                if type.lower() == "f":
                    count = min(img_count, len(photo01))
                else:
                    count = 1
                # print(count)

                for i in range(count):
                    image: JmImageDetail = photo01[i]
                    if os.path.exists(os.path.join(folder_path, f'{i}.jpg')):
                        os.remove(os.path.join(folder_path, f'{i}.jpg'))
                    client.download_by_image_detail(image, os.path.join(folder_path, f'{i}.jpg'))

                if not nonH_tags :
                    #添加防gank
                    for i in range(count):
                        image_path= os.path.join(folder_path, f'{i}.jpg')
                        if os.path.exists(image_path):
                            from PIL import Image as ProcessImage
                            original_image = ProcessImage.open(image_path)
                            # 获取原始图片的宽度和高度
                            width, height = original_image.size
                            # 创建一张新的空白图片，大小为原图的宽度和五倍高度
                            new_image = ProcessImage.new('RGB', (width, height * 5), color=(255, 255, 255))
                            # 将原图粘贴到新图片的下半部分
                            new_image.paste(original_image, (0, height * 4))
                            # 保存最终结果
                            new_image.save(image_path)

                # if os.path.exists('./data/plugins/astrbot_plugins_JMPlugins/result.jpg'):
                #     os.remove('./data/plugins/astrbot_plugins_JMPlugins/result.jpg')
                # client.download_by_image_detail(image, './data/plugins/astrbot_plugins_JMPlugins/result.jpg')
                #
                # # 给图片添加防gank
                # if os.path.exists('./data/plugins/astrbot_plugins_JMPlugins/result.jpg'):
                #     from PIL import Image as ProcessImage
                #     original_image = ProcessImage.open('./data/plugins/astrbot_plugins_JMPlugins/result.jpg')
                #     # 获取原始图片的宽度和高度
                #     width, height = original_image.size
                #     # 创建一张新的空白图片，大小为原图的宽度和五倍高度
                #     new_image = ProcessImage.new('RGB', (width, height * 5), color=(255, 255, 255))
                #     # 将原图粘贴到新图片的下半部分
                #     new_image.paste(original_image, (0, height * 4))
                #     # 保存最终结果
                #     new_image.save('./data/plugins/astrbot_plugins_JMPlugins/result.jpg')

                # 发送图片
                all_nodes = []

                node = Node(
                    uin=botid,
                    name="仙人",
                    content=
                    [
                        Plain("...\n"),
                        Plain(f"id:{album.id}\n"),
                        Plain(f"本子名称：{album.name}\n"),
                        Plain(f"作者：{album.author}\n"),
                        Plain(f"只会发送前{img_count}张图片，剩余的自己去搜打撤")
                    ]
                )
                tag_node = Node(
                    uin=botid,
                    name="仙人",
                    content=[
                        Plain("...\n"),
                        Plain(f"tags：{album.tags}\n")
                    ]
                )
                all_nodes.append(node)
                all_nodes.append(tag_node)

                for i in range(count):
                    image_path= os.path.join(folder_path, f'{i}.jpg')
                    if os.path.exists(image_path):
                        picture_node = Node(
                            uin=botid,
                            name="仙人",
                            content=
                            [
                                Image.fromFileSystem(image_path)
                            ]
                        )
                        all_nodes.append(picture_node)

                resNode = Nodes(
                    nodes=all_nodes
                )

                # picture_node = Node(
                #     uin=botid,
                #     name="仙人",
                #     content=
                #     [
                #         Image.fromFileSystem("./data/plugins/astrbot_plugins_JMPlugins/result.jpg")
                #     ]
                # )
                # resNode = Nodes(
                #     nodes=[node, tag_node, picture_node]
                # )

                #如果图片发送失败，就只发送封面

                try:
                    yield event.chain_result([resNode])
                except Exception as e:
                    line_node= Node(
                        uin=botid,
                        name="仙人",
                        content=[
                            Plain("图片发送失败，只发送封面")
                        ]
                    )
                    node = Node(
                        uin=botid,
                        name="仙人",
                        content=
                        [
                            Plain("...\n"),
                            Plain(f"id:{album.id}\n"),
                            Plain(f"本子名称：{album.name}\n"),
                            Plain(f"作者：{album.author}\n"),
                            Plain(f"只会发送前{img_count}张图片，剩余的自己去搜打撤")
                        ]
                    )
                    tag_node = Node(
                        uin=botid,
                        name="仙人",
                        content=[
                            Plain("...\n"),
                            Plain(f"tags：{album.tags}\n")
                        ]
                    )
                    image_path_01 = os.path.join(folder_path, f'{0}.jpg')
                    surface_node = Node(
                        uin=botid,
                        name="仙人",
                        content=
                        [
                            Image.fromFileSystem(image_path_01)
                        ]
                    )
                    new_all_nodes = []
                    new_all_nodes.append(line_node)
                    new_all_nodes.append(node)
                    new_all_nodes.append(tag_node)
                    new_all_nodes.append(surface_node)
                    newresNode = Nodes(
                        nodes=new_all_nodes
                    )
                    yield event.chain_result([newresNode])

            except Exception as e:
                print(e)
                node = Node(
                    uin=botid,
                    name="仙人",
                    content=
                    [
                        Plain("...\n"),
                        Plain(f"id:{album.id}\n"),
                        Plain(f"本子名称：{album.name}\n"),
                        Plain(f"作者：{album.author}"),
                    ]
                )
                tag_node = Node(
                    uin=botid,
                    name="仙人",
                    content=[
                        Plain("...\n"),
                        Plain(f"tags：{album.tags}\n")
                    ]
                )
                RIP_node = Node(
                    uin=botid,
                    name="仙人",
                    content=
                    [
                        Plain("封面下载失败或者发送失败")
                    ]
                )
                resNode = Nodes(
                    nodes=[node, tag_node, RIP_node]
                )
                yield event.chain_result([resNode])

        else:
            # 只发送名字
            node = Node(
                uin=botid,
                name="仙人",
                content=
                [
                    Plain("...\n"),
                    Plain(f"id:{album.id}\n"),
                    Plain(f"本子名称：{album.name}\n"),
                    Plain(f"作者：{album.author}"),
                    Plain(f"tags：{album.tags}\n")
                ]
            )
            yield event.chain_result([node])

    @jm_command_group.command("rand")
    async def jm_rand_command(self, event: AstrMessageEvent):
        ''' 这是一个 获取随机本子 指令'''
        global last_random_time, Current_random_time, flag02, Cover_tag2
        Cover_tag2 = 0
        '''这是一个 获取本子名字 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return
            Current_random_time = int(datetime.now().timestamp())
            time_diff_in_seconds = Current_random_time - last_random_time
            last_random_time = Current_random_time
            if time_diff_in_seconds < CoolDownTime:
                cd_time = CoolDownTime - time_diff_in_seconds
                if flag02 == 0:
                    flag02 += 1
                    yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
                else:
                    flag02 += 1
                return

            flag02 = 0
        # 随机获取本子
        #获取当前最新编号
        client = JmOption.copy_option(option).new_jm_client()
        album: JmSearchPage = client.search_site(search_query="blue archive", page=1)
        latest_id, _ = next(iter(album))
        #print(latest_id)
        try:
            latest_id_int=int(latest_id)
        except:
            latest_id_int = 1230000

        random_album = random.randint(1, latest_id_int)
        album = ''
        empty_tag = 0
        try:
            client = JmOption.copy_option(option).new_jm_client()
            page = client.search_site(search_query=random_album)
            album: JmAlbumDetail = page.single_album
        except:
            empty_tag = 1
        chain = []
        if empty_tag == 1:
            chain = [
                Reply(id=event.message_obj.message_id),
                Plain("...\n"),
                Plain(f"随机本子：id：{random_album}\n"),
                Plain("该本子不存在或已下架:(")
            ]
        else:
            chain = [
                Reply(id=event.message_obj.message_id),
                Plain("...\n"),
                Plain(f"随机本子：id：{random_album}\n"),
                Plain(f"本子名称：{album.name}\n"),
                Plain(f"作者：{album.author}"),
            ]
        yield event.chain_result(chain)

    @jm_command_group.command("key")
    async def jm_key_command(self, event: AstrMessageEvent, key: str,filterid: str = "0", IsSendAllstr = "n"):
        ''' 这是一个 根据关键字搜索本子 指令'''
        global last_search_comic_time, Current_search_comic_time, flag04
        Cover_tag2 = 0
        '''这是一个 获取本子名字 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return
            Current_search_comic_time = int(datetime.now().timestamp())
            time_diff_in_seconds = Current_search_comic_time - last_search_comic_time
            last_search_comic_time = Current_search_comic_time
            if time_diff_in_seconds < CoolDownTime:
                cd_time = CoolDownTime - time_diff_in_seconds
                if flag04 == 0:
                    flag04 += 1
                    yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
                else:
                    flag04 += 1
                return

            flag04 = 0

        album = ''
        empty_tag = 0
        try:
            client = JmOption.copy_option(option).new_jm_client()
            album: JmSearchPage = client.search_site(search_query=key, page=1)
        except:
            empty_tag = 1

        if empty_tag == 1:
            yield event.plain_result("未找到该关键字相关的本子")
        else:
            # 判断是否有要过滤的
            int_filterid=0
            if filterid.isdigit():
                int_filterid = int(filterid)
            else:
                pass

            #判断只是发名字还是把封面
            if IsSendAllstr=="Y" or IsSendAllstr == "y":
                #取出符合条件的album_id
                result_album_id=[]
                result_album_title=[]
                result_tag=[]
                for album_id, title in album:
                    if int(album_id) < int_filterid:
                         continue
                    result_album_id.append(album_id)
                    result_album_title.append(title)

                #下载封面，按照albumid顺序下载
                folder_path = './data/plugins/astrbot_plugins_JMPlugins/pic/'
                count= len(result_album_id)
                maxcount=15

                global cover_count

                yield event.plain_result(f"找到{count}个结果，正在下载封面,最多下载{cover_count}个封面")
                count=min(cover_count,count)

                for i in range(count):
                    try:
                        client = JmOption.copy_option(option).new_jm_client()
                        page = client.search_site(search_query=result_album_id[i])
                        album: JmAlbumDetail = page.single_album
                    except:
                        result_tag.append(" ")
                        continue

                    result_tag.append(album.tags)

                    photo: JmPhotoDetail = album.getindex(0)
                    photo01 = client.get_photo_detail(photo.photo_id, False)

                    image: JmImageDetail = photo01[0]
                    if os.path.exists(os.path.join(folder_path, f'{i}.jpg')):
                        os.remove(os.path.join(folder_path, f'{i}.jpg'))
                    client.download_by_image_detail(image, os.path.join(folder_path, f'{i}.jpg'))

                #添加防挡
                for i in range(count):
                    image_path= os.path.join(folder_path, f'{i}.jpg')
                    if os.path.exists(image_path):
                        from PIL import Image as ProcessImage
                        original_image = ProcessImage.open(image_path)
                        # 获取原始图片的宽度和高度
                        width, height = original_image.size
                        # 创建一张新的空白图片，大小为原图的宽度和五倍高度
                        new_image = ProcessImage.new('RGB', (width, height * 5+200), color=(255, 255, 255))
                        # 将原图粘贴到新图片的下半部分
                        new_image.paste(original_image, (0, height * 4))
                        # 保存最终结果
                        new_image.save(image_path)

                #添加到node里面并发送
                All_nodes=[]
                from astrbot.api.message_components import Node, Plain, Image
                botid=event.get_self_id()
                for i in range(count):
                    node = Node(
                        uin=botid,
                        name="仙人",
                        content=
                        [
                            Plain("...\n"),
                            Plain(f"id:{result_album_id[i]}\n"),
                            Plain(f"本子名称：{result_album_title[i]}\n"),
                            Plain(f"tag:{result_tag[i]}")
                        ]
                    )
                    img_path=os.path.join(folder_path, f'{i}.jpg')
                    if os.path.exists(img_path):
                        pic_node=Node(
                            uin=botid,
                            name="仙人",
                            content=[
                                Image.fromFileSystem(img_path)
                            ]
                        )
                    else:
                        pic_node = Node(
                            uin=botid,
                            name="仙人",
                            content=[
                               Plain("未找到封面或者封面下载失败请窒息")
                            ]
                        )
                    All_nodes.append(node)
                    All_nodes.append(pic_node)

                resNode = Nodes(
                    nodes=All_nodes
                )
                # 新添加的
                try:
                    yield event.chain_result([resNode])
                except Exception as e:
                    print(e)
                    new_All_nodes = []
                    from astrbot.api.message_components import Node, Plain, Image
                    botid = event.get_self_id()

                    notion_node = Node(
                        uin=botid,
                        name="仙人",
                        content=[
                            Plain("发送带图片的聊天记录失败，因此仅发送文字版的")
                        ]
                    )

                    new_All_nodes.append(notion_node)

                    for i in range(count):
                        node = Node(
                            uin=botid,
                            name="仙人",
                            content=
                            [
                                Plain("...\n"),
                                Plain(f"id:{result_album_id[i]}\n"),
                                Plain(f"本子名称：{result_album_title[i]}\n"),
                                Plain(f"tag:{result_tag[i]}")
                            ]
                        )
                        new_All_nodes.append(node)

                    newresNode = Nodes(
                        nodes=new_All_nodes
                    )
                    yield event.chain_result([newresNode])

            else:
                str = ''

                for album_id, title in album:
                    if int(album_id) < int_filterid:
                        continue
                    str += f"{album_id}:{title}\n"

                if str =='':
                    str="未搜索到结果"

                botid = event.get_self_id()
                from astrbot.api.message_components import Node, Plain, Image
                node = Node(
                    uin=botid,
                    name="仙人",
                    content=[
                        Plain(str)
                    ]
                )
                yield event.chain_result([node])

    # @jm_command_group.command("autokey")
    # async def jm_autokey_command(self, event: AstrMessageEvent):
    #     if event.get_message_type() == MessageType.FRIEND_MESSAGE:
    #         if event.get_sender_id() not in white_list_user:
    #             yield event.plain_result("该指令仅限管理员使用")
    #             return
    #     if event.get_message_type() == MessageType.GROUP_MESSAGE:
    #         if event.get_group_id() not in white_list_group:
    #             yield event.plain_result("该群没有权限使用该指令")
    #             return
    #
    #     yield event.plain_result("正在自动搜索")
    #     folder_path = './data/plugins/astrbot_plugins_JMPlugins/pic/'
    #     global cover_count
    #     # 定时任务
    #     result_album_id,result_album_title,result_tag = search_title_and_pic(folder_path,option,cover_count)
    #     count = len(result_album_id)
    #
    #     All_nodes = []
    #     from astrbot.api.message_components import Node, Plain, Image
    #     botid = event.get_self_id()
    #     for i in range(count):
    #         node = Node(
    #             uin=botid,
    #             name="仙人",
    #             content=
    #             [
    #                 Plain("...\n"),
    #                 Plain(f"id:{result_album_id[i]}\n"),
    #                 Plain(f"本子名称：{result_album_title[i]}\n"),
    #                 Plain(f"标签：{result_tag[i]}\n"),
    #             ]
    #         )
    #         img_path = os.path.join(folder_path, f'{i}.jpg')
    #         if os.path.exists(img_path):
    #             pic_node = Node(
    #                 uin=botid,
    #                 name="仙人",
    #                 content=[
    #                     Image.fromFileSystem(img_path)
    #                 ]
    #             )
    #         else:
    #             pic_node = Node(
    #                 uin=botid,
    #                 name="仙人",
    #                 content=[
    #                     Plain("未找到封面或者封面下载失败请窒息")
    #                 ]
    #             )
    #         All_nodes.append(node)
    #         All_nodes.append(pic_node)
    #
    #         resNode = Nodes(
    #             nodes=All_nodes
    #         )
    #
    #     yield event.chain_result([resNode])

    @filter.permission_type(PermissionType.ADMIN)
    @jm_command_group.command("promote")
    async def jm_promote_command(self, event: AstrMessageEvent, type: str, name: str):
        ''' 这是一个 晋升某人的权限 的指令'''
        if type == "group":
            if name in white_list_group:
                yield event.plain_result("该群已经在白名单中")
                return
            else:
                white_list_group.append(name)
                with open(white_list_path, 'w') as file:
                    data = {
                        "groupIDs": white_list_group,
                        "userIDs": white_list_user,
                    }
                    json.dump(data, file)
                yield event.plain_result("该群已成功加入白名单")
        if type == "user":
            if name in white_list_user:
                yield event.plain_result("该用户已经在白名单中")
                return
            else:
                white_list_user.append(name)
                with open(white_list_path, 'w') as file:
                    data = {
                        "groupIDs": white_list_group,
                        "userIDs": white_list_user,
                    }
                    json.dump(data, file)
                yield event.plain_result("该用户已成功加入白名单")

    @filter.permission_type(PermissionType.ADMIN)
    @jm_command_group.command("demote")
    async def jm_demote_command(self, event: AstrMessageEvent, type: str, name: str):
        ''' 这是一个 撤销某人的权限 的指令'''
        if type == "group":
            if name in white_list_group:
                white_list_group.remove(name)
                with open(white_list_path, 'w') as file:
                    data = {
                        "groupIDs": white_list_group,
                        "userIDs": white_list_user,
                    }
                    json.dump(data, file)
                yield event.plain_result("该群已成功撤销白名单")
            else:
                yield event.plain_result("该群不在白名单中")
        if type == "user":
            if name in white_list_user:
                white_list_user.remove(name)
                with open(white_list_path, 'w') as file:
                    data = {
                        "groupIDs": white_list_group,
                        "userIDs": white_list_user,
                    }
                    json.dump(data, file)
                yield event.plain_result("该用户已成功撤销白名单")
            else:
                yield event.plain_result("该用户不在白名单中")

    @jm_command_group.command("block")
    async def jm_block_command_group(self, event: AstrMessageEvent, type: str, album_id: str):
        ''' 这是一个 封面黑名单 指令组'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return

        if type == "add":
            if album_id in block_list:
                yield event.plain_result("该本子已经在黑名单中")
                return
            else:
                block_list.append(album_id)
                with open(blocklist_path, 'w') as file:
                    data = {
                        "albumID": block_list,
                    }
                    json.dump(data, file)
                yield event.plain_result("该本子已成功加入黑名单")
        if type == "remove":
            if album_id in block_list:
                block_list.remove(album_id)
                with open(blocklist_path, 'w') as file:
                    data = {
                        "albumID": block_list,
                    }
                    json.dump(data, file)
                yield event.plain_result("该本子已成功移除黑名单")

    @jm_command_group.command("history")
    async def jm_history_command(self, event: AstrMessageEvent):
        '''这是一个 获取本子历史记录 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return

        abs_history_json_path = os.path.abspath(history_json_path)
        file_url = f"file://{abs_history_json_path}"
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
        assert isinstance(event, AiocqhttpMessageEvent)
        if (event.get_message_type() == MessageType.FRIEND_MESSAGE):
            user_id = event.get_sender_id()
            client = event.bot
            payloads2 = {
                "user_id": user_id,
                "message": [
                    {
                        "type": "file",
                        "data": {
                            "file": file_url,
                        }
                    }
                ]
            }
            response = await client.api.call_action('send_private_msg', **payloads2)  # 调用 协议端  API
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            group_id = event.get_group_id()
            client = event.bot
            payloads2 = {
                "group_id": group_id,
                "message": [
                    {
                        "type": "file",
                        "data": {
                            "file": file_url,
                        }
                    }
                ]
            }
            response = await client.api.call_action('send_group_msg', **payloads2)  # 调用 协议端

    @jm_command_group.command("rank")
    async def jm_rank_command(self, event: AstrMessageEvent, time: str):
        ''' 这是一个 排行榜 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return

        if time not in ['m', 'w', 'a', 'd']:
            yield event.plain_result("参数错误，请使用m/w/d/a")
            return

        try:
            client = JmOption.copy_option(option).new_jm_client()
            page = ""
            hint = ""
            if time == 'm':
                hint = "本月热门本子："
                page: JmCategoryPage = client.categories_filter(
                    page=1,
                    time=JmMagicConstants.TIME_MONTH,
                    category=JmMagicConstants.CATEGORY_ALL,
                    order_by=JmMagicConstants.ORDER_BY_VIEW,
                )
            elif time == 'w':
                hint = "本周热门本子："
                page: JmCategoryPage = client.categories_filter(
                    page=1,
                    time=JmMagicConstants.TIME_WEEK,
                    category=JmMagicConstants.CATEGORY_ALL,
                    order_by=JmMagicConstants.ORDER_BY_VIEW,
                )
            elif time == 'd':
                hint = "今日热门本子："
                page: JmCategoryPage = client.categories_filter(
                    page=1,
                    time=JmMagicConstants.TIME_TODAY,
                    category=JmMagicConstants.CATEGORY_ALL,
                    order_by=JmMagicConstants.ORDER_BY_VIEW,
                )
            elif time == 'a':
                hint = "全部热门本子："
                page: JmCategoryPage = client.categories_filter(
                    page=1,
                    time=JmMagicConstants.TIME_ALL,
                    category=JmMagicConstants.CATEGORY_ALL,
                    order_by=JmMagicConstants.ORDER_BY_VIEW,
                )
            result_str = ""
            for aid, title in page:
                result_str += f"{aid}:{title}\n"

            botid = event.get_self_id()
            from astrbot.api.message_components import Node, Plain, Image
            node = Node(
                uin=botid,
                name="仙人",
                content=[
                    Plain(f"{hint}：\n{result_str}")
                ]
            )
            yield event.chain_result([node])
        except:
            yield event.plain_result("搜索失败")
            return

    @jm_command_group.command("f")
    async def jm_f_command(self, event: AstrMessageEvent,type:str, album_id: str):
        ''' 这是一个 收藏JMid 指令组'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return

        global favor_list,favorite_path

        if type == "add":
            if album_id in favor_list:
                yield event.plain_result("该本子已经在收藏夹中")
                return
            else:
                favor_list.append(album_id)
                with open(favorite_path, 'w') as file:
                    data = {
                        "albumID": favor_list,
                    }
                    json.dump(data, file)
                yield event.plain_result("该本子已成功加入收藏夹")
        if type == "remove":
            if album_id in block_list:
                favor_list.remove(album_id)
                with open(favorite_path, 'w') as file:
                    data = {
                        "albumID": favor_list,
                    }
                    json.dump(data, file)
                yield event.plain_result("该本子已成功移除收藏夹")

        if type == "show":
            if len(favor_list) == 0:
                yield event.plain_result("收藏夹为空")
                return
            else:
                result_str = ""
                for aid in favor_list:
                    result_str += f"{aid}\n"
                botid = event.get_self_id()

                from astrbot.api.message_components import Node, Plain, Image
                node = Node(
                    uin=botid,
                    name="仙人",
                    content=[
                        Plain(f"收藏夹：\n{result_str}")
                    ]
                )
                yield event.chain_result([node])



    @jm_command_group.command("help")
    async def jm_help_command(self, event: AstrMessageEvent):
        ''' 这是一个 帮助 指令'''
        str = ""
        str += "本插件提供以下指令：\n"
        str += "id [id] {f/F}：获取本子名称(以及封面图),后面加上参数f/F会不只发送封面图，不添加参数默认只发送封面图\n"
        str += "rank [m/w/d/a]：获取本子排行榜\n"
        str += "rand：随机获取本子\n"
        str += "key [关键字] {filter_id=0}：根据关键字搜索本子,并且过滤掉比{filter_id}小的本子\n"
        str += "history：获取本子历史记录\n"
        # str += "对图片回复/search   ：搜索图片\n"

        botid = event.get_self_id()
        from astrbot.api.message_components import Node, Plain, Image
        node = Node(
            uin=botid,
            name="仙人",
            content=[
                Plain(str)
            ]
        )
        yield event.chain_result([node])

    @jm_command_group.command("set")
    async def jm_set_command(self, event: AstrMessageEvent, value: str):
        ''' 这是一个 设置发送图片数量 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return
        global img_count
        if value.isdigit():
            value=int(value)
            if value <1:
                yield event.plain_result("数量不能小于1")
            else:
                img_count = int(value)
                yield event.plain_result(f"发送图片数量已设置为{img_count}")
        else:
            yield event.plain_result("参数错误，请使用数字")


    @filter.command("search")
    async def jm_search_command(self, event: AstrMessageEvent):
        ''' 这是一个 搜索图片 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return

        global last_search_picture_time, Current_search_picture_time, flag03
        Current_search_picture_time = int(datetime.now().timestamp())
        time_diff_in_seconds = Current_search_picture_time - last_search_picture_time
        last_search_picture_time = Current_search_picture_time
        if time_diff_in_seconds < CoolDownTime:
            cd_time = CoolDownTime - time_diff_in_seconds
            if flag03 == 0:
                flag03 += 1
                yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
            else:
                flag03 += 1
            return
        flag03 = 0

        image_url = ''
        message_chain = event.get_messages()
        for msg in message_chain:
            # print(msg)
            # print("\n")
            if msg.type == 'Image':
                PictureID = msg.file
                print(f"图片ID: {PictureID}")
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payloads2 = {
                    "file_id": PictureID
                }
                response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
                # print(response)
                image_url = response['file']

            elif msg.type == 'Reply':
                # 处理回复消息
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payload = {
                    "message_id": msg.id
                }
                response = await client.api.call_action('get_msg', **payload)  # 调用 协议端  API
                # print(response)
                reply_msg = response['message']
                for msg in reply_msg:
                    if msg['type'] == 'image':
                        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import \
                            AiocqhttpMessageEvent
                        assert isinstance(event, AiocqhttpMessageEvent)
                        client = event.bot
                        payloads2 = {
                            "file_id": msg['data']['file']
                        }
                        response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
                        image_url = response['file']

        print(f"图片URL: {image_url}")
        if image_url == '':
            yield event.plain_result("未检测到图片")
            return
        else:
            try:
                # ascii2d暂时没反应
                engin = Ascii2D(base_url="https://ascii2d.obfs.dev")
                resp = await engin.search(file=image_url)
                raw = resp.raw
                count = 0
                result_str = ''
                for r in raw:
                    if (r.url == ""):
                        continue
                    result_str += f"{count}:{r.url}\n"
                    count += 1
                    if count == 2:
                        break
                if count == 0:
                    yield event.plain_result("未找到相似图片")
                else:
                    botid = event.get_self_id()
                    from astrbot.api.message_components import Node, Plain, Image
                    node = Node(
                        uin=botid,
                        name="仙人",
                        content=[
                            Plain("找到相似图片：\n"),
                            Plain(result_str)
                        ]
                    )
                    yield event.chain_result([node])

            except Exception as e:
                print(e)
                yield event.plain_result("搜索图片失败")


    #设置定时任务，获取群聊/私聊的消息串
    @filter.permission_type(PermissionType.ADMIN)
    @jm_command_group.command("addlist")
    async def jm_addlist_command(self, event: AstrMessageEvent):
        """ 这是一个 添加群聊/私聊消息串 指令"""
        umo = event.unified_msg_origin
        print(umo)
        add_unified_msg(umo)
        yield event.plain_result(f"添加成功")
    @filter.permission_type(PermissionType.ADMIN)
    @jm_command_group.command("removelist")
    async def jm_removelist_command(self, event: AstrMessageEvent):
        """ 这是一个 删除群聊/私聊消息串 指令"""
        umo = event.unified_msg_origin
        remove_unified_msg(umo)
        yield event.plain_result(f"删除成功")

        
async def test_send_message(context: Context):
    umos = get_unified_msg()  # 修复：使用正确的函数获取消息列表
    print(umos)
    from astrbot.api.event import MessageChain
    message_chain = MessageChain().message("Hello!")
    for umo in umos:
        try:
            await context.send_message(umo, message_chain)  # 修复：使用await而不是yield
        except Exception as e:
            print(e)
            continue

async def send_daily_message(context: Context,botid):
    # 下载图片
    folder_path = './data/plugins/astrbot_plugins_JMPlugins/pic_daily/'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    global cover_count
    # 定时任务
    result_album_id, result_album_title, result_tag = search_title_and_pic(download_path=folder_path, option=option, max_count=cover_count)
    count = len(result_album_id)
    # print(len(result_album_id),len(result_album_title),len(result_tag))

    from astrbot.api.event import MessageChain
    message_chain = MessageChain()

    from astrbot.api.message_components import Node, Plain, Image

    if count == 0:
        time_node = Node(
            uin=botid,
            name="仙人",
            content=[
                Plain("前段时间没有更新新的本子，起飞失败")
            ]
        )
        message_chain.chain.append(time_node)
        #发送写好的图片
        pic_path = "./data/plugins/astrbot_plugins_JMPlugins/no_new_benzi.gif"
        if os.path.exists(pic_path):
            image_node = Node(
                uin=botid,
                name="仙人",
                content=[
                    Image.fromFileSystem(pic_path)
                ]
            )
            message_chain.chain.append(image_node)
    else:
        time_node =Node(
            uin=botid,
            name="仙人",
            content=[
                Plain("前一时间段内更新的本子有：")
            ]
        )
        message_chain.chain.append(time_node)

        total_len = len(result_album_id)

        # 前15个加上封面，后面的不加封面

        for i in range(total_len):
            # 添加安全检查，防止tag索引超出范围
            tag_str = []
            if i >= len(result_tag):
                tag_str = "tag获取失败"
            else:
                tag_str = result_tag[i]
            node = Node(
                uin=botid,
                name="仙人",
                content=
                [
                    Plain("...\n"),
                    Plain(f"id:{result_album_id[i]}\n"),
                    Plain(f"本子名称：{result_album_title[i]}\n"),
                    Plain(f"标签：{tag_str}\n"),
                ]
            )
            if i >= cover_count:
                message_chain.chain.append(node)
                continue

            #判断tag里面是否有需要过滤的内容：
            filter_tag = ['NTR','猎奇','寝取']
            if any(tag in tag_str for tag in filter_tag):
                print("检测到了过滤内容")
                # 检验是否有用来替换屏蔽图片的图片
                pic_path="./data/plugins/astrbot_plugins_JMPlugins/seia_blockpic.jpg"
                if os.path.exists(pic_path):
                    pic_node = Node(
                        uin=botid,
                        name="仙人",
                        content=[
                            Image.fromFileSystem(pic_path)
                        ]
                    )
                else:
                    pic_node = Node(
                        uin=botid,
                        name="仙人",
                        content=[
                            Plain("检测到过滤内容，图片已屏蔽"),
                        ]
                    )
            else:
                img_path = os.path.join(folder_path, f'{i}.jpg')
                if os.path.exists(img_path):
                    pic_node = Node(
                        uin=botid,
                        name="仙人",
                        content=[
                            Image.fromFileSystem(img_path)
                        ]
                    )
                else:
                    pic_node = Node(
                        uin=botid,
                        name="仙人",
                        content=[
                            Plain("未找到封面或者封面下载失败请窒息")
                        ]
                    )
            message_chain.chain.append(node)
            message_chain.chain.append(pic_node)

    umos = get_unified_msg()

    for umo in umos:
        try:
            await context.send_message(umo, message_chain)
        except Exception as e:
            print(e)
            # 发送纯文字版本的更新本子
            from astrbot.api.event import MessageChain
            message_chain = MessageChain()
            if count == 0:
                time_node = Node(
                    uin=botid,
                    name="仙人",
                    content=[
                        Plain("前段时间没有更新新的本子，起飞失败")
                    ]
                )
                message_chain.chain.append(time_node)
                # 发送写好的图片
                pic_path = "./data/plugins/astrbot_plugins_JMPlugins/no_new_benzi.gif"
                if os.path.exists(pic_path):
                    image_node = Node(
                        uin=botid,
                        name="仙人",
                        content=[
                            Image.fromFileSystem(pic_path)
                        ]
                    )
                    message_chain.chain.append(image_node)
            else:
                info_node = Node(
                    uin=botid,
                    name="仙人",
                    content=[
                        Plain("图片发送失败，仅发送文本信息")
                    ]
                )
                time_node = Node(
                    uin=botid,
                    name="仙人",
                    content=[
                        Plain("前一时间段内更新的本子有：")
                    ]
                )
                message_chain.chain.append(info_node)
                message_chain.chain.append(time_node)

                for i in range(len(result_album_id)):
                    # 添加安全检查，防止tag索引超出范围
                    tag_str = ""
                    if i >= len(result_tag):
                        tag_str = "tag获取失败"
                    else:
                        tag_str = result_tag[i]

                    node = Node(
                        uin=botid,
                        name="仙人",
                        content=
                        [
                            Plain("...\n"),
                            Plain(f"id:{result_album_id[i]}\n"),
                            Plain(f"本子名称：{result_album_title[i]}\n"),
                            Plain(f"标签：{tag_str}\n"),
                        ]
                    )

                    message_chain.chain.append(node)
                try:
                    await context.send_message(umo, message_chain)
                except Exception as e:
                    print(e)
            continue




