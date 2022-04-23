# -*- coding: utf-8 -*-
#  mssqlcle 碎片扫描. 注意：有很多无校验的页，会引入一些的垃圾
from PyQt5.QtCore import QThread, pyqtSignal
import time, struct, sqlite3
import mssql_check

s = struct.unpack


# 扫描线程, 需要传参数
class Scan_1(QThread):  # 类Scan_1继承自 QThread
    PUP = pyqtSignal(int)  # 更新进度条的信号
    LUP = pyqtSignal(str)

    def __init__(self, parent=None):  # 解析函数
        super(Scan_1, self).__init__(parent)
        self.f_name = 0
        self.db_name = 0
        self.logging = 0
        self.start_off = 0
        self.end_off = 0
        self.endian = 0
        self.page_size = 0
        self.scan_size = 0
        self.file_infos = []

    def run(self):
        self.mssql_scan(self.f_name, self.db_name, self.logging, self.start_off, self.end_off, self.scan_size)

    def mssql_scan(self, f_name, db_name, logging, start_off, end_off, scan_size):  # 源文件名，扫描的起始字节，size，输出的sqlite数据库名
        begin = time.time()
        print("\n\nDatetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(begin)))  # current time
        logging.info("\n\nDatetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(begin)))
        print('f_name:%s, db_name:%s ' % (f_name, db_name))
        logging.info('f_name:%s\ndb_name:%s\n' % (f_name, db_name))
        f = open(f_name, 'rb')
        f1 = open(db_name, 'wb');
        f1.close()
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("create table mssql_page(id integer primary key,offset,page_type,obj_id,ind_id,page_no,file_no)")
        cursor.execute("create index ind_page on mssql_page(page_no,offset)")  # 创建索引

        scan_size = scan_size  # 扫描 的步长 ,精度, 影响I/O速度
        buff_size = 8 * 1024 * 1024  # buffer大小， 8M
        page_size = 8192  # 页面大小
        start = start_off  # //512*512   # 扫描起始偏移
        f_size = end_off - start
        loop_1 = f_size // buff_size
        loop_1_1 = f_size % buff_size
        loop_2 = buff_size // scan_size
        loop_2_1 = loop_1_1 // scan_size
        sum = 0;
        page_1 = 0;
        page_15 = 0;
        page_2 = 0;
        page_3 = 0;
        page_10 = 0;
        step = 0

        for i in range(0, loop_1 + 1):  # 扫描文件的所有buffer块
            f.seek(i * buff_size + start)
            data = f.read(buff_size + page_size)
            if (i < loop_1):  # 处理文件的所有buffer块
                for ii in range(0, loop_2):
                    if step <= 15 and step > 0:
                        step -= 1
                        continue
                    chk = 0
                    pos1 = ii * scan_size
                    data1 = data[pos1:pos1 + page_size]
                    data2 = s("<4B2HIHHIHHI2HIH", data1[0:38])
                    data3 = s("<B", data1[5:6])  # page_type
                    chk1 = mssql_check.mssql_page_check_1(data1)
                    if chk1 == 1:
                        if data3[0] % 4 == 2:  # 校验和校验
                            chk2 = 1  # mssql_check.mssql_page_check_2(data1)
                            if chk2 == 1:
                                chk = 1
                            else:
                                chk = 0
                        elif data3[0] % 4 == 1:  # 残缺页校验
                            chk3 = mssql_check.mssql_page_check_3(data1)
                            if chk3 == 1:
                                data1 = mssql_check.page_handle(data1)
                                chk4 = mssql_check.mssql_page_check_4(data1)  # 无校验页的校验,检验页尾行偏移
                                if chk4 == 1 and data2[1] != 15 and data2[15] > 0:
                                    chk = 1
                                elif chk4 == 1 and data2[1] == 15 and data2[15] == 0:
                                    chk = 1
                        elif data3[0] % 4 == 0:  # 无校验。 尽量避免掉此类页面的干扰
                            chk4 = mssql_check.mssql_page_check_4(data1)
                            if chk4 == 1 and data2[1] != 15 and data2[15] > 0:
                                chk = 1
                            elif chk4 == 1 and data2[1] == 15 and data2[15] == 0:
                                chk = 1
                        else:
                            chk = 0

                        if chk == 1:  # 统计信息
                            if data2[1] == 1:  # 数据页
                                page_1 += 1
                            elif data2[1] == 15:
                                page_15 += 1
                            elif data2[1] == 2:
                                page_2 += 1
                            elif data2[1] == 3:
                                page_3 += 1
                            elif data2[1] == 10:
                                page_10 += 1
                            offset = i * buff_size + ii * scan_size
                            sum += 1
                            step = 15
                            cursor.execute(
                                "insert into mssql_page(offset,page_type,obj_id,ind_id,page_no,file_no) values(?,?,?,?,?,?)",
                                (offset, data2[1], data2[12], data2[5], data2[15], data2[16]))
                            if sum % 10000 == 0:  # 每10000条commit一次, 频繁提交会影响I/O速度 　
                                conn.commit()
            elif (i == loop_1):  # 处理文件尾部不足buffer的块
                for ii in range(0, loop_2_1):
                    if step <= 15 and step > 0:
                        step -= 1
                        continue
                    chk = 0
                    pos1 = ii * scan_size
                    data1 = data[pos1:pos1 + page_size]
                    data2 = s("<4B2HIHHIHHI2HIH", data1[0:38])
                    data3 = s("<B", data1[5:6])  # page_type
                    chk1 = mssql_check.mssql_page_check_1(data1)
                    offset = i * buff_size + ii * scan_size
                    if offset > f_size - page_size:
                        break
                    if chk1 == 1:
                        if data3[0] % 4 == 2:
                            chk2 = 1  # mssql_check.mssql_page_check_2(data1)
                            if chk2 == 1:
                                chk = 1
                            else:
                                chk = 0
                        elif data3[0] % 4 == 1:
                            chk3 = mssql_check.mssql_page_check_3(data1)
                            if chk3 == 1:
                                data1 = mssql_check.page_handle(data1)
                                chk4 = mssql_check.mssql_page_check_4(data1)
                                if chk4 == 1 and data2[1] != 15 and data2[15] > 0:
                                    chk = 1
                                elif chk4 == 1 and data2[1] == 15 and data2[15] == 0:
                                    chk = 1
                        elif data3[0] % 4 == 0:
                            chk4 = mssql_check.mssql_page_check_4(data1)
                            if chk4 == 1 and data2[1] != 15 and data2[15] > 0:
                                chk = 1
                            elif chk4 == 1 and data2[1] == 15 and data2[15] == 0:
                                chk = 1
                        else:
                            chk = 0

                        if chk == 1:
                            if data2[1] == 1:
                                page_1 += 1
                            elif data2[1] == 15:
                                page_15 += 1
                            elif data2[1] == 2:
                                page_2 += 1
                            elif data2[1] == 3:
                                page_3 += 1
                            elif data2[1] == 10:
                                page_10 += 1
                            sum += 1
                            step = 15
                            cursor.execute(
                                "insert into mssql_page(offset,page_type,obj_id,ind_id,page_no,file_no) values(?,?,?,?,?,?)",
                                (offset, data2[1], data2[12], data2[5], data2[15], data2[16]))

            if i % (loop_1 // 1000 + 1) == 0 or i == loop_1:  # 输出扫描进度
                progress = ((i + 1) / (loop_1 + 1)) * 100
                now = time.time()
                speed = i * 8 / (now - begin + 1)
                print("Buffer:%d/%d; Percent:%5.1f%%; Find:%d, %dM, I/O:%4.1fM/s\r" % (
                i, loop_1, progress, sum, sum * 8 // 1024, i * 8 / (now - begin + 1)), end="")
                self.PUP.emit(progress)  # 传递参数
                self.LUP.emit(" Buf:%d/%d,Percent:%4.1f%%, Find:%d=%dM, I/O:%4.1fM/s,Time:%dMin" % (
                i, loop_1, progress, sum, sum * page_size / 1024 / 1024, speed,
                ((loop_1 + 1 - i) * 8 / ((speed + 0.01) * 60) + 1)))  # 传递参数

        print("\n总页数:%d; 数据页:%d,索引页:%d,LOB页:%d,IAM页:%d,文件头:%d " % (
        sum, page_1, page_2, page_3, page_10, page_15))  # 总页数,空页数,数据页数
        logging.info(
            "\n总页数:%d; 数据页:%d,索引页:%d,LOB页:%d,IAM页:%d,文件头:%d " % (sum, page_1, page_2, page_3, page_10, page_15))
        conn.commit();
        cursor.close();
        conn.close();
        f.close()
        end = time.time()
        print("Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end)), end='')  # current time
        print("\t Used time: %d:" % ((end - begin) // 3600) + time.strftime('%M:%S', time.localtime(end - begin)))  # 用时
        print(
            "File size: %6.2f G, I/O: %4.1f M/s" % (f_size / 1024 / 1024 / 1024, f_size / 1024 / 1024 / (end - begin)))
        logging.info("Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end)) + "\t 扫描完成,用时: %d:" % (
                    (end - begin) // 3600) + time.strftime('%M:%S', time.localtime(end - begin)))
        logging.info("File size:%6.2fG, 平均I/O:%4.1fM/s" % (
        f_size / 1024 / 1024 / 1024, f_size / 1024 / 1024 / (end - begin + 1)))

# #  f_name = "\\\\.\\PhysicalDrive1"
# f_name = r'C:\Users\zsz\PycharmProjects\sqlserver\scan_fragment\test\Landesk_1.MDF'
# db_name = r'C:\Users\zsz\PycharmProjects\sqlserver\scan_fragment\test\Landesk_1.db'
# end_off = 0
# mssql_scan(f_name,db_name,0,end_off,512)
