# -*- coding: utf-8 -*-
# 读取数据库文件进行解析,, 主函数 模块. 能解析 SQL2005/2008r2/2012
from PyQt5.QtCore import QThread, pyqtSignal
import struct   # ,time
import init
s = struct.unpack

class Unload_DB(QThread):
    PUP  = pyqtSignal(int)    # 更新进度条的信号
    LUP  = pyqtSignal(str)
    def __init__(self, parent = None):     # 解析函数
        super(Unload_DB,self).__init__(parent)
        self.file_infos = []
        self.tables,self.view_all,self.program_all,self.trigger_all,self.default_all,self.user_all,self.prog_all = 0,0,0,0,0,0,0


    # 文件信息
    def file_init(self,fn):
        self.file_infos = []
        for f_name in fn:                    # 每个文件头信息
            f = open (f_name,'rb')
            data = f.read(8192)
            file_info = init.file_blk_0(data)
            f.seek(8192*9)
            data = f.read(8192)
            version1,version2,first_07,db_name = init.file_blk_9(data)
            file_info.f_name = f_name
            file_info.file = f
            file_info.version1 = version1
            file_info.version2 = version2
            file_info.boot = first_07
            file_info.db_name = db_name
            self.file_infos.append(file_info)
        return self.file_infos

    def run(self):
        self.unload_db(self.file_infos)

    def unload_db(self,file_infos):
    #    print("Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))  # current time
        first_07 = file_infos[0].boot
        f = file_infos[0].file
        version = file_infos[0].version1
        tab_data_07 = init.init_07(file_infos[0],first_07)
        print("tab_data_07/02 over ....")
        if version[3:] != '0':
            print("tab_data_29 in ....")
            self.PUP.emit(10)                  # 传递参数
            self.LUP.emit("\t初始化 init_29 ...")
            tab_data_29 = init.init_29(f,tab_data_07)
            print("tab_data_29 over ....")
            self.PUP.emit(30)                  # 传递参数
            self.LUP.emit("\t初始化 init_22_05 ...")
            tab_data_22,tab_data_05 = init.init_22_05(f,tab_data_07,tab_data_29)
            print("tab_data_22,tab_data_05 over ....")
            self.PUP.emit(50)                  # 传递参数
            self.LUP.emit("\t初始化 用户表 ...")
            tab_all,view_all,program_all,trigger_all,default_all,user_all,prog_all = init.init_all_2008(f,tab_data_22,tab_data_29,tab_data_05,tab_data_07)  # 获得所有表的结构
            self.PUP.emit(100)                  # 传递参数
            self.LUP.emit("\t初始化 完成 ...")

            print("unload all over")
        elif version[3:] == '0':
            self.PUP.emit(10)                  # 传递参数
            self.LUP.emit("\t初始化 init_29 ...")
            tab_data_2 = tab_data_07
            tab_data_1,tab_data_3 = init.init_1_3(f,tab_data_2)
            print("init_1_3 over ....")
            self.PUP.emit(40)                  # 传递参数
            self.LUP.emit("\t初始化 用户表 ...")
            tab_all,view_all,program_all,trigger_all,default_all,user_all,prog_all = init.init_all_2000(f,tab_data_1,tab_data_2,tab_data_3)
            print("init_all_2000 over ....")
            self.PUP.emit(100)                  # 传递参数
            self.LUP.emit("\t解析 完成 ...")

        self.tables,self.view_all,self.program_all,self.trigger_all,self.default_all,self.user_all,self.prog_all =\
            tab_all,view_all,program_all,trigger_all,default_all,user_all,prog_all

    def unload_tab(self,file_infos,tab,db):
        f = file_infos[0].file
        tab_data = init.unload_tab(f,tab)
        return tab_data
    # save table
    def save_tab(self,tab_data,tab,conn):
        if tab.tab_name != 'sysowners':
            init.save_tab(tab_data,tab,conn)


