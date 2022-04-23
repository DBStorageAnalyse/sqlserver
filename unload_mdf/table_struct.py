# -*- coding: utf-8 -*-
# 定义 表结构  # 重要

class File_Info():
    def __init__(self):
        self.f_name = ''    # 文件路径
        self.f_no = 0       # 文件号
        self.file = 0
        self.f_type = '' 	# 文件类型
        self.blk_sum = 0    # 文件的块/页 总数
        self.db_name = 0       # 数据库名
        self.gp_id = 0      # 文件组ID
        self.gp_name = ''   # 文件组名
        self.version1 = 0   # 原始版本
        self.version2 = 0   # 现在版本
        self.boot = 0       # 启动页

class st_db:    # 数据库
    def __init__(self):
        self.db_id = 0      #数据库 ID
        self.db_name = ''   #数据库名
        self.db_version = ''#数据库版本  # mssql_2008, mysql_5.1 等
        self.page_size = 8192  #页面大小,固定为8192字节
        self.endian = '<'     #大小端. 0小端,1大端
        self.os = ''        #OS信息
        self.tab_sum = 0    #表的数量
        self.tab = []       #表

class st_user: # 表
    def __init__(self):
        self.user_id = 0          # 用户 ID
        self.user_name = ''       # 用户名
        self.user_type = ''       # 用户类型

class st_table: # 表
    def __init__(self):
        self.user_id = 0          # 用户 ID
        self.user_name = ''       # 用户名
        self.tab_obj_id = 0       # 表的 object_id
        self.auid_obj_id = 0      # 表的 obj_id
        self.auid_ind_id = 0      # 表的 ind_id
        self.tab_name = ''        # 表名  #有的表只有object_id没有表名
        self.col_sum = 0          # 表的总列数
        self.nullable_sum = 0     # 可为空的列数
        self.var_len_sum = 0      # 变长列的列数
        self.col = []             # 列信息
     #   self.created = ''         # 表的创建时间
        self.pgfirst = 0          # 表数据起始页号
        self.pgfirstiam = 0       # 表数据IAM起始页号
        self.sql = ''

class st_view: # view
    def __init__(self):
        self.view_id = 0          # view ID
        self.view_name = ''       # view 名称
        self.user_id = 0

class st_program: # program
    def __init__(self):
        self.program_id = 0          # program ID
        self.program_name = ''       # program 名称
        self.user_id = 0

class st_column:    # 列
    def __init__(self):
        self.tab_obj_id = 0     #表的object_id
        self.col_id = 0         #列id
        self.col_name = ''      #列名
        self.col_x_type = 0     #列的数据类型(系统)
        self.col_u_type = 0     #列的数据类型(用户)
        self.col_type = ''      #列的数据类型名称
        self.col_len = 0        #列长度
        self.prec = 0           #精度
        self.scale = 0          #小数位数
        self.collationid = 0    #排序规则编号
        self.seed = 0           #自增种子.  标识种子+标识增量
        self.def_data = 'NULL'  #默认值
        self.nullable_is = ''    #是否可为空
        self.varlen_is = 0      #是否是变长
        self.pkey_is = 0        #是否是主键

class st_page:  # 页面
    def __init__(self):
        self.check = 0      #校验和
        self.page_no = 0    #页面编号，从0编号
        self.file_no = 1    #文件号， 从1编号
        self.page_prev = 0  #上一页
        self.page_next = 0  #下一页
        self.page_type = 0  #页面类型：数据页，IAM页，索引页
        self.obj_id = 0     #obj_id
        self.ind_id = 0     #ind_id
        self.rec_sum = 0    #页面中记录数量,即slot数量
        self.page_level = 0 #页面level
        self.flagBits = 0   #页面校验标志
        self.page_slot= []  #页尾slot
        self.record = []    #页面中的记录

class st_record:   # 数据记录
    def __init__(self):
        self.null_map = []
        self.col_sum = 0
        self.var_col_sum = 0
        self.var_col_over = []    # col溢出
        self.var_col_off = []     # 边长列结束偏移列表
        self.col_data1 = []       # 记录的解析后列数据(表结构中的顺序)

