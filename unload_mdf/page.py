# -*- coding: utf-8 -*-
# page ,  record
import struct
import table_struct,data_type
s = struct.unpack       # B,H,I

def page_handle(in_data):  # 处理残缺页校验的页数据,恢复校验前的
    check_value = s("<I", in_data[60:64])
    value = []
    for i in range(0, 16):
        value.append((check_value[0] >> (i*2)) & 0x00000003)
    new_data = bytearray(8192)
    for i in range(0, 16):
        if i == 0:
            new_data[i*512:i*512+512] = in_data[i*512:i*512+512]
        else:
            magic = struct.unpack("B", in_data[i*512+511:i*512+512])
            if value[0] == (magic[0] & 0x03):
                new_data[i*512:i*512+511] = in_data[i*512:i*512+511]
                new_data[i*512+511:i*512+512] = struct.pack("B", (magic[0] & 0xFC) + value[i])
            else:
                print("Page Err:%d Sector Check Failure!" % i)  # 此处校验位不对
                new_data[i*512:i*512+511] = in_data[i*512:i*512+511]
                new_data[i*512+511:i*512+512] = struct.pack("B", (magic[0] & 0xFC) + value[i])
    return  new_data

def page_init(in_data):  #初始化页面信息
    page_size = 8192
    page1 = table_struct.st_page()
    try:
        chk_type = s("B", in_data[5:6])  # 报这个错的，一般是 此页面数据没找到
    except struct.error:
        return page1,in_data
    data = in_data
    if chk_type[0]%4 == 1 : # 处理残缺页校验的页数据
        data = page_handle(in_data)
    data1 = s("<4B2HIHHIHHI2HIH", data[0:38])
    page1.page_no = data1[15]
    page1.page_prev = data1[6]
    page1.page_next = data1[9]
    page1.page_type = data1[1]
    page1.obj_id = data1[12]
    page1.ind_id = data1[5]
    page1.page_level = data1[3]
    page1.rec_sum = data1[11]
    for i in range(0,page1.rec_sum):
        slot1 = s("<H",data[page_size-i*2-2:page_size-i*2])   # slot_off_list
        page1.page_slot.append(slot1[0])   # 一般每个页面里slot数量在 1-100.
    return page1,data

# 正常记录解析，    行溢出 还没加(重构前有)
def record(f,in_data,table):   #解析 compact 记录  in_data(输入页面数据),table(表结构)
    page1,in_data = page_init(in_data)  # 初始化页面
    for i in range(page1.rec_sum): # 页中的所有记录
        record1 = table_struct.st_record()
        off_set = page1.page_slot[i]                # 记录偏移
        try:
            header1 = s("<2h",in_data[off_set:off_set+4])    # 记录头
        except struct.error:
            continue
        header_a = header1[0]                       # 记录类型
        if header_a in (12,28,60,167):             # 删除记录
            continue
        off1 = header1[1] + off_set                 # 列信息的位置偏移
        try:
            col_sum = s('<H',in_data[off1:off1+2])  # 记录中的列数
        except struct.error:
            continue
        record1.col_sum = col_sum[0]                # 此记录的总列数
        if record1.col_sum>500:
            continue
        null_map_len = (record1.col_sum+7)//8       # null位图的长度
        null_map_len1 = (table.col_sum+7)//8

        frm = '<'+ str(null_map_len) + 'B'
        null_map = s(frm,in_data[off1+2:off1+2+null_map_len]) # null位图  +++++++++++++++++++++++++++++++++
        null_map1 = []
        for i1 in range(null_map_len1):
            for i2 in range(0,8):
                if i1*8+i2 < record1.col_sum:
                    a = null_map[i1]>>i2
                    col_is_null = a%2                  # 此列是否为 null，1=null
                elif i1*8+i2 >= record1.col_sum:
                    col_is_null = 1
                null_map1.append(col_is_null)       # 记录中的位图是描述的原表结构的null情况
        record1.null_map = null_map1                            # null位图  ++++++++++++++++++++++++++++++++

        var_col_sum = s('<H',in_data[off1+2+null_map_len:off1+4+null_map_len])   # 变长列数量
        if table.var_len_sum == 0 or header_a == 16:    # 无变长列
            var_col_sum = [0,]
        record1.var_col_sum = var_col_sum[0]    # 变长列数量
        for ii in range(record1.var_col_sum): # 变长列 偏移
            try:
                var_col_off1 = s('<H',in_data[off1+4+null_map_len+2*ii:off1+6+null_map_len+2*ii])
            except struct.error:
                continue
            var_col_off = var_col_off1[0]
            var_col_over = 0
            if var_col_off > 32768 :       # 字段 溢出,标志
                var_col_off -= 32768
                var_col_over = 1
            record1.var_col_over.append(var_col_over)
            record1.var_col_off.append(var_col_off)

        if page1.obj_id == -1 :                      # 测试用
            print('i:%d, page_no:%d,obj_id:%d,ind_id:%d,level:%d,rec_sum:%d, off_set:%d,col_sum:%d,null_map_len:%d,null_map_len1:%d'%\
            (i,page1.page_no,page1.obj_id,page1.ind_id,page1.page_level,page1.rec_sum,off_set,record1.col_sum,null_map_len,null_map_len1))

    # 解析记录的各列数据, 行溢出先略,  ======================================
        col_off = off_set + 4   # 各列的起始偏移
        var_list = 0
        bit_1 = 0; bit_2 = 0; data_out = 0
        var_off = off1 + null_map_len + 4 + record1.var_col_sum*2
        col_sum = table.col_sum
        # if record1.col_sum > table.col_sum:
        #     col_sum = record1.col_sum
        for ii3 in range(col_sum):
            len1 = table.col[ii3].col_len            # 列数据类型长度
            col_is_null = record1.null_map[ii3]      # 列是否为空
            if col_is_null == 0:                     # 如果列 不为空
                if table.col[ii3].varlen_is == 0:    # 如果列 是定长
                    if table.col[ii3].col_x_type in (3,239):  # nchar, ntext
                        len1 = len1*1

                    elif table.col[ii3].col_x_type==104 :     # bit
                        if bit_1%8 == 0 :
                            len1 = 1
                            bit_2_1 = s('B',in_data[col_off:col_off+len1])
                            bit_2 = bit_2_1[0]
                        else:
                            len1 = 0
                        a = bit_2>>bit_1
                        if bit_1>=8 :
                            a = bit_2>>(bit_1-8)
                        col_is_true = a%2
                        if col_is_true == 1:
                            data_out = 'true'
                        elif col_is_true == 0:
                            data_out = 'false'
                        bit_1 += 1
                        col_off += len1
                        record1.col_data1.append(data_out)
                        continue
                    col_data_1 = in_data[col_off:col_off + len1]
                    col_off += len1

                elif table.col[ii3].varlen_is == 1 :  # 是变长
                    try:
                        if var_list == 0 :      # 第一个变长
                            len1 = record1.var_col_off[var_list] - header1[1] - (null_map_len + 4 + record1.var_col_sum*2)
                        elif var_list > 0 :
                            len1 = record1.var_col_off[var_list] - record1.var_col_off[var_list-1]  # 常出错地方
                    except IndexError:
                        #print('变长数组溢出，page_no:%s,off_set:%s'%(page1.page_no,off_set))
                        data_out = ''
                        record1.col_data1.append(data_out)
                        var_list = var_list + 1
                        var_off += len1
                        continue

                    if record1.var_col_over[var_list] == 1 :                # col溢出
                        col_data_1 = in_data[col_off:col_off + len1]
                   #     print(page1.page_no,len1,col_off)
                        try :
                            data_out = col_over(f,col_data_1,table.col[ii3])
                        except IndexError :
                            data_out = ''
                        record1.col_data1.append(data_out)
                        var_list = var_list + 1
                        var_off += len1
                        continue
                    var_list = var_list + 1
                    col_data_1 = in_data[var_off:var_off + len1]
                    var_off += len1

                col_data2 = data_type.data_type(col_data_1,table.col[ii3])  # 列数据解析

            elif col_is_null == 1 :                   # 如果列为空
                if table.col[ii3].varlen_is == 0 : # 是定长
                    if table.col[ii3].col_x_type in (3,239):
                        len1 = len1*1
                    elif table.col[ii3].col_x_type==104 : # bit
                        if bit_1%8 == 0 :
                            len1 = 1
                            bit_2_1 = s('B',in_data[col_off:col_off+len1])
                            bit_2 = bit_2_1[0]
                        else:
                            len1 = 0
                        bit_1 += 1
                    col_off += len1
                elif table.col[ii3].varlen_is == 1 :  # 是变长
                    var_list = var_list + 1
                    len1 = 0
                col_data2 = ''  # 列数据解析
                # if table.col[ii3].col_id != ii3 :
                #     continue
            record1.col_data1.append(col_data2)
        page1.record.append(record1)   # 把记录放到 页面的记录容器里,会很多
    return  page1

# 删除记录解析， bits, 行溢出 还没加(重构前有)
def record_2(f,in_data,table):   # 解析 compact 记录  in_data(输入页面数据),table(表结构)
    page1 = table_struct.st_page()
    chk_type = s("B", in_data[5:6])  # 报这个错的，一般是 此页面数据没找到
    if chk_type[0]%4 == 1 : # 处理残缺页校验的页数据
        in_data = page_handle(in_data)
    data1 = s("<4B2HIHHIHHI2HIH", in_data[0:38])
    page1.page_no = data1[15]
    page1.page_type = data1[1]
    page1.obj_id = data1[12]
    page1.ind_id = data1[5]
    len_0 = s("<H", in_data[6:8])
    off_set = 96
    while off_set < 8190 :      # 在页面中扫描所有 记录头有删除标志的记录的位置
        data = in_data[off_set:8190]
        if len_0[0] == 256 :
            off = data.find(b'\x30\x00',0,-1)# 30, 3c,70
        else :
            off = data.find(b'\x30\x00',0,-1)
        if off != -1 :
            off = off + off_set
            len_2 = s("<H", in_data[off+2:off+4])
            off_1 = off + len_2[0]
            if off_1 > 8190:
                off_set = off + 1
                continue
            len_2 = s("<H", in_data[off_1:off_1+2]) # 记录中的列数
            if len_2[0] == table.col_sum :
                page1.page_slot.append(off)
                off_set = off_1
            else:
                off_set = off + 1
        else:
            off_set = off_set + 1

    for i in range(len(page1.page_slot)):              # 页中的所有记录
        record1 = table_struct.st_record()
        off_set = page1.page_slot[i]                        # 记录偏移
        try:
            header1 = s("<2h",in_data[off_set:off_set+4])    # 记录头
        except struct.error:
            continue
        header_a = header1[0]                       # 记录类型
        header_b = header1[1]
        # if header_b != 356:
        #     continue
        # if header_a in (12,28,60,167):         # 删除记录
        #     continue
        off1 = header1[1] + off_set                 # 列信息的位置偏移
        try:
            col_sum = s('<H',in_data[off1:off1+2])
        except struct.error:
            continue
        record1.col_sum = col_sum[0]                # 此记录的总列数
        null_map_len = (record1.col_sum+7)//8       # null位图的长度
        null_map_len1 = (table.col_sum+7)//8
        if null_map_len >10 :
            continue
        frm = '<'+ str(null_map_len) + 'B'
        null_map = s(frm,in_data[off1+2:off1+2+null_map_len]) # null位图  +++++++++++++++++++++++++++++++++
        null_map1 = []
        for i1 in range(null_map_len1):
            for i2 in range(0,8):
                if i1*8+i2 < record1.col_sum:
                    a = null_map[i1]>>i2
                    col_is_null = a%2                  # 此列是否为 null，1=null
                elif i1*8+i2 >= record1.col_sum:
                    col_is_null = 1
                null_map1.append(col_is_null)       # 记录中的位图是描述的原表结构的null情况
        record1.null_map = null_map1                            # null位图  ++++++++++++++++++++++++++++++++

        var_col_sum = s('<H',in_data[off1+2+null_map_len:off1+4+null_map_len])   # 变长列数量
        if table.var_len_sum == 0 or header_a == 16:    # 无变长列
            var_col_sum = [0,]
        record1.var_col_sum = var_col_sum[0]    # 变长列数量
        for ii in range(record1.var_col_sum): # 变长列 偏移
            try:
                var_col_off1 = s('<H',in_data[off1+4+null_map_len+2*ii:off1+6+null_map_len+2*ii])
            except struct.error:
                continue
            var_col_off = var_col_off1[0]
            var_col_over = 0
            if var_col_off > 32768 :       # 字段 溢出,标志
                var_col_off -= 32768
                var_col_over = 1
            record1.var_col_over.append(var_col_over)
            record1.var_col_off.append(var_col_off)

        # if page1.obj_id == 1 :                      # 测试用
        #     print('i:%d, page_no:%d,obj_id:%d,ind_id:%d,level:%d,rec_sum:%d, off_set:%d,col_sum:%d,null_map_len:%d,null_map_len1:%d'%\
        #     (i,page1.page_no,page1.obj_id,page1.ind_id,page1.page_level,page1.rec_sum,off_set,record1.col_sum,null_map_len,null_map_len1))

    # 解析记录的各列数据, 行溢出先略,  ======================================
        col_off = off_set + 4   # 各列的起始偏移
        var_list = 0
        bit_1 = 0; bit_2 = 0; data_out = 0
        var_off = off1 + null_map_len + 4 + record1.var_col_sum*2
        for ii3 in range(len(table.col)):
            len1 = table.col[ii3].col_len            # 列数据类型长度
            col_is_null = record1.null_map[ii3]      # 列是否为空
            if col_is_null == 0:                     # 如果列 不为空
                if table.col[ii3].varlen_is == 0:    # 如果列 是定长
                    if table.col[ii3].col_x_type in (3,239):  # nchar, ntext
                        len1 = len1*1
                    col_data_1 = in_data[col_off:col_off + len1]
                    col_off += len1
                elif table.col[ii3].varlen_is == 1 :  # 是变长
                    if var_list == 0 :      # 第一个变长
                        try:
                            len1 = record1.var_col_off[var_list] - header1[1] - (null_map_len + 4 + record1.var_col_sum*2)
                        except IndexError:
                            continue
                    elif var_list > 0 :
                        try:
                            len1 = record1.var_col_off[var_list] - record1.var_col_off[var_list-1]  # 常出错地方
                        except IndexError:
                            continue
                    var_list = var_list + 1
                    col_data_1 = in_data[var_off:var_off + len1]
                    var_off += len1
                col_data2 = data_type.data_type(col_data_1,table.col[ii3])  # 列数据解析

            elif col_is_null == 1:                   # 如果列为空
                if table.col[ii3].varlen_is == 0 : # 是定长
                    if table.col[ii3].col_x_type in (3,239):
                        len1 = len1*1
                    col_off += len1
                elif table.col[ii3].varlen_is == 1 :  # 是变长
                    var_list = var_list + 1
                    len1 = 0
                col_data2 = ''  # 列数据解析

            record1.col_data1.append(col_data2)

        page1.record.append(record1)   # 把记录放到 页面的记录容器里,会很多
    return  page1

# 列数据溢出
def col_over(f,data,col_1):
    data_out = ''
    if col_1.col_x_type in(34,99,35) :      # text,ntext,img
        rowid = s("<IHH",data[8:16])
        file_no = rowid[1]
        page_no = rowid[0]
        slot_no = rowid[2]
  #      print(page_no,slot_no)
        f.seek(page_no*8192)
        in_data = f.read(8192)
        page1,in_data = page_init(in_data)
     #   print(page1.page_no,page1.page_slot)
        if page1.page_type != 3:
            return data_out
        off = page1.page_slot[slot_no]
        rec_over_h = s("<HHQH",in_data[off:off+14])
        rec_len = rec_over_h[1]
        rec_type = rec_over_h[3]
        if rec_type == 3:       # DATA
            data = in_data[off+14:off+rec_len]
            try:
                if col_1.col_x_type == 35:
                    data_out = str(data,encoding="gbk").rstrip()
                else:
                    data_out = str(data,encoding="utf-16").rstrip()
            except UnicodeDecodeError:
                data_out = ''
        elif rec_type == 0:     # small
            rec_len_1 = s("<H",in_data[off+14:off+16])
            data = in_data[off+20:off+20+rec_len_1[0]]
            try:
                if col_1.col_x_type == 35:
                    data_out = str(data,encoding="gbk").rstrip()
                else:
                    data_out = str(data,encoding="utf-16").rstrip()
            except UnicodeDecodeError:
                data_out = ''
        elif rec_type == 5:     # large
            data_1 = ''
            rec_h_1 = s("<HH",in_data[off+14:off+18])
            MaxLinks = rec_h_1[0]   # 最大链接数
            CurLinks = rec_h_1[1]   # 实际链接数
            for i in range(CurLinks):
                rec_h_2 = in_data[off+20+i*12:off+36+i*12]
                data_out_1 = col_over(f,rec_h_2,col_1)
            #    print(data_out_1)
                data_1 = data_1 + data_out_1
            data_out = data_1
    elif col_1.col_x_type in(165,231,167) :     # varchar,nvarchar,varbinary
        data_1 =  ''
        len_1 = len(data)//12
        for i in range(1,len_1):
            rec_h_2 = data[(i*12-4):(i+1)*12]
            rowid = s("<IHH",rec_h_2[8:16])
            id = col_1.col_x_type
            if col_1.col_x_type == 167:
                col_1.col_x_type = 35
            else:
                col_1.col_x_type = 99

            data_out_1 = col_over(f,rec_h_2,col_1)
            col_1.col_x_type = id
            data_1 = data_1 + data_out_1
        #    print(data_1)
        data_out = data_1

        print('varchar 行溢出，')

    return data_out


