#!/usr/bin/env python
#coding: utf8
# 
import time
now = time.strftime('%Y-%m-%d %H:%M:%S')
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='mactrends', password='jmf12345')
cr = conn.cursor()
res = {}
template_id = 67
for line in open(r'pro_email.txt','r').readlines():
    code = line.strip()
    if code:
        print template_id,code
        cr.execute("select id from product_product where default_code = '%s'"%code)
        id = cr.fetchall()[0][0]
        print id
        cr.execute("update product_product set etemplate_id = %s where id = %s"%(template_id, id))
    else:
        template_id += 1

        
conn.commit()
