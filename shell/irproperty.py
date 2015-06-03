#!/usr/bin/env python
#coding: utf8
# 
import time
now = time.strftime('%Y-%m-%d %H:%M:%S')
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='mactrends', password='jmf12345')
cr = conn.cursor()

conn1 = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='release_0825', password='jmf12345')
cr1 = conn1.cursor()

cr.execute("select id from ir_property order by id desc")
cc = cr.fetchall()[0][0] 
cr1.execute("select id,purchase_price_unit from product_product where purchase_price_unit is not null and purchase_price_unit>0")
old = cr1.fetchall()
for id,price in old:
    cc += 1
    cr.execute("insert into ir_property (id,create_uid,write_uid,create_date,write_date,\
            value_float,name,type,company_id,fields_id,res_id)\
             values(%s,1,1,%s,%s,\
             %s,'purchase_price_unit','float',5,7243,%s)",
            (cc,now,now,price,"product.template,%s"%id))
cc += 1
cr.execute("ALTER SEQUENCE ir_property_id_seq RESTART with %s"%cc)
        
conn.commit()
