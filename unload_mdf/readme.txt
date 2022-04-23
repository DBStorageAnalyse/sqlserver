# -*- coding: utf-8 -*-
  SQL Server mdf 解析工具

先解析 出几个重要系统表， 然后通过这几个系统表的数据 来解析全部。
手工解析07 29 表.
BOOT ->07H ->29H ->32H/22H-> (29H/07H/05H/07H) -> 所有表/其他对象
cd /d C:\Python34\Scripts
cxfreeze C:\Users\zsz\PycharmProjects\sqlserver\test\ui_unload.py --target-dir=C:\Users\zsz\PycharmProjects\sqlserver\test\tt
cd /d C:\Users\zsz\PycharmProjects\sqlserver\test
pyinstaller -F -w C:\Users\zsz\PycharmProjects\sqlserver\test\ui_unload.py
pyinstaller 不支持 pymssql
history =============================================================================
2015-4-20   V1.0.0
支持sql2005/2008/2012/2014,不支持sql2000
2015-6-10   V1.0.3
2015-7-01   V1.0.6
2015-7-18   V1.1.0
加入图形界面
不支持行迁移,行链接
2015-7-31    V1.1.2
fix bugs
设置窗口可见，但没功能
2015-8-11    V1.1.6
优化界面功能
2015-11-11    V1.2.0
优化界面和功能
2015-11-13   V1.3.0
重构界面
完善功能，修复bugs
2015-11-14   V1.4.0
增加通过IAM位图解析表数据
改进bit字段存储
2015-11-17   V1.5.0
加入导出表数据到sql server数据库
修复bugs
2015-11-18   V1.6.0
加入存储过程，视图等对象的解析
2015-11-25   V1.7.0
加入表数据 delete 的 解析恢复
修复 记录解析，datetime 等的bugs
2015-11-26   V1.8.0
修复 记录解析，money,numeric,decimal,int,bigint 等的bugs
2015-11-27   V1.9.0
加入col溢出的解析
修复 bugs
2016-01-03   V1.10.0
三库 联调 1
2016-04-14   V1.12.0
完善显示记录数，完善decimal类型
2016-04-24   V2.1.0
重构记录解析
2016-05-20   V2.2.0
加入注册验证
2016-06-15   V2.2.5
完善bit解析
完善界面和功能(关于)
2016-06-15   V2.2.6
重构了user解析
加入导出到数据库
pyinstaller 暂不支持pymssql,改用pyodbc
2016-06-21   V2.3.0
三库 联调 2
2016-07-27   V2.4.0
加入多线程界面显示


遗留问题： 删中间列的解析
---------------------------------------------------------------------------------------
表结构上删除列，记录中总列数大于表总列数。  学生成绩管理系统.mdf  tab_name:班级信息,obj_id:885578193, pgfirst:204, pgfirstiam:205
记录中列数大于表的列数。  aa.mdf  的表 BankCode （删中间列） 在系统表syscolpars中的列序号有异常
表结构增加列，记录存储中总列数小于表总列数。 dbLogTest.mdf中 tab_name:log_test,obj_id:2105058535, pgfirst:79, pgfirstiam:80
学生成绩管理系统.mdf  sysmergepublications 表中，有很多bit字段。


# create table tab_info(id integer primary key,tab_obj_id,user_name,tab_name,col_sum,nullable_sum)
# create table col_info(id integer primary key,tab_obj_id,col_id,col_name,col_x_type,col_u_type,col_len,prec,scale,collationid,seed,nullable_is,var_len_is,def_data)
# col_info给解析系统表用，只存几个系统表的列信息，或给没有系统表时手工解析单表用
# insert into col_info(tab_obj_id,col_id,col_name,col_x_type,col_u_type,col_len,prec,scale,collationid,seed,nullable_is,var_len_is,def_data)
values(1,1,'a',1,1,4,0,0,null,null,1,0,0,null)




rasky@develer.com
10.1.4.1\MSSQL2008R2