import psycopg2
dbname = 'release_0202'
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname=dbname, password='jmf12345')
cr = conn.cursor()

dbname1 = 'mactrends'
conn1 = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname=dbname1, password='jmf12345')
cr1 = conn1.cursor()

cr.execute("select id,refund_reason from account_invoice where refund_reason is not null")
ans = cr.fetchall()
for id,refund_reason in ans:
    cc = 0
    cr1.execute("select id,name from account_refund_reason")
    refs = cr1.fetchall()
    for r_id,r_name in refs:
        if r_name == refund_reason:
            print id,refund_reason
            cr1.execute("update account_invoice set refund_reason=%s where id=%s"%(r_id,id))
            conn1.commit()

            cc = 1
    if cc == 0:
        cr1.execute("update account_invoice set refund_reason=3 where id = %s"%id)
        conn1.commit()
        print '----',id,refund_reason
            #print '-------',r_id,r_name

conn1.close()
conn.close()
