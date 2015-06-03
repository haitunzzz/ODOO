# -*- coding: utf-8 -*-
from openerp.osv import osv
class purchase_confirm(osv.osv_memory):
    _name = "purchase.confirm"


    def do_confirm(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        active_ids = context.get('active_ids',[])
        context.update({'confirm':1})
        return self.pool.get('purchase.order').wkf_confirm_order(cr, uid, active_ids, context=context)

