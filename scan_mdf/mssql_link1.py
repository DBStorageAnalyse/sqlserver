# -*- coding: utf-8 -*-
# sql server 物理拼接碎片, 物理连续的页(中间间隔小于8个页的)和半页拼接
import sqlite3, struct, time
import mssql_check, file_info


class INFO():
    def __init__(self):
        self.page_sum = 0
        self.link1_sum = 0


def link_1(db_name, logging):  # sqlite数据库名。 连续的页拼接，很消耗内存
    print("1.select in memory. Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    logging.info("1.select in memory. Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("select offset,page_no,file_no from mssql_page where file_no=1")
    v_2 = []
    v_1 = cursor.fetchall()  # 取出数据, 里边的成员不能修改
    v_1.append(v_1[0])  # 多插一个进去
    len1 = len(v_1)
    info = INFO()
    info.page_sum = len1 - 1
    # print("v_1:%d m"%(v_1.__sizeof__()/1024/1024))      # 内存量
    # print('offset:%d, len(v_1): %d'%(v_1[len1-1].offset,len1))
    page_sum = 0
    print("3.bigen 合并. Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    logging.info("3.bigen 合并. Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    for i in range(0, len1 - 1):  # 太多了，注意性能，，
        if i % 100000 == 0:
            print("i:%d/%d; Percent:%5.1f%%;  \r" % (i, len1, (i / (len1 + 1)) * 100), end="")
        if i == 0:  # 第一个页
            aa_2 = mssql_check.values2()
            aa_2.offset_1 = v_1[0][0]
            aa_2.page_no_1 = v_1[0][1]
            aa_2.file_no_1 = v_1[0][2]
            v_2.append(aa_2)
            del aa_2
        #    拼碎片
        bool_1 = (v_1[i][2] == v_1[i + 1][2]) and (v_1[i + 1][0] - v_1[i][0]) / 8192 == (
                    v_1[i + 1][1] - v_1[i][1]) and (v_1[i + 1][1] - v_1[i][1]) > 0 and (v_1[i + 1][1] - v_1[i][1]) <= 8
        # 合并的中间不是页的要清零，防止解析记录是=时的干扰。
        if bool_1 == 1:
            v_2[-1].offset_2 = v_1[i][0]
            v_2[-1].page_no_2 = v_1[i][1]
            v_2[-1].file_no_2 = v_1[i][2]
            if v_2[-1].page_sum == 1:
                v_2[-1].offset_1 = v_1[i][0]
                v_2[-1].page_no_1 = v_1[i][1]
                v_2[-1].file_no_1 = v_1[i][2]
                v_2[-1].page_sum = 2
            if v_2[-1].file_no_1 == 0:
                v_2[-1].file_no_1 = v_1[i + 1][2]
            if v_2[-1].file_no_2 == 0:
                v_2[-1].file_no_2 = v_1[i + 1][2]
        if bool_1 == 0:
            v_2[-1].offset_2 = v_1[i][0]
            v_2[-1].page_no_2 = v_1[i][1]
            v_2[-1].file_no_2 = v_1[i][2]
            v_2[-1].page_sum = v_2[-1].page_no_2 - v_2[-1].page_no_1 + 1
            aa_2 = mssql_check.values2()  # 下一个碎片开始
            aa_2.offset_1 = v_1[i + 1][0]
            aa_2.page_no_1 = v_1[i + 1][1]
            aa_2.file_no_1 = v_1[i + 1][2]
            aa_2.offset_2 = v_1[i + 1][0]
            aa_2.page_no_2 = v_1[i + 1][1]
            aa_2.file_no_2 = v_1[i + 1][2]
            aa_2.page_sum = 1
            if i != len(v_1) - 2:
                v_2.append(aa_2)
            del aa_2
    del v_1
    info.link1_sum = len(v_2)
    # link_1记录片段信息：片段号，片段中页数，起始页信息(物理偏移，页号，文件号)，结束页信息(物理偏移，页号，文件号)
    cursor.execute(
        "create table link_1(id integer primary key,offset_1,offset_2,page_sum,page_no_1,page_no_2,file_no_1,g1_id,g1in_id,s_pos,e_pos)")
    print("4.bigen insert. Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    logging.info("4.bigen insert. Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    for i in range(0, len(v_2)):
        cursor.execute(
            "insert into link_1(page_sum,offset_1,page_no_1,offset_2,page_no_2,file_no_1) values(?,?,?,?,?,?)",
            (v_2[i].page_sum, v_2[i].offset_1, v_2[i].page_no_1, v_2[i].offset_2, v_2[i].page_no_2, v_2[i].file_no_1))
        if i % 10000 == 0:
            print("i:%d/%d; Percent:%5.1f%%;  \r" % (i, len(v_2), (i / len(v_2)) * 100), end="")
            conn.commit()
    conn.commit()
    cursor.close()
    conn.close()
    print("5.over. Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    logging.info("5.over. Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    return info


def link_2(f_name, db_name, logging):  # 源文件名，sqlite数据库名
    f = open(f_name, 'rb')
    begin = time.time()
    print('f_name:%s,db_name:%s' % (f_name, db_name))
    print("1.select Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(begin)))  # current time
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("select offset_1,offset_2,page_no_1,page_no_2,file_no_1 from link_1 order by page_no_1")  # 从前向后拼接
    values = cursor.fetchall()  # 取出数据
    v_1 = []  # 就是用来修改的
    page_size = 8192
    print("2.begin in memory. Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    for i in range(0, len(values)):
        aa_1 = mssql_check.values2()
        aa_1.offset_1 = values[i][0]
        aa_1.offset_2 = values[i][1]
        aa_1.page_no_1 = values[i][2]
        aa_1.page_no_2 = values[i][3]
        aa_1.file_no_1 = values[i][4]
        v_1.append(aa_1)
        del aa_1
    v_1.append(v_1[0])
    del values
    g_id = 0
    print("3.bigen 合并. Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    for i in range(0, len(v_1) - 1):  # 外循环， 注意性能，小心内存。 很慢 ++++++++++++++
        if v_1[i].page_sum == 5:  # 标记 update过的
            continue
        else:
            g_id += 1
            gin_id = 1
            cursor.execute("update link_1 set g1_id=%d,g1in_id=%d,s_pos=%d,e_pos=%d where offset_1=%d " % (
            g_id, gin_id, 0, 0, v_1[i].offset_1))
        # conn.commit()
        # print(" i: %d; \r"%i,end="")
        offset = v_1[i].offset_2 + page_size
        f.seek(offset)
        data1 = f.read(page_size)  # 取出碎片尾的页, 看它是否为一个半页
        chk1 = mssql_check.mssql_page_check_1(data1)  # 特征值校验
        data3 = struct.unpack("<B", data1[5:6])  # chk_type
        data4 = struct.unpack("<IH", data1[32:38])  # page_no,file_no
        bool = chk1 == 1 and data4[0] == v_1[i].page_no_2 + 1 and data4[1] == v_1[i].file_no_1  # 是否是半页
        for ii in range(i + 1, len(v_1) - 1):  # 内循环
            if (bool and v_1[ii].page_no_1 == v_1[i].page_no_2 + 2 and v_1[i].file_no_1 == v_1[ii].file_no_1):
                pos = 0  # 进行半页面组合
                f.seek(v_1[ii].offset_1 - page_size)
                data2 = f.read(page_size)  # 取出碎片前的半页。
                if data3[0] % 4 == 2:
                    for i1 in range(0, 15):  # 连接半页
                        data = data1[0:512 * (i1 + 1)] + data2[512 * (i1 + 1):512 * (16)]
                        chk = mssql_check.mssql_page_check_2(data)
                        if chk == 1:  # 通过校验
                            pos = i1 + 1
                            break
                elif data3[0] % 4 == 1:
                    for i2 in range(0, 15):
                        data = data1[0:512 * (i2 + 1)] + data2[512 * (i2 + 1):512 * (16)]
                        chk = mssql_check.mssql_page_check_3(data)
                        if chk == 1:  # 通过校验
                            pos = i2 + 1
                            break
                else:
                    pos = 0

                if pos != 0:  # 如果找到了连续的碎片
                    gin_id += 1
                    v_1[i].page_no_2 = v_1[ii].page_no_2
                    cursor.execute("update link_1 set g1_id=%d,g1in_id=%d,s_pos=%d,e_pos=%d where offset_1=%d " % (
                    g_id, gin_id, (16 - pos), 0, v_1[ii].offset_1))
                    cursor.execute("update link_1 set e_pos=%d where offset_1=%d " % (pos, v_1[i].offset_1))
                    v_1[ii].page_sum = 5

            elif v_1[ii].page_no_1 > v_1[i].page_no_2 + 2:
                break
            else:
                if v_1[ii].page_sum == 5:
                    continue
        if i % 10000 == 0:  # 每10000条commit一次, 频繁提交会影响I/O速度 　
            conn.commit()
    del v_1
    conn.commit()
    cursor.close()
    conn.close()
    f.close()
    link_2_1(db_name)  # 生成 link_2 表
    print("4.ok   Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(begin)))


def link_2_1(db_name):  # 生成 link_2表
    # select offset_1,page_sum,page_no_1,page_no_2 from link_1 where file_no_1 = 1 order by page_no_1 desc #  # 逆序 拼接
    # 对结果集进行聚合。
    # create table aa1 as select count(*) b_count,group_id,start_pos,start_page from link_1 group by g_id;
    # create table aa2 as select group_id,end_page from by_gfile where gin_id=1;
    # create table aa3 as select a.*,b.end_page,(b.end_page-a.start_page) page_count from aa1 a,aa2 b where a.group_id=b.group_id;
    # drop table aa1; drop table aa2;
    # 正序 拼接
    # select offset_1,page_sum,page_no_1,page_no_2 from link_1 where file_no_1 = 1 order by page_no_1  # 先排序下（可不需要）

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("create table aa1 as select g1_id,file_no_1,page_no_2,offset_2 from link_1 group by g1_id;")
    cursor.execute("create table aa2 as select g1_id,offset_1,page_no_1 from link_1 where g1in_id=1;")
    cursor.execute(
        "create table link_2 as select b.g1_id,(a.page_no_2-b.page_no_1+1) page_sum,b.offset_1,a.offset_2,b.page_no_1,a.page_no_2,a.file_no_1 from aa1 a,aa2 b where a.g1_id=b.g1_id;")
    cursor.execute("alter table link_2 add g2_id int;")
    cursor.execute("alter table link_2 add g2in_id int;")
    cursor.execute("drop table aa1;")
    cursor.execute("drop table aa2;")
    conn.commit();
    cursor.close();
    conn.close()


def link_wl(f_name, db_name, logging):  # 物理拼接汇总
    info = link_1(db_name, logging)  # 物理连续拼接
    link_2(f_name, db_name, logging)  # 半页拼接
    file_infos = file_info.get_info(db_name, f_name)  # 获取碎片中(有头部)的数据库文件信息
    print(
        "\n物理拼接(link_1,link_2,link_3)完成...Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    logging.info(
        "\n物理拼接(link_1,link_2,link_3)完成...Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

    return file_infos, info

# f_name = r'.\test\DB_002_Data.MDF'
# db_name = r'.\test\DB_002_Data.db'
# link_2(f_name,db_name)              # 半页拼接
# link_2_1(db_name)                   # 生成 link_2表
# file_info.get_info(db_name,f_name)  # 获取数据库文件信息
