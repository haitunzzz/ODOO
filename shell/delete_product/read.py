#!/usr/bin/env python
#coding: utf8
# 
import time
now = time.strftime('%Y-%m-%d %H:%M:%S')
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='mactrends', password='jmf12345')
cr = conn.cursor()

e = []
n = []
'''
for line in open(r'drepeat','r').readlines():
    if not line:
        continue
    item = line.strip().split('Deleted')
    item = filter(lambda x:x,item)
    code = item[0].strip()
    pname = item[1].strip()
    cr.execute("select id from product_product where default_code='%s' and name_template='%s'"%(code,pname))
    new = cr.fetchall()
    print(code,pname,new)
    try:
        if new and new[0] and new[0][0]:
            new_id = new[0][0]
            #e.append(code)
            cr.execute("delete from product_product where id=%s"%new_id)
            cr.execute("delete from product_template where id=%s"%new_id)
            conn.commit()
        #else:
        #    print('----------',code,pname)
        #    n.append(code)
    except Exception as e:
        print(e)
        print(code,pname)
        n.append(code)
        conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='mactrends', password='jmf12345')
        cr = conn.cursor()
for line in open(r'modify.csv','r').readlines():
    if not line:
        continue
    item = line.strip().split(' ')
    item = filter(lambda x:x,item)
    print(item)
    code = item[0]
    pallet_length = item[1]
    volume_per_pallet = item[2]
    cr.execute("select id from product_product where default_code='%s'"%code)
    new = cr.fetchall()
    if new and new[0] and new[0][0]:
        new_id = new[0][0]
        print(new_id)
        e.append(new_id)
        cr.execute("update product_product set pallet_length=%s, volume_per_pallet=%s where id=%s"%(pallet_length,volume_per_pallet,new_id))
    else:
        print(code)
        n.append(code)
        continue
'''
for line in open(r'deleted.csv','r').readlines():
    if not line:
        continue
    code = line.strip()
    #print(code)
    cr.execute("select id from product_product where default_code='%s'"%code)
    new = cr.fetchall()
    if new and new[0] and new[0][0]:
        new_id = new[0][0]
        print(new_id)
    else:
        #print(new)
        n.append(code)
        continue
    try:
        cr.execute("delete from product_product where id=%s"%new_id)
        cr.execute("delete from product_template where id=%s"%new_id)
        conn.commit()
    except:
        e.append(new_id)
        conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='mactrends', password='jmf12345')
        cr = conn.cursor()
#print(e)
print(n)
#conn.commit()
conn.close()
