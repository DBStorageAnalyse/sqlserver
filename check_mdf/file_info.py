# -*- coding: utf-8 -*-
# 获取数据库文件信息, 用在link_2
import sqlite3, struct, os.path
import mssql_check

s = struct.unpack  # B H I


# 首页， 获取文件的大小
def file_info_1(data):
    slot = s("<H", data[8190:8192])
    file_type = ''
    f_type = s("<I", data[slot[0] + 4:slot[0] + 8])
    type = {0: 'mdf', 1: 'ndf', 2: 'ldf'}
    if f_type[0] in (0, 1, 2):
        file_type = type[f_type[0]]
    data_1 = data[slot[0]:slot[0] + 200]
    off_0 = data_1.find(b'\xff\xff\xff\xff', 0, -1)
    f_no, g_no, f_size1 = s("<2HI", data[slot[0] + off_0 - 8:slot[0] + off_0])

    return f_no, g_no, f_size1, file_type


# boot页，获取数据库名称，数据库版本.
def file_info_2(data):
    version2, version1 = s("<2H", data[100:104])
    try:
        db_name = str(data[148:400], encoding="utf-16").rstrip('†')  # 数据库名
    except UnicodeDecodeError:
        db_name = ''
    return db_name, version1, version2


# 08表，获取数据库文件路径, 32页
def file_info_3(data):
    data1 = s("<H", data[22:24])  # 记录数量
    for i in range(0, data1[0]):
        sl = s("<H", data[(8190 - i * 2):(8192 - i * 2)])
        slot = sl[0]
        f_no = s("<H", data[slot + 8:slot + 10])
        f_name = str(data[slot + 10:slot + 266], encoding="utf-16").rstrip()  # utf-16
        f_path = str(data[slot + 266:slot + 786], encoding="utf-16").rstrip()
        #     print("f_no:%d, f_name:%s, f_path:%s "%(f_no[0],f_name,f_path))
        if i == 0:
            return f_name, f_path


# 文件信息汇总
def file_info_all(f, page_no_1, page_no_2):
    data1 = [];
    data2 = [];
    data3 = []
    file_type = '';
    f_name = '';
    f_path = '';
    f_no = 0;
    g_no = 0;
    f_size1 = 0;
    version1 = 0;
    version2 = 0;
    pos = 0
    file_info1 = mssql_check.file_info()
    if page_no_1 == 0:
        f.seek(pos)
        if page_no_2 < 9:
            data = f.read(8192)
            data1 = data[0:8192]  # 首页
        if page_no_2 >= 9 and page_no_2 < 32:
            data = f.read(8192 * 10)
            data1 = data[0:8192]  # 首页
            data2 = data[8192 * 9:8192 * 10]  # boot页
        if page_no_2 >= 32:
            data = f.read(8192 * 33)
            data1 = data[0:8192]  # 首页
            data2 = data[8192 * 9:8192 * 10]  # boot页
            data3 = data[8192 * 32:8192 * 33]  # 08表数据页
    elif page_no_1 > 0 and page_no_1 <= 9 and page_no_2 >= 9:
        pos1 = pos + (9 - page_no_1) * 8192
        f.seek(pos1)
        data2 = f.read(8192)  # boot页
        if page_no_2 >= 32:
            pos2 = pos + (32 - page_no_1) * 8192
            f.seek(pos2)
            data3 = f.read(8192)  # 08表数据页
    elif page_no_1 > 9 and page_no_1 <= 32 and page_no_2 >= 32:
        pos = pos + (32 - page_no_1) * 8192
        f.seek(pos)
        data3 = f.read(8192)  # 08表数据页

    version1 = 0;
    version2 = 0;
    db_name = ''
    if len(data2):
        chk_type = s("B", data2[5:6])
        if chk_type[0] % 4 == 1:  # 处理残缺页校验的页数据
            data2 = mssql_check.page_handle(data2)
        db_name, version1, version2 = file_info_2(data2)  # boot页，获取数据库名称，数据库版本.
    if len(data1):
        chk_type = s("B", data1[5:6])
        if chk_type[0] % 4 == 1:  # 处理残缺页校验的页数据
            data1 = mssql_check.page_handle(data1)
        f_no, g_no, f_size1, file_type = file_info_1(data1)  # 首页，获取文件的大小
    if len(data3):
        chk_type = s("B", data3[5:6])
        if chk_type[0] % 4 == 1:  # 处理残缺页校验的页数据
            data3 = mssql_check.page_handle(data3)
        f_name, f_path = file_info_3(data3)  # 08表，获取数据库文件路径,32页
    file_info1.f_name = f.name  # 获取文件名
    file_info1.file_type = file_type
    file_info1.db_name = db_name
    file_info1.f_logic_name = f_name
    file_info1.f_logic_path = f_path
    file_info1.f_no = f_no
    file_info1.g_no = g_no
    file_info1.f_size0 = os.path.getsize(f.name)  # 获取文件名
    file_info1.f_size1 = f_size1  # page_sum
    file_info1.version1 = version1  # 创建版本
    file_info1.version2 = version2  # 现在版本
    return file_info1


# 碎片link_1后的文件头信息， 在此 没有用
def get_info(db_name, f_name):  # sqlite数据库名，源文件名
    f = open(f_name, 'rb')
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(
        "select offset_1,page_no_1,page_no_2,file_no_1,page_sum from link_1 where page_no_1<10 and page_no_2>=0 order by page_sum desc")  # 从link1中读记录
    values = cursor.fetchall()
    len1 = len(values)
    print('\n================================== Page_Header SUM: %d ==================================' % len1)
    a = 0
    for i in range(0, len1):
        pos = values[i][0]
        page_no_1 = values[i][1]
        page_no_2 = values[i][2]
        if page_no_1 < 10:
            a += 1
            print('\nID:%d ,' % a, end='')
            file_info_all(f, pos, page_no_1, page_no_2)
    conn.close()
    f.close()
