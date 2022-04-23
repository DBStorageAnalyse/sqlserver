# -*- coding: utf-8 -*-
mssql 数据文件检测工具

# 检测出各对象信息/结构, 各页信息, 统计信息，校验方式。
# 物理结构： 顺序的扫描，检测页号文件号，页类型，固定位置的空间管理页面。
# 逻辑结构： 按照逻辑检索结构，定位重要的系统表
# 检测中间数据支持本地化，存入sqlite,支持保存/打开检测工程

检测等级：
1. 文件级检测
2. 页面级检测
3. 记录级检测
4. dbcc级检测

==============================================================================
mssql_scan.py 是主文件, 扫描碎片. ok
mssql_check.py 是页面校验算法. ok
注意：有很多无校验的页，会引入很多的垃圾.
temp.mdf 会有干扰。里边有很多不规范的页，会造成很多碎片

cxfreeze C:\Users\zsz\PycharmProjects\sqlserver\test\ui_unload.py --target-dir=C:\Users\zsz\PycharmProjects\sqlserver\test\tt
cd /d C:\Users\zsz\PycharmProjects\sqlserver\test
pyinstaller -F -w C:\Users\zsz\PycharmProjects\sqlserver\test\ui_check.py
history: ====================================================================
mssql check tool v1.0  2015-3-1
mssql 数据文件碎片扫描工具
无GUI界面,buffer:8M
磁盘I/O:  40M/s 140G/h ; 80M/s  280G/h ; 100M/s  350G/h

mssql check tool v1.3.1  2015-8-1
加入GUI图形界面。（pyqt）
完善功能，修复bugs

mssql check tool v1.3.2  2015-8-18
加入 GAM,SGAM,PFS 过滤
单线程，无进度显示
此版本有 release

mssql check tool v1.4.0  2015-10-14
加入多线程
加入HEX查看

mssql check tool v1.5.0  2016-01-08
改进checksum，大幅提高速度 70-80M/s
改进校验准确度

mssql check tool v1.5.2  2016-05-23
加入注册验证
release并测试

mssql check tool v1.6.0  2016-06-21
三库 联调 1

mssql check tool v1.7.0  2016-07-27
加入多线程界面显示



