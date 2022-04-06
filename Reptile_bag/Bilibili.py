# -*- coding: utf-8 -*-
import httpx
import json
import time
import re


class BilibiliUp:
    """
    Bilibili Up类：Up相关信息
    """
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)\
     AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
    }
    cookie = {}

    def __init__(self, name='', mid=''):
        # UP信息
        self.name = name
        self.mid = mid
        self.sign = ''
        self.sex = ''
        self.fans = ''
        self.attention = ''
        self.image_url = ''
        self.flag = 0
        self.level = ''
        # 直播间信息
        self.liveStatus = 0
        self.liveURL = ''
        self.title = ''
        self.roomid = ''
        self.live_info_flag = True

    def __str__(self):
        if self.flag:
            return f"""======ID{self.mid}======
名字：{self.name}
性别：{self.sex}
粉丝数：{self.fans}
关注数：{self.attention}
等级：{self.level}
签名：{self.sign}
======================
空间：
https://space.bilibili.com/{self.mid}
"""
        else:
            return """查无up信息"""

    def get_html(self, url):
        """
        向网站发送请求，代码格式固定
        :param url: 请求网站
        :return: 返回json代码对象
        """
        r = httpx.get(url=url, headers=self.headers, cookies=self.cookie)
        r.raise_for_status()
        return r.content.decode()

    def get_information(self):
        """
        得到页面信息
        :return: flag(有无该up), image_url, mid, name, sex, sign, \
            self.fans, self.attention, self.level  # 返回信息
        """
        if self.mid == '':
            self.get_bup_mid()
            if self.mid == '':
                return self.flag, self.image_url, self.mid, self.name, self.sex, self.sign, \
                 self.fans, self.attention, self.level
        url = f"https://api.bilibili.com/x/web-interface/card?mid={self.mid}&jsonp=jsonp&article=true"
        html = self.get_html(url)  # 得到json
        value = json.loads(html)  # 加载json
        self.flag = True  # flag，判断是否有这个页面
        self.image_url = value.get("data").get("card").get("face")
        self.mid = value.get("data").get("card").get("mid")  # json得到mid号
        self.name = value.get("data").get("card").get("name")
        self.sex = value.get("data").get("card").get("sex")
        self.sign = value.get("data").get("card").get("sign")
        self.fans = value.get("data").get("card").get("fans")
        self.attention = value.get("data").get("card").get("attention")
        self.level = value.get("data").get("card").get("level_info").get("current_level")
        if self.mid == "":  # mid号为空，则没有这个用户
            self.flag = False
        return self.flag, self.image_url, self.mid, self.name, self.sex, self.sign, \
            self.fans, self.attention, self.level  # 返回信息

    def get_bup_mid(self):
        """获取up的mid
        :return: mid_user_list:列表，存放所查到相关up的mid信息
        """
        # url = "https://search.bilibili.com/upuser?keyword=" + self.name
        url = f"https://api.bilibili.com/x/web-interface/search/type?__refresh__=true&_extra=&context=&page=1&page_size=36&platform=pc&keyword={self.name}&search_type=bili_user"
        response = httpx.get(url=url, headers=self.headers)
        dict_res = json.loads(response.text)
        user_list = dict_res['data']['result']
        if len(user_list) > 0:
            self.mid = user_list[0]['mid']
        else:
            self.mid = ''
        return user_list

    def get_live_info(self):
        """得到页面信息
        :return: flag(有无该up), image_url, mid, name, sex, sign, \
            self.fans, self.attention, self.level  # 返回信息
        """
        if self.mid == '':
            self.get_bup_mid()
        url = f"https://api.bilibili.com/x/space/acc/info?mid={self.mid}&jsonp=jsonp"
        html = self.get_html(url=url)
        value = json.loads(html)
        try:
            self.liveStatus = value['data']['live_room']['liveStatus']
            self.liveURL = value['data']['live_room']['url']
            self.title = value['data']['live_room']['title']
            self.roomid = str(value['data']['live_room']['roomid'])
            if self.roomid == '0':
                self.live_info_flag = False
            else:
                self.live_info_flag = True
            return value['data']['live_room']
        except:
            self.live_info_flag = False
            return 0


class BilibiliLive:
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)\
     AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
    }
    bili_jct = ''

    def __init__(self, roomid='', name=''):
        self.roomid = roomid
        self.name = name
        self.flag_live_stop = True
        self.flag_record_stop = True
        self.cookies = {}

    def get_html(self, url):
        """向网站发送请求，代码格式固定

        :param url: 请求网站
        :return: 返回json代码对象
        """
        r = httpx.get(url=url, headers=self.headers, cookies=self.cookies)
        r.raise_for_status()
        return r.content.decode()

    def get_live_msg(self):
        url = 'https://api.live.bilibili.com/xlive/web-room/v1/dM/gethistory?roomid=' + self.roomid
        html = self.get_html(url)  # 得到json
        value = json.loads(html)  # 加载json
        try:
            live_list = []
            for item in value["data"]["room"]:
                live_list.append({
                    'text': item['text'],
                    'uid': item['uid'],
                    "nickname": item["nickname"],
                    "timeline": item["timeline"]
                })
            return live_list
        except:
            return '出错!'

    def send_msg(self, msg):
        url_send = 'https://api.live.bilibili.com/msg/send'
        if self.bili_jct == '':
            self._get_csrf()
        data = {
            'bubble': '0',
            'msg': msg,
            'color': '16777215',
            'mode': '1',
            'fontsize': '25',
            'rnd': '1637816500',
            'roomid': self.roomid,
            'csrf': self.bili_jct,
            'csrf_token': self.bili_jct
        }
        ret = httpx.post(url=url_send, data=data, cookies=self.cookies)
        return ret

    def get_live_info(self) -> dict:
        """
        获得UP的直播信息
        :return: 返回UP的直播信息的字典类型
        若无该UP信息，则返回0
        """
        url = 'https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom?room_id=' + self.roomid
        html = self.get_html(url=url)
        value = json.loads(html)
        try:
            return value['data']
        except:
            return 0

    def flv_download(self, qn=10000, line=0, flag_record=0):
        '''
        执行视频录制，qn表示
        :param qn: 视频质量（原画、蓝光、高清……）的数字
        line: 0:主线路   1：备线1   2：备线2   3：备线3
        flag_record : 0：不录制  1：录制
        :return:
        '''
        url = 'https://api.live.bilibili.com/room/v1/Room/playUrl?cid=' + self.roomid + '&' + 'qn=' + str(qn) +'&platform=web'
        html = self.get_html(url=url)
        value = json.loads(html)
        flv_url = value['data']['durl'][line]['url']
        self.current_qn = value['data']['durl'][line]['url']
        if flag_record == 0:
            self.flag_record_stop = False
        else:
            self.flag_live_stop = False
        with httpx.stream('GET', url=flv_url, headers=self.headers, cookies=self.cookies) as r:
            yield r

    def _get_csrf(self):
        reg = 'bili_jct=(.*?);'
        list_csrf = re.findall(reg, self.cookies['Cookie'])
        if len(list_csrf) != 0:
            self.bili_jct = list_csrf[0]


'''
    测试
'''
if __name__ == '__main__':
    bup = BilibiliUp(name='虎见狼')
    bup.get_information()
    print(bup)  # 打印up信息
    print(bup.get_live_info())
