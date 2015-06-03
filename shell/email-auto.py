import psycopg2
dbname = 'mactrends'
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname=dbname, password='jmf12345')
cr = conn.cursor()

date = '2015-04-12'
uid = 1

'''
cr.execute("INSERT INTO auto_email_so(create_uid,create_date, write_date, write_uid,template_so,name,company_id, template_sq ,if_con_notify ,if_sq_notify,if_prepay_notify, template_prepay) VALUES (%s,'%s','%s',%s,47,'Default - NZ',5,41,True,True,True,44);"%(uid,date,date,uid))
cr.execute("INSERT INTO auto_email_so(create_uid,create_date, write_date, write_uid,template_so,name,company_id, template_sq ,if_con_notify ,if_sq_notify,if_prepay_notify, template_prepay) VALUES (%s,'%s','%s',%s,48,'Default - AU',4,42,True,True,True,46);"%(uid,date,date,uid))
cr.execute("INSERT INTO auto_email_so(create_uid,create_date, write_date, write_uid,template_so,name,company_id, template_sq ,if_con_notify ,if_sq_notify,if_prepay_notify, template_prepay) VALUES (%s,'%s','%s',%s,49,'Default - UK',7,43,True,True,True,45);"%(uid,date,date,uid))
'''


cr.execute("select id,company_id,if_con_notify ,if_sq_notify,if_prepay_notify from sale_order")
ans = cr.fetchall()
auto = []
sale_tem = {}
for id,company_id,if_con_notify ,if_sq_notify,if_prepay_notify in ans:
    #if all false auto_email = null
    if not if_con_notify and not if_sq_notify and not if_prepay_notify:
        continue
    idd = str(company_id) + str(if_con_notify or False) + ',' + str(if_sq_notify or False) + ',' + str(if_prepay_notify or False)
    if idd not in auto:
        auto.append(idd)
        print id,company_id,idd
        if company_id == 4:
            auto_name = 'AU: sq-' + str(if_sq_notify or False) + ',con-' +str(if_con_notify or False) + ',pay-' +str(if_prepay_notify or False)
            cr.execute("INSERT INTO auto_email_so(create_uid,create_date, write_date, write_uid,template_so,name,company_id, template_sq ,if_con_notify ,if_sq_notify,if_prepay_notify, template_prepay) VALUES (%s,'%s','%s',%s,48,'%s',null,42,%s,%s,%s,46);"%(uid,date,date,uid,auto_name,if_con_notify or False,if_sq_notify or False,if_prepay_notify or False))
        if company_id == 5:
            auto_name = 'NZ: sq-' + str(if_sq_notify or False) + ',con-' +str(if_con_notify or False) + ',pay-' +str(if_prepay_notify or False)
            cr.execute("INSERT INTO auto_email_so(create_uid,create_date, write_date, write_uid,template_so,name,company_id, template_sq ,if_con_notify ,if_sq_notify,if_prepay_notify, template_prepay) VALUES (%s,'%s','%s',%s,47,'%s',null,41,%s,%s,%s,44);"%(uid,date,date,uid,auto_name,if_con_notify or False,if_sq_notify or False,if_prepay_notify or False))
        if company_id == 7:
            auto_name = 'UK: sq-' + str(if_sq_notify or False) + ',con-' +str(if_con_notify or False) + ',pay-' +str(if_prepay_notify or False)
            cr.execute("INSERT INTO auto_email_so(create_uid,create_date, write_date, write_uid,template_so,name,company_id, template_sq ,if_con_notify ,if_sq_notify,if_prepay_notify, template_prepay) VALUES (%s,'%s','%s',%s,49,'%s',null,43,%s,%s,%s,45);"%(uid,date,date,uid,auto_name,if_con_notify or False,if_sq_notify or False,if_prepay_notify or False))

        #conn.commit()
            '''
               id    | create_uid |        create_date         |         write_date         | write_uid | value_text | value_float |    name    | value_integer |   type   | company_id | fields_id | value_datetime | value_binary | value_reference |      res_id
               ---------+------------+----------------------------+----------------------------+-----------+------------+-------------+------------+---------------+----------+------------+-----------+----------------+--------------+-----------------+------------------
                1100410 |          1 | 2015-02-27 06:56:08.857853 | 2015-02-27 06:56:08.857853 |         1 |            |             | auto_email |               | many2one |          8 |      7462 |                |              | auto.email.so,3 | sale.order,25041
            '''
    if company_id == 4:
        auto_name = 'AU: sq-' + str(if_sq_notify or False) + ',con-' +str(if_con_notify or False) + ',pay-' +str(if_prepay_notify or False)
        cr.execute("select id from auto_email_so where name = '%s'"%auto_name)
        ids = cr.fetchall()
        #print ids
        cr.execute("update sale_order set auto_email = %s where id = %s"%(ids[0][0],id))
    if company_id == 5:
        auto_name = 'NZ: sq-' + str(if_sq_notify or False) + ',con-' +str(if_con_notify or False) + ',pay-' +str(if_prepay_notify or False)
        cr.execute("select id from auto_email_so where name = '%s'"%auto_name)
        ids = cr.fetchall()
        cr.execute("update sale_order set auto_email = %s where id = %s"%(ids[0][0],id))
    if company_id == 7:
        auto_name = 'UK: sq-' + str(if_sq_notify or False) + ',con-' +str(if_con_notify or False) + ',pay-' +str(if_prepay_notify or False)
        cr.execute("select id from auto_email_so where name = '%s'"%auto_name)
        ids = cr.fetchall()
        cr.execute("update sale_order set auto_email = %s where id = %s"%(ids[0][0],id))




conn.commit()
conn.close()
