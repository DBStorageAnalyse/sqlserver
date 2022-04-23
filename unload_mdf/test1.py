# -*- coding: utf-8 -*-
import os.path, struct, sqlite3
import table_struct, pymssql, page

s = struct.unpack


# 测试 表的页面 链接
def init_link(f, tab_data_07):
    tab_data_22 = 0
    for i in range(0, len(tab_data_07)):
        for ii in range(0, tab_data_07[i].rec_sum):
            if tab_data_07[i].record[ii].col_data1[2] == 281474978938880 and tab_data_07[i].record[ii].col_data1[
                1] == 1:  # 22 表
                # ownerid：281474978938880 （22表） 327680 （05表）458752（07表） 281474979397632（29表） 281474977562624（0D表）281474979987456（1D表）
                pgfirst = tab_data_07[i].record[ii].col_data2[5]
                print(pgfirst)
                tab_data_22 = page_link1(f, pgfirst)
                print('afdff')


def page_link1(f, pgfirst):  # 文件，要解析的页链的起始页面号， 测试 链接
    page_size = 8192
    f_size = os.path.getsize(f.name)  # 获取文件大小，只能处理文件,不能磁盘
    f_pg_size = f_size // 8192
    next_page = pgfirst
    while (next_page != 0 and next_page < f_pg_size):  # 下一页不溢出
        pos1 = (next_page) * page_size
        f.seek(pos1)  # 要判断返回值，是否成功
        data = f.read(page_size)
        data1 = data[0:page_size]
        data3 = s('<I', data1[24:28])  # obj_id
        print('page_no: %d, obj_id: %d ===========' % (next_page, data3[0]))
        #  page1 = page.record(data1,table)  # 解析页面记录.  ***************
        data2 = s('<I', data1[16:20])
        next_page = data2[0]  # 下一页的页号


# 扫描所有的页面，解析obj_id符合的页面
def page_scan(f, tab):
    page_size = 8192;
    page_sum = 0
    f_size = os.path.getsize(f.name)  # 获取文件大小，只能处理文件,不能磁盘
    f_pg_size = f_size // 8192
    tables = [];
    tab_data = []
    tables.append(tab)
    for i in range(0, f_pg_size):  # 下一页不溢出
        pos1 = i * page_size
        f.seek(pos1)  # 要判断返回值，是否成功
        data = f.read(page_size)
        data1 = data[0:page_size]
        data2 = s('<H', data1[6:8])  # ind_id，auid_ind_id
        data3 = s('<I', data1[24:28])  # obj_id，auid_obj_id
        data4 = s('<I', data1[16:20])  # page_no
        for tab in tables:
            if data3[0] == tab.auid_obj_id and data2[0] == 256:
                page_sum += 1
                #   tab.pgfirst = page_sum
                page1 = page.record_2(f, data1, tab)  # 解析页面记录.  ***************
                tab_data.append(page1)
        del data, data1
    print('i:%d, page_no:%d, obj_id:%d, ind_id:%d, page_sum:%d ===========\r' % (
    i, data4[0], data3[0], data2[0], page_sum))
    return tab_data


def init_tab(db):
    # 读取sqlite数据库表，获得配置信息 和 表结构信息
    # db = './db_info.db'           # 数据库文件名称
    conn = sqlite3.connect(db)  # 打开数据库
    cursor = conn.cursor()
    cursor.execute("select * from tab_info ")
    values_tab = cursor.fetchall()  # 返回数据为二维数组
    tables = []  #
    for i in range(len(values_tab)):  # 初始化表结构
        table1 = table_struct.st_table()
        table1.tab_obj_id = values_tab[i][1]
        table1.tab_name = values_tab[i][3]
        table1.col_sum = values_tab[i][4]
        table1.nullable_sum = values_tab[i][5]
        cursor.execute(
            "select c.* from tab_info t,col_info c where c.tab_obj_id = t.tab_obj_id and t.tab_obj_id=%d order by c.col_id" % table1.tab_obj_id)
        values_col = cursor.fetchall()
        if len(values_col) == 0:
            table1.col_sum = 0
        var_len_sum = 0  # 变长列数
        for ii in range(0, table1.col_sum):
            column1 = table_struct.st_column()
            column1.tab_obj_id = values_col[ii][1]
            column1.col_id = values_col[ii][2]
            column1.col_name = values_col[ii][3]
            column1.col_x_type = values_col[ii][4]
            column1.col_u_type = values_col[ii][5]
            column1.col_len = values_col[ii][6]
            column1.varlen_is = values_col[ii][12]
            table1.col.append(column1)
            if column1.varlen_is == 0:
                table1.col_1.append(column1)
            elif column1.varlen_is == 1:
                var_len_sum = var_len_sum + 1
        table1.var_len_sum = var_len_sum
        for ii in range(0, table1.col_sum):
            if table1.col[ii].varlen_is == 1:
                column1 = table1.col[ii]
                table1.col_1.append(column1)
        tables.append(table1)
    cursor.close()
    conn.close()
    return tables

# f = open (r'h:\aaaa.mdf','rb')
# db = r'.\tables.db'
# page_scan(f,db)

# conn = pymssql.connect(host="127.0.0.1\MSSQL2005",user="sa",password="bysjhf808.",database="master")
# cur=conn.cursor()
# cur.execute('select top 1 * from sysobjects;')
# print(cur.fetchall())
# data=cur.fetchall()
