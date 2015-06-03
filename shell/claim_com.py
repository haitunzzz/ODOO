
import psycopg2
dbname = 'mactrends'
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname=dbname, password='jmf12345')
cr = conn.cursor()

cr.execute("select cc.id,rp.id,cc.company_id,rp.company_id from crm_claim as cc,res_partner as rp where cc.partner_id=rp.id")
ans = cr.fetchall()
for cc_id,rp_id,cc_com,rp_com in ans:
    if rp_com and cc_com!=rp_com:
        cr.execute("update res_partner set company_id=%s where id=%s"%(cc_com,rp_id))
        print cc_id,rp_id,cc_com,rp_com
        conn.commit()

conn.close()
