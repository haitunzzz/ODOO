# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010-2014 Elico Corp. All Rights Reserved.
#    Alex Duan <alex.duan@elico-corp.com>
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

from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
import webbrowser
    
import logging
_logger = logging.getLogger(__name__)
import re
from datetime import datetime
    
class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _has_prepaid(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            payment_ids = [move.move_id.id for move in sale.payment_ids]
            res[sale.id] = bool(payment_ids)
        return res

    def _tradevine_url(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = ""
            if sale.tradevine_list_id:
                res[sale.id] = "http://www.trademe.co.nz/Browse/Listing.aspx?id=%s"%sale.tradevine_list_id
        return res

    def _ebay_url(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = ""
            if sale.client_order_ref:
                Ebay = re.search('Ebay\d*', sale.client_order_ref)
                if Ebay is not None:
                    Ebay = Ebay.group().split('Ebay')[-1]
                    if sale.company_id.id == 4:
                        res[sale.id] = 'http://www.ebay.com.au/itm/' + Ebay
                    elif sale.company_id.id == 7:
                        res[sale.id] = 'http://www.ebay.com.uk/itm/' + Ebay
                    elif sale.company_id.id == 8 and sale.ebay_config_id and sale.ebay_config_id.site_id and sale.ebay_config_id.site_id.url:  #VG
                        res[sale.id] = 'http://'+ sale.ebay_config_id.site_id.url + '/itm/' + Ebay
        return res


    def _test_delivered_do(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = bool(sale.picking_ids)
            for picking in sale.picking_ids:
                if picking.type == 'out' and picking.state != 'done':
                    res[sale.id] = False
                    break
        return res

    def _test_delivered_int(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = bool(sale.picking_ids)
            for picking in sale.picking_ids:
                if picking.type == 'internal' and picking.state != 'done':
                    res[sale.id] = False
                    break
        return res

    def _date_done_int(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            for picking in sale.picking_ids:
                if picking.type == 'internal' and picking.state == 'done':
                    res[sale.id] = picking.date_done
                    break
        return res

    def _carrier_id(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            for picking in sale.picking_ids:
                if picking.type == 'out' and picking.state == 'done':
                    res[sale.id] = picking.carrier_id.id
                    break
        return res

    def _carrier_tracking_ref(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            for picking in sale.picking_ids:
                if picking.type == 'out' and picking.state == 'done':
                    res[sale.id] = picking.carrier_tracking_ref
                    break
        return res

    def _number_of_packages(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = 0
            for picking in sale.picking_ids:
                if picking.type == 'out' and picking.state == 'done':
                    res[sale.id] = picking.number_of_packages
                    break
        return res

    def _has_refund(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = sum([ inv.type == 'out_refund' and inv.amount_total - inv.residual or 0 for inv in sale.invoice_ids])
        return res

    def _unfull_refund(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = sale.amount_total - sale.refund
        return res

    def _get_invoices(self, cr, uid, ids, context=None):
        # direct access to the m2m table is the less convoluted way to achieve this (and is ok ACL-wise)
        cr.execute("select DISTINCT order_id from sale_order_invoice_rel where invoice_id = ANY(%s)", (list(ids),))
        return [i[0] for i in cr.fetchall()]

    def _color(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = 0
            if not sale.is_preorder and sale.residual > 0.001:
                res[sale.id] = (datetime.utcnow() - datetime.strptime(sale.create_date, '%Y-%m-%d %H:%M:%S')).days
        return res

    _columns = {
        'is_preorder': fields.boolean('Is Preorder', help="If prepay order"),
        'if_sq_notify': fields.boolean('Email SQ Notification', help="Send SQ Notification Auto"),
        'if_prepay_notify': fields.boolean('Email Prepay Notification', help="Send Prepat Notification Auto"),
        'if_con_notify': fields.boolean('Email SO Confirmation', help="Send Confirmation Notification Auto"),
        'if_validated': fields.boolean('Validated Quotations', help="Validated Quotations"),
        'has_prepaid': fields.function(
            _has_prepaid,
            string='Has been Prepaid',
            type='boolean',
            store=True
            ),
        'shipping_method': fields.selection((
                ('collection','Collection'), 
                ('post','Post'), 
                ('courier','Courier'), 
                ('free','Free Shipping'), 
                ('transport','Own Transport'),
                ('freight','Freight')),'Shipping Method'),
        'tradevine_list_id': fields.char('ExternalListingID', size=64, readonly=True), #byzhangxue
        'tradevine_list_url': fields.function(
            _tradevine_url,
            string='Tradevine Url',
            type='char',
            size=64,
            readonly=True
            ),
        'ebay_url': fields.function(
            _ebay_url,
            string='Ebay Url',
            type='char',
            size=64,
            readonly=True
            ),
        'shipped_do': fields.function(
            _test_delivered_do,
            string = 'Delivered DO', 
            readonly=True, 
            type='boolean'),
        'shipped_int': fields.function(
            _test_delivered_int,
            string = 'Delivered INT', 
            readonly=True, 
            type='boolean'),
        'date_done_int': fields.function(
            _date_done_int,
            string = 'INT Date of Transfer', 
            type='datetime',
            readonly=True), 
        'carrier_id': fields.function(
            _carrier_id,
            string = 'Carrier', 
            type='many2one',
            relation='delivery.carrier',
            readonly=True), 
        'carrier_tracking_ref': fields.function(
            _carrier_tracking_ref,
            string = 'Carrier Tracking Ref', 
            type='char',
            size=32,
            readonly=True), 
        'number_of_packages': fields.function(
            _number_of_packages,
            string = 'Number of Packages', 
            type='integer',
            readonly=True), 
        'is_createpq': fields.boolean('Create Purchase Quotation'),
        'related_po': fields.char('Related PO', size=64, readonly=True),
        'refund': fields.function(
            _has_refund,
            string='Refunded',
            type='float',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['payment_ids','invoice_ids'], 10),
                'account.invoice': (_get_invoices, ['amount_total', 'residual'], 10), #Issue166
            },
            ),
        'create_date': fields.datetime('Creation Date', readonly=True),
        'color': fields.function(
            _color,
            string='Payment Days',
            type='integer',
            #store=True
            ), #Issue 204
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('obsoleted', 'Obsoleted'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the quotation or sales order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the sales order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),#Issue250
        'unfullrefund': fields.function(
            _unfull_refund,
            string='unFullRefunded',
            type='float',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['payment_ids','invoice_ids'], 10),
                'account.invoice': (_get_invoices, ['amount_total', 'residual'], 10), #Issue166
            },), #Issue166
        'claim_type': fields.selection((
                ('freight','Freight Claim'),
                ('warranty','Warranty Claim')),'Is Claim Order'), #Issue288
        'if_inner_partner': fields.boolean('Is Inter-company Sales'), #Issue292
    }
    """
        'shipped': fields.function(
            _test_delivered,
            string = 'Delivered', 
            readonly=True, 
            type='boolean',
            help="It indicates that the sales order has been delivered. This field is updated only after the scheduler(s) have been launched."),
        """

    _defaults = {
            'if_sq_notify': True,
            'if_prepay_notify': True,
            'if_con_notify': True,
            'if_validated': False,
            }

    def create(self, cr, uid, vals, context=None):
        sale = super(sale_order, self).create(cr, uid, vals, context=context)
        sale_obj = self.browse(cr, uid, sale)
        #Issue292
        if sale_obj.partner_id:
            cr.execute("select partner_id from res_company")
            inner_partners = cr.fetchall()
            if inner_partners and sale_obj.partner_id.id in [p[0] for p in inner_partners]:
                self.write(cr, uid, [sale_obj.id], {'if_inner_partner':True})
        return sale

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = super(sale_order, self).write(cr, uid, ids, vals, context=context)
        if 'note' in vals and ((context and not context.get('from stock')) or not context):
            for order in self.browse(cr, uid, ids):
                for picking in order.picking_ids:
                    picking.write({'note':vals['note']})
        return res

    def action_button_validate(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'if_validated': True}, context=context)

    def action_button_unvalidate(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'if_validated':False}, context=context)

    def _prepare_order_picking(self, cr, uid, order, context=None):
        picking = super(sale_order, self)._prepare_order_picking(cr, uid, order, context=context)
        picking.update({'note':order.note})
        return picking

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=None, date_invoice = False, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            if not order.amount_total:
                self.write(cr, uid, [order.id], {'invoiced':True ,'state':'progress'})
                res = 0
            else:
                res = super(sale_order, self).action_invoice_create(cr, uid, [order.id], grouped=grouped, states=states, date_invoice = date_invoice, context=context)
        return res

    def action_ship_end(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_ship_end(cr, uid, ids, context=context)
        for order in self.browse(cr, uid, ids, context=context):
            #zhangxue
            if not order.amount_total and order.invoiced:
                self.write(cr, uid, [order.id], {'state': 'done'})
        return res

    # plugin_tradevine by zhangxue issue 98
    def get_so_values(self, cr, uid, order, customer_id, context=None):
        so_vals = super(sale_order, self).get_so_values(cr, uid, order, customer_id, context=context)
        if 'ExternalListingID' in order:
            so_vals.update({'tradevine_list_id': order['ExternalListingID']}) #byzhangxue
        return so_vals
    
    #Issue244
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        result = super(sale_order, self).search(cr, uid, args, offset, limit=limit, order=order, context=context, count=count)
        #_logger.info('------- context %s args %s result %s order %s',context,args,result,order)
        #if result and context and context.get('default_product_id') and not context.get('future_display_name'):
        if context and context.get('default_product_id') and not context.get('future_display_name'):
            company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
            product_id = context['default_product_id']
            query = "select id from sale_order \
                    where id in (select order_id from sale_order_line where product_id = %s) \
                    and company_id = %s "
            if args and result and isinstance(result,list):
                query += "and id in ("+ ','.join([str(i) for i in result])+") "
            if order:
                query += "order by %s"%order

            cr.execute(query,(product_id, company_id))
            orders = cr.fetchall()
            result = [order[0] for order in orders]
        return result

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        #_logger.info('------- context %s domain %s',context,domain)
        if context and context.get('default_product_id') and not context.get('future_display_name'):
            company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
            product_id = context['default_product_id']
            cr.execute("select id from sale_order \
                where id in (select order_id from sale_order_line where product_id = %s) \
                and company_id = %s",(product_id, company_id))
            orders = cr.fetchall()
            order_ids = [order[0] for order in orders]
            domain += [('id', 'in', tuple(order_ids))]
        return super(sale_order, self).read_group(cr, uid, domain, fields, groupby, 
                offset=offset, limit=limit, context=context, orderby=orderby)

    #Issue250
    def action_button_obsoleted(self, cr, uid, ids, context=None):
        for sale in self.browse(cr, uid, ids, context=context):
            for line in sale.order_line:
                self.pool.get('sale.order.line').write(cr, uid, [line.id], {'state': 'obsoleted'}, context=context)
        return self.write(cr, uid, ids, {'state': 'obsoleted'}, context=context)

    #Issue373
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', order.company_id.id), ('currency', '=', order.pricelist_id.currency_id.id)],
            limit=1)
        if journal_ids:
            invoice_vals.update({'journal_id': journal_ids[0]})
        return invoice_vals

class sale_order_line(osv.osv):

    _inherit = 'sale.order.line'

    _columns = {
#        'purchase_price': fields.related('product_id', 'standard_price', string='Cost Price', digits=(16,2), type='float', readonly=True),
        'date_order': fields.related('order_id', 'date_order', type='date', store=True, string='Date', readonly=True),
        'residual': fields.related('order_id', 'residual', type='float', string='Balance', readonly=True),
        #Issue245
        'amount_total': fields.related('order_id', 'amount_total', type='float', store=True, string='Total', readonly=True),
        'state': fields.selection([('cancel', 'Cancelled'),('draft', 'Draft'),('obsoleted','Obsoleted'),('confirmed', 'Confirmed'),('exception', 'Exception'),('done', 'Done')], 'Status', required=True, readonly=True,
                help='* The \'Draft\' status is set when the related sales order in draft status. \
                    \n* The \'Confirmed\' status is set when the related sales order is confirmed. \
                    \n* The \'Exception\' status is set when the related sales order is set as exception. \
                    \n* The \'Done\' status is set when the sales order line has been picked. \
                    \n* The \'Cancelled\' status is set when a user cancel the sales order related.'),#Issue250
        }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product,
                qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                partner_id=partner_id, lang=lang, update_tax=update_tax,
                date_order=date_order, context=context)
        if product:
            product = self.pool.get('product.product').browse(cr, uid, product, context=context)
            uom_id = product.uom_id.id or False
            res['value'].update({'product_uom': uom_id})
        return res

    '''
    def action_view_orders(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'sale', 'action_orders')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #sale order
        line = self.browse(cr, uid, ids[0], context=context)
        cr.execute("select id from sale_order \
                where id in (select order_id from sale_order_line where product_id = %s)\
                and company_id=%s",(line.product_id.id,line.company_id.id))
        orders = cr.fetchall()[0]
        _logger.info('zx----orders %s'%orders)
        result['domain'] = "[('id', 'in', [" + ','.join([str(i) for i in orders]) + "])]"
        res = mod_obj.get_object_reference(cr, uid, 'sale', 'view_order_form')
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = line.order_id.id
        return result
    '''


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
