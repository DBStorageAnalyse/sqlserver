# -*- coding: utf-8 -*-
# sql server 拼接 页号连续的碎片, 用的 GAM 和 SGAM 筛选
import sqlite3,time,struct
s = struct.unpack   # B H I

def link_3(f_name,db_name):  # 源文件名，sqlite数据库名
    f = open (f_name,'rb')
    begin = time.time()
    print("1.Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(begin)))  # current time
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("select g1_id,offset_1,page_no_1,page_no_2,file_no_1 from link_2 order by page_no_1")  # 从前向后拼接
    values = cursor.fetchall()  # 取出数据
    v_1 = []  # 就是用来修改的
    page_size = 8192
    for i in range(0,len(values)):
        aa_1 = init.values2()
        aa_1.offset_1 = values[i][1]
        aa_1.page_no_1 = values[i][2]
        aa_1.page_no_2 = values[i][3]
        aa_1.file_no_1 = values[i][4]
        v_1.append(aa_1)
        del aa_1
    v_1.append(v_1[0])
    del values
    print('开始 拼接......')
    g_id = 0
    for i in range(0,len(v_1)-1):  # 外循环， 注意性能，小心内存。 很慢 ++++++++++++++
        if v_1[i].page_sum == 5:  # 标记 update过的
            continue
        else:
            g_id += 1
            gin_id = 1
            cursor.execute("update link_2 set g2_id=%d,g2in_id=%d where offset_1=%d "%(g_id,gin_id,v_1[i].offset_1))
        for ii in range(i+1,len(v_1)-1):    # 内循环
                if v_1[ii].page_no_1 == v_1[i].page_no_2 + 1 and v_1[i].file_no_1 == v_1[ii].file_no_1 :
                    page_1 = v_1[i].page_no_2
                    if (page_1+1) % 8 !=0 :
                        f.seek(v_1[i].offset_2)
                        data_1 = f.read(96)
                        data_1_1 = s('<H',data_1[6:8])
                        data_1_2 = s('<I',data_1[24:28])
                        f.seek(v_1[ii].offset_1)
                        data_2 = f.read(96)
                        data_2_1 = s('<H',data_2[6:8])
                        data_2_2 = s('<I',data_2[24:28])
                        if data_1_1[0] == data_2_1[0] and data_1_2[0] == data_2_2[0] :
                            gin_id += 1
                            cursor.execute("update link_2 set g2_id=%d,g2in_id=%d where offset_1=%d "%(g_id,gin_id,v_1[ii].offset_1))
                            v_1[ii].page_sum = 5
                    else:
                        gin_id += 1
                        cursor.execute("update link_2 set g2_id=%d,g2in_id=%d where offset_1=%d "%(g_id,gin_id,v_1[ii].offset_1))
                        v_1[ii].page_sum = 5
                elif v_1[ii].page_no_1 > v_1[i].page_no_2 + 1 :
                    break

        if i%1000 == 0 :  # 每10000条commit一次, 频繁提交会影响I/O速度 　
            conn.commit()
    del v_1
    conn.commit()
    cursor.close()
    conn.close()
    # f.close()
    print("2.Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(begin)))  # current time
    print('完成 拼接......')

def link_3_1(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("create table aa1 as select g2_id,file_no_1,page_no_2,offset_2 from link_2 group by g2_id;")
    cursor.execute("create table aa2 as select g2_id,offset_1,page_no_1 from link_2 where g2in_id=1;")
    cursor.execute("create table link_3 as select b.g2_id,(a.page_no_2-b.page_no_1+1) page_sum,b.offset_1,a.offset_2,b.page_no_1,a.page_no_2,a.file_no_1 from aa1 a,aa2 b where a.g2_id=b.g2_id;")
    cursor.execute("alter table link_3 add g3_id int;")
    cursor.execute("alter table link_3 add g3in_id int;")
    cursor.execute("drop table aa1;")
    cursor.execute("drop table aa2;")
    conn.commit(); cursor.close(); conn.close()
    print('完成 写入 link_3 ......')


f_name = r'C:\Users\zsz\PycharmProjects\sqlserver\scan_fragment\test\DB_002_Data.MDF'  # tt_type   dbLogTest pubs  A8_V10_2011  学生成绩管理系统  DB_002_Data
db_name = r'C:\Users\zsz\PycharmProjects\sqlserver\scan_fragment\test\DB_002_Data.db'     #   30547 总页数: 528; 数据页: 239, page_2:98, page_3:84, page_10:98, 文件头: 1
# f_name = r'K:\pos_40g\free_2'
# db_name = r'K:\pos_40g\free_2.db'

link_3(f_name,db_name)      # 拼接 页号连续的
link_3_1(db_name)           # 生成 link_3表

