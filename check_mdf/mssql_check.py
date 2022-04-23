# -*- coding: utf-8 -*-
# mssql 页面校验算法
import struct, ctypes

s = struct.unpack  # B H I


class file_info:
    def __init__(self):
        self.f_name = ''  # 现在的物理路径
        self.f_no = 0
        self.g_no = 0
        self.f_size0 = 0  # 文件真实大小(文件系统属性中的)
        self.f_size1 = 0  # 文件头记录的总页数
        self.real_sum = 0  # 文件实际的总页数
        self.file_type = ''
        self.version1 = 0  # 创建版本
        self.version2 = 0  # 现在版本
        self.db_name = ''
        self.f_logic_name = ''  # 逻辑文件名
        self.f_logic_path = ''  # 逻辑路径
        self.err_pages = []


class err_page:
    def __init__(self):
        self.blk_no = 0  # 块号
        self.page_no = 0  # 页号
        self.page_type = 0  # 页类型
        self.page_off = 0  # 页的物理偏移
        self.chk_err = ''  # 错误信息


# 页头特征值校验，重要。 要尽可能的详细准确
def mssql_page_check_1(data):  # 要尽量优化
    data1 = s("<4Q", data[64:96])
    data2 = s("<H", data[38:40])
    data3 = s("<H", data[50:52])
    data = s("<4B2HIHHIHHI2HIH", data[0:38])  # B H I
    if data[0] == 1 and (
            data[2] == 0 or data[2] == 4 or data[2] == 0x80 or data[2] == 0x84 or (data[2] == 1 and data[1] == 11)) \
            and (data1[0] == 0 and data1[1] == 0 and data1[2] == 0 and data1[3] == 0) \
            and data[3] < 5 and data[7] < 50 and data[10] < 50 and (
            data[12] != 0 or (data[12] == 0 and data[1] == 7)) and data2[0] == data3[0] \
            and (data[1] > 0 and data[1] < 21 and data[1] != 5 and data[1] != 12) and (
            data[16] > 0 and data[16] < 50) and data[11] < 900 \
            and data[13] <= 8096 and data[14] >= 96 and data[14] <= 8190 and data[8] < 8058:
        # data[16/7/10]:文件号,限定为<50 ;data[1]:页面类型;data[11]:页中记录数量；data[13]：自由空间;data[14]:空闲空间起始;data[3]:索引level;data[8]:固定列总长度;data[12]:obj_id
        return 1


dll = ctypes.windll.LoadLibrary('MsSqlPageCheck.dll')


# checksum 校验
def mssql_page_check_2(data):
    a1 = len(data)
    chk = dll.MsSqlCheckSum(data, a1)
    return chk


# 残缺页校验
def mssql_page_check_3(data):
    a1 = len(data)
    chk = dll.MsSqlIncomplete(data, a1)
    return chk


# 无校验页的校验,检验页尾行偏移. 还需要加入更严格的条件
def mssql_page_check_4(data):
    data1 = s("<H", data[22:24])  # 记录数量
    data2 = s("<H", data[30:32])  # m_freeData
    data3 = s("<I", data[32:36])  # 页号
    data0 = s("<H", data[4:6])
    d1 = data0[0] & 0x000f  # 088x
    #  print('%s, %d '%(hex(data0[0]),d1))
    for i in range(0, data1[0]):  # 页尾 太严格了， 有些正常页也被过滤掉了。
        try:
            data4 = s("<H", data[(8190 - i * 2):(8192 - i * 2)])
        except struct.error:
            continue
        if (data4[0] < 96 or data4[0] > data2[0]):  # d1 != 8 and   +++++++++++++++++++++++++++++++++++++==
            if data4[0] == 0:
                # print('page_no: %d slot 00 ..........'%data3[0] )
                a = 0
            return 1
        # elif d1 == 8 and ((data3[0]<96 and data3[0]>0) or data3[0]>data2[0]):
        #     return 0
    return 1


# 处理残缺页校验的页数据,恢复校验前的
def page_handle(in_data):  # 慢
    check_value = s("<I", in_data[60:64])
    value = []
    for i in range(0, 16):
        value.append((check_value[0] >> (i * 2)) & 0x00000003)
    new_data = bytearray(8192)
    for i in range(0, 16):
        if i == 0:
            new_data[i * 512:i * 512 + 512] = in_data[i * 512:i * 512 + 512]
        else:
            magic = struct.unpack("B", in_data[i * 512 + 511: i * 512 + 512])
            if value[0] == (magic[0] & 0x03):
                new_data[i * 512:i * 512 + 511] = in_data[i * 512:i * 512 + 511]
                new_data[i * 512 + 511:i * 512 + 512] = struct.pack("B", (magic[0] & 0xFC) + value[i])
            else:
                a = 0
            #    print("Err:%d Sector Check Failure!" % i)
    return new_data
