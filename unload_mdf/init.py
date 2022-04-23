# -*- coding: utf-8 -*-
# 有系统表的从系统表中读取表结构信息放到 sqlite中(或不取),没有系统表的从sql文件或ini文件中获取系统表信息存储到sqlite中,
# 再 从sqlite库里读取表结构到结构体中 ,来初始化表结构. sqlite中的 table 和 column表
import sqlite3,os.path,struct,pyodbc
import page,table_struct    # test1
s = struct.unpack

# 解析首页
def file_blk_0(data):
    file_info = table_struct.File_Info()
    try:
        page1,data = page.page_init(data)
        off_set = page1.page_slot[0]
        file_type = {0:'mdf',1:'ndf',2:'ldf'}
        f_type = s("<I",data[off_set+4:off_set+8])
        file_info.f_type = file_type[f_type[0]]
        f_1 = s("<2HI",data[off_set+126:off_set+134])
        if f_1[2] == 4294967295:
            f_1 = s("<2HI",data[off_set+122:off_set+130])
        file_info.f_no = f_1[0]
        file_info.gp_id = f_1[1]
        file_info.blk_sum = f_1[2]
    except struct.error:
        return file_info
    return file_info
# 解析boot页
def file_blk_9(data):
    ver = {515:'7.0',539:'2000',611:'2005',655:'2008',661:'2008r2',706:'2012',782:'2014'}
    version1,version2 = s("<2H",data[100:104])
    first = s("<I",data[612:616])
    first_07 = first[0]
    if first_07 == 0:
        first_07 = 24
    db_name = (str(data[148:180],encoding="utf-16").rstrip(str(b'\x20\x20',encoding="utf-16"))).rstrip(str(b'\x00',encoding="ascii"))  # utf-8 ascii gbk
    collation = s("<I",data[488:492])
    db_collation = collation[0]         # 语言排序规则
    version1,version2 = ver[version1],ver[version2]
    return version1,version2,first_07,db_name

# 链式解析page
def page_link(f,pgfirst,table): #　文件，要解析的页链的起始页面号，表
    page_size = 8192
    f_size = os.path.getsize(f.name)  # 获取文件大小，只能处理文件,不能磁盘
    f_pg_size = f_size//8192
    next_page = pgfirst
    tab_data = []
    while(next_page != 0 and next_page<f_pg_size):  # 下一页不溢出
        pos1 = (next_page)*page_size
        f.seek(pos1)  # 要判断返回值，是否成功
        data = f.read(page_size)
        data1 = data[0:page_size]
        page1 = page.record(f,data1,table)  # 解析页面记录.  ***************
        tab_data.append(page1)
        data2 = s('<I',data1[16:20])
        next_page = data2[0]
        if len(tab_data)>500:
            next_page = 0
    return tab_data
# IAM位图式解析page，解析正常记录
def IAM_info(f,pgfirstiam,table):
        page_size = 8192; next_page = pgfirstiam
        f_size = os.path.getsize(f.name)  # 获取文件大小，只能处理文件,不能是磁盘
        f_pg_size = f_size//8192
        tab_data = []
        while(next_page != 0 and next_page<f_pg_size):  # 下一页不溢出
            page_1 = []; page_2 = []
            pos1 = (next_page)*page_size
            f.seek(pos1)
            data = f.read(page_size)
            data1 = data[0:page_size]
            data2 = s('<I',data[16:20])
            next_page = data2[0]
            slot_1 = s('<H',data1[page_size-4:page_size-2])
            iam_start = s('<I',data1[136:140])
            for i in range(8):
                data_1 = s('<IH',data1[142+i*6:148+i*6])
                if data_1[0] != 0:
                    page_1.append(data_1[0])
            data3 = data[slot_1[0]+4:slot_1[0]+4+7992]        # 位图
            for i in range(7992):
                if i*8*8 >= f_pg_size:
                    break
                for ii in range(8):
                    d1 = data3[i]>>ii
                    d1_1 = d1%2
                    if d1_1 == 1:
                        page_no1 = iam_start[0] + (i*8 + ii)*8
                        page_2.append(page_no1)
            for page_no in page_1:
                pos1 = (page_no)*page_size
                f.seek(pos1)
                data = f.read(page_size)
                data1 = data[0:page_size]
                if len(data1) == 0:
                    continue
                page_type = s('<B',data1[1:2])
                page_obj_id = s('<I',data1[24:28])
                if page_type[0] == 1 and page_obj_id[0] == table.auid_obj_id :
                    page1 = page.record(f,data1,table)  # 解析页面记录.  ***************
                    tab_data.append(page1)
            for page_no in page_2:
                for i in range(8):
                    pos1 = (page_no+i)*page_size
                    f.seek(pos1)
                    data = f.read(page_size)
                    data1 = data[0:page_size]
                    if len(data1) == 0:
                        continue
                    page_type = s('<B',data1[1:2])
                    page_obj_id = s('<I',data1[24:28])
                    if page_type[0] == 1 and page_obj_id[0] == table.auid_obj_id :
                        page1 = page.record(f,data1,table)  # 解析页面记录.  ***************
                        tab_data.append(page1)
                if len(tab_data)>100:   # 限制解析数量
                    break
        return tab_data
# IAM位图式解析page,解析删除记录
def IAM_info_2(f,pgfirstiam,table):
        page_size = 8192; next_page = pgfirstiam
        f_size = os.path.getsize(f.name)  # 获取文件大小，只能处理文件,不能是磁盘
        f_pg_size = f_size//8192
        tab_data = []
        while(next_page != 0 and next_page<f_pg_size):  # 下一页不溢出
            page_1 = []; page_2 = []
            print('IAM_info_2解析 %d 页...'%next_page)
            pos1 = (next_page)*page_size
            f.seek(pos1)
            data = f.read(page_size)
            data1 = data[0:page_size]
            data2 = s('<I',data[16:20])
            next_page = data2[0]
            slot_1 = s('<H',data1[page_size-4:page_size-2])
            iam_start = s('<I',data1[136:140])
            for i in range(8):
                data_1 = s('<IH',data1[142+i*6:148+i*6])
                if data_1[0] != 0:
                    page_1.append(data_1[0])
            data3 = data[slot_1[0]+4:slot_1[0]+4+7992]        # 位图
            for i in range(7992):
                if i*8*8 >= f_pg_size:
                    break
                for ii in range(8):
                    d1 = data3[i]>>ii
                    d1_1 = d1%2
                    if d1_1 == 1:
                        page_no1 = iam_start[0] + (i*8 + ii)*8
                        page_2.append(page_no1)
            for page_no in page_1:
                pos1 = (page_no)*page_size
                f.seek(pos1)
                data = f.read(page_size)
                data1 = data[0:page_size]
                if len(data1) == 0:
                    continue
                page_type = s('<B',data1[1:2])
                page_obj_id = s('<I',data1[24:28])
                if page_type[0] == 1 and page_obj_id[0] == table.auid_obj_id :
                    page1 = page.record_2(f,data1,table)  # 解析页面记录.  ***************
                    tab_data.append(page1)
            for page_no in page_2:
                for i in range(8):
                    pos1 = (page_no+i)*page_size
                    f.seek(pos1)
                    data = f.read(page_size)
                    data1 = data[0:page_size]
                    if len(data1) == 0:
                        continue
                    page_type = s('<B',data1[1:2])
                    page_obj_id = s('<I',data1[24:28])
                    if page_type[0] == 1 and page_obj_id[0] == table.auid_obj_id :
                        page1 = page.record_2(f,data1,table)  # 解析页面记录.  ***************
                        tab_data.append(page1)
                # if len(tab_data)>100:
                #     break
        return tab_data
# 扫描所有的页面，解析obj_id符合的页面
def page_scan(f,tab):
    page_size = 8192; page_sum = 0
    f_size = os.path.getsize(f.name)  # 获取文件大小，只能处理文件,不能磁盘
    f_pg_size = f_size//8192
    tab_data = []; re_sum = 0
    for i in range(0,f_pg_size):  # 下一页不溢出
        pos1 = i*page_size
        f.seek(pos1)  # 要判断返回值，是否成功
        data = f.read(page_size)
        data1 = data[0:page_size]
        data2 = s('<H',data1[6:8])      # ind_id，auid_ind_id
        data3 = s('<I',data1[24:28])    # obj_id，auid_obj_id
        data4 = s('<I',data1[32:36])    # page_no
        data5 = s('<B',data1[1:2])    # page_type
        if data3[0] == tab.auid_obj_id and data5[0] == 1 :     #256,1  and data2[0] == tab.auid_ind_id   tab.auid_obj_id  1113771025
            page_sum += 1
            page1 = page.record_2(f,data1,tab)  # 解析页面记录.  ***************
            page1 = page.record(f,data1,tab)  # 解析页面记录.  ***************
            tab_data.append(page1)
            re_sum += len(page1.record)
            print('i:%d, page_no:%d, obj_id:%d, ind_id:%d, page_sum:%d, re_sum：%d===========\r'%(i,data4[0],data3[0],data2[0],page_sum,re_sum))
    return tab_data

# 初始化数据库信息，包含07，09表结构
db1 = table_struct.st_db()
def init_sys(version):
    # 读取sqlite数据库表，获得配置信息 和 表结构信息
    db = './db_info.db'           # 数据库文件名称
    conn = sqlite3.connect(db)  # 打开数据库
    cursor = conn.cursor()
    cursor.execute("select * from tab_info order by id")
    values_tab = cursor.fetchall()      # 返回数据为二维数组

    db1.tab_sum = len(values_tab)  #
    for i in range(0,db1.tab_sum): # 初始化表结构
        table1 = table_struct.st_table()
        table1.tab_obj_id = values_tab[i][1]
        table1.auid_obj_id = table1.tab_obj_id
        table1.tab_name = values_tab[i][3]
        table1.col_sum = values_tab[i][4]
        table1.nullable_sum = values_tab[i][5]
        cursor.execute("select c.* from tab_info t,col_info c where c.tab_obj_id = t.tab_obj_id and t.tab_obj_id=%d order by c.col_id"%table1.tab_obj_id)
        values_col = cursor.fetchall()
        if len(values_col) == 0:
            table1.col_sum = 0
        var_len_sum = 0  # 变长列数
        for ii in range(0,table1.col_sum):
            column1 = table_struct.st_column()
            column1.tab_obj_id = values_col[ii][1]
            column1.col_id = values_col[ii][2]
            column1.col_name = values_col[ii][3]
            column1.col_x_type = values_col[ii][4]
            column1.col_u_type = values_col[ii][5]
            column1.col_len = values_col[ii][6]
            column1.varlen_is = values_col[ii][12]
            table1.col.append(column1)
            if column1.varlen_is == 1 :
                var_len_sum = var_len_sum + 1   # 变长列数
        table1.var_len_sum = var_len_sum
        if version in (2005,2012) and table1.tab_obj_id == 7 :  #sql2005/2012 的 07 表少一列
            del table1.col[-1]  #   删除最后一个
            table1.col_sum -= 1
        db1.tab.append(table1)
    cursor.close()
    conn.close()

# 初始化07表
def init_07(file_info,pgfirst):
    version = file_info.version1
    f = file_info.file
    init_sys(version)   # 初始化 db1
    db1.db_name = file_info.db_name
    db1.db_version = file_info.version1
    if version != '2000':
        tab_data_07 = page_link(f,pgfirst,db1.tab[0])
    elif version == '2000':
        tab_data_07 = page_link(f,pgfirst,db1.tab[2])   # 02 表
    return tab_data_07

# 初始化29表
def init_29(f,tab_data_07):
    tab_data_29 = []
    for i in range(len(tab_data_07)):
        for ii in range(len(tab_data_07[i].record)):
            if  tab_data_07[i].record[ii].col_data1[2] == 281474979397632 and tab_data_07[i].record[ii].col_data1[1] == 1 : # 29 表
                pgfirstiam = tab_data_07[i].record[ii].col_data1[7]  # 位图式
                tab_data_29 = IAM_info(f,pgfirstiam,db1.tab[1])
    return tab_data_29

# 初始化 22,05 系统表
def init_22_05(f,tab_data_07,tab_data_29):
    tab_data_22 = 0; tab_data_05 = 0
    for i in range(len(tab_data_07)):
        for ii in range(len(tab_data_07[i].record)):
            if  tab_data_07[i].record[ii].col_data1[2] == 281474978938880 and tab_data_07[i].record[ii].col_data1[1] == 1 : # 22 表
                pgfirstiam = tab_data_07[i].record[ii].col_data1[7]
                tab_22 = tab_info2008(tab_data_29,34,'sysschobjs',4)
                tab_22.auid_obj_id = 34
                tab_data_22 = IAM_info(f,pgfirstiam,tab_22)
            if  tab_data_07[i].record[ii].col_data1[2] == 327680 and tab_data_07[i].record[ii].col_data1[1] == 1 : # 05 表
                pgfirstiam = tab_data_07[i].record[ii].col_data1[7]
                tab_05 = tab_info2008(tab_data_29,5,'sysrowsets',4)
                tab_05.auid_obj_id = 5
                tab_data_05 = IAM_info(f,pgfirstiam,tab_05)
            # if  tab_data_07[i].record[ii].col_data1[2] == 281474979987456 and tab_data_07[i].record[ii].col_data1[1] == 1 : # 32 表
            #     pgfirstiam = tab_data_07[i].record[ii].col_data1[7]
            #     tab_32 = tab_info(tab_data_29,50,'',4)
            #     tab_data_32 = IAM_info(f,pgfirstiam,tab_32)
    return tab_data_22,tab_data_05

# 初始化所有表
def init_all_2008(f,tab_data_22,tab_data_29,tab_data_05,tab_data_07):
    tab_all = []; view_all = []; program_all = [];trigger_all = [];default_all =[]
    for i in range(0,len(tab_data_22)):
        for i1 in range(0,len(tab_data_22[i].record)):
            obj_id = tab_data_22[i].record[i1].col_data1[0]         #　object_id，内部id
            obj_name = tab_data_22[i].record[i1].col_data1[1]
            user_id = tab_data_22[i].record[i1].col_data1[2]        # nsid 用户ID
            obj_type = tab_data_22[i].record[i1].col_data1[5]
            if obj_type in ('U','S'):    # 获取所有表的表结构
                tab = tab_info2008(tab_data_29,obj_id,obj_name,user_id)
                tab.pgfirst,tab.pgfirstiam,tab.auid_obj_id,tab.auid_ind_id = init_all_1(obj_id,tab_data_05,tab_data_07)  # 获取auid_obj_id
                print('tab_name:%s, object_id:%d, auid_obj_id/obj_id:%d,auid_ind_id:%d\n'%(obj_name,obj_id,tab.auid_obj_id,tab.auid_ind_id))
                tab_all.append(tab)
            elif obj_type == 'V':       # 视图
                view = table_struct.st_view()
                view.view_name = obj_name
                view.view_id = obj_id
                view.user_id = user_id
                view_all.append(view)
            elif obj_type in ('P','FN','IF','TF','X'):       # 存储过程
                program = table_struct.st_program()
                program.program_name = obj_name
                program.program_id = obj_id
                program.user_id = user_id
                program_all.append(program)
            elif obj_type == 'TR':       # 触发器
                view = table_struct.st_view()
                view.view_name = obj_name
                view.view_id = obj_id
                view.user_id = user_id
                trigger_all.append(view)
            elif obj_type == 'D':       # 默认值
                view = table_struct.st_view()
                view.view_name = obj_name
                view.view_id = obj_id
                view.user_id = user_id
                default_all.append(view)
    tab_all.sort(key=lambda x:(x.tab_name))     # 按表名 排序 。支持多关键字排序
    view_all.sort(key=lambda x:(x.view_name))   # 按 名 排序 。支持多关键字排序
    program_all.sort(key=lambda x:(x.program_name))   # 按 名 排序 。支持多关键字排序
    trigger_all.sort(key=lambda x:(x.view_name))   # 按 名 排序 。支持多关键字排序
    default_all.sort(key=lambda x:(x.view_name))   # 按 名 排序 。支持多关键字排序

    user_all = []; prog_all = []
    for i in range(len(tab_all)):
        if tab_all[i].tab_name == 'sysowners':    # 解sysowners表数据
            data1 = unload_tab(f,tab_all[i])
            for data1_1 in data1:
                for record in data1_1.record:
                    user1 = table_struct.st_user()
                    user1.user_id =  record.col_data1[0]
                    user1.user_name = record.col_data1[1]
                    user1.user_type = record.col_data1[2]
                    user_all.append(user1)
                    for ii in range(len(tab_all)):
                        if tab_all[ii].user_id == user1.user_id:
                            tab_all[ii].user_name = user1.user_name

        elif tab_all[i].tab_name == 'sysobjvalues':    # 解sysobjvalues表数据
            data2 = unload_tab(f,tab_all[i])
            for data2_1 in data2:
                for record in data2_1.record:
                    prog_all.append(record.col_data1)

    return tab_all,view_all,program_all,trigger_all,default_all,user_all,prog_all
# 通过29表和obj_id初始化 普通表的结构
def tab_info2008(tab_data_29,obj_id,tab_name,user_id):
    table1 = table_struct.st_table()
    table1.tab_obj_id = obj_id
    table1.tab_name = tab_name
    table1.user_id = user_id
    type = {35:'text', 34:'image', 175:'char',167:'varchar',239:'nchar',231:'nvarchar',99:'ntext',40: 'date',41:'time',\
            42:'datetime2',43:'datetimeoffset',61:'datetime',48:'tinyint', 52:'smallint',56: 'int',58:'smalldatetime', \
            59:'real',122:'smallmoney',127:'bigint',62: 'float',106:'decimal',60: 'money',189:'timestamp',165:'varbinary',\
            108:'numeric',173:'binary',36:'uniqueidentifier',98:'sql_variant',104:'bit',241:'xml',256:'sysname'}  # 临时的处理办法
    for i in range(len(tab_data_29)):
        loop1 = len(tab_data_29[i].record)     # tab_data_29[i].rec_sum
        for ii in range(loop1):
           if  tab_data_29[i].record[ii].col_data1[0] == obj_id :
                column1 = table_struct.st_column()
                column1.tab_obj_id = tab_data_29[i].record[ii].col_data1[0]
                column1.col_id = tab_data_29[i].record[ii].col_data1[2]     # 列号，从1编号
                column1.col_name = tab_data_29[i].record[ii].col_data1[3]
                column1.col_x_type = tab_data_29[i].record[ii].col_data1[4]
                column1.col_u_type = tab_data_29[i].record[ii].col_data1[5]
                column1.col_type = type[column1.col_x_type]
                column1.col_len = tab_data_29[i].record[ii].col_data1[6]
                column1.prec = tab_data_29[i].record[ii].col_data1[7]
                column1.scale = tab_data_29[i].record[ii].col_data1[8]
                null = {0:'null',1:'not null'}      # 是否可为空
                column1.nullable_is = null[tab_data_29[i].record[ii].col_data1[10]%2]
                if column1.col_x_type in (165,167,173,175,231,239) :
                    column1.col_type = type[column1.col_x_type]+'(%s)'%column1.col_len
                    if column1.col_len == -1:
                        column1.col_type = type[column1.col_x_type]+'(max)'
                    if column1.col_x_type in (231,239) :
                        if column1.col_len > 4000 and column1.col_len <= 8000:
                            column1.col_type = type[column1.col_x_type]+'(%s)'%(int(column1.col_len/2))
                if column1.col_x_type in (106,108) :
                    column1.col_type = type[column1.col_x_type]+'(%s,%s)'%(column1.prec,column1.scale)
                column1.varlen_is = 0
                table1.col.append(column1)

    table1.col_sum = len(table1.col)
    table1.col.sort(key=lambda x:(x.col_id))   # 排序 。支持多关键字排序
    var_len_sum = 0  # 变长列数
    ss = 'create table ' + table1.tab_name + '('
    for ii in range(0,table1.col_sum):
        if table1.col[ii].col_x_type in (34,35,98,99,129,130,165,167,231,241) :   # 处理变长列
            table1.col[ii].varlen_is = 1
            var_len_sum = var_len_sum + 1
        if ii == table1.col_sum-1 :     #　　建表语句
            ss += "[%s] %s);"%(table1.col[ii].col_name,table1.col[ii].col_type)
        else: ss += '[%s] %s,'%(table1.col[ii].col_name,table1.col[ii].col_type)
    table1.sql = ss
    table1.var_len_sum = var_len_sum

    return table1
# 获取auid_obj_id
def init_all_1(obj_id,tab_data_05,tab_data_07):  # 通过05和07表定位
    rowsetid = 0 ; pgfirst = 0; pgfirstiam = 0; pgroot = 0; auid = 0;pcdata = 0;pcused=0;rcrows = 0;auid_obj_id = 0;auid_ind_id = 0
    for i in range(len(tab_data_05)):
        for i1 in range(0,tab_data_05[i].rec_sum):
            if obj_id == tab_data_05[i].record[i1].col_data1[2] and tab_data_05[i].record[i1].col_data1[3] in(0,1) : # idminor取0,1
                rowsetid = tab_data_05[i].record[i1].col_data1[0]
                rcrows = tab_data_05[i].record[i1].col_data1[7]
                break
    for i in range(len(tab_data_07)):
        for i1 in range(len(tab_data_07[i].record)):
            if rowsetid == tab_data_07[i].record[i1].col_data1[2] and tab_data_07[i].record[i1].col_data1[1] == 1: # 行内数据
                pgfirst = tab_data_07[i].record[i1].col_data1[5]
                pgroot = tab_data_07[i].record[i1].col_data1[6]
                pgfirstiam = tab_data_07[i].record[i1].col_data1[7]
                pcused = tab_data_07[i].record[i1].col_data1[8]
                pcdata = tab_data_07[i].record[i1].col_data1[9]
                auid = tab_data_07[i].record[i1].col_data1[0]
                auid_obj_id = (auid>>16)&0xFFFFFFFF          # 从 AUID 中 解出来的 obj_id
                auid_ind_id = (auid>>48)                     # 从 AUID 中 解出来的 ind_id

    print('05_07_info: rowsetid:%s/%d,auid:%s/%d,pgfirst:%d,pgroot:%d,pgfirstiam:%d,pcused:%d,pcdata:%d,rcrows:%d'%(hex(rowsetid),rowsetid,hex(auid),auid,pgfirst,pgroot,pgfirstiam,pcused,pcdata,rcrows)) # 输出 空间管理信息 （05,07）
    return pgfirst,pgfirstiam,auid_obj_id,auid_ind_id

# sql2000的1表和3表
def init_1_3(f,tab_data_07):
    tab_data_1 = [];tab_data_3 = []
    for i in range(len(tab_data_07)):
        for ii in range(len(tab_data_07[i].record)):
            if  tab_data_07[i].record[ii].col_data1[0] == 1 and tab_data_07[i].record[ii].col_data1[3] == 1: # 1 表
               pgfirstiam = tab_data_07[i].record[ii].col_data1[20]  # 位图式
               tab_data_1 = IAM_info(f,pgfirstiam,db1.tab[4])
            elif  tab_data_07[i].record[ii].col_data1[0] == 3 and tab_data_07[i].record[ii].col_data1[3] == 1 : # 3 表
               pgfirstiam = tab_data_07[i].record[ii].col_data1[20]  # 位图式
               tab_data_3 = IAM_info(f,pgfirstiam,db1.tab[3])
    return tab_data_1,tab_data_3

def init_all_2000(f,tab_data_1,tab_data_2,tab_data_3):
    tab_all = []; view_all = []; program_all = [];trigger_all = [];default_all =[]
    for i in range(0,len(tab_data_1)):
        for i1 in range(0,len(tab_data_1[i].record)):
            try:
                obj_id = tab_data_1[i].record[i1].col_data1[1]         #　object_id，内部id
            except IndexError:
                print('IndexError: obj_id ... ')
                continue
            obj_name = str(tab_data_1[i].record[i1].col_data1[0])
            user_id = tab_data_1[i].record[i1].col_data1[4]        # nsid 用户ID
            obj_type = tab_data_1[i].record[i1].col_data1[2]
            if obj_type in ('U','S'):    # 获取所有表的表结构   60：sysobjvalues
                tab = tab_info2000(tab_data_3,obj_id,obj_name,user_id)
                for ii in range(len(tab_data_2)):
                    for ii1 in range(0,len(tab_data_2[ii].record)):
                        if obj_id == tab_data_2[ii].record[ii1].col_data1[0] and tab_data_2[ii].record[ii1].col_data1[3] in(0,1) : # idminor取0,1
                            tab.pgfirst = tab_data_2[ii].record[ii1].col_data1[2]
                            tab.pgfirstiam = tab_data_2[ii].record[ii1].col_data1[20]
                            tab.auid_ind_id = tab_data_2[ii].record[ii1].col_data1[3]
                            tab.auid_obj_id = tab.tab_obj_id
                            break
                print('tab_name:%s, object_id:%d, auid_obj_id:%d,auid_ind_id:%d'%(obj_name,obj_id,tab.auid_obj_id,tab.auid_ind_id))
                tab_all.append(tab)
            elif obj_type == 'V':       # 视图
                view = table_struct.st_view()
                view.view_name = obj_name
                view.view_id = obj_id
                view.user_id = user_id
                view_all.append(view)
            elif obj_type in ('P','FN','IF','TF','X'):       # 存储过程
                program = table_struct.st_program()
                program.program_name = obj_name
                program.program_id = obj_id
                program.user_id = user_id
                program_all.append(program)
            elif obj_type == 'TR':       # 触发器
                view = table_struct.st_view()
                view.view_name = obj_name
                view.view_id = obj_id
                view.user_id = user_id
                trigger_all.append(view)
            elif obj_type == 'D':       # 默认值
                view = table_struct.st_view()
                view.view_name = obj_name
                view.view_id = obj_id
                view.user_id = user_id
                default_all.append(view)

    tab_all.sort(key=lambda x:(x.tab_name))   # 按表名 排序 。支持多关键字排序
    view_all.sort(key=lambda x:(x.view_name))   # 按 名 排序 。支持多关键字排序
    program_all.sort(key=lambda x:(x.program_name))   # 按 名 排序 。支持多关键字排序
    trigger_all.sort(key=lambda x:(x.view_name))   # 按 名 排序 。支持多关键字排序
    default_all.sort(key=lambda x:(x.view_name))   # 按 名 排序 。支持多关键字排序

    user_all = []; prog_all = []
    for i in range(len(tab_all)):
        if tab_all[i].tab_name == 'sysusers':    # 解sysusers表数据
            data1 = unload_tab(f,tab_all[i])
            for data1_1 in data1:
                for record in data1_1.record:
                    user1 = table_struct.st_user()
                    user1.user_id =  record.col_data1[0]
                    user1.user_name = record.col_data1[2]
                    user1.user_type = record.col_data1[1]
                    user_all.append(user1)
                    for ii in range(len(tab_all)):
                        if tab_all[ii].user_id == user1.user_id:
                            tab_all[ii].user_name = user1.user_name


        elif tab_all[i].tab_name == 'syscomments':    # 解syscomments表数据
            data2 = unload_tab(f,tab_all[i])
            for data2_1 in data2:
                for record in data2_1.record:
                    prog_all.append(record.col_data1)

    return tab_all,view_all,program_all,trigger_all,default_all,user_all,prog_all

# 通过3表和obj_id初始化 普通表的结构
def tab_info2000(tab_data_3,obj_id,tab_name,user_id):
    table1 = table_struct.st_table()
    table1.tab_obj_id = obj_id
    table1.tab_name = tab_name
    table1.user_id = user_id
    type = {35:'text', 34:'image', 175:'char',167:'varchar',239:'nchar',231:'nvarchar',99:'ntext',40: 'date',41:'time',\
            42:'datetime2',43:'datetimeoffset',61:'datetime',48:'tinyint', 52:'smallint',56: 'int',58:'smalldatetime', \
            59:'real',122:'smallmoney',127:'bigint',62: 'float',106:'decimal',60: 'money',189:'timestamp',165:'varbinary',\
            108:'numeric',173:'binary',36:'uniqueidentifier',98:'sql_variant',104:'bit',241:'xml',256:'sysname'}  # 临时的处理办法
    for i in range(len(tab_data_3)):
        loop1 = len(tab_data_3[i].record)     # tab_data_29[i].rec_sum
        for ii in range(loop1):
           if  tab_data_3[i].record[ii].col_data1[1] == obj_id :
                column1 = table_struct.st_column()
                column1.tab_obj_id = tab_data_3[i].record[ii].col_data1[1]
                column1.col_id = tab_data_3[i].record[ii].col_data1[8]     # 列号，从1编号
                column1.col_name = tab_data_3[i].record[ii].col_data1[0]
                column1.col_x_type = tab_data_3[i].record[ii].col_data1[2]
                column1.col_u_type = tab_data_3[i].record[ii].col_data1[4]
                column1.col_type = type[column1.col_x_type]
                column1.col_len = tab_data_3[i].record[ii].col_data1[5]
                column1.prec = tab_data_3[i].record[ii].col_data1[6]
                column1.scale = tab_data_3[i].record[ii].col_data1[7]
                null = {0:'null',1:'not null'}      # 是否可为空
                column1.nullable_is = null[tab_data_3[i].record[ii].col_data1[3]%2]
                if column1.col_x_type in (165,167,173,175,231,239) :
                    column1.col_type = type[column1.col_x_type]+'(%s)'%column1.col_len
                    if column1.col_len == -1:
                        column1.col_type = type[column1.col_x_type]+'(max)'
                    if column1.col_x_type in (231,239) :
                        if column1.col_len > 4000 and column1.col_len <= 8000:
                            column1.col_type = type[column1.col_x_type]+'(%s)'%(int(column1.col_len/2))
                if column1.col_x_type in (106,108) :
                    column1.col_type = type[column1.col_x_type]+'(%s,%s)'%(column1.prec,column1.scale)
                column1.varlen_is = 0
                table1.col.append(column1)

    table1.col_sum = len(table1.col)
    table1.col.sort(key=lambda x:(x.col_id))   # 排序 。支持多关键字排序
    var_len_sum = 0  # 变长列数
    ss = 'create table ' + table1.tab_name + '('
    for ii in range(0,table1.col_sum):
        if table1.col[ii].col_x_type in (34,35,98,99,129,130,165,167,231,241) :   # 处理变长列
            table1.col[ii].varlen_is = 1
            var_len_sum = var_len_sum + 1
        if ii == table1.col_sum-1 :     #　　建表语句
            ss += "[%s] %s);"%(table1.col[ii].col_name,table1.col[ii].col_type)
        else: ss += '[%s] %s,'%(table1.col[ii].col_name,table1.col[ii].col_type)
    table1.sql = ss
    table1.var_len_sum = var_len_sum

    return table1


# 解析指定表
def unload_tab(f,tab):     # 解析指定表
    pgfirstiam = tab.pgfirstiam
    tab_data = IAM_info(f,pgfirstiam,tab)        # 以IAM 位图 式 来解析
    # 解析 删除记录的表(delete)
    if tab.tab_name in ('Crm_tb_Visit','Crm_Customer'):       # 指定要解析的表  pos_t_vip_cost   pos_t_vip_info
      #  tab_data = IAM_info_2(f,pgfirstiam,tab)         # 以IAM 位图 式 来解析 删除记录的表数据
        tab_data = page_scan(f,tab)               # 以全文件扫描页面 来解析 删除记录的表数据
    return tab_data


# 把表数据存储在mssql中
def save_tab(tab_data,tab,conn):  # 保存数据到 数据库中
    # db = 'host="10.1.4.1\MSSQL2008r2",user="sa",password="bysjhf808.",database="aa"'
    # conn = pyodbc.connect(db)
    cursor = conn.cursor()
    print(tab.sql)
    sql_1 = 'drop table %s;'%(tab.tab_name)
    try:
        cursor.execute(sql_1)      # 删除 表
    except (pyodbc.OperationalError, pyodbc.ProgrammingError) :
        aa = 0
    cursor.execute(tab.sql)    # 创建解析的表，然后把解析的数据存储进去
    for i in range(len(tab_data)):
        for i1 in range(len(tab_data[i].record)):
            ss = ''
            for i2 in range(tab.col_sum):
                if i2 == tab.col_sum-1 :
                    ss += "'%s'"%str(tab_data[i].record[i1].col_data1[i2])
                    try:
                        ss += "'%s'"%str(tab_data[i].record[i1].col_data1[i2])
                    except IndexError:
                        ss = ''
                        print('insert 语句拼接 溢出')
                        continue
                else:
                    try:
                        ss += "'%s',"%str(tab_data[i].record[i1].col_data1[i2])
                    except IndexError:
                        ss = ''
                        print('insert 语句拼接 溢出')
                        continue
            try:
                print("insert into %s values( %s );"%(tab.tab_name,ss) )
                cursor.execute("insert into %s values( %s );"%(tab.tab_name,ss) )      # 插入数据
            except (sqlite3.OperationalError,UnicodeEncodeError,pyodbc.OperationalError,pyodbc.ProgrammingError):
                continue
        conn.commit()
    cursor.close()
    #conn.close()
    print('表：%s 导入完成...'%tab.tab_name)

