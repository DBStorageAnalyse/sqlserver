# -*- coding: utf-8 -*-
# 把碎片导出为文件.由sqlite数据库表给出碎片位置
import sqlite3,time

# 按查询位置输出为mdf
def data_out1(file_in,file_out,db_name,out_sql):  # 源文件，目标文件，数据库
    begin = time.time()
    print("Out Begin Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(begin)))
    f1 = open (file_in,'rb')
    f2 = open(file_out,'w+b')
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
   # out_sql = "select offset_1,offset_2,page_no_1 from link_1 where page_sum>0 order by page_no_1"
    cursor.execute(out_sql)
    buffer_size = 1024*1024*8  # 8M 的buffer
    for i,val in enumerate(cursor):
        print("out: %d \r"%(i),end="")
        start_pos = val[0]
        end_pos = val[1] + 8192
        f2_off = val[2]*8192
        f2.seek(f2_off)
        loop1 = (end_pos - start_pos)//buffer_size  #
        for ii in range(loop1+1):
            if ii == loop1:     # 最后的不足buffer的
                f1.seek(start_pos+ii*buffer_size)
                data = f1.read(end_pos - start_pos-ii*buffer_size)
                f2.write(data)
            else:               # 碎片中的整buffer的
                f1.seek(start_pos+ii*buffer_size)
                data = f1.read(buffer_size)
                f2.write(data)
    conn.close()
    f1.close()
    f2.close()
    end = time.time()
    print("\nOut End Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(end)))  # current time
    print("Used time: %d:"%((end-begin)//3600) + time.strftime('%M:%S',time.localtime(end-begin))) # 用时
    return 0

# 按页号位置输出为mdf
def data_out2(file_in,file_out,db_name,out_sql):  # 源文件，目标文件，数据库
    begin = time.time()
    print("Datetime: " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(begin)))
    f1 = open (file_in,'rb'); f2 = open(file_out,'w+b')
    conn = sqlite3.connect(db_name); cursor = conn.cursor()
    pagesize = 8192
   # cursor.execute("select offset_1,offset_2,page_no_1 from link_1 where file_no_1=20 order by page_no_1,page_sum desc,offset_1") # order by page_no_1
    cursor.execute(out_sql)
    buffer_size = 1024*1024*8       # 8M 的buffer
    for i, val in enumerate(cursor):
        print("out: %d \r "%i,end="")
        start_pos = val[0]
        end_pos = val[1] + pagesize
        f2_off = val[2]*pagesize
        f2.seek(f2_off)
        loop1 = (end_pos - start_pos)//buffer_size
        for ii in range(0,loop1+1):
            if ii == loop1 :
                f1.seek(start_pos+ii*buffer_size)
                data = f1.read(end_pos - start_pos-ii*buffer_size)
                f2.write(data)
            else:
                f1.seek(start_pos+ii*buffer_size)
                data = f1.read(buffer_size)
                f2.write(data)
    conn.close()
    f1.close()
    f2.close()
    end = time.time()
    print("\nDatetime: " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(end)))  # current time
    print("Used time: %d:"%((end-begin)//3600) + time.strftime('%M:%S',time.localtime(end-begin))) # 用时
    return 0


# file_in = r'H:\Free space'
# file_out = r'H:\aaaa'
# db_name = r'H:\Free space.1.db'
# data_out1(file_in,file_out,db_name)

