###################################################################
#           Copyright (c) 2020 by TAOS Technologies, Inc.
#                     All rights reserved.
#
#  This file is proprietary and confidential to TAOS Technologies.
#  No part of this file may be reproduced, stored, transmitted,
#  disclosed or used in any form or by any means other than as
#  expressly provided by the written permission from Jianhui Tao
#
###################################################################

# -*- coding: utf-8 -*-

import sys
import os

from util.log import *
from util.cases import *
from util.sql import *
from util.dnodes import *

class TDTestCase:
    def init(self, conn, logSql):
        tdLog.debug("start to execute %s" % __file__)
        tdSql.init(conn.cursor(), logSql)
        
        self.ts = 1420041600000 # 2015-01-01 00:00:00  this is begin time for first record
        self.num = 10


    def caseDescription(self):

        '''
        this test case is for aggregate function elapsed , elapsed function can only used for the timestamp primary key column (ts) , 
        it has two input parameters,  the first parameter is necessary, basic SQL as follow:
        
        ===================================================================================================================================
        SELECT ELAPSED(field_name[, time_unit]) FROM { tb_name | stb_name } [WHERE clause] [INTERVAL(interval [, offset]) [SLIDING sliding]];
        ===================================================================================================================================

        elapsed function can acting on ordinary tables and super tables , notice that this function is related to the timeline.
        If it acts on a super table , it must be group by tbname . by the way ,this function support nested query.

        The scenarios covered by the test cases are as follows:

        ====================================================================================================================================

        case1: select * from table|stable[group by tbname]|regular_table

        case2:select elapsed(ts) from table|stable where clause interval (units) [fill(LINEAR,NEXT,PREV,VALUE,NULL)] [group by tbname] order [by ts desc asc|desc];
        
        case3:select elapsed(ts) , elapsed(ts,unit_time1)*regular_num1 , elapsed(ts,unit_time1)+regular_num2 from table|stable where clause interval (units) [fill(LINEAR,NEXT,PREV,VALUE,NULL)] [group by tbname] order [by ts desc asc|desc];
        
        //mixup with all functions only once query (it's different with nest query)
        case4:select elapsed(ts), count(*), avg(col), twa(col), irate(col), sum(col), stddev(col), leastsquares(col, 1, 1),min(col), max(col), first(col), last(col), percentile(col, 20), apercentile(col, 30), last_row(col), spread(col)from table|stable where clause interval (units)  [fill(LINEAR,NEXT,PREV,VALUE,NULL)] [group by tbname] order [by ts desc asc|desc];
       
        //mixup with ordinary col 
        case5:select ts ,elapsed(ts)*10 ,col+5 from table|stable where clause interval (units) [fill(LINEAR,NEXT,PREV,VALUE,NULL)] [group by tbname] order [by ts desc asc|desc];
        
        //nest query
        case6:select elapsed(ts) from (select elapsed(ts), count(*), avg(col), twa(col), irate(col), sum(col), stddev(col), leastsquares(col, 1, 1),min(col), max(col), first(col), last(col), percentile(col, 20), apercentile(col, 30), last_row(col), spread(col)from table|stable where clause interval (units)  [fill(LINEAR,NEXT,PREV,VALUE,NULL)] [group by tbname] order [by ts desc asc|desc]) where clause interval (units)  [fill(LINEAR,NEXT,PREV,VALUE,NULL)] [group by tbname] order [by ts desc asc|desc];
        
        //clause about filter condition
        case7:select  elapsed(ts) from table|stable[group by tbname] where [ts|col|tag >|<|=|>=|<=|=|<>|!= value] | [between ... and ...] |[in] |[is null|not null] interval (unit_time) ;
        case8:select  elapsed(ts) from table|stable[group by tbname] where clause1 and clause 2 and clause3  interval (unit_time)  ;

        //JOIN query
        case9:select elapsed(ts) from TABLE1 as tb1 , TABLE2 as tb2 where join_condition [TABLE1 and TABLE2 can be stable|table|sub_table|empty_table]

        //UNION ALL query
        case10:select elapsed(ts) from TABLE1 union all select elapsed(ts) from TABLE2 [TABLE1 and TABLE2 can be stable|table|sub_table|empty_table]

        // Window aggregation

        case11:select elapsed(ts) from t1 where  clause session(ts, time_units) ;
        case12:select elapsed(ts) from t1 where  clause state_window(regular_nums); 

        // Continuous query
        case13:create table select elapsed(ts)  ,avg(col) from (select elapsed(ts) ts_inter ,avg(col) col from stable|table interval (unit_time) [fill(LINEAR,NEXT,PREV,VALUE,NULL)][group by tbname])  interval (unit_time) [fill(LINEAR,NEXT,PREV,VALUE,NULL) sliding(unit_time_windows);

        ========================================================================================================================================

        this test case notice successful execution and correctness of results.

        ''' 
        return 

    def checkData(self, row, col, data):
        self.checkRowCol(row, col)
        if self.queryResult[row][col] != data:
            if self.cursor.istype(col, "TIMESTAMP"):
                # suppose user want to check nanosecond timestamp if a longer data passed
                if isinstance(data, int) or isinstance(data, float):
                    if pd.to_datetime(self.queryResult[row][col]) == pd.to_datetime(data):
                        tdLog.info("sql:%s, row:%d col:%d data:%d == expect:%s" %
                            (self.sql, row, col, self.queryResult[row][col], data))
                elif (len(data) >= 28):
                    if pd.to_datetime(self.queryResult[row][col]) == pd.to_datetime(data):
                        tdLog.info("sql:%s, row:%d col:%d data:%d == expect:%s" %
                            (self.sql, row, col, self.queryResult[row][col], data))
                else:
                    if self.queryResult[row][col] == _parse_datetime(data):
                        tdLog.info("sql:%s, row:%d col:%d data:%s == expect:%s" %
                            (self.sql, row, col, self.queryResult[row][col], data))
                return

            if str(self.queryResult[row][col]) == str(data):
                tdLog.info("sql:%s, row:%d col:%d data:%s == expect:%s" %
                            (self.sql, row, col, self.queryResult[row][col], data))
                return
            elif isinstance(data, float) and abs(self.queryResult[row][col] - data) <= 0.000001:
                tdLog.info("sql:%s, row:%d col:%d data:%f == expect:%f" %
                            (self.sql, row, col, self.queryResult[row][col], data))
                return
            else:
                caller = inspect.getframeinfo(inspect.stack()[1][0])
                args = (caller.filename, caller.lineno, self.sql, row, col, self.queryResult[row][col], data)
                tdLog.exit("%s(%d) failed: sql:%s row:%d col:%d data:%s != expect:%s" % args)

        if data is None:
            tdLog.info("sql:%s, row:%d col:%d data:%s == expect:%s" %
                       (self.sql, row, col, self.queryResult[row][col], data))
        elif isinstance(data, str):
            tdLog.info("sql:%s, row:%d col:%d data:%s == expect:%s" %
                       (self.sql, row, col, self.queryResult[row][col], data))
        elif isinstance(data, datetime.date):
            tdLog.info("sql:%s, row:%d col:%d data:%s == expect:%s" %
                       (self.sql, row, col, self.queryResult[row][col], data))
        elif isinstance(data, float):
            tdLog.info("sql:%s, row:%d col:%d data:%s == expect:%s" %
                       (self.sql, row, col, self.queryResult[row][col], data))
        else:
            tdLog.info("sql:%s, row:%d col:%d data:%s == expect:%d" %
                       (self.sql, row, col, self.queryResult[row][col], data))

    def check_results(self , sql ,results):
        data = tdSql.getResult(sql)
        if results == data:
            tdLog.info("sql:%s,check results data:%s == expect:%d" %
                       (self.sql, data,results))
        else:
            tdLog.exit("sql:%s,check results failed data:%s == expect:%d" %
                       (self.sql, data,results))
        

    def prepare_data(self):

        tdLog.info (" ====================================== prepare data ==================================================")
        
        tdSql.execute('drop database if exists testdb ;')
        tdSql.execute('create database testdb keep 36500;')
        tdSql.execute('use testdb;')

        tdSql.execute('create stable stable_1(ts timestamp ,tscol timestamp, q_int int , q_bigint bigint , q_smallint smallint , q_tinyint tinyint, q_float float ,\
             q_double double , bin_chars binary(20)) tags(loc nchar(20) ,ind int,tstag timestamp);')
        tdSql.execute('create stable stable_2(ts timestamp ,tscol timestamp, q_int int , q_bigint bigint , q_smallint smallint , q_tinyint tinyint, q_float float ,\
             q_double double, bin_chars binary(20) ) tags(loc nchar(20),ind int,tstag timestamp);')
        # create empty stables
        tdSql.execute('create stable stable_empty(ts timestamp ,tscol timestamp, q_int int , q_bigint bigint , q_smallint smallint , q_tinyint tinyint, q_float float ,\
             q_double double, bin_chars binary(20) ) tags(loc nchar(20),ind int,tstag timestamp);')
        tdSql.execute('create stable stable_sub_empty(ts timestamp ,tscol timestamp, q_int int , q_bigint bigint , q_smallint smallint , q_tinyint tinyint, q_float float ,\
             q_double double, bin_chars binary(20) ) tags(loc nchar(20),ind int,tstag timestamp);')

        # create empty sub_talbes and regular tables
        tdSql.execute('create table sub_empty_1 using stable_sub_empty tags("sub_empty_1",3,"2015-01-01 00:02:00")')
        tdSql.execute('create table sub_empty_2 using stable_sub_empty tags("sub_empty_2",3,"2015-01-01 00:02:00")')
        tdSql.execute('create table regular_empty (ts timestamp , tscol timestamp ,q_int int , q_bigint bigint , q_smallint smallint , q_tinyint tinyint , q_float float , q_double double , bin_chars binary(20)) ;')

        tdSql.execute('create table sub_table1_1 using stable_1 tags("sub1_1",1,"2015-01-01 00:00:00")')
        tdSql.execute('create table sub_table1_2 using stable_1 tags("sub1_2",2,"2015-01-01 00:01:00")')
        tdSql.execute('create table sub_table1_3 using stable_1 tags("sub1_3",3,"2015-01-01 00:02:00")')

        tdSql.execute('create table sub_table2_1 using stable_2 tags("sub2_1",1,"2015-01-01 00:00:00")')
        tdSql.execute('create table sub_table2_2 using stable_2 tags("sub2_2",2,"2015-01-01 00:01:00")')
        tdSql.execute('create table sub_table2_3 using stable_2 tags("sub2_3",3,"2015-01-01 00:02:00")')

        tdSql.execute('create table regular_table_1 (ts timestamp , tscol timestamp ,q_int int , q_bigint bigint , q_smallint smallint , q_tinyint tinyint , q_float float , q_double double, bin_chars binary(20)) ;')
        tdSql.execute('create table regular_table_2 (ts timestamp , tscol timestamp ,q_int int , q_bigint bigint , q_smallint smallint , q_tinyint tinyint , q_float float , q_double double , bin_chars binary(20)) ;')
        tdSql.execute('create table regular_table_3 (ts timestamp , tscol timestamp ,q_int int , q_bigint bigint , q_smallint smallint , q_tinyint tinyint , q_float float , q_double double , bin_chars binary(20)) ;')
        
        tablenames = ["sub_table1_1","sub_table1_2","sub_table1_3","sub_table2_1","sub_table2_2","sub_table2_3","regular_table_1","regular_table_2","regular_table_3"]

        tdLog.info("insert into records ")

        for tablename in tablenames:

            for i in range(self.num):  
                sql= 'insert into %s values(%d, %d,%d, %d, %d, %d, %f, %f, "%s")' % (tablename,self.ts + i*10000, self.ts + i*10,2147483647-i, 9223372036854775807-i, 32767-i, 127-i, i, i,("bintest"+str(i)))
                print(sql)
                tdSql.execute(sql)

        tdLog.info("=============================================data prepared done!=========================")

    def abnormal_common_test(self):

        tdLog.info (" ====================================== elapsed illeagal params ==================================================")

        tablenames = ["sub_table1_1","sub_table1_2","sub_table1_3","sub_table2_1","sub_table2_2","sub_table2_3","regular_table_1","regular_table_2","regular_table_3"]

        abnormal_list = ["()","(NULL)","(*)","(abc)","( , )","(NULL,*)","( ,NULL)","(%)","(+)","(*,)","(*, /)","(ts,10)","(ts,*)" "(ts,tbname*10)","(ts,tagname)","(ts,now-2d+3m)","(ts,2d+3m-2s)",
        "(ts,2d+3m-2s,)","(ts+1d,10s)","(ts+10d,NULL)" ,"(ts,now -1m%1d)","(ts+10d)","(ts+10d,_c0)","(ts+10d,)","(ts,%)","(ts, , )","(ts,abc)","(ts,/)","(ts,*)","(ts,now)","(ts,now+1d)","(ts,_c0)","(ts,1s,100)",
        "(ts,1s,abc)","(ts,1s,_c0)","(ts,1s,*)","(ts,1s,NULL)","(ts,,_c0)","(ts,tbname)","(ts,tbname,ts)","(ts,0,tbname)","('2021-11-18 00:00:10')","('2021-11-18 00:00:10', 1s)",
        "('2021-11-18T00:00:10+0800', '1s')","('2021-11-18T00:00:10Z', '1s')","('2021-11-18T00:00:10+0800', 10000000d,)","('ts', ,2021-11-18T00:00:10+0800, )"]
        
        for tablename in tablenames:
            for abnormal_param in abnormal_list:

                if tablename.startswith("stable"):
                    basic_sql= "select elapsed" + abnormal_param + " from " + tablename + " group by tbname ,ind order by tbname;"  #stables
                else:
                    basic_sql= "select elapsed" + abnormal_param + " from " + tablename + ";"  # regular table
                tdSql.error(basic_sql)

    def abnormal_use_test(self):

        tdLog.info (" ====================================== elapsed use abnormal ==================================================")

        sqls_list = ["select elapsed(ts) from regular_empty group by tbname,ind order by desc; ",
                    "select elapsed(ts) from regular_empty group by tbname,ind order by desc; ",
                    "select elapsed(ts) from regular_table_1 group by tbname,ind order by desc; ",
                    "select elapsed(ts) from sub_table1_1  group by tbname,ind order by desc; ",
                    "select elapsed(ts) from sub_table1_1  group by tbname,ind order by desc; ",
                    "select elapsed(ts,10s) from stable_empty group by ts order by ts;",
                    "select elapsed(ts,10s) from stable_1 group by ind order by ts;",
                    "select elapsed(ts,10s) from stable_2 group by tstag order by ts;",
                    "select elapsed(ts,10s) from stable_1 group by tbname,tstag,tscol order by ts;",
                    "select elapsed(ts,10s),ts from stable_1 group by tbname ,ind order by ts;",
                    "select ts,elapsed(ts,10s),tscol*100 from stable_1 group by tbname ,ind order by ts;",
                    "select elapsed(ts) from stable_1 group by tstag order by ts;",
                    "select elapsed(ts) from sub_empty_1 group by tbname,ind ,tscol order by ts desc;",
                    "select tbname, tscol,elapsed(ts) from sub_table1_1 group by tbname ,ind order by ts desc;",
                    "select elapsed(tscol) from sub_table1_1 order by ts desc;",
                    "select elapsed(tstag) from sub_table1_1 order by ts desc;",
                    "select elapsed(ind) from sub_table1_1 order by ts desc;",
                    "select elapsed(tscol) from sub_empty_1 order by ts desc;",
                    "select elapsed(tstag) from sub_empty_1 order by ts desc;",
                    "select elapsed(ind) from sub_table1_1 order by ts desc;",
                    "select elapsed(ind,10s) from sub_table1_1 order by ts desc;",
                    "select elapsed(tscol,10s) from sub_table1_1 order by ts desc;",
                    "select elapsed(tstag,10s) from sub_table1_1 order by ts desc;",
                    "select elapsed(q_int,10s) from sub_table1_1 order by ts desc;",
                    "select elapsed(loc,10s) from sub_table1_1 order by ts desc;",
                    "select elapsed(q_bigint,10s) from sub_table1_1 order by ts desc;",
                    "select elapsed(bin_chars,10s) from sub_table1_1 order by ts desc;"]
        for sql in sqls_list :
            tdSql.error(sql)

    def query_filter(self):

        tdLog.info (" ====================================== elapsed query filter ==================================================")
        
        for i in range(self.num):
            ts_start_time = self.ts + i*10000
            ts_col_start_time = self.ts + i*10
            ts_tag_time = "2015-01-01 00:01:00"
            ts_end_time = self.ts + (self.num-1-i)*10000
            ts_col_end_time = self.ts + (self.num-1-i)*10

            filter_sql = "select elapsed(ts,10s) from stable_1 where  ts >= %d group by tbname " %(ts_start_time)
            tdSql.query(filter_sql)
            tdSql.checkRows(3)
            tdSql.checkData(0,0,float(self.num -i-1))
            tdSql.checkData(1,0,float(self.num -i-1))
            tdSql.checkData(2,0,float(self.num -i-1))

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  ts >= %d  " %(ts_start_time)
            tdSql.query(filter_sql)
            tdSql.checkRows(1)
            tdSql.checkData(0,0,float(self.num -i-1))
                     

            filter_sql = "select elapsed(ts,10s) from stable_1 where  ts >= %d  and tscol >= %d and tstag='2015-01-01 00:01:00'group by tbname " %(ts_start_time,ts_col_start_time)
            tdSql.query(filter_sql)
            tdSql.checkRows(1)
            tdSql.checkData(0,0,float(self.num -i-1))

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  ts >= %d  and tscol >= %d  " %(ts_start_time,ts_col_start_time)
            tdSql.query(filter_sql)
            tdSql.checkRows(1)
            tdSql.checkData(0,0,float(self.num -i-1))

            filter_sql = "select elapsed(ts,10s) from stable_1 where  ts >= %d  and tscol > %d and tstag='2015-01-01 00:01:00' group by tbname" %(ts_start_time,ts_col_start_time)
            tdSql.query(filter_sql)
            
            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num -i-2))

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  ts >= %d  and tscol > %d " %(ts_start_time,ts_col_start_time)
            tdSql.query(filter_sql)
            
            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num -i-2))

            filter_sql = "select elapsed(ts,10s) from stable_1 where  ts > %d  and tscol > %d and tstag < '2015-01-01 00:01:00' group by tbname " %(ts_start_time,ts_col_start_time)
            tdSql.query(filter_sql)

            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num -i-2))

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  ts > %d  and tscol > %d  " %(ts_start_time,ts_col_start_time)
            tdSql.query(filter_sql)

            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num -i-2))

            filter_sql = "select elapsed(ts,10s) from stable_1 where  ts > %d  and tscol <= %d and tstag < '2015-01-01 00:01:00' group by tbname" %(ts_start_time,ts_col_start_time)
            tdSql.query(filter_sql)
            tdSql.checkRows(0)

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  ts > %d  and tscol <= %d " %(ts_start_time,ts_col_start_time)
            tdSql.query(filter_sql)
            tdSql.checkRows(0)

            filter_sql = "select elapsed(ts,10s) from stable_1 where  ts < %d  and tscol <= %d and tstag < '2015-01-01 00:01:00' group by tbname" %(ts_end_time,ts_col_end_time)
            tdSql.query(filter_sql)
            
            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num -i-2))

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  ts < %d  and tscol <= %d " %(ts_end_time,ts_col_end_time)
            tdSql.query(filter_sql)
            
            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num -i-2))

            filter_sql = "select elapsed(ts,10s) from stable_1 where  ts < %d  and tscol <= %d  group by tbname " %(ts_end_time,ts_col_end_time)
            tdSql.query(filter_sql)

            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(3)
                tdSql.checkData(0,0,float(self.num - i - 2))
                tdSql.checkData(1,0,float(self.num - i - 2))
                tdSql.checkData(2,0,float(self.num - i - 2))

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  ts < %d  and tscol <= %d   " %(ts_end_time,ts_col_end_time)
            tdSql.query(filter_sql)

            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num - i - 2))
                
            filter_sql = "select elapsed(ts,10s) from stable_1 where  ts = %d  and tscol < %d  group by tbname " %(ts_end_time,ts_col_end_time)
            tdSql.query(filter_sql)
            tdSql.checkRows(0)

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  ts = %d  and tscol < %d  " %(ts_end_time,ts_col_end_time)
            tdSql.query(filter_sql)
            tdSql.checkRows(0)

            filter_sql = "select elapsed(ts,10s) from stable_1 where  q_tinyint != %d  and tscol < %d  group by tbname " %(i,ts_col_end_time)
            tdSql.query(filter_sql)

            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(3)
                tdSql.checkData(0,0,float(self.num -i-2))
                tdSql.checkData(1,0,float(self.num -i-2))
                tdSql.checkData(2,0,float(self.num -i-2))

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  q_tinyint != %d  and tscol < %d   " %(i,ts_col_end_time)
            tdSql.query(filter_sql)

            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num -i-2))
                
            filter_sql = "select elapsed(ts,10s) from stable_1 where  q_tinyint != %d  and tscol <= %d  group by tbname " %(i,ts_col_end_time)
            tdSql.query(filter_sql)
            
            if i == self.num:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(3)
                tdSql.checkData(0,0,float(self.num - i - 1))
                tdSql.checkData(1,0,float(self.num - i - 1))
                tdSql.checkData(2,0,float(self.num - i - 1))

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  q_tinyint != %d  and tscol <= %d   " %(i,ts_col_end_time)
            tdSql.query(filter_sql)
            
            if i == self.num:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num - i - 1))

            filter_sql = "select elapsed(ts,10s) from stable_1 where  q_tinyint <> %d  and tscol < %d  group by tbname " %(i,ts_col_end_time)
            tdSql.query(filter_sql)

            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(3)
                tdSql.checkData(0,0,float(self.num -i-2))
                tdSql.checkData(1,0,float(self.num -i-2))
                tdSql.checkData(2,0,float(self.num -i-2))

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  q_tinyint <> %d  and tscol < %d   " %(i,ts_col_end_time)
            tdSql.query(filter_sql)

            if i == self.num-1:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num -i-2))

            filter_sql = "select elapsed(ts,10s) from stable_1 where  q_tinyint <> %d  and tscol <= %d  group by tbname " %(i,ts_col_end_time)
            tdSql.query(filter_sql)
            
            if i == self.num:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(3)
                tdSql.checkData(0,0,float(self.num - i - 1))
                tdSql.checkData(1,0,float(self.num - i - 1))
                tdSql.checkData(2,0,float(self.num - i - 1))

            filter_sql = "select elapsed(ts,10s) from sub_table1_1 where  q_tinyint <> %d  and tscol <= %d  " %(i,ts_col_end_time)
            tdSql.query(filter_sql)
            
            if i == self.num:
                tdSql.checkRows(0)
            else:
                tdSql.checkRows(1)
                tdSql.checkData(0,0,float(self.num - i - 1))

            # filter between and 
            tdSql.query("select elapsed(ts,10s) from sub_table1_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and q_tinyint between 125 and 127 and tscol <= '2015-01-01 00:01:00.000'  ")
            tdSql.checkData(0,0,2)
            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and \
            q_tinyint between 125 and 127 and tscol <= '2015-01-01 00:01:00.000' group by tbname ")
            tdSql.checkData(0,0,2)
            tdSql.checkData(1,0,2)
            tdSql.checkData(2,0,2)

            # filter in and or 
            tdSql.query("select elapsed(ts,10s) from sub_table1_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and q_tinyint between 125 and 127 and tscol <= '2015-01-01 00:01:00.000'  ")
            tdSql.checkData(0,0,2)

            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and q_tinyint between 125 and 127 and tscol <= '2015-01-01 00:01:00.000' group by tbname ")
            tdSql.checkData(0,0,2)
            tdSql.checkData(1,0,2)
            tdSql.checkData(2,0,2)

            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and q_tinyint in (125,126,127) and tscol <= '2015-01-01 00:01:00.000' group by tbname ")
            tdSql.checkData(0,0,2)
            tdSql.checkData(1,0,2)
            tdSql.checkData(2,0,2)

            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and bin_chars in ('bintest0','bintest1') and tscol <= '2015-01-01 00:01:00.000' group by tbname ")
            tdSql.checkData(0,0,1)
            tdSql.checkData(1,0,1)
            tdSql.checkData(2,0,1)

            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and bin_chars in ('bintest0','bintest1') and tscol <= '2015-01-01 00:01:00.000' group by tbname ")
            tdSql.checkData(0,0,1)
            tdSql.checkData(1,0,1)
            tdSql.checkData(2,0,1)
            
            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and bin_chars like 'bintest_' and tscol <= '2015-01-01 00:01:00.000' group by tbname ")
            tdSql.checkData(0,0,6)
            tdSql.checkData(1,0,6)
            tdSql.checkData(2,0,6)

            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and bin_chars like 'bintest_' and tscol <= '2015-01-01 00:01:00.000' group by tbname ")
            tdSql.checkData(0,0,6)
            tdSql.checkData(1,0,6)
            tdSql.checkData(2,0,6)

            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and bin_chars is not null  and tscol <= '2015-01-01 00:01:00.000' group by tbname; ")
            tdSql.checkData(0,0,6)
            tdSql.checkData(1,0,6)
            tdSql.checkData(2,0,6)

            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and bin_chars is null  and tscol <= '2015-01-01 00:01:00.000' group by tbname; ")
            tdSql.checkRows(0)

            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and bin_chars match '^b'  and tscol <= '2015-01-01 00:01:00.000' group by tbname; ")
            tdSql.checkRows(3)
            tdSql.checkData(0,0,6)
            tdSql.checkData(1,0,6)
            tdSql.checkData(2,0,6)

            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and bin_chars nmatch '^a'  and tscol <= '2015-01-01 00:01:00.000' group by tbname; ")
            tdSql.checkRows(3)
            tdSql.checkData(0,0,6)
            tdSql.checkData(1,0,6)
            tdSql.checkData(2,0,6)

            tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and bin_chars ='bintest1' or bin_chars ='bintest2' and tscol <= '2015-01-01 00:01:00.000' group by tbname; ")
            tdSql.checkRows(3)
            tdSql.checkData(0,0,6)
            tdSql.checkData(1,0,6)
            tdSql.checkData(2,0,6)
            
            tdSql.query("select elapsed(ts,10s) from stable_1 where (ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000')  or (ts between '2015-01-01 00:01:00.000'  and '2015-01-01 00:02:00.000') group by tbname; ")
            tdSql.checkRows(3)
            tdSql.checkData(0,0,9)
            tdSql.checkData(1,0,9)
            tdSql.checkData(2,0,9)

    def query_interval(self):

        tdLog.info (" ====================================== elapsed interval sliding fill ==================================================")

        # empty interval
        tdSql.query("select max(q_int)*10 from stable_empty where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(prev);")
        tdSql.checkRows(0)
        tdSql.query("select max(q_int)*10 from sub_empty_2 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(prev);")
        tdSql.checkRows(0)

        tdSql.query("select elapsed(ts,10s)*10 from stable_empty where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(prev) group by tbname;")
        tdSql.checkRows(0)
        tdSql.query("select elapsed(ts,10s)*10 from sub_empty_2 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(prev);")
        tdSql.checkRows(0)
        
        for i in range(self.num):
            ts_start_time = self.ts + i*10000
            ts_col_start_time = self.ts + i*10
            ts_tag_time = "2015-01-01 00:01:00"
            ts_end_time = self.ts + (self.num-1-i)*10000
            ts_col_end_time = self.ts + (self.num-1-i)*10
            

            # only interval 
            interval_sql = "select elapsed(ts,10s) from stable_1 where  ts <=%d interval(10s) group by tbname " %(ts_start_time)
            tdSql.query(interval_sql)
            tdSql.checkRows(3*(i+1))

            interval_sql = "select elapsed(ts,10s) from sub_table1_1 where  ts <=%d interval(10s) " %(ts_start_time)
            tdSql.query(interval_sql)
            tdSql.checkRows(i+1)
            for x in range(i+1):
                if x == i:
                    tdSql.checkData(x,1,0)
                else :
                    tdSql.checkData(x,1,1)
                
        # interval and fill , fill_type =  ["NULL","value,100","prev","next","linear"]

        # interval (10s)  and time range is outer records 

        tdSql.query("select elapsed(ts,10s)*10 from stable_empty where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(prev) group by tbname;")
        tdSql.checkRows(0)

        tdSql.query("select elapsed(ts,10s)*10 from sub_empty_2 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(prev);")
        tdSql.checkRows(0)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(prev) group by tbname;")
        tdSql.checkRows(180)
        tdSql.checkData(0,1,10)
        tdSql.checkData(9,1,0)
        tdSql.checkData(59,1,0)
        tdSql.checkData(60,1,10)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(next) group by tbname;")
        tdSql.checkRows(180)
        tdSql.checkData(0,1,10)
        tdSql.checkData(9,1,0)
        tdSql.checkData(10,1,None)
        tdSql.checkData(59,1,None)
        tdSql.checkData(60,1,10)
        tdSql.checkData(61,1,10)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(linear) group by tbname;")
        tdSql.checkRows(180)
        tdSql.checkData(0,1,10)
        tdSql.checkData(9,1,0)
        tdSql.checkData(10,1,None)
        tdSql.checkData(59,1,None)
        tdSql.checkData(60,1,10)
        tdSql.checkData(61,1,10)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(NULL) group by tbname;")
        tdSql.checkRows(180)
        tdSql.checkData(0,1,10)
        tdSql.checkData(9,1,0)
        tdSql.checkData(10,1,None)
        tdSql.checkData(59,1,None)
        tdSql.checkData(60,1,10)
        tdSql.checkData(61,1,10)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(10s) fill(value ,2) group by tbname;")
        tdSql.checkRows(180)
        tdSql.checkData(0,1,10)
        tdSql.checkData(9,1,0)
        tdSql.checkData(10,1,2)
        tdSql.checkData(59,1,2)
        tdSql.checkData(60,1,10)
        tdSql.checkData(61,1,10)
        
        # interval (20s)  and time range is outer records 
        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(20s) fill(prev) group by tbname,ind ;")
        tdSql.checkRows(90)
        tdSql.checkData(0,1,20)
        tdSql.checkData(4,1,10)
        tdSql.checkData(5,1,10)
        tdSql.checkData(29,1,10)
        tdSql.checkData(30,1,20)
        tdSql.checkData(31,1,20)
       
        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(20s) fill(next) group by tbname,ind ;")
        tdSql.checkRows(90)
        tdSql.checkData(0,1,20)
        tdSql.checkData(4,1,10)
        tdSql.checkData(5,1,None)
        tdSql.checkData(29,1,None)
        tdSql.checkData(30,1,20)
        tdSql.checkData(31,1,20)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(20s) fill(linear) group by tbname,ind ;")
        tdSql.checkRows(90)
        tdSql.checkData(0,1,20)
        tdSql.checkData(4,1,10)
        tdSql.checkData(5,1,None)
        tdSql.checkData(29,1,None)
        tdSql.checkData(30,1,20)
        tdSql.checkData(31,1,20)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(20s) fill(NULL) group by tbname,ind ;")
        tdSql.checkRows(90)
        tdSql.checkData(0,1,20)
        tdSql.checkData(4,1,10)
        tdSql.checkData(5,1,None)
        tdSql.checkData(29,1,None)
        tdSql.checkData(30,1,20)
        tdSql.checkData(31,1,20)
        
        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:10:00.000' interval(20s) fill(value ,2) group by tbname,ind ;")
        tdSql.checkRows(90)
        tdSql.checkData(0,1,20)
        tdSql.checkData(4,1,10)
        tdSql.checkData(5,1,2)
        tdSql.checkData(29,1,2)
        tdSql.checkData(30,1,20)
        tdSql.checkData(31,1,20)

        # interval (20s)  and time range is in records 

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:01:00.000' interval(20s) fill(prev) group by tbname,ind ;")
        tdSql.checkRows(9)
        tdSql.checkData(0,1,20)
        tdSql.checkData(2,1,10)
        tdSql.checkData(3,1,20)
        tdSql.checkData(5,1,10)
        tdSql.checkData(7,1,20)
        tdSql.checkData(8,1,10)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:01:00.000' interval(20s) fill(next) group by tbname,ind ;")
        tdSql.checkRows(9)
        tdSql.checkData(0,1,20)
        tdSql.checkData(2,1,10)
        tdSql.checkData(3,1,20)
        tdSql.checkData(5,1,10)
        tdSql.checkData(7,1,20)
        tdSql.checkData(8,1,10)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:01:00.000' interval(20s) fill(linear) group by tbname,ind ;")
        tdSql.checkRows(9)
        tdSql.checkData(0,1,20)
        tdSql.checkData(2,1,10)
        tdSql.checkData(3,1,20)
        tdSql.checkData(5,1,10)
        tdSql.checkData(7,1,20)
        tdSql.checkData(8,1,10)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:01:00.000' interval(20s) fill(NULL) group by tbname,ind ;")
        tdSql.checkRows(9)
        tdSql.checkData(0,1,20)
        tdSql.checkData(2,1,10)
        tdSql.checkData(3,1,20)
        tdSql.checkData(5,1,10)
        tdSql.checkData(7,1,20)
        tdSql.checkData(8,1,10)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:01:00.000' interval(20s) fill(value ,2 ) group by tbname,ind ;")
        tdSql.checkRows(9)
        tdSql.checkData(0,1,20)
        tdSql.checkData(2,1,10)
        tdSql.checkData(3,1,20)
        tdSql.checkData(5,1,10)
        tdSql.checkData(7,1,20)
        tdSql.checkData(8,1,10)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2015-01-01 00:00:00.000' and ts <'2015-01-01 00:01:00.000' interval(20s) group by tbname,ind ;")
        tdSql.checkRows(9)
        tdSql.checkData(0,1,20)
        tdSql.checkData(2,1,10)
        tdSql.checkData(3,1,20)
        tdSql.checkData(5,1,10)
        tdSql.checkData(7,1,20)
        tdSql.checkData(8,1,10)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2014-12-31 23:59:00.000' and ts <'2015-01-01 00:01:00.000' interval(20s) fill(NULL) group by tbname,ind ;")
        tdSql.checkRows(18)
        tdSql.checkData(0,1,None)
        tdSql.checkData(2,1,None)
        tdSql.checkData(3,1,20)
        tdSql.checkData(5,1,10)
        tdSql.checkData(7,1,None)
        tdSql.checkData(8,1,None)
        tdSql.checkData(9,1,20)

        # interval sliding

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2014-12-31 23:59:00.000' and ts <'2015-01-01 00:01:00.000' interval(20s) sliding(20s) fill(NULL) group by tbname,ind ;")
        tdSql.checkRows(18)
        tdSql.checkData(0,1,None)
        tdSql.checkData(2,1,None)
        tdSql.checkData(3,1,20)
        tdSql.checkData(5,1,10)
        tdSql.checkData(7,1,None)
        tdSql.checkData(8,1,None)
        tdSql.checkData(9,1,20)

        tdSql.query("select elapsed(ts,10s)*10 from stable_1 where ts >= '2014-12-31 23:59:00.000' and ts <'2015-01-01 00:01:00.000' interval(20s) sliding(10s) fill(NULL) group by tbname,ind ;")
        tdSql.checkRows(39)
        tdSql.checkData(0,1,None)
        tdSql.checkData(2,1,None)
        tdSql.checkData(6,1,10)
        tdSql.checkData(7,1,20)
        tdSql.checkData(12,1,0)
        tdSql.checkData(13,1,None)
        tdSql.checkData(15,1,None)
        tdSql.checkData(19,1,10)
        tdSql.checkData(20,1,20)
        tdSql.checkData(25,1,0)
         
    def query_mix_common(self):

        tdLog.info (" ======================================elapsed mixup with common col, it will not support =======================================")

        tdSql.query("select elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  and ind =1  group by tbname; ")
        tdSql.checkRows(1)
        tdSql.checkData(6)

        tdSql.query("select elapsed(ts,10s) from sub_table1_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  ; ")
        tdSql.checkRows(1)
        tdSql.checkData(6)

        tdSql.error("select ts,elapsed(ts,10s) from sub_empty_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000' ; ")
        tdSql.error("select ts,elapsed(ts,10s) from stable_empty where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  group by tbname; ")

        tdSql.error("select ts,elapsed(ts,10s) from sub_table1_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000' ; ")
        tdSql.error("select ts,elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  group by tbname; ")

        tdSql.error("select q_int,elapsed(ts,10s) from sub_table1_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000' ; ")
        tdSql.error("select q_int,elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  group by tbname; ")

        tdSql.error("select ts,q_int,elapsed(ts,10s) from sub_table1_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000' ; ")
        tdSql.error("select ts,q_int,elapsed(ts,10s) from stable_1 where ts between '2015-01-01 00:00:00.000'  and '2015-01-01 00:01:00.000'  group by tbname; ")

    def query_mix_Aggregate(self):

        tdLog.info (" ====================================== elapsed mixup with aggregate ==================================================")

        tdSql.query("select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) from sub_table1_1 ; ")

        data = tdSql.getResult("select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) from sub_table1_1 ; ")

        querys = ["count(*)","avg(q_int)", "twa(q_tinyint)", "irate(q_int)","sum(q_double)","stddev(q_float)","LEASTSQUARES(q_int,0,1)", "elapsed(ts,10s)"]

        for index , query in enumerate(querys):
            sql = "select %s from sub_table1_1 " %(query)
            tdSql.query(sql)
            tdSql.checkData(0,0,data[0][index])

        tdSql.query("select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) from stable_1  group by tbname; ")

        data = tdSql.getResult("select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) from stable_1 ; ")

        querys = ["count(*)","avg(q_int)", "twa(q_tinyint)", "irate(q_int)","sum(q_double)","stddev(q_float)","LEASTSQUARES(q_int,0,1)", "elapsed(ts,10s)"]

        for index , query in enumerate(querys):
            sql = "select %s from stable_1 group by tbname  " %(query)
            tdSql.query(sql)
            tdSql.checkData(0,0,data[0][index])
            tdSql.checkData(1,0,data[0][index])
            tdSql.checkData(2,0,data[0][index])

        
        # Arithmetic with elapsed for common table

        operators = ["+" ,"-" , "*" ,"/" ,"%"]
        querys_oper = ["count(*)","avg(q_int)", "twa(q_tinyint)", "irate(q_int)","sum(q_double)","stddev(q_float)", "elapsed(ts,10s)"]

        for operator in operators:

            query_datas=[]

            sql_common= "select "

            for index , query in enumerate(querys_oper):
                
                query_data = tdSql.getResult("select %s from sub_table1_1;"%query)
                
                query_datas.append(query_data[0][0])
                sql_common += " %s %s " %(query,operator)
            sql_common=sql_common[:-2] + " from sub_table1_1;"

            tdSql.query(sql_common)
            results= query_datas[0]
            if operator == "+":
                for data in query_datas[1:]: 
                    results += data
                tdSql.checkData(0,0,results)

            results= query_datas[0]
            if operator == "-":
                for data in query_datas[1:]:
                    results -= data
                tdSql.checkData(0,0,results)

            results= query_datas[0]
            if operator == "*":
                for data in query_datas[1:]:
                    results *= data
                tdSql.checkData(0,0,results)

            results= query_datas[0]
            if operator == "/":
                for data in query_datas[1:]:
                    results /= data
                tdSql.checkData(0,0,results)

            results= query_datas[0]
            if operator == "%":
                for data in query_datas[1:]:
                    results %= data
                tdSql.checkData(0,0,results)


        # Arithmetic with elapsed for super table

        operators = ["+" ,"-" , "*" ,"/" ,"%"]
        querys_oper = ["count(*)","avg(q_int)", "twa(q_tinyint)", "irate(q_int)","sum(q_double)","stddev(q_float)", "elapsed(ts,10s)"]

        for operator in operators:

            query_datas=[]

            sql_common= "select "

            for index , query in enumerate(querys_oper):
                
                query_data = tdSql.getResult("select %s from stable_1 group by tbname;"%query)
                
                query_datas.append(query_data[0][0])
                sql_common += " %s %s " %(query,operator)
            sql_common=sql_common[:-2] + " from stable_1 group by tbname;"

            tdSql.query(sql_common)
            results= query_datas[0]
            if operator == "+":
                for data in query_datas[1:]: 
                    results += data
                tdSql.checkData(0,0,results)
                tdSql.checkData(1,0,results)
                tdSql.checkData(2,0,results)


            results= query_datas[0]
            if operator == "-":
                for data in query_datas[1:]:
                    results -= data
                tdSql.checkData(0,0,results)
                tdSql.checkData(1,0,results)
                tdSql.checkData(2,0,results)

            results= query_datas[0]
            if operator == "*":
                for data in query_datas[1:]:
                    results *= data
                tdSql.checkData(0,0,results)
                tdSql.checkData(1,0,results)
                tdSql.checkData(2,0,results)

            results= query_datas[0]
            if operator == "/":
                for data in query_datas[1:]:
                    results /= data
                tdSql.checkData(0,0,results)
                tdSql.checkData(1,0,results)
                tdSql.checkData(2,0,results)

            results= query_datas[0]
            if operator == "%":
                for data in query_datas[1:]:
                    results %= data
                tdSql.checkData(0,0,results)
                tdSql.checkData(1,0,results)
                tdSql.checkData(2,0,results)

    def query_mix_select(self):

        tdLog.info (" ====================================== elapsed mixup with select function =================================================")

        querys = ["max(q_int)","min(q_int)" , "first(q_tinyint)", "first(*)","last(q_int)","last(*)","top(q_double,1)","bottom(q_float,1)","PERCENTILE(q_int,10)","APERCENTILE(q_int,10)","last_row(q_int)", "last_row(*)" , "interp(q_int)" ,"elapsed(ts,10s)"]

        for index , query in enumerate(querys):

            
            sql1 = "select elapsed(ts,10s),%s from sub_table1_1 " %(query)
            sql2 = "select elapsed(ts,10s),%s from stable_1  group by tbname" %(query)

            if query in ["top(q_double,1)","bottom(q_float,1)","last_row(*)","last_row(q_int)","interp(q_int)"]: # not support mixup with top and bottom
                
                print(sql1)
                print(sql2)
                if query in ["PERCENTILE(q_int,10)"]:  # not support group by tbname
                    tdSql.error(sql1)
                    tdSql.error(sql2)
                    continue
                else:

                    tdSql.error(sql1)
                    tdSql.error(sql2)
                    continue
                tdSql.execute(sql1)
                tdSql.execute(sql2)
        
        querys_mix = ["max(q_int)","min(q_int)" , "first(q_tinyint)", "first(q_int)","last(q_int)","PERCENTILE(q_int,10)","APERCENTILE(q_int,10)","elapsed(ts,10s)"]
        
        tdSql.query("select max(q_int),min(q_int) , first(q_tinyint), first(q_int),last(q_int),PERCENTILE(q_int,10),APERCENTILE(q_int,10) ,elapsed(ts,10s) from sub_table1_1 ; ")

        data = tdSql.getResult("select max(q_int),min(q_int) , first(q_tinyint), first(q_int),last(q_int),PERCENTILE(q_int,10),APERCENTILE(q_int,10) ,elapsed(ts,10s) from sub_table1_1 ; ")

        for index , query in enumerate(querys_mix):
            sql = "select %s from sub_table1_1 " %(query)
            tdSql.query(sql)
            tdSql.checkData(0,0,data[0][index])

        tdSql.query("select max(q_int),min(q_int) , first(q_tinyint), first(q_int),last(q_int),APERCENTILE(q_int,10) ,elapsed(ts,10s) from stable_1 group by tbname ; ")

        data = tdSql.getResult("select max(q_int),min(q_int) , first(q_tinyint), first(q_int),last(q_int),APERCENTILE(q_int,10) ,elapsed(ts,10s) from stable_1 group by tbname ; ")

        querys_mix = ["max(q_int)","min(q_int)" , "first(q_tinyint)", "first(q_int)","last(q_int)","APERCENTILE(q_int,10)","elapsed(ts,10s)"]

        for index , query in enumerate(querys_mix):
            sql = "select %s from stable_1 group by tbname " %(query)
            tdSql.query(sql)
            tdSql.checkData(0,0,data[0][index])
            tdSql.checkData(1,0,data[0][index])
            tdSql.checkData(2,0,data[0][index])
        
        operators = ["+" ,"-" , "*" ,"/" ,"%"]
        querys_oper = querys_mix

        for operator in operators:

            query_datas=[]

            sql_common= "select "

            for index , query in enumerate(querys_oper):
                
                query_data = tdSql.getResult("select %s from sub_table1_1;"%query)
                
                query_datas.append(query_data[0][0])
                sql_common += " %s %s " %(query,operator)
            sql_common=sql_common[:-2] + " from sub_table1_1;"

            tdSql.query(sql_common)
            results= query_datas[0]
            if operator == "+":
                for data in query_datas[1:]: 
                    results += data
                tdSql.checkData(0,0,results)

            results= query_datas[0]
            if operator == "-":
                for data in query_datas[1:]:
                    results -= data
                tdSql.checkData(0,0,results)

            results= query_datas[0]
            if operator == "*":
                for data in query_datas[1:]:
                    results *= data
                tdSql.checkData(0,0,results)

            results= query_datas[0]
            if operator == "/":
                for data in query_datas[1:]:
                    results /= data
                tdSql.checkData(0,0,results)

            results= query_datas[0]
            if operator == "%":
                for data in query_datas[1:]:
                    results %= data
                tdSql.checkData(0,0,results)


        # Arithmetic with elapsed for super table

        operators = ["+" ,"-" , "*" ,"/" ,"%"]
        querys_oper = querys_mix

        for operator in operators:

            query_datas=[]

            sql_common= "select "

            for index , query in enumerate(querys_oper):
                
                query_data = tdSql.getResult("select %s from stable_1 group by tbname;"%query)
                
                query_datas.append(query_data[0][0])
                sql_common += " %s %s " %(query,operator)
            sql_common=sql_common[:-2] + " from stable_1 group by tbname;"

            tdSql.query(sql_common)
            results= query_datas[0]
            if operator == "+":
                for data in query_datas[1:]: 
                    results += data
                tdSql.checkData(0,0,results)
                tdSql.checkData(1,0,results)
                tdSql.checkData(2,0,results)


            results= query_datas[0]
            if operator == "-":
                for data in query_datas[1:]:
                    results -= data
                tdSql.checkData(0,0,results)
                tdSql.checkData(1,0,results)
                tdSql.checkData(2,0,results)

            results= query_datas[0]
            if operator == "*":
                for data in query_datas[1:]:
                    results *= data
                tdSql.checkData(0,0,results)
                tdSql.checkData(1,0,results)
                tdSql.checkData(2,0,results)

            results= query_datas[0]
            if operator == "/":
                for data in query_datas[1:]:
                    results /= data
                tdSql.checkData(0,0,results)
                tdSql.checkData(1,0,results)
                tdSql.checkData(2,0,results)

            results= query_datas[0]
            if operator == "%":
                for data in query_datas[1:]:
                    results %= data
                tdSql.checkData(0,0,results)
                tdSql.checkData(1,0,results)
                tdSql.checkData(2,0,results)
                
    def query_mix_compute(self):

        tdLog.info (" ====================================== elapsed mixup with compute function =================================================")

        querys = ["diff(q_int)","DERIVATIVE(q_int,1s,1)","spread(ts)","spread(q_tinyint)","ceil(q_float)","floor(q_float)","round(q_float)"]

        for index , query in enumerate(querys):

            sql1 = "select elapsed(ts,10s),%s from sub_table1_1 " %(query)
            sql2 = "select elapsed(ts,10s),%s from stable_1  group by tbname" %(query)
            if query in ["diff(q_int)","DERIVATIVE(q_int,1s,1)","ceil(q_float)","floor(q_float)","round(q_float)"]:
                tdSql.error(sql1)
                tdSql.error(sql2)
                continue
            tdSql.query(sql1)
            tdSql.query(sql2)
        
        # only support mixup with spread 

        sql = "select spread(ts)*10,spread(q_tinyint)-10,elapsed(ts,10s) from sub_table1_1 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev) ;"
        tdSql.execute(sql)

        data = tdSql.getResult(sql)

        sql = "select spread(ts)*10,spread(q_tinyint)-10,elapsed(ts,10s) from stable_1 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev) group by tbname;"
        tdSql.execute(sql)

        querys_mix = ["spread(ts)","spread(q_tinyint)-10","elapsed(ts,10s)"]

        for index , query in enumerate(querys_mix):
            sql = "select %s from sub_table1_1 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev) ; " %(query)
            tdSql.query(sql)
        
        operators = ["+" ,"-" , "*" ,"/" ,"%"]
        querys_oper = querys_mix

        for operator in operators:

            sql_common= "select "

            for index , query in enumerate(querys_oper):
                
                sql_common += " %s %s " %(query,operator)
            sql_common=sql_common[:-2] + " from stable_1 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev) group by tbname;"

            tdSql.query(sql_common)

        for index , query in enumerate(querys_mix):
            sql = "select %s from stable_1 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev) group by tbname ; " %(query)
            tdSql.query(sql)
        
        operators = ["+" ,"-" , "*" ,"/" ,"%"]
        querys_oper = querys_mix

        for operator in operators:

            sql_common= "select "

            for index , query in enumerate(querys_oper):
                
                sql_common += " %s %s " %(query,operator)
            sql_common=sql_common[:-2] + " from stable_1 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev) group by tbname;"

            tdSql.query(sql_common)
    
    def query_mix_arithmetic(self):
        
        tdLog.info (" ====================================== elapsed mixup with arithmetic =================================================")
 
        tdSql.execute("select elapsed(ts,10s)+1 ,elapsed(ts,10s)-2,elapsed(ts,10s)*3,elapsed(ts,10s)/4,elapsed(ts,10s)%5 from sub_table1_1 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev) ; ")
        tdSql.execute("select elapsed(ts,10s)+1 ,elapsed(ts,10s)-2,elapsed(ts,10s)*3,elapsed(ts,10s)/4,elapsed(ts,10s)%5 from stable_1 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev) group by tbname; ")
         
        queries = ["elapsed(ts,10s)+1" ,"elapsed(ts,10s)-2","elapsed(ts,10s)*3","elapsed(ts,10s)/4","elapsed(ts,10s)%5" ]
        
        for index ,query in enumerate(queries):
            sql = "select %s from sub_table1_1 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev) ;" % (query)
            data =  tdSql.getResult(sql)
            tdSql.query("select elapsed(ts,10s)+1 ,elapsed(ts,10s)-2,elapsed(ts,10s)*3,elapsed(ts,10s)/4,elapsed(ts,10s)%5 from sub_table1_1 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev) ; ")
            tdSql.checkData(0,index+1,data[0][1])

    def query_with_join(self):

        tdLog.info (" ====================================== elapsed mixup with join =================================================")
        
        tdSql.error("select elapsed(ts,10s) from stable_empty TABLE1 , stable_empty TABLE2  where TABLE1.ts =TABLE2.ts; ")
        tdSql.error("select elapsed(ts,10s) from stable_empty TABLE1 , stable_empty TABLE2  where TABLE1.ts =TABLE2.ts group by tbname; ")

        tdSql.execute("select elapsed(ts,10s) from sub_empty_1 TABLE1 , sub_empty_2 TABLE2  where TABLE1.ts =TABLE2.ts; ")
        tdSql.error("select elapsed(ts,10s) from stable_1 TABLE1 , stable_2 TABLE2  where TABLE1.ts =TABLE2.ts and TABLE1.ind =TABLE2.ind; ")
        tdSql.error("select elapsed(ts,10s) from stable_1 TABLE1 , stable_2 TABLE2  where TABLE1.ts =TABLE2.ts and TABLE1.ind =TABLE2.ind group by tbname,ind; ") # join not support group by

        tdSql.error("select elapsed(ts,10s) from sub_empty_1 TABLE1 , stable_2 TABLE2  where TABLE1.ts =TABLE2.ts and TABLE1.ind =TABLE2.ind ; ")
        tdSql.execute("select elapsed(ts,10s) from sub_empty_1 TABLE1 , sub_empty_2 TABLE2  where TABLE1.ts =TABLE2.ts ; ")

        tdSql.query("select elapsed(ts,10s) from sub_table1_1 TABLE1 , sub_table1_2 TABLE2  where TABLE1.ts =TABLE2.ts ; ")
        tdSql.checkData(0,0,9)

        tdSql.query("select elapsed(ts,10s) from sub_empty_1 TABLE1 , sub_table1_2 TABLE2  where TABLE1.ts =TABLE2.ts ; ")
        tdSql.checkRows(0)

        tdSql.query("select elapsed(ts,10s) from sub_empty_1 TABLE1 , regular_empty  TABLE2  where TABLE1.ts =TABLE2.ts ; ")
        tdSql.checkRows(0)

        tdSql.query("select elapsed(ts,10s) from sub_empty_1 TABLE1 , regular_table_1  TABLE2  where TABLE1.ts =TABLE2.ts ; ")
        tdSql.checkRows(0)

        tdSql.query("select elapsed(ts,10s) from sub_table1_3 TABLE1 , regular_table_1  TABLE2  where TABLE1.ts =TABLE2.ts ; ")
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)

        tdSql.query("select elapsed(ts,10s) from regular_table_1 ; ")
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)

    def query_with_union(self):

        tdLog.info (" ====================================== elapsed mixup with union all =================================================")

        # union all with empty 

        tdSql.query("select elapsed(ts,10s) from regular_table_1  union all  select elapsed(ts,10s) from regular_table_2;")

        tdSql.query("select elapsed(ts,10s) from regular_table_1  where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)  union all \
        select elapsed(ts,10s) from regular_table_2 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev);")
        tdSql.checkRows(1200)
        tdSql.checkData(0,1,0.1)
        tdSql.checkData(500,1,0)

        tdSql.query("select elapsed(ts,10s) from sub_empty_1  where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)  union all \
        select elapsed(ts,10s) from regular_table_2 where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev);")
        tdSql.checkRows(600)
        tdSql.checkData(0,1,0.1)
        tdSql.checkData(500,0,0)
        
        tdSql.query('select elapsed(ts,10s) from sub_empty_1 union all select elapsed(ts,10s) from sub_empty_2;')
        tdSql.checkRows(0)

        tdSql.query('select elapsed(ts,10s) from regular_table_1 union all select elapsed(ts,10s) from sub_empty_1;')
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)

        tdSql.query('select elapsed(ts,10s) from sub_empty_1 union all select elapsed(ts,10s) from regular_table_1;')
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)

        tdSql.query('select elapsed(ts,10s) from sub_empty_1 union all select elapsed(ts,10s) from sub_table1_1;')
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)

        tdSql.query('select elapsed(ts,10s) from sub_table1_1 union all select elapsed(ts,10s) from sub_empty_1;')
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)

        tdSql.query('select elapsed(ts,10s) from sub_empty_1 union all select elapsed(ts,10s) from regular_table_1;')
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)

        tdSql.error('select elapsed(ts,10s) from sub_empty_1 union all select elapsed(ts,10s) from stable_sub_empty group by tbname;')

        tdSql.error('select elapsed(ts,10s) from regular_table_1 union all select elapsed(ts,10s) from stable_sub_empty group by tbname;')

        tdSql.query('select elapsed(ts,10s) from sub_empty_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(1s) fill(prev) union all select elapsed(ts,10s) from sub_empty_2 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(1s) fill(prev);')
        tdSql.checkRows(0)

        tdSql.error('select elapsed(ts,10s) from sub_empty_1   union all select elapsed(ts,10s) from stable_empty  group by tbname;')
        
        tdSql.error('select elapsed(ts,10s) from sub_empty_1  interval(1s)  union all select elapsed(ts,10s) from stable_empty interval(1s)  group by tbname;')
    
        tdSql.error('select elapsed(ts,10s) from sub_empty_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(1s) fill(prev) union all select elapsed(ts,10s) from stable_empty where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(1s) fill(prev) group by tbname;')
        
        tdSql.query("select elapsed(ts,10s) from stable_empty  group by tbname union all select elapsed(ts,10s) from stable_empty group by tbname ;")
        tdSql.checkRows(0)

        tdSql.query("select elapsed(ts,10s) from stable_empty  group by tbname union all select elapsed(ts,10s) from stable_1 group by tbname ;")
        tdSql.checkRows(0)

        tdSql.query("select elapsed(ts,10s) from stable_1  group by tbname union all select elapsed(ts,10s) from stable_1 group by tbname ;")
        tdSql.checkRows(6)
        tdSql.checkData(0,0,9)
        tdSql.checkData(5,0,9)

        tdSql.query("select elapsed(ts,10s) from stable_1  group by tbname union all select elapsed(ts,10s) from stable_2 group by tbname ;")
        tdSql.checkRows(6)
        tdSql.checkData(0,0,9)
        tdSql.checkData(5,0,9)

        tdSql.query('select elapsed(ts,10s) from stable_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) group by tbname union all\
             select elapsed(ts,10s) from stable_2 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) group by tbname ;')
        tdSql.checkRows(360)
        tdSql.checkData(0,1,1)
        tdSql.checkData(50,1,0)
        
        # bug : TD-12229
        # tdSql.query('select elapsed(ts,10s) from stable_empty group by tbname union all  select elapsed(ts,10s) from stable_2 group by tbname ;')
        # tdSql.checkRows(3)

        tdSql.query('select elapsed(ts,10s) from stable_1 group by tbname union all  select elapsed(ts,10s) from stable_empty group by tbname ;')
        tdSql.checkRows(3)


        # tdSql.query('select elapsed(ts,10s) from stable_empty where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) group by tbname union all\
        #      select elapsed(ts,10s) from stable_2 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) group by tbname ;')
        # tdSql.checkRows(180)

        tdSql.query('select elapsed(ts,10s) from stable_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) group by tbname union all\
             select elapsed(ts,10s) from stable_empty where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) group by tbname ;')
        tdSql.checkRows(180)

        # union all with sub table and regular table

        # sub_table with sub_table 

        tdSql.query('select elapsed(ts,10s) from sub_table1_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev)  union all\
             select elapsed(ts,10s) from sub_table2_2 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) ;')
        tdSql.checkRows(120)
        tdSql.checkData(0,1,1)
        tdSql.checkData(12,1,0)

        tdSql.query('select elapsed(ts,10s) from sub_table1_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev)  union all\
             select elapsed(ts,10s) from sub_table1_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) ;')
        tdSql.checkRows(120)
        tdSql.checkData(0,1,1)
        tdSql.checkData(12,1,0)

        tdSql.query('select elapsed(ts,10s) from regular_table_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev)  union all\
             select elapsed(ts,10s) from sub_table1_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) ;')
        tdSql.checkRows(120)
        tdSql.checkData(0,1,1)
        tdSql.checkData(12,1,0)

        tdSql.query('select elapsed(ts,10s) from regular_table_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev)  union all\
             select elapsed(ts,10s) from regular_table_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) ;')
        tdSql.checkRows(120)
        tdSql.checkData(0,1,1)
        tdSql.checkData(12,1,0)

        tdSql.query('select elapsed(ts,10s) from regular_table_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev)  union all\
             select elapsed(ts,10s) from regular_table_2 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) ;')
        tdSql.checkRows(120)
        tdSql.checkData(0,1,1)
        tdSql.checkData(12,1,0)

        tdSql.query('select elapsed(ts,10s) from regular_table_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev)  union all\
             select elapsed(ts,10s) from regular_table_2 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) ;')
        tdSql.checkRows(120)
        tdSql.checkData(0,1,1)
        tdSql.checkData(12,1,0)
        
        tdSql.query('select elapsed(ts,10s) from sub_empty_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev)  union all\
             select elapsed(ts,10s) from regular_table_2 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) ;')
        tdSql.checkRows(60)
        tdSql.checkData(0,1,1)
        tdSql.checkData(12,1,0)

        tdSql.query('select elapsed(ts,10s) from regular_table_2 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev)  union all\
             select elapsed(ts,10s) from sub_empty_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) ;')
        tdSql.checkRows(60)
        tdSql.checkData(0,1,1)
        tdSql.checkData(12,1,0)

        # stable with stable 

        tdSql.query('select elapsed(ts,10s) from stable_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev)  group by tbname union all\
             select elapsed(ts,10s) from stable_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) group by tbname;')
        tdSql.checkRows(360)
        tdSql.checkData(0,1,1)
        tdSql.checkData(12,1,0)

        tdSql.query('select elapsed(ts,10s) from regular_table_2  interval(10s)  union all  select elapsed(ts,10s) from sub_empty_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev);')
        tdSql.checkRows(10)
        tdSql.checkData(0,1,1)
        tdSql.checkData(9,1,0)

        tdSql.query('select elapsed(ts,10s) from regular_table_2  interval(10s)  union all  select elapsed(ts,10s) from regular_table_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(10s) fill(prev) ;')
        tdSql.checkRows(70)
        tdSql.checkData(0,1,1)
        tdSql.checkData(9,1,0)

        tdSql.query('select elapsed(ts,10s) from regular_table_2  interval(10s) order by ts desc union all  select elapsed(ts,10s) from regular_table_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000"  interval(10s) fill(prev) order by ts asc;')
        tdSql.checkRows(70)
        tdSql.checkData(0,1,0)
        tdSql.checkData(1,1,1)
        tdSql.checkData(9,1,1)

        tdSql.query('select elapsed(ts,10s) from stable_1 group by tbname, ind  order by ts desc union all  select elapsed(ts,10s) from stable_2 group by tbname, ind  order by ts asc ;')
        tdSql.checkRows(6)
        tdSql.checkData(0,0,9)

        tdSql.query('select elapsed(ts,10s) from stable_1 group by tbname, ind  order by ts desc union all  select elapsed(ts,10s) from stable_1 group by tbname, ind  order by ts asc ;')
        tdSql.checkRows(6)
        tdSql.checkData(0,0,9)

        tdSql.query('select elapsed(ts,10s) from stable_1  interval(10s) group by tbname,ind order by ts desc union all  select elapsed(ts,10s) from stable_2 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000"  interval(10s) fill(prev) group by tbname,ind order by ts asc ;')
        tdSql.checkRows(210)
        tdSql.checkData(0,1,0)
        tdSql.checkData(1,1,1)
        tdSql.checkData(9,1,1)

        tdSql.query('select elapsed(ts,10s) from stable_2  interval(10s) group by tbname,ind order by ts desc union all  select elapsed(ts,10s) from stable_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000"  interval(10s) fill(prev) group by tbname,ind order by ts asc ;')
        tdSql.checkRows(210)
        tdSql.checkData(0,1,0)
        tdSql.checkData(1,1,1)
        tdSql.checkData(9,1,1)

        tdSql.query('select elapsed(ts,10s) from stable_1  interval(10s) group by tbname,ind order by ts desc union all  select elapsed(ts,10s) from stable_1 where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000"  interval(10s) fill(prev) group by tbname,ind order by ts asc ;')
        tdSql.checkRows(210)
        tdSql.checkData(0,1,0)
        tdSql.checkData(1,1,1)
        tdSql.checkData(9,1,1)

    def query_nest(self):

        tdLog.info (" ====================================== elapsed query for nest =================================================")

        # ===============================================outer nest============================================
        
        # regular table

        tdSql.query("select elapsed(ts,10s) from (select ts from regular_table_1 );")
        tdSql.checkData(0,0,9)

        # bug : TD-12164 

        # tdSql.error("select elapsed(ts,10s) from (select qint ts from regular_table_1 );")
        # tdSql.error("select elapsed(tbname ,10s) from (select qint tbname from regular_table_1 );")
        # tdSql.error("select elapsed(tsc ,1s) from (select q_int tsc from regular_table_1) ;")
        # tdSql.error("select elapsed(tsv ,1s) from (select elapsed(ts,1s) tsv from regular_table_1);")
        # tdSql.error("select elapsed(ts ,1s) from (select elapsed(ts,1s) ts from regular_table_1);")
        # tdSql.error("select elapsed(tsc ,1s) from (select tscol tsc from regular_table_1) ;")
        
        # # bug TD-12276
        # tdSql.query("select elapsed(ts,10s) from (select ts,tbname from regular_table_1 order by ts asc );")
        # tdSql.checkData(0,0,9)

        # tdSql.query("select elapsed(ts,10s) from (select ts,tbname  from regular_table_1 order by ts desc );")
        # tdSql.checkData(0,0,9)

        tdSql.query("select elapsed(ts,10s) from (select ts ,max(q_int),tbname  from regular_table_1 order by ts  ) interval(1s);")
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)

        tdSql.query("select elapsed(ts,10s) from (select ts ,q_int,tbname  from regular_table_1 order by ts  ) interval(1s);")
        tdSql.checkRows(10)
        tdSql.checkData(0,0,0)

        # sub table

        tdSql.query("select elapsed(ts,10s) from (select ts from sub_table1_1  );")
        tdSql.checkData(0,0,9)

        tdSql.query("select elapsed(ts,10s) from (select ts ,max(q_int),tbname  from sub_table1_1 order by ts  ) interval(1s);")
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)

        tdSql.query("select elapsed(ts,10s) from (select ts ,q_int,tbname  from sub_table1_1 order by ts  ) interval(1s);")
        tdSql.checkRows(10)
        tdSql.checkData(0,0,0)

        tdSql.query("select elapsed(ts,10s) from (select ts ,tbname,top(q_int,3)  from sub_table1_1   ) interval(10s);")
        tdSql.checkRows(3)
        tdSql.checkData(0,0,1)

        tdSql.query("select elapsed(ts,10s) from (select ts ,tbname,bottom(q_int,3)  from sub_table1_1   ) interval(10s);")
        tdSql.checkRows(3)
        tdSql.checkData(0,0,1)

        tdSql.query("select elapsed(ts,10s) from (select ts ,tbname,last_row(*)  from sub_table1_1   ) interval(10s);")
        tdSql.checkRows(1)
        tdSql.checkData(0,0,0)

        tdSql.query("select elapsed(ts,10s) from (select ts ,tbname,last_row(q_int)  from sub_table1_1   ) interval(10s);")
        tdSql.checkRows(1)
        tdSql.checkData(0,0,0)

        tdSql.error("select elapsed(ts,10s) from (select ts ,count(*),tbname  from sub_table1_1 order by ts  ) interval(1s);")

        querys = ["count(*)","avg(q_int)","twa(q_tinyint)", "irate(q_int)","sum(q_double)","stddev(q_float)","LEASTSQUARES(q_int,0,1)","elapsed(ts,10s)"]
        
        for query in querys:
            sql1 = "select elapsed(ts,10s) from (select %s from regular_table_1 order by ts  ) interval(1s); " % query
            sql2 = "select elapsed(ts,10s) from (select ts , tbname ,%s from regular_table_1 order by ts  ) interval(1s); " % query
            sql3 = "select elapsed(ts,10s) from (select ts , tbname ,%s from stable_1 group by tbname, ind order by ts  ) interval(1s); " % query
            sql4 = "select elapsed(ts,10s) from (select %s from sub_table2_1  order by ts  ) interval(1s); " % query
            sql5 = "select elapsed(ts,10s) from (select ts , tbname ,%s from sub_table2_1  order by ts  ) interval(1s); " % query

            tdSql.error(sql1)
            tdSql.error(sql2)
            tdSql.error(sql3)
            tdSql.error(sql4)
            tdSql.error(sql5)

        
        # # bug TD-12164
        # tdSql.error( "select elapsed(ts00 ,1s) from (select elapsed(ts,1s) ts00 from regular_table_1) ; " )
        # tdSql.error( "select elapsed(ts ,1s) from (select elapsed(ts,1s) ts from regular_table_1) ; " )
        
        # tdSql.error( "select elapsed(ts00 ,1s) from (select elapsed(ts,1s) ts00 from stable_1 group by tbname ) ; " )
        # tdSql.error( "select elapsed(ts ,1s) from (select elapsed(ts,1s) ts from stable_1 group by tbname) ; " )


        # stable 

        tdSql.error("select elapsed(ts,10s) from (select ts from stable_1 ) group by tbname ;")

        tdSql.error("select elapsed(ts,10s) from (select ts ,max(q_int),tbname  from stable_1 group by tbname order by ts ) interval(1s) group by tbname;")

        tdSql.error("select elapsed(ts,10s) from (select ts ,q_int,tbname  from stable_1 order by ts ) interval(1s) group by tbname;")

        # mixup with aggregate 

        querys = ["max(q_int)","min(q_int)" , "first(q_tinyint)", "first(*)","last(q_int)","last(*)","top(q_double,1)",
        "bottom(q_float,1)","PERCENTILE(q_int,10)","APERCENTILE(q_int,10)","last_row(q_int)", "last_row(*)" , "interp(q_int)" ,"elapsed(ts,10s)"]

        for index , query in enumerate(querys):

            sql1 = "select elapsed(ts,10s) from (select %s from sub_table1_1) where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(10s) fill(prev) ;  " %(query)
            sql2 = "select elapsed(ts,10s) from (select %s from stable_1 ) where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(10s) fill(prev)  group by tbname; " %(query)
            sql3 = "select elapsed(ts,10s) from (select %s from stable_1 group by tbname) where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(10s) fill(prev)  group by tbname; " %(query)

            if query in ["top(q_double,1)","bottom(q_float,1)","interp(q_int)"  ]: 
                print(sql1 )
                print(sql2)
                tdSql.query(sql1)
                tdSql.error(sql2)
            else:
                tdSql.error(sql1)
                tdSql.error(sql2)
                tdSql.error(sql3)

        tdSql.query("select elapsed(ts,10s) from (select ts,tbname  from regular_table_1 order by ts  ) where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev);")
        tdSql.checkRows(600)

        tdSql.query("select elapsed(ts,10s) from (select ts ,max(q_int),tbname  from regular_table_1 order by ts  ) where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev);")
        tdSql.checkRows(600)

        # ===============================================inner nest============================================

        # sub table

        tdSql.query("select data from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from sub_table1_1 ); ")
        tdSql.checkData(0,0,9)

        tdSql.query("select data from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from sub_table1_1 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(600)
        tdSql.checkData(0,0,0.1)

        tdSql.query("select * from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 ); ")
        tdSql.checkData(0,7,9)

        tdSql.query("select * from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(600)
        tdSql.checkData(0,0,0.1)

        tdSql.query("select max(data) from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 ); ")
        tdSql.checkData(0,0,9)

        tdSql.query("select max(data) from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(1)
        tdSql.checkData(0,0,0.1)

        tdSql.query("select max(data) from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from sub_empty_2 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(0)

        tdSql.query("select max(data),min(data),avg(data) from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(1)

        tdSql.query("select ceil(data),floor(data),round(data) from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(600)

        tdSql.query("select spread(data) from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(1)
       
        tdSql.query("select diff(data) from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(599)

        tdSql.query("select DERIVATIVE(data ,1s ,1) from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(598)

        tdSql.query("select ceil(data)from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(600)

        tdSql.query("select floor(data)from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(600)

        tdSql.query("select round(data)from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(600)

        tdSql.query("select data*10+2 from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(600)

        tdSql.query("select data*10+2 from (select count(*),avg(q_int) , twa(q_tinyint), irate(q_int),sum(q_double),stddev(q_float),LEASTSQUARES(q_int,0,1), elapsed(ts,10s) data from regular_table_3 \
         where ts>=\"2015-01-01 00:00:00.000\"  and ts < \"2015-01-01 00:10:00.000\" interval(1s) fill(prev)); ")
        tdSql.checkRows(600)

    def query_session_windows(self):
        # bug TD-12344  

        # session not support stable
        # tdSql.error('select elapsed(ts,10s) from stable_1  where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000"  session(ts ,10s) group by tbname,ind order by ts asc ')

        tdSql.query('select elapsed(ts,10s) from sub_table1_1  session(ts,1w) ; ')
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)
        tdSql.query('select elapsed(ts,10s) from sub_table1_1   where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" session(ts,1w) ; ')
        tdSql.checkRows(1)
        tdSql.checkData(0,0,9)

        # new feature  : not support  select ts in outer query.

        # tdSql.query('select elapsed(ts,10s) from  ( select * from sub_table1_1   where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000") session(ts,1w) ; ')
        # tdSql.checkRows(1)
        # tdSql.checkData(0,0,9)

        # tdSql.query('select elapsed(ts,10s) from  ( select ts ,q_int from sub_table1_1   where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000") session(ts,1w) ; ')
        # tdSql.checkRows(1)
        # tdSql.checkData(0,0,9)

        tdSql.error('select elapsed(ts,10s) from sub_table1_1   where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(20s) fill (next) session(ts,1w) ; ')
        
        tdSql.query('select elapsed(ts,10s) from sub_empty_1  where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000"  session(ts,1w) ; ')
        tdSql.checkRows(0)

        # windows state
        # not support stable

        tdSql.error('select elapsed(ts,10s) from stable_1  where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000"  state_window(q_int) group by tbname,ind order by ts asc ')

        tdSql.query('select elapsed(ts,10s) from sub_table1_1  state_window(q_int) ; ')
        tdSql.checkRows(10)
        tdSql.checkData(0,0,0)
        tdSql.query('select elapsed(ts,10s) from sub_table1_1   where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" state_window(q_int) ; ')
        tdSql.checkRows(10)
        tdSql.checkData(0,0,0)

        # tdSql.query('select elapsed(ts,10s) from  ( select * from sub_table1_1   where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000") state_window(q_int) ; ')
        # tdSql.checkRows(10)
        # tdSql.checkData(0,0,0)

        # tdSql.query('select elapsed(ts,10s) from  ( select ts ,q_int from sub_table1_1   where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000") state_window(q_int) ; ')
        # tdSql.checkRows(10)
        # tdSql.checkData(0,0,0)

        tdSql.error('select elapsed(ts,10s) from sub_table1_1   where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000" interval(20s) fill (next) state_window(q_int) ; ')
        
        tdSql.query('select elapsed(ts,10s) from sub_empty_1  where ts>="2015-01-01 00:00:00.000"  and ts < "2015-01-01 00:10:00.000"  state_window(q_int); ')
        tdSql.checkRows(0)

        
    def continuous_query(self):
        tdSql.execute('create table elapsed_t as select elapsed(ts) from sub_table1_1  interval(1m) sliding(30s);')
        tdSql.execute('create table elapsed_tb as select elapsed(ts) from stable_1  interval(1m) sliding(30s) group by tbname;')
        tdSql.error('create table elapsed_tc as select elapsed(ts) from stable_1  interval(10s) sliding(5s) interval(1m) sliding(30s) group by tbname;')

    def run(self):
        tdSql.prepare()
        self.prepare_data()
        self.query_session_windows()
  


    def stop(self):
        tdSql.close()
        tdLog.success("%s successfully executed" % __file__)

tdCases.addWindows(__file__, TDTestCase())
tdCases.addLinux(__file__, TDTestCase())


