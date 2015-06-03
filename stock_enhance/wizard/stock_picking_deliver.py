# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import logging
_logger = logging.getLogger(__name__)

class stock_picking_deliver(osv.osv_memory):
    _name = "stock.picking.deliver"
    _description = "Deliver Stock Pickings"
    _columns = {
    }

    def deliver_pickings(self, cr, uid, ids, context=None):
        obj_picking = self.pool.get('stock.picking')
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        ids_picking = []
        ids_picking_zx = []
        model = 'stock.picking' #Issue297
        data = obj_picking.browse(cr, uid, context['active_ids'], context=context)
        for picking in data:
            #must be paid before delivered ----zhangxue
            if picking.origin:
                domain = [('name', '=', picking.origin)]
                sale_obj = self.pool.get('sale.order')
                sale_ids = sale_obj.search(cr, uid, domain, context=context)
                for sale in sale_obj.browse(cr, uid, sale_ids, context):
                    #if not sale.invoiced:
                    if abs(sale.amount_total - sale.amount_paid) > 0.001: #Issue 200
                        ids_picking_zx.append(picking.id)
                        #raise osv.except_osv('Warning', 'The SO %s must be\
                        #      fully paid before you can process this delivery.' % picking.origin)
            if picking.state == 'assigned' and (picking.id not in ids_picking_zx):
                ids_picking.append(picking.id)

        if not ids_picking:
            raise osv.except_osv(_('Warning!'), _('Selected Pickings does not in Ready to Transfer state or not paid!'))

        if picking.type != 'internal':
            model += '.' + picking.type

        #obj_picking.action_done(cr, uid, ids_picking, context=context)
        for picking_id in ids_picking:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_done', cr)

        if ids_picking_zx:
            return {
                    'domain': "[('id','in',["+','.join(map(str, ids_picking_zx))+"])]",
                    'type': 'ir.actions.act_window',
                    'name': _('Not Paid'),
                    'view_type': 'form',
                    'view_mode': 'tree',
                    'res_model': model,
                    'target': 'current',
                    'nodestroy': True,
                    }

        return {'type': 'ir.actions.act_window_close',
                "flags": {'1':ids_picking_zx,
                            '2':ids_picking,
                            '3':model}}

stock_picking_deliver()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

