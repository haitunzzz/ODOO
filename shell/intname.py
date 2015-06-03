import psycopg2
dbname = 'mactrends'
#dbname = "release_0407"
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname=dbname, password='jmf12345')
cr = conn.cursor()

#cr.execute("select id,company_id from stock_picking where type = 'internal' and name is null order by id")

cr.execute("select name,id from res_company")
ans = cr.fetchall()
for id,company_id in ans:
    cr.execute("select prefix,number_next,id from ir_sequence where company_id=%s and name like %s",(company_id,"%Picking INT"))
    seq = cr.fetchall()
    for prefix,number_next,irid in seq:
        cr.execute("select last_value from ir_sequence_%s"%str(irid).zfill(3))
        number_next = cr.fetchall()[0][0] +1
        name_num = str(number_next).zfill(4)
        print  prefix, irid, number_next, prefix[:4]+"150"+name_num
#        cr.execute("update stock_picking set name = %s where id=%s",(prefix[:4]+"150"+name_num,id))
        cr.execute("update ir_sequence set number_next = %s where id=%s",(number_next,irid))
        cr.execute("ALTER SEQUENCE ir_sequence_%s RESTART %s"%(str(irid).zfill(3), number_next))

conn.commit()
conn.close()
