#!/usr/bin/env python
#coding: utf8
# by zhangxue
# 
from openerp.osv import fields, osv
import time

class res_partner(osv.osv):
    _inherit = "res.partner"
    
    _columns = {
        'invoice_user_id': fields.many2one('res.users', 'Invoice Responsible', help='The internal user that is in charge of confirm invoice'),
        #'if_autopay': fields.boolean('Is Auto Payment'),
            }

