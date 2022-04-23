# -*- coding: utf-8 -*-
# 表结构信息获取. 配置文件格式 按配置文件说明制作
# 从建表sql 中获取数据库信息，写出到ini或数据库
import re,configparser,sqlite3

class Column:
    def __init__(self):
        self.col_id = 0
        self.column_name = ''    # 列名
        self.data_type = '' # 数据类型
        self.prec = 0  # 括号数1
        self.scale = 0 # 括号数2
        self.column_len = 0  # 数据长度
        self.var_len_is = 1  # 是否是边长
        self.define = '' # 默认值
        self.nullable_is = 1    # 是否可以为空，1是 0不可为空
       # self.enums = list() # enum 类型

class Table:
    def __init__(self,num,schema,name):
        self.num = num          # 表编号，从1开始
        self.user_name = schema
        self.table_name = name
        self.auid_obj_id = 0      # 表的 obj_id
        self.auid_ind_id = 0      # 表的 ind_id
        self.tab_name = ''        # 表名  #有的表只有object_id没有表名
        self.var_len_sum = 0      # 变长列的列数
        self.col = []
    @property
    def col_sum(self):
        return len(self.col)

    @property
    def nullable_sum(self): # 可为空的列数
        nullable_sum = 0
        for column in self.col:
            if column.nullable_is == 1:
                nullable_sum += 1
        return int(nullable_sum)

# 列数据长度
def parse_len(type_name, column_stmt):
    type_len = {'text': 0, 'image': 0, 'ntext': 0, 'date': 3, 'datetime': 8,'tinyint':1, 'smallint': 2, 'int': 4, 'bigint': 8,\
                'float': 8,  'money': 8,'smallmoney':4 ,'timestamp':8}
    if type_name in type_len:
        return  type_len[type_name]
    elif type_name == 'numeric' or type_name == 'decimal':
            m1 = re.search(r'\((\d+), (\d+)\)', column_stmt)
            prec = int(m1.group(1))
            if prec<=9 :
                return 5
            elif prec>9 and prec<=19 :
                return 9
            elif prec>19 and prec<=28 :
                return 13
            elif prec>28 and prec<=38 :
                return 17
    elif type_name == 'char' or type_name == 'nchar' or type_name == 'varchar' or type_name == 'nvarchar':
        return  int(re.search(r'\]\((\d+)\)', column_stmt).group(1))  # mssql
    else:
        return  0  # mssql

# 从create语句中提取列信息
def parse_create_stmt(create_stmt):
  #  iter = re.finditer(r'\n\t\[(\w+)\] \[(\w+)\].*', create_stmt)  # 标准格式sql语句
    iter = re.finditer(r'\n\t\[(\w+)\] \[(\w+)\].*', create_stmt)
    columns = []; col_id = 0
    for m in iter:   # 每一行
        column = Column()
        col_id += 1
        column.col_id = col_id
        column.column_name = m.group(1)
        column.data_type = m.group(2)
        column.column_len = parse_len(m.group(2), m.group())
        column.var_len_is = int(m.group(2) in ('varchar','nvarchar','text','ntext','image'))    # 变长类型
        if re.search("NOT NULL", m.group()):
            column.nullable_is = 0
        else:
            column.nullable_is = 1

        if column.data_type == 'numeric' or column.data_type == 'decimal':
            m1 = re.search(r'\((\d+), (\d+)\)', m.group())
            column.prec = int(m1.group(1))
            column.scale = int(m1.group(2))
        elif column.data_type == 'char' or column.data_type == 'nchar' or column.data_type == 'varchar' or column.data_type == 'nvarchar':
            m1 = re.search(r'\((\d+)\)', m.group())
            column.prec = 0
            column.scale = 0
        columns.append(column)
    return columns

# 将table信息写入配置文件
def save_table(table):
    type_id = {'text':35, 'image': 34, 'char':175,'varchar':167,'nchar':239,'nvarchar':231,'ntext': 99, 'date': 40, 'datetime': 61,'tinyint':48, 'smallint': 52,  'int': 56, 'bigint': 127, 'float': 62,'decimal':106, 'money': 60,'timestamp':189}
    conf = configparser.ConfigParser()
    # 写入数据库信息
    conf.add_section('db_info')
    conf.set('db_info', 'db_id', '30')
    conf.set('db_info', 'db_version', '0')  # 系统表的数量
    conf.set('db_info', 'sys_tab_count ', '0')  # 系统表的数量
    conf.set('db_info', 'user_tab_count ', '1') # 用户表的数量
    # 写入表信息
    conf.add_section('tab_info_%d'% table.num)
    conf.set('tab_info_%d'% table.num , 't_name', table.table_name)
    conf.set('tab_info_%d'% table.num , 't_type', str(table.table_type)) #'table_%d' % table.num,
    conf.set('tab_info_%d'% table.num, 't_obj_id', '1' )  # 系统表里记录的id
    conf.set('tab_info_%d'% table.num, 't_obj_auid', '1' )    # 表对应的页里面记录的id
    conf.set('tab_info_%d'% table.num , 't_col_sum', str(table.column_sum))
    conf.set('tab_info_%d'% table.num , 'nullmap_is', str(table.nullmap_is))
    #写入列信息
    column_num = 1
    for column in table.columns:
        conf.add_section('col_info_%d_%d' % (table.num,column_num))
        conf.set('col_info_%d_%d' %(table.num,column_num), 'c_name', column.column_name)
        conf.set('col_info_%d_%d' %(table.num,column_num), 'c_Stype', column.column_data_type)

        if column.column_data_type == 'numeric'or column.column_data_type == 'decimal':
            conf.set('col_info_%d_%d' %(table.num,column_num), 'c_prec', column.prec)
            conf.set('col_info_%d_%d' %(table.num,column_num), 'c_scale', column.scale)  # scale
        elif  column.column_data_type == 'money':
            conf.set('col_info_%d_%d' %(table.num,column_num), 'c_prec', '19')
            conf.set('col_info_%d_%d' %(table.num,column_num), 'c_scale', '4')
        elif column.column_data_type == 'char' or column.column_data_type == 'nchar' or column.column_data_type == 'varchar' or column.column_data_type == 'nvarchar':
            conf.set('col_info_%d_%d' %(table.num,column_num), 'c_prec', column.prec)
            conf.set('col_info_%d_%d' %(table.num,column_num), 'c_scale', column.scale)

        conf.set('col_info_%d_%d' %(table.num,column_num), 'c_Utype', str(type_id[column.column_data_type])) # c_Utype
        conf.set('col_info_%d_%d' %(table.num,column_num), 'c_len', str(column.column_length))
        conf.set('col_info_%d_%d' %(table.num,column_num), 'c_is_var', str(column.column_var_is))
        conf.set('col_info_%d_%d' %(table.num,column_num), 'column_define', '0')
        conf.set('col_info_%d_%d' %(table.num,column_num), 'column_pkey_is', '0')
        conf.set('col_info_%d_%d' %(table.num,column_num), 'c_is_nullable', str(column.column_nullable_is))
        column_num += 1
    conf.write(open(r'h:\ss.ini' , 'a'))#% (table.table_name)
# 将table信息写入sqlite的表中
def save_table2(table,out):
    type_id = {'text':35, 'image': 34, 'char':175,'varchar':167,'nchar':239,'nvarchar':231,'ntext': 99, 'date': 40, 'datetime': 61,\
    'tinyint':48, 'smallint': 52,  'int': 56, 'bigint': 127, 'float': 62,'decimal':106, 'money': 60,'smallmoney':122,'timestamp':189}
    conn = sqlite3.connect(out)  # 打开数据库
    cursor = conn.cursor()
    cursor.execute("insert into tab_info(tab_obj_id,user_name,tab_name,col_sum,nullable_sum) values(%d,'%s','%s',%d,%d)"%\
                   (table.num,table.user_name,table.table_name,table.col_sum,table.nullable_sum))
    for col in table.col:
        cursor.execute("insert into col_info(tab_obj_id,col_id,col_name,col_u_type,col_len,prec,scale,nullable_is,var_len_is) values(%d,%d,'%s',%d,%d,%d,%d,%d,%d)"%\
        (table.num,col.col_id,col.column_name,type_id[col.data_type],col.column_len,col.prec,col.scale,col.nullable_is,col.var_len_is))
    conn.commit()

# 主函数
def table_frm(sql_file_name,out):
    f = open(sql_file_name,encoding='utf-8')
    data = f.read()
    pattern_create_stmt = re.compile(r'CREATE TABLE \[(\w+)\]\.\[(\w+)\]\(\n(.+\n)*')  # 用于匹配mssql的标准create块
    iter = pattern_create_stmt.finditer(data)
    table_num = 1
    for m in iter:
        table = Table(table_num, m.group(1), m.group(2))
        table.col = parse_create_stmt(m.group()) # m.group() 一个create 语句
     #   save_table(table)
        save_table2(table,out)
        print("%s.%s"%(table.user_name,table.table_name))
        table_num += 1


sql_file_name = r'C:\Users\zsz\Desktop\qinghai_his\sqlserver\bsuis_sc.sql'
out = r'C:\Users\zsz\Desktop\qinghai_his\sqlserver\tab_bsuis_sc.db'
table_frm(sql_file_name,out)

