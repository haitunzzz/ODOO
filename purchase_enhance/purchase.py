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

import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, orm
import logging
_logger = logging.getLogger(__name__)
from openerp.tools.translate import _
from openerp import netsvc


class purchase_order(osv.osv):
    _inherit = "purchase.order"
    
    def _pallet_length(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for po in self.browse(cursor, user, ids, context=context):
            res[po.id] = sum([line.product_id.pallet_length for line in po.order_line])
        return res

    def _date_delivery(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for po in self.browse(cursor, user, ids, context=context):
            for picking in po.picking_ids:
                if picking.type == 'in' and picking.state == 'done':
                    res[po.id] = picking.date_done
        return res

    _columns = {
        'if_notification': fields.boolean('Notification', help="Notification"),
        'related_so': fields.char('Related SO', size=64, readonly=True),
        'pallet_length':fields.function(
            _pallet_length,
            string='Total Pallet Length',
            type='float',
            digits=(16,1),
            ),
        #Issue228
        'date_delivery': fields.function(
            _date_delivery,
            string='Actual Delivery Date', 
            type='datetime', 
            readonly=True),
        'cost_estimated': fields.char('Estimated Cost', size=64),
        'cost_actual': fields.char('Actual Cost', size=64),
        'cost_damage': fields.char('Delivery Damage Cost', size=64),
        #Issue253
        'container': fields.char('Container #', size=64),
        #Issue282
        'warn': fields.text('Warn'),
    }

    _defaults = {
            'if_notification': False,
            }

    #Issue282
    def action_send_warnemail(self, cr, uid, ids, context=None):
        """
        Send to QC  Manager
        """
        template_pool = self.pool.get('email.template')
        mail_pool     = self.pool.get('mail.mail')
        attach_pool   = self.pool.get('ir.attachment')
        stock_pool    = self.pool.get('stock.picking')
        template = self.pool.get('ir.model.data').get_object(cr, uid, 'purchase_enhance', 'email_template_purchase_warn')
        for order in self.browse(cr, uid, ids):
            email_to = []
            for line in order.order_line:
                if line.product_id.qc_manager and line.product_id.qc_manager.email:
                    email_to.append(line.product_id.qc_manager.email)
            if email_to:
                template_pool.write(cr, uid, [template.id], {'email_to':','.join(list(set(email_to)))})
                template_pool.send_mail(cr, uid, template.id, order.id, force_send=False)
        return True

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        '''
            context.update({
                'active_model': self._name,
                'active_ids': ids,
                'active_id': len(ids) and ids[0] or False
                })
            '''
        for order in self.browse(cr, uid, ids, context=context):
            if not order.minimum_planned_date:
                raise osv.except_osv('Invalid Action!', 'NO Expected Date! Please check it!')
            if not order.if_notification:
                for line in order.order_line:
                    #issue 63 (ps:product_get_cost_field standard_price->cost_price)
                    if (not line.product_id.standard_price) and (not line.product_id.is_kit):
                        #_logger.warning("You have products with no cost!")
                        self.write(cr, uid, [order.id], {'if_notification':True})
                        raise osv.except_osv(_('Warning!'),_("You have product (%s) with no cost!"%line.product_id.name_template))
                        '''
                        return {
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'purchase.confirm',
                            'type': 'ir.actions.act_window',
                            'target': 'new',
                            'context': context,
                            'nodestroy': True,
                            }
                        '''
            if order.company_id.id in (4,5,7):
                #Issue119
                if order.company_id.id == 5:
                    #send freight@mactrends.com
                    ir_model_data = self.pool.get('ir.model.data')
                    try:
                        template_id = ir_model_data.get_object_reference(cr, uid, 'purchase_enhance','email_template_purchase_confirm')[1]
                    except ValueError:
                        template_id = False
                    if template_id:
                        template_obj = self.pool.get('email.template')
                        template_obj.write(cr, 1, [template_id], {'email_to':'freight@mactrends.com'})
                        mail_id = template_obj.send_mail(cr, uid, template_id, order.id, True)

                self.pool.get('res.users').write(cr, 1, 86, {'company_id':8}, context=context)
                sale_obj = self.pool.get('sale.order')
                partner = order.company_id.partner_id
                currency_id = order.pricelist_id.currency_id.id
                pricelist = self.pool.get('product.pricelist').search(cr, 86, [('currency_id','=',currency_id)])
                if pricelist and pricelist[0]:
                    pricelist_id = pricelist[0]
                else:
                    admin_hk = self.pool.get('res.users').browse(cr, 86, 86, context=context)
                    pricelist_id = admin_hk.partner_id.property_product_pricelist and admin_hk.partner_id.property_product_pricelist.id or 9

                sname = self.pool.get('ir.sequence').get(cr, uid, 'sale.order', context={'force_company':8})
                sale = {
                        'name': sname,
                        'origin': order.name,
                        'client_order_ref': order.name,
                        #'shop_id': ,
                        #'date_order': ,
                        'partner_id': partner.id,
                        'partner_invoice_id': partner.id,
                        'partner_shipping_id': partner.id,
                        #'order_policy': 'manual',
                        'pricelist_id': pricelist_id,
                        #'invoice_quantity': 'order',
                        'related_po': order.id,
                        'estimated_delivery_date': order.minimum_planned_date,
                        'company_id': 8,
                        }
                order_id = sale_obj.create(cr, 86, sale, context=context)
                self.write(cr, uid, order.id, {'related_so':order_id, 'origin':order.origin and order.origin + ':' + sname or sname}, context=context)
                for line in order.order_line:
                    line_vals = {
                            'order_id': order_id,
                            'name': line.product_id.name,
                            'product_id': line.product_id.id,
                            'price_unit': line.price_unit,
                           # 'type': ,
                            'product_uom_qty': line.product_qty,
                            'product_uom': line.product_uom.id,
                            'company_id': 8,
                            }
                    self.pool.get('sale.order.line').create(cr, 86, line_vals, context=context)
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_validate(86, 'sale.order', order_id, 'order_confirm', cr)
                wf_service.trg_validate(86, 'sale.order', order_id, 'manual_invoice', cr)
        return super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)


purchase_order()


class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"

    def _get_uom_id(self, cr, uid, *args):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False

    def _standard_price(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = line.product_id.standard_price
        return res

    def _total_margin(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = line.product_qty * line.target_margin
        return res

    _columns = {
        #'standard_price': fields.related('product_id','standard_price',type='float',relation='product.product', string='Cost Price', readonly=True),
        'standard_price':fields.function(
            _standard_price,
            string='Cost Price',
            type='float',
            digits=(16,2),
            ), #Issue 173
        'volume_per_pallet': fields.related('product_id','volume_per_pallet',type='integer',relation='product.product', string='Pallet Quantity', readonly=True),
        'product_uom': fields.related('product_id', 'uom_id', string='Unit of Measure', type='many2one', relation='product.uom', store=True, readonly=True),
        'target_selling': fields.char('Target Selling Price'), #Issue322
        'target_margin': fields.char('Target Margin'), #Issue322
        'total_margin':fields.function(
            _total_margin,
            string='Total Margin',
            type='float'), #Issue322
    }

    _defaults = {
        'product_uom' : _get_uom_id,
        }

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}

        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned, name=name, price_unit=price_unit, context=context)

        if not product_id:
            return res

        product_product = self.pool.get('product.product')
        product = product_product.browse(cr, uid, product_id, context=context)
        if product.purchase_price_unit:
            res['value'].update({'price_unit':product.purchase_price_unit})
        #Issue 123
        if (qty and qty == product.volume_per_pallet) or not qty:
            res['value'].update({'product_qty':product.volume_per_pallet})

        return res

purchase_order_line()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

