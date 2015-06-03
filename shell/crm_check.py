import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname='mactrends', password='jmf12345')
cr = conn.cursor()
cr.execute("select id,number,partner_id,company_id,(select company_id from res_partner where id=partner_id) from crm_claim")
for id,name,partner_id,company_id,pcompany_id in cr.fetchall():
    if company_id != pcompany_id and pcompany_id:
        print(id,name,partner_id,company_id,pcompany_id)

