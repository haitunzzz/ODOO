#!/usr/bin/env python
#coding: utf8

import json 
import requests
import psycopg2
dbname = 'mactrends'
conn = psycopg2.connect(host='127.0.0.1', port=4432, user='erp', dbname=dbname, password='jmf12345')
cr = conn.cursor()

move_lines = []
for line in open(r'vg_stock.csv','r').readlines():
        word = line.strip().split(',')
        if not word[0]:
            continue
        code =  word[0]
        name =  word[1]
        qty =  word[2]
        cr.execute("select id from product_product where default_code='%s'"%code)
        p_id = cr.fetchall()[0][0]
        move_lines.append([0, False,{
                    'company_id': 8,
                    #'cubic_qty': 0,
                    #'cubic_volume': 0,
                    #'cubic_weight': 0,
                    'date': "2015-02-25 08:00:00",
                    'date_expected': "2015-02-25 08:00:00",
                    #'item_sscc': false,
                    #'line_comod': false,
                    #'line_unit_commod_items_count': 0,
                    'location_dest_id': 101,
                    'location_id': 6,
                    'name': "[%s] %s"%(code,name),
                    #'no_of_items': 0,
                    #'origin': false,
                    'partner_id': 37778,
                    #'picking_id': false,
                    #'prodlot_id': false,
                    'product_id': p_id,
                    'product_qty': qty,
                    'product_uom': 42,
                    #'product_uos': false,
                    'product_uos_qty': qty,
                    #'tracking_id': false,
                    'type': "in",
            }])
#print move_lines



url = 'http://:6162'
a = {'jsonrpc':'2.0','method':'call','params':{'db':dbname,'login':'','password':'','base_location':url},'id':'r7'}
r = requests.post(url+'/web/session/authenticate', data=json.dumps(a))
auinfo = json.loads(r.text)
headers = r.headers

print (1,r.text)
rheaders = {
        'Cookie': headers['set-cookie'],
        }


prjson = {
        "jsonrpc":"2.0",
        "method":"call",
        "params":{
            "model":"stock.picking.in",
            "method":"create",
            "args":[{
                #'auto_picking': false,
                'company_id': 8,
                'date': "2015-02-25 08:00:00",
                #'date_done': false,
                #'invoice_state': "none",
                #'message_follower_ids': false,
                #'message_ids': false,
                'move_lines': move_lines,
                'move_type': "direct",
                #'note': false,
                'origin': 'test',
                'partner_id': 37778,
                #'purchase_id': false,
                'stock_journal_id': 60,
                'type': "in",
                'warehouse_id': 14,
                }],
            "kwargs":{"context":{"lang":"en_US","tz":"NZ","uid":86,
                'contact_display': "partner_address",
                'default_type': "in",
                }},
            "session_id":auinfo[u'result'][u'session_id'],
            "context":{"lang":"en_US","tz":"NZ","uid":86},
            },
        "id":"r7"
        }

url2 = url+'/web/dataset/call_kw'
r = requests.post(url2, data=json.dumps(prjson), headers=rheaders)
#rres = json.loads(r.text)

print (2,r.text)

