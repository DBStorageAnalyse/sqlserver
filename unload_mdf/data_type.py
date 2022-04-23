# -*- coding: utf-8 -*-
# 数据类型解析，持续完善
import struct, time, decimal

s = struct.unpack  # B H I


def data_type(data, col_1):
    if len(data) == 0:
        return ''
    # 整数 int,bigint,smallint,tinyint ...
    if col_1.col_x_type in (1, 48, 52, 56, 127):
        if col_1.col_len == 1:
            a = s("<B", data)
        elif col_1.col_len == 2:
            a = s("<h", data)
        elif col_1.col_len == 4:
            a = s("<i", data)
        elif col_1.col_len == 8:
            a = s("<q", data)
        data_out = a[0]
        return data_out

    # 字符 char,varchar ...
    elif col_1.col_x_type in (2, 175, 167):
        data_out = ''
        try:
            data_out = str(data, encoding="gbk").rstrip()  # ascii,gbk,gb2312   .strip()
        except UnicodeDecodeError:
            data_out = ''
            return data_out
        if col_1.col_len == 2 and data == b'\x00\x00':
            data_out = ''
        elif col_1.col_len == 1 and data == b'\x00':
            data_out = ''
        return data_out

    # 字符 nchar, nvarchar  ...
    elif col_1.col_x_type in (3, 231, 239):
        try:
            data_out = str(data, encoding="utf-16").rstrip()  # utf-8 ,utf-16 去字符串尾部的空格
        except UnicodeDecodeError:
            data_out = 'nvarchar溢出'
        return data_out
    elif col_1.col_x_type == 99:
        data_out = 'ntext'
        return data_out

    # 日期时间 datetime ,date ,time, smalldatetime, timestamp ...
    elif col_1.col_x_type == 58:  # smalldatetime
        a = s("<2H", data)
        date1 = a[1];
        time1 = a[0]
        time2 = date1 * 24 * 60 * 60 - 2209017600 + time1 * 60
        data_out = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time2)))
        return data_out
    elif col_1.col_x_type == 40:  # date
        a = s("<HB", data)
        date = (a[1] * 65536 + a[0] - 693595) * 24 * 60 * 60 - 2209017600
        try:
            data_out = str(time.strftime('%Y-%m-%d', time.localtime(date)))
        except OSError:
            data_out = ''
        return data_out
    elif col_1.col_x_type == 41:  # time
        if len(data) == 5:
            a = s("<IB", data)
            time1 = (a[1] * 4294967296 + a[0]) / 10 / 1000 / 1000
            data_out = str(time.strftime('%H:%M:%S.', time.localtime(time1))) + ('%.7f' % (time1))[-7:]
        else:
            data_out = ''
        return data_out
    elif col_1.col_x_type == 61:  # datetime
        a = s("<Ii", data)
        date1 = a[1];
        time1 = a[0] / 300
        time2 = date1 * 24 * 60 * 60 - 2209017600 + time1
        try:
            data_out = str(time.strftime('%Y-%m-%d %H:%M:%S.', time.localtime(time2))) + ('%.3f' % (time1))[-3:]
        except OSError:
            data_out = ''
        #    print('时间溢出...')
        return data_out
    elif col_1.col_x_type in (189, 42):  # timestamp,datetime2,, 没有解析
        data_out = ''
        return data_out

    # numeric,decimal,money
    elif col_1.col_x_type in (108, 106):  # numeric,decimal
        data_out = 0
        if col_1.col_len == 9:
            data1 = s('<Q', data[1:9])
            prec = col_1.prec
            scale = col_1.scale
            data_1 = data1[0]
            data_out = decimal.Decimal(data_1 / decimal.Decimal(str(10 ** scale)))
        elif col_1.col_len == 5:
            data1 = s('<I', data[1:5])
            prec = col_1.prec
            scale = col_1.scale
            data_1 = data1[0]
            data_out = decimal.Decimal(data_1 / decimal.Decimal(str(10 ** scale)))
        elif col_1.col_len == 13:
            data1 = s('<Q', data[1:9])
            data2 = s('<I', data[9:13])
            prec = col_1.prec
            scale = col_1.scale
            data_1 = data2[0] * (256 ** 8) + data1[0]
            data_out = decimal.Decimal(data_1 / decimal.Decimal(str(10 ** scale)))
        elif col_1.col_len == 17:
            data1 = s('<Q', data[1:9])
            data2 = s('<Q', data[9:17])
            prec = col_1.prec
            scale = col_1.scale
            #    aa = '%%%d.%df'%(prec,scale)
            data_1 = data2[0] * (256 ** 8) + data1[0]
            #    print('%d %d,%d,%s'%(data2[0],data1[0],data_1,decimal.Decimal(data_1/decimal.Decimal(str(10**scale)))))
            data_out = decimal.Decimal(data_1 / decimal.Decimal(str(10 ** scale)))  # .strip()
        return data_out

    elif col_1.col_x_type == 62:  # fload
        if col_1.col_len == 8:
            data1 = s('<d', data[0:8])
            data_out = data1[0]
        return data_out
    elif col_1.col_x_type == 59:  # real
        if col_1.col_len == 4:
            data1 = s('<f', data[0:4])
            data_out = data1[0]
        return data_out
    elif col_1.col_x_type == 60:  # money
        if col_1.col_len == 8:
            try:
                data1 = s('<q', data[0:8])
                data_out = float(data1[0] / 10000)
            except struct.error:
                data_out = 0
            data_out = '%.4f' % (data_out)
        return data_out
    elif col_1.col_x_type == 122:  # smallmoney
        if col_1.col_len == 4:
            data1 = s('<i', data[0:4])
            data_out = float(data1[0] / 10000)
            data_out = '%.4f' % (data_out)
        return data_out

    # page_file,  binary
    elif col_1.col_x_type in (5, 173):
        if col_1.col_len == 6:
            data1 = s('<IH', data)
            return data1[0]
        else:
            return 0

    elif col_1.col_x_type in (-1, 98):
        try:
            data_out = str(data, encoding="gbk").rstrip()  # utf-8 ,utf-16 去字符串尾部的空格
        except UnicodeDecodeError:
            data_out = 'sql_variant溢出'
        return data_out

    # 其他 uniqueidentifier,geography,sql_variant,xml
    elif col_1.col_x_type in (36, 130, 241):
        return 0
    else:
        return 0
