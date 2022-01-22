from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
# from PyQt5.QtCore import *
# from PyQt5.QtMultimedia import *
# from PyQt5.QtMultimediaWidgets import QVideoWidget
from gui.BliveWindow import Ui_Blive_window
from gui.SettingWindow import Ui_Setting_window

import sys
import os
from Reptile_bag.Bilibili import BilibiliUp, BilibiliLive
import httpx
import json
import threading
import time
import re


class MyMainForm(QMainWindow, Ui_Blive_window):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        # 子窗口
        self.setting_window = SettingWindow()
        # 链接函数
        self.button_search.clicked.connect(self.button_search_down)
        self.button_record.clicked.connect(self.button_record_down)
        self.button_link.clicked.connect(self.button_link_down)
        self.button_stop.clicked.connect(self.button_stop_down)
        self.button_send.clicked.connect(self.button_send_down)
        self.button_live.clicked.connect(self.button_live_down)
        self.button_open.clicked.connect(self.button_open_down)
        self.button_clear.clicked.connect(self.button_clear_down)
        self.setting_window.button_confirm.clicked.connect(self.button_confirm_setting_down)
        # 菜单栏
        self.actionExit.triggered.connect(self.close)
        self.actionSave.triggered.connect(self.save_init)
        self.actionInit.triggered.connect(self.set_file_path)
        self.actionShowHelp.triggered.connect(self.helper)
        self.actionAbout.triggered.connect(self.about_browser)
        self.actionLoad.triggered.connect(self.log_in)
        self.actionSetting.triggered.connect(self.setting_window_show)
        # 软件一些参数初始化载入
        self.blive_init()

    def blive_init(self):
        """
        初始化内容
        :return:
        """
        self.live_up = BilibiliLive()
        self.flag_link = False              # 连接标志：1为接入
        self.flag_record = False            # 1 为正在录制  0为未进行录制
        self.flag_live = False              # 1 为正在观看直播内容
        self.flag_Th_live_done = False      # 1 为线程结束
        self.file_name = ''                 # 文件名字
        self.q_n = 0                        # 默认画质 数字越大，画质越好
        self.line_n = 0                     # 默认主线路
        self.record_path = ''
        # 载入数据
        self.load_init()

    def button_search_down(self):
        info = self.lineEdit_UP.text()  # 获取输入框的信息
        self.textEdit_danmu.moveCursor(QTextCursor.End)  # 移动光标至末尾
        try:
            bup = BilibiliUp(mid=info)
            bup.get_information()
            bup.get_live_info()
            if not bup.flag:
                msg = '查无此UP'
            else:
                msg = f'{bup.name}({bup.mid})的房间号为:{bup.roomid}'
                self.live_up.name = bup.name
                self.live_up.roomid = bup.roomid
                self.save_init()
            self.textEdit_danmu.append(msg)
            self.textEdit_danmu.moveCursor(QTextCursor.End)  # 移动光标至末尾
            self.lineEdit_room_id.setText(bup.roomid)
            self.lineEdit_UP.setText(bup.name)
        except:  # 搜索up信息
            bup = BilibiliUp(name=info)
            mid_list = bup.get_bup_mid()
            if len(mid_list) > 0:
                bup.get_information()
                bup.get_live_info()
                msg = f'{bup.name}({bup.mid})的房间号为:{bup.roomid}'
                self.live_up.name = bup.name
                self.live_up.roomid = bup.roomid
                self.save_init()
            else:
                msg = '查无此UP'
            self.textEdit_danmu.append(msg)
            self.textEdit_danmu.moveCursor(QTextCursor.End)  # 移动光标至末尾
            self.lineEdit_room_id.setText(bup.roomid)
            self.lineEdit_UP.setText(bup.name)

    def button_link_down(self):
        """
        连接按钮按下
        :return:
        """
        self.live_up.roomid = self.lineEdit_room_id.text()   # 获取输入框的信息
        self.textEdit_danmu.append(f'正在连接中...\n房间ID号为' + self.live_up.roomid)
        dict_info = self.live_up.get_live_info()
        self.textEdit_danmu.moveCursor(QTextCursor.End)  # 移动光标至末尾
        if dict_info:
            self.textEdit_danmu.append('已连接')
            self.save_init()
            if dict_info['room_info']['live_status'] == 1:
                self.textEdit_danmu.append('当前直播状态：直播中')
            else:
                self.textEdit_danmu.append('当前直播状态：未开播')
            self.button_link.setEnabled(False)
            self.button_search.setEnabled(False)
            self.button_stop.setEnabled(True)
            self.button_live.setEnabled(True)
            self.button_record.setEnabled(True)
            self.lable_live_title.setText(dict_info['room_info']["title"])
            self.download_pic(dict_info['anchor_info']['base_info']['face'])
            # 说明图片位置，并导入图片到画布上
            up_head_pic = QImage('up_head_pic.gif')
            pixmap_up_head_pic = QPixmap.fromImage(up_head_pic.scaled(self.label_head_pic.size()))
            self.label_head_pic.setPixmap(pixmap_up_head_pic)
            msg_th = threading.Thread(target=self.load_msg)
            msg_th.start()
        else:
            self.textEdit_danmu.append('连接房间' + self.live_up.roomid + '失败！')
            self.textEdit_danmu.moveCursor(QTextCursor.End)  # 移动光标至末尾

    def button_stop_down(self):
        """
        停止按钮按下，停止连接
        :return: 0 失败  1 成功
        """
        a = QMessageBox.question(self, '询问', '是否确认断开连接', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if a == QMessageBox.Yes:
            # 关闭
            self.flag_live = False      # 关闭直播
            self.flag_record = False    # 关闭录制
            self.flag_link = False      # 关闭连接
            self.button_live.setText('观看直播')
            self.button_record.setText('录制')
            self.button_record.setStyleSheet("")
            self.button_link.setEnabled(True)
            self.button_search.setEnabled(True)
            self.button_stop.setEnabled(False)
            self.button_live.setEnabled(False)
            self.button_record.setEnabled(False)
            return 1
        else:
            return 0

    def button_record_down(self):
        if self.flag_record:
            self.flag_record = False
            self.button_record.setText('录制')
            self.button_record.setStyleSheet("")
            self.live_up.flag_record_stop = 1
        else:
            if self.live_up.get_live_info().get('room_info').get('live_status') == 1:
                self.button_record.setText('停止录制')
                self.button_record.setStyleSheet("color: red")
                self.live_up.flag_record_stop = 0
                record_live_th = threading.Thread(target=self.record_live)
                record_live_th.start()
                self.flag_record = 1
            else:
                self.textEdit_danmu.append('未开播，无法录制！')
                self.textEdit_danmu.moveCursor(QTextCursor.End)

    def button_live_down(self):
        if self.flag_live:
            # self.live_room_window.show()
            os.startfile(os.getcwd() + '/cache/' + f'{self.live_up.roomid}.flv')
        else:
            if self.live_up.get_live_info().get('room_info').get('live_status') == 1:
                # self.live_room_window.show()
                self.button_live.setText('打开直播')
                live_th = threading.Thread(target=self.live_now, name='直播线程')
                live_th.start()
                self.flag_live = True
                while 1:
                    if os.path.isfile(os.getcwd() + '/cache/' + f'{self.live_up.roomid}.flv'):
                        os.startfile(os.getcwd() + '/cache/' + f'{self.live_up.roomid}.flv')
                        break
            else:
                self.textEdit_danmu.append('未开播，无法观看！')
                self.textEdit_danmu.moveCursor(QTextCursor.End)

    def button_open_down(self):
        if self.record_path == '':
            if not os.path.exists('./live_record'):
                os.mkdir('./live_record')  # 创建文件夹
            self.record_path = '.\\live_record'
            os.startfile(os.getcwd() + "\\live_record")
        else:
            if not os.path.exists('./live_record'):
                os.mkdir('./live_record')  # 创建文件夹
            if self.file_name == '':
                os.system(f"start " + self.record_path)
            else:
                path = str(self.record_path + '\\' + self.file_name)
                os.system(f"explorer /select," + path.replace('/', '\\'))

    def button_clear_down(self):
        self.textEdit_danmu.setText('')

    def button_send_down(self):
        try:
            msg = self.textEdit_send.toPlainText()
            if msg == '':
                self.textEdit_danmu.append('弹幕不能为空！')
            else:
                ret = self.live_up.send_msg(msg)
                dict_ret = json.loads(ret.text)
                if dict_ret['message'] != "":
                    self.textEdit_danmu.append(f'发送失败！{dict_ret["message"]}')
                self.textEdit_send.setText('')
        except:
            self.textEdit_danmu.append('发送失败！')

    def download_pic(self, url):
        r = httpx.get(url)
        with open('up_head_pic.gif', 'wb') as f:
            f.write(r.content)

    def load_msg(self):
        """
        显示直播信息
        :return:
        """
        try:
            a = []
            self.flag_link = True
            while self.flag_link:
                time.sleep(0.5)
                b = self.live_up.get_live_msg()
                for item in b:
                    if item not in a:
                        self.textEdit_danmu.append(
                            f"[{item['timeline']}] {item['nickname']}({item['uid']}):{item['text']}")
                        a.append(item)
                        time.sleep(0.1)
                        self.textEdit_danmu.moveCursor(QTextCursor.End)  # 移动光标至末尾
                if len(a) >= 30:
                    a = a[-30:]
            self.textEdit_danmu.append('已停止')
            time.sleep(0.1)
            self.textEdit_danmu.moveCursor(QTextCursor.End)  # 移动光标至末尾
        except:
            return -1

    def record_live(self):
        generator = self.live_up.flv_download(self.q_n, self.line_n, 1)

        if not os.path.exists(self.record_path):
            os.mkdir('.\\live_record')  # 创建文件夹
            self.record_path = '.\\live_record'

        self.file_name = f'{self.live_up.roomid}_' + str(int(time.time())) + '.flv'
        with open(self.record_path + '\\' + self.file_name, 'wb') as file:
            # 用一个生成器来迭代
            for r in generator:
                for data in r.iter_bytes():
                    file.write(data)
                    file.flush()
                    if not self.flag_record:
                        return 0

    def live_now(self):
        # generator = self.live_up.flv_download(self.q_n, self.line_n, 0)
        # player = QMediaPlayer()
        # player.setVideoOutput(self.live_room_window.video_live)  # 视频播放输出的widget，就是上面定义的
        # player.setMedia(QMediaContent(QFileDialog.getOpenFileUrl()[0]))  # 选取视频文件
        # for r in generator:
        #     player.play()  # 播放视频

        # 放缓存区，不录制，完成直接删除
        generator = self.live_up.flv_download(self.q_n, self.line_n, 0)
        if not os.path.exists('./cache'):
            os.mkdir('./cache')  # 创建
        if os.path.isfile('./cache/' + f'{self.live_up.roomid}.flv'):
            os.remove(f"./cache/{self.live_up.roomid}.flv")
        with open('./cache/' + f'{self.live_up.roomid}.flv', 'wb') as file:
            for r in generator:
                for data in r.iter_bytes():
                    file.write(data)
                    file.flush()
                    if not self.flag_live:
                        break
                if not self.flag_live:
                    break
        os.remove(f"./cache/{self.live_up.roomid}.flv")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '询问',
                                     "是否确认退出", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.flag_link:
                self.button_stop_down()
            self.save_init()
            event.accept()
        else:
            event.ignore()

    def save_init(self):
        """
        保存配置
        :return:
        """
        dict_save = {}
        dict_save['up_name'] = self.live_up.name
        dict_save['roomid'] = self.live_up.roomid
        dict_save['record_path'] = self.record_path
        dict_save['q_n'] = self.q_n
        dict_save['line_n'] = self.line_n
        dict_save['cookies'] = self.live_up.cookies
        with open('init.json', mode='w', encoding='utf-8') as f:  # 将列表里储存的字典一次性写入.json
            json.dump(dict_save, f)

    def load_init(self):
        """
        载入配置
        :return:
        """
        if os.path.exists('./init.json'):
            with open('./init.json', 'r') as js_file:
                dict_save = json.load(js_file)
                self.live_up.name = dict_save['up_name']
                self.lineEdit_UP.setText(self.live_up.name)
                self.live_up.roomid = dict_save['roomid']
                self.lineEdit_room_id.setText(self.live_up.roomid)
                self.record_path = dict_save['record_path']
                self.q_n = dict_save['q_n']
                self.line_n = dict_save['line_n']
                self.live_up.cookies = dict_save['cookies']

                reg = r'DedeUserID=(.*?);'
                list_mid = re.findall(reg, self.live_up.cookies['Cookie'])
                if len(list_mid) != 0:
                    bup = BilibiliUp(mid=list_mid[0])
                    bup.get_information()
                    self.textEdit_danmu.append(f'检测到Cookies登录账号为:{bup.name}({bup.mid})')
                    self.label_load_info.setText(f'已登录({bup.name})')
                else:
                    self.textEdit_danmu.append(f'未检测到Cookies登录的账号')
                    self.label_load_info.setText(f'未登录')

                if self.line_n == 0:
                    self.setting_window.radioButton_line_0.setChecked(True)
                elif self.line_n == 1:
                    self.setting_window.radioButton_line_1.setChecked(True)
                else:
                    self.setting_window.radioButton_line_2.setChecked(True)

                if self.q_n == 10000:
                    self.setting_window.radioButton_qn_1.setChecked(True)
                elif self.q_n == 400:
                    self.setting_window.radioButton_qn_2.setChecked(True)
                else:
                    self.setting_window.radioButton_qn_0.setChecked(True)

        if self.live_up.cookies == {}:
            self.live_up.cookies = {
                'Cookie': "_uuid=B7B3476F-9795-1CA8-C5A5-B1F2582EA64865975infoc; buvid3=CFE1E7DB-C099-4984-9DC0-39CA64AC471118564infoc; buvid_fp=CFE1E7DB-C099-4984-9DC0-39CA64AC471118564infoc; buvid_fp_plain=CFE1E7DB-C099-4984-9DC0-39CA64AC471118564infoc; CURRENT_FNVAL=80; blackside_state=1; rpdid=|(J~|)|JllmR0J'uYu~~~|~ku; LIVE_BUVID=AUTO1616201968656729; fingerprint3=282e4d4fea4abd03277d2212a65bc9e5; fingerprint_s=91dbff0fd81fa7feb3dd2a7f29be10c2; sid=7fqxvdm6; bp_t_offset_26744383=567006623048833728; innersign=0; bp_video_offset_26744383=569966525538179202; fingerprint=8e7db9bbcc6afb644a6cb2f1d2aef9ec; PVID=4; Hm_lvt_8a6e55dbd2870f0f5bc9194cddf32a02=1631547010; Hm_lpvt_8a6e55dbd2870f0f5bc9194cddf32a02=1631547010"}

    def set_file_path(self):
        path = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if path:
            self.record_path = path
            self.save_init()

    def log_in(self):
        cookies, ok = QInputDialog.getText(self, "Cookies登录", "输入您的Cookies值")
        if ok:
            if type(self.live_up.cookies) != 'dict':
                self.live_up.cookies = {}
            self.live_up.cookies['Cookie'] = cookies
            self.save_init()
            reg = r'DedeUserID=(.*?);'
            list_mid = re.findall(reg, self.live_up.cookies['Cookie'])
            if len(list_mid) != 0:
                bup = BilibiliUp(mid=list_mid[0])
                bup.get_information()
                self.textEdit_danmu.append(f'检测到Cookies登录账号为:{bup.name}({bup.mid})')
                self.label_load_info.setText(f'已登录({bup.name})')
            else:
                self.textEdit_danmu.append(f'未检测到Cookies登录的账号')
                self.label_load_info.setText(f'未登录')

    def helper(self):
        QMessageBox.information(self, "帮助", "1. 输入UP的名字或MID，并进行【查询】，会自动输入房间号，点击【连接】即可。\n"
                                            "2.【断开连接】时注意【停止录制】与关闭直播间\n"
                                            "3.【录制】可以将直播间视频进行录制，可以在菜单栏设置中设置保存的文件夹位置\n"
                                            "4.【观看直播】可以打开直播间，进行观看\n"
                                            "5. 弹幕【发送】需要使用【Cookies登录】，在设置->登录，输入Cookies值，如要退出则输入为空即可."
                                            "按F12选择网络，登录B站后点击网络文件即可找到Cookies")

    def about_browser(self):
        QMessageBox.information(self, "关于", "软件声明：\n"
                                            "    本软件为免费软件，用户可以非商业性下载、安装及使用\n"
                                            "软件仅供学习参考，技术交流Q群：229893011")

    def setting_window_show(self):
        self.setting_window.show()

    def button_confirm_setting_down(self):
        if self.setting_window.radioButton_line_0.isChecked():
            self.line_n = 0
        if self.setting_window.radioButton_line_1.isChecked():
            self.line_n = 1
        if self.setting_window.radioButton_line_2.isChecked():
            self.line_n = 2

        if self.setting_window.radioButton_qn_0.isChecked():
            self.q_n = 0
        if self.setting_window.radioButton_qn_1.isChecked():
            self.q_n = 10000
        if self.setting_window.radioButton_qn_2.isChecked():
            self.q_n = 400

        self.save_init()
        self.setting_window.close()


# 子窗口
class SettingWindow(QDialog, Ui_Setting_window):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)


if __name__ == "__main__":
    # 固定的，PyQt5程序都需要QApplication对象。sys.argv是命令行参数列表，确保程序可以双击运行
    app = QApplication(sys.argv)
    # 初始化
    myWin = MyMainForm()
    # 将窗口控件显示在屏幕上
    myWin.show()
    # 程序运行，sys.exit方法确保程序完整退出。
    sys.exit(app.exec_())
