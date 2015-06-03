import psycopg2
dbname = 'mactrends'
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname=dbname, password='jmf12345')
cr = conn.cursor()

cr.execute("select id,name,state,partner_id from sale_order where state not in ('done','cancel','draft')")
ans = cr.fetchall()

for id,name,state,partner_id in ans:
    cr.execute("select distinct state from stock_picking where sale_id=%s"%id)
    sp_state = [i and i[0] for i in cr.fetchall()]
    cr.execute("select distinct state from account_invoice where origin='%s'"%name)
    inv_state = [i and i[0] for i in cr.fetchall()]
    #print sp_state,inv_state
    if name.startswith('2') and len(sp_state) == 1 and sp_state[0] == 'done' and len(inv_state) == 1 and inv_state[0] == 'open' :
        print id,name,state,partner_id
        cr.execute("select id,partner_id from account_move where ref='%s' or name='%s'"%(name,name))
        am = cr.fetchall()
        for move_id,move_partner_id in am:
            print 'm--- ',move_id,move_partner_id
            if partner_id!=move_partner_id:
                cr.execute("update account_move set partner_id=%s where id=%s"%( partner_id,move_id))
                cr.execute("update account_move_line set partner_id=%s where move_id=%s"%( partner_id,move_id))
                conn.commit()


conn.close()
