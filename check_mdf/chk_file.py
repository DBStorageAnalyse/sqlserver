# -*- coding: utf-8 -*-
# 统计，检测 数据文件, 给出报告
from PyQt5.QtCore import QThread, pyqtSignal
import time,struct,sqlite3,os.path
import mssql_check,file_info
s = struct.unpack   # B H I

 # 库文件信息
def f_info(f_name):
    f = open(f_name,'rb')
    file_info1 = file_info.file_info_all(f,0,32)  # 汇总库文件信息
    return file_info1

# 主函数，界面加入多线程
class SCAN(QThread):   # 类check继承自 QThread
    PUP  = pyqtSignal(int)    # 更新进度条的信号
    LUP  = pyqtSignal(str)

    def __init__(self,parent = None):     # 解析函数
        super(SCAN,self).__init__(parent)
        self.file_info = file_info
        self.start_pg_no = 0
        self.level = 0
        self.db = ''
        self.err_pages = []

    # 检测系统页,高级检测（暂时不支持）
    def chk_sys_page(self,f_name,db):
        self.mssql_scan(f_name,0,db)
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
       # cursor.execute("create index index_1 on mssql_page(id,page_no)")  # 创建索引
       # cursor.execute("select page_no,page_type from mssql_page where page_type=15")  #

    # 检测mdf文件所有页, 单独开的线程
    def run(self):
        f_name = self.file_info.f_name; db = self.db
        begin = time.time()
        print('开始检测:%s, db:%s '%(f_name,db))
        f = open (f_name,'rb')
        conn = sqlite3.connect(db); cursor = conn.cursor()
     #   cursor.execute(" create table mssql_page(id integer primary key,offset,page_type,page_no,file_no,chk1,chk2,chk3,chk4,zero)")
        buff_size = 8*1024*1024  # buffer大小, 8M
        page_size = 8192         # 页面大小
        f_size = os.path.getsize(f.name)  # 只能处理文件,不能磁盘
        start = self.start_pg_no*8192   # 扫描起始偏移
        f_size -= start
        loop_1 = f_size//buff_size
        loop_1_1 = f_size%buff_size
        loop_2 = buff_size//page_size
        loop_2_1 = loop_1_1//page_size
        self.file_info.real_sum = f_size//page_size
        sum = 0 ; page_1 = 0 ; page_15 = 0 ; page_2 = 0 ;page_3 = 0 ;page_10 = 0 ;err = 0;
        gam,sgam = self.gam_info(f)
        pfs = self.pfs_info(f)

        for i in range(0,loop_1+1):         # 扫描文件的所有buffer块
            f.seek(i*buff_size+start)
            data = f.read(buff_size+page_size)
            if(i < loop_1):             # 处理文件的所有buffer块
                for ii in range(0,loop_2):
                    chk = 0; chk0 = 0; chk00 = 1; chk_err = ''
                    pos1 = ii*page_size
                    data1 = data[pos1:pos1+page_size]
                    data2 = s("<4B2HIHHIHHI2HIH",data1[0:38])
                    data3 = s("<B",data1[5:6])                      # check_type
                    offset = i*buff_size + ii*page_size
                    chk1 = mssql_check.mssql_page_check_1(data1)         # 页头特征值校验
                    if data2[15] == (i*loop_2+ii+self.start_pg_no) :     # 页的物理位置正确
                        chk0 = 1
                    else:
                        chk0 = 0; chk_err += 'page#,'
                    if chk1 == 1 : # 页头正确
                        a = 0
                    else:
                        chk_err += 'header,'

                    if data3[0]%4 == 1 :                                # 校验类型为 残缺页校验
                        chk3 = mssql_check.mssql_page_check_3(data1)    # 残缺页校验
                        if chk3 == 1 :
                            data1 = mssql_check.page_handle(data1)
                            chk4 = mssql_check.mssql_page_check_4(data1)    # 页尾校验
                            if chk4==1 and data2[1] != 15 and data2[15] >0 :
                                chk = 1
                            elif chk4==1 and data2[1] == 15 and data2[15]==0 :
                                chk = 1
                            else:
                                chk = 0; chk_err += '页尾校验,'
                        else:
                            chk = 0; chk_err += '残缺页校验,'
                    elif data3[0]%4 == 2 :                              # 校验类型为 checksum
                        chk2 = mssql_check.mssql_page_check_2(data1)    # checksum 校验
                        if chk2 == 1:
                            chk = 1
                        else:
                            chk = 0; chk_err += 'checksum,'
                    elif data3[0]%4 == 0 :                              # 校验类型为 无校验
                            chk4 = mssql_check.mssql_page_check_4(data1)
                            if chk4==1 and data2[1] != 15 and data2[15] >0 :
                                chk = 1
                            elif chk4==1 and data2[1] == 15 and data2[15]==0 :
                                chk = 1
                            else:
                                chk = 0; chk_err += '页尾校验,'
                    else:
                        chk = 0; chk_err += 'unknow,'
                    if data2[0] == 0 and data2[1] == 0:
                        chk00 = 0; chk_err = '全零,'

                    if chk == 1 :   # 统计信息
                        if data2[1] == 1 :
                            page_1 += 1
                        elif data2[1] == 15 :
                            page_15 += 1
                        elif data2[1] == 2 :
                            page_2 += 1
                        elif data2[1] == 3 :
                            page_3 += 1
                        elif data2[1] == 10 :
                            page_10 += 1
                        sum += 1
                      #      cursor.execute("insert into mssql_page(offset,page_type,page_no,file_no) values(?,?,?,?)",(offset,data2[1],data2[15],data2[16]))
                        if sum%10000 == 0 :  # 每10000条commit一次, 频繁提交会影响I/O速度 　
                                conn.commit()
                    elif (chk1 != 1 or chk0 != 1 or chk00 == 0 or chk == 0) and gam[offset//8192//8] == 0 :
                        if (offset//8192 in (4,5) and chk00 == 0) or pfs[offset//8192] == 0:  # (offset//8192 in (4,5) and chk00 == 0) or
                            continue
                        err_page = mssql_check.err_page()
                        err_page.blk_no = offset//8192
                        err_page.page_off = offset
                        err_page.page_no = data2[15]
                        err_page.page_type = data2[1]
                        err_page.chk_err = chk_err
                        self.err_pages.append(err_page)
            #            print("Error:%d page: %d, %s"%(err,i*1024+ii+start_pg_no,chk_err))
                        err += 1

            elif(i == loop_1) :   # 处理文件尾部不足buffer的块
                for ii in range(0,loop_2_1):
                    chk = 0; chk0 = 0; chk00 = 1;chk_err = ''
                    pos1 = ii*page_size
                    data1 = data[pos1:pos1+page_size]
                    data2 = s("<4B2HIHHIHHI2HIH",data1[0:38])
                    data3 = s("<B",data1[5:6])                  # check_type
                    chk1 = mssql_check.mssql_page_check_1(data1)
                    offset = i*buff_size + ii*page_size
                    if offset > f_size - page_size :
                        break
                    if data2[15] == (i*loop_2+ii+self.start_pg_no) :     # 页的物理位置正确
                        chk0 = 1
                    else:
                        chk0 = 0
                        chk_err += 'page#,'
                    if chk1 == 1 : # 页头正确
                        a = 0
                    else:
                        chk_err += 'header,'

                    if data3[0]%4 == 1 :                                # 校验类型为残缺页校验
                            chk3 = mssql_check.mssql_page_check_3(data1)    # 残缺页校验
                            if chk3 == 1 :
                                data1 = mssql_check.page_handle(data1)
                                chk4 = mssql_check.mssql_page_check_4(data1)    # 无校验页的校验，页尾校验
                                if chk4==1 and data2[1] != 15 and data2[15] >0 :
                                    chk = 1
                                elif chk4==1 and data2[1] == 15 and data2[15]==0 :
                                    chk = 1
                                else:
                                    chk = 0
                                    chk_err += '页尾校验,'
                            else:
                                chk = 0
                                chk_err += '残缺页校验,'
                    elif data3[0]%4 == 2 :  # 校验类型为checksum
                        if chk1 == 1:   # 页头正确
                            chk2 = mssql_check.mssql_page_check_2(data1)    # checksum 校验
                            if chk2 == 1:
                                chk = 1
                            else:
                                chk = 0
                                chk_err += 'checksum,'
                    elif data3[0]%4 == 0 : # 校验类型为 无校验
                            chk4 = mssql_check.mssql_page_check_4(data1)
                            if chk4==1 and data2[1] != 15 and data2[15] >0 :
                                chk = 1
                            elif chk4==1 and data2[1] == 15 and data2[15]==0 :
                                chk = 1
                            else:
                                chk = 0
                                chk_err += '页尾校验,'
                    else:
                        chk = 0
                        chk_err += 'unknow,'
                    if data2[0] == 0 and data2[1] == 0:
                        chk00 = 0
                        chk_err = '全零,'

                    if chk == 1 :   # 统计信息
                            if data2[1] == 1 :
                                page_1 += 1
                            elif data2[1] == 15 :
                                page_15 += 1
                            elif data2[1] == 2 :
                                page_2 += 1
                            elif data2[1] == 3 :
                                page_3 += 1
                            elif data2[1] == 10 :
                                page_10 += 1
                            sum += 1
                      #      cursor.execute("insert into mssql_page(offset,page_type,page_no,file_no) values(?,?,?,?)",(offset,data2[1],data2[15],data2[16]))
                            if sum%10000 == 0 :  # 每10000条commit一次, 频繁提交会影响I/O速度 　
                                    conn.commit()
                    elif (chk1 != 1 or chk0 != 1 or chk00 == 0 or chk == 0) and gam[offset//8192//8] == 0:
                        if (offset//8192 in (4,5) and chk00 == 0) or pfs[offset//8192] == 0:  #
                            continue
                        err_page = mssql_check.err_page()
                        err_page.blk_no = offset//8192
                        err_page.page_off = offset
                        err_page.page_no = data2[15]
                        err_page.page_type = data2[1]
                        err_page.chk_err = chk_err
                        self.err_pages.append(err_page)
                   #     print("Error:%d page: %d, %s"%(err,i*1024+ii+start_pg_no,chk_err)) # 测试用
                        err += 1

            if i%(loop_1//1000+1) == 0 or i==loop_1 or i==0:  # 输出扫描进度
                progress = ((i+1)/(loop_1+1))*100
                self.PUP.emit(progress)
                self.LUP.emit(" Percent:%5.1f%%"%(progress))
                print("Buffer:%d/%d; Percent:%5.1f%%; err:%d \r"%(i,loop_1,progress,err),end="")

        conn.commit(); cursor.close(); conn.close()
        f.close()
        end = time.time()
        print("\n总页数:%d; 数据页:%d,索引页:%d,LOB页:%d,IAM页:%d,文件头:%d "%(sum,page_1,page_2,page_3,page_10,page_15))
        print("File size: %5.1f G, I/O: %4.1f M/s"%(f_size/1024/1024/1024,f_size/1024/1024/(end-begin+1)))

    def get_return(self):
        return self.err_pages

    # 解析 GAM,SGAM 页，获取分配信息
    def gam_info(self,f):
        gam = [];sgam = []
        f_size = os.path.getsize(f.name)
        gam_sum = (f_size//4188012544)+1
        for i in range(gam_sum):
            if i == 0:
                off = 8192*2
            else:
                off = 511232*8192*(i)
            f.seek(off)
            data = f.read(8192*2)
            data1 = s('7988B',data[194:194+7988])
            data2 = s('7988B',data[8192+194:8192+194+7988])
            for i in range(len(data1)):
                for ii in range(8):
                    d1 = data1[i]>>ii
                    d1_1 = d1&0x01
                    gam.append(d1_1)
                    d2 = data2[i]>>ii
                    d2_1 = d2&0x01
                    sgam.append(d2_1)
        return gam,sgam

    # 解析 pfs 页，获取分配信息
    def pfs_info(self,f):
        pfs = [];off = 0
        f_size = os.path.getsize(f.name)
        gam_sum = (f_size//66256896)+1
        for i in range(gam_sum):
            if i == 0:
                off = 8192*1
            else:
                off = 8088*8192*i
            f.seek(off)
            data = f.read(8192)
            data1 = s('8088B',data[100:100+8088])
            for i in range(len(data1)):
                    d1 = data1[i]>>6
                    d1_1 = d1&0x01
                    pfs.append(d1_1)
        return pfs

