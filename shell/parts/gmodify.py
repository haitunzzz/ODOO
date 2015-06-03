#!/usr/bin/env python
#coding: utf8
# 
import time
now = time.strftime('%Y-%m-%d %H:%M:%S')
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='mactrends', password='jmf12345')
cr = conn.cursor()
res = {}
for line in open(r'gnew.csv','r').readlines():
        word = line.strip().split(' ')
        word = filter(lambda x:x, word)
        if not word[0]:
            continue
        code = word[0].strip()
        p_name = line.strip().split(code)[-1].strip()
        print(code,p_name)
        cr.execute("update product_template set name=%s where id=(select id from product_product where default_code=%s and id>16878)",(p_name,code))
        conn.commit()
