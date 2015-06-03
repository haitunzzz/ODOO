#!/usr/bin/env python
#coding: utf8
# 
import time
now = time.strftime('%Y-%m-%d %H:%M:%S')
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='mactrends', password='jmf12345')
cr = conn.cursor()
cr.execute("select count(*),default_code from product_product group by default_code order by count desc")
cc = []
for c,code in cr.fetchall():
    if c > 1:
        cc.append(code)
print(cc)
