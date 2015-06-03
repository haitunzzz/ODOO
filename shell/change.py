import psycopg2
dbname = 'release_0417'
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname=dbname, password='jmf12345')
cr = conn.cursor()

cr.execute("update ir_cron set active=False")
cr.execute("update base_action_rule set active=False")
cr.execute("delete from ir_mail_server")
cr.execute("update email_template set email_to=null, email_cc=null, email_recipients=null, if_sms=False")

conn.commit()
conn.close()
