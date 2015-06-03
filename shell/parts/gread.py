#!/usr/bin/env python
#coding: utf8
# 
import time
now = time.strftime('%Y-%m-%d %H:%M:%S')
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='mactrends', password='jmf12345')
cr = conn.cursor()
cr.execute("select id from product_template order by id desc")
new_id = cr.fetchall()[0][0]
res = {}
for line in open(r'gnew.csv','r').readlines():
        word = line.strip().split(' ')
        word = filter(lambda x:x, word)
        if not word[0]:
            continue
        code = word[0].strip()
        p_name = word[1].strip()
        new_id += 1
        print(new_id,code,p_name)
        cr.execute('insert into product_template(id,create_uid,write_uid,create_date,write_date,standard_price,uom_id,cost_method,categ_id,name,uom_po_id,type,supply_method,procure_method, company_id,sale_ok,purchase_ok) values (%s,1,1,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, 1,True,True)',(new_id,now,now,0,42,"standard",14,p_name,42,"product","buy","make_to_stock"))
        cr.execute('insert into product_product(id,create_uid,write_uid,create_date,write_date,product_tmpl_id,valuation,purchase_line_warn,sale_line_warn, default_code,name_template,active,purchase_requisition,is_parts) values (%s,1,1,%s,%s,%s,%s,%s,%s, %s,%s,True,True,False)',(new_id,now,now,new_id,"real_time","no-message","no-message", code,p_name))

new_id += 1
cr.execute("ALTER SEQUENCE product_product_id_seq RESTART with %s"%new_id)
cr.execute("ALTER SEQUENCE product_template_id_seq RESTART with %s"%new_id)
        
conn.commit()
