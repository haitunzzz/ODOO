#!/usr/bin/env python
#coding: utf8
# 
import time
now = time.strftime('%Y-%m-%d %H:%M:%S')
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='mactrends', password='jmf12345')
cr = conn.cursor()

conn1 = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='release_0918', password='jmf12345')
cr1 = conn1.cursor()

'''
company_id=5
cr.execute("select res_id from ir_property \
                    where company_id = %s \
                    and fields_id=937 \
                    and value_integer > 0"%company_id)
res = cr.fetchall()
a = map(lambda x: x[0] and x[0].split(',')[1], res)
print('---',res, a)
#return [('id','=',map(lambda x: (x and x[0]) and x[0].split(',')[1], res))]
'''
cr.execute("select id from ir_property order by id desc")
cc = cr.fetchall()[0][0] 
cr1.execute("select id,sale_ok from product_template where sale_ok=True")
old = cr1.fetchall()
for id,sale_ok in old:
    cc += 1
    cr.execute("insert into ir_property (id,create_uid,write_uid,create_date,write_date,\
            value_integer,name,type,company_id,fields_id,res_id)\
             values(%s,1,1,%s,%s,\
             1,'sale_ok','boolean',5,937,%s)",
            (cc,now,now,"product.template,%s"%id))
cc += 1
cr.execute("ALTER SEQUENCE ir_property_id_seq RESTART with %s"%cc)
        
conn.commit()
