# -*- coding: utf-8 -*-
mssql scan tool /   mssql数据文件碎片扫描拼接工具

==============================================================================
mssql_scan.py 是主文件, 扫描碎片. ok
mssql_check.py 是页面校验算法. ok
注意：有很多无校验的页，会引入很多的垃圾.
temp.mdf 会有干扰。里边有很多不规范的页，会造成很多碎片

mssql_link1.py 是碎片拼接1， 一般能减少碎片到 1/100--1/1000.  ok
mssql_link2.py 是碎片拼接2，通过半页来拼接，半页很少，准确度高，效果差。 ok,待测
先半页(注意校验方式，无校验的没法拼)， 再页号连续（无多个选择时）
mssql_link3.py 是通过PFS IAM来拼接碎片
file_info.py  获取文件信息
data_out1.py 是碎片导出为文件
table_frm.py  # 表结构信息获取
从表结构sql中获取表结构写出到ini或sqlite表中。

=============================================================================
案例：
1T的库，1.4亿条，2.5G的db.
500G的库，link_1前5000万条，1.1G的db.
380G的库, 5000万条，800M的DB
155G的库, 2000万条,  436M的DB
I/O: 35m/s，100M/s  (数据页面密集时速度到200M/s,即步长为8k时200m/s,512B时90m/s,速度与步长有关)
磁盘I/O: 20M/s 70G/h ; 40M/s 140G/h ; 80M/s  280G/h ; 100M/s  350G/h

C:\Python34\Scripts> cxfreeze C:\Users\zsz\PycharmProjects\sqlserver\test\ui_scan.py --target-dir=C:\Users\zsz\PycharmProjects\sqlserver\test\tt
 --base-name=C:\Python34\Lib\site-packages\cx_Freeze\bases\Win32GUI.exe
pyinstaller -F -w C:\Users\zsz\PycharmProjects\sqlserver\test\ui_scan.py
=============================================================================
history:
mssql scan tool v1.0  2015-3-1
mssql 数据文件碎片扫描工具
无GUI界面,双击 mssql_scan.py 启动
buffer:8M  I/O:20M/s

mssql scan tool v1.0.1  2015-8-10
无GUI界面,支持 碎片扫描， 物理拼接

mssql scan tool v1.1.1  2015-9-1
加入界面,整合模块

mssql scan tool v1.2.0  2016-2-17
优化功能，修复baugs

mssql scan tool v1.3.0  2016-02-17
加入导出功能
加入注册验证
优化功能，修复baugs
link_1,link_2 的算法需要完善
mssql scan tool v1.3.2  2016-02-27
优化功能，修复baugs
mssql scan tool v1.4.0  2016-05-23
优化功能，修复baugs
mssql scan tool v1.5.0  2016-06-21
3库联调
mssql scan tool v1.6.0  2016-07-05
完善导出模块
mssql scan tool v1.6.2  2016-07-06
修复link_1中的bug
修复结束偏移的设置
mssql scan tool v1.6.2  2016-07-14
优化
mssql scan tool v1.7.0  2016-07-27
加入多线程，界面加入进度显示



考虑c/s或b/s 模式, 获取信息
加个bak扫描：法1. 头部起始筛选 法2.扫描头部获取大小读到尾部取出文件。

-------- link_2 --------------------------------------------
从后到前拼接， 逆序拼接准确率高些
select offset_1,page_sum,page_no_1,page_no_2 from link_1 where file_no_1 = 1 order by page_no_1 desc
对结果集进行聚合。
create table aa1 as select count(*) b_count,group_id,start_pos,start_page from by_gfile group by group_id;
create table aa2 as select group_id,end_page from by_gfile where gin_id=1;
create table aa3 as select a.*,b.end_page,(b.end_page-a.start_page) page_count from aa1 a,aa2 b where a.group_id=b.group_id;
drop table aa1; drop table aa2;

