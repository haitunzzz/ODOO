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
from operator import itemgetter
from itertools import groupby
from openerp import netsvc

import requests

class stock_location(osv.osv):
    _inherit = "stock.location"

    def _product_value_ats(self, cr, uid, ids, field_names, arg, context=None):
        """Computes stock value (real and virtual) for a product, as well as stock qty (real and virtual).
        @param field_names: Name of field
        @return: Dictionary of values
        """
        prod_id = context and context.get('product_id', False)

        if not prod_id:
            return dict([(i, 0.0) for i in ids])

        product_product_obj = self.pool.get('product.product')

        cr.execute('select distinct product_id, location_id from stock_move where location_id in %s', (tuple(ids), ))
        dict1 = cr.dictfetchall()
        cr.execute('select distinct product_id, location_dest_id as location_id from stock_move where location_dest_id in %s', (tuple(ids), ))
        dict2 = cr.dictfetchall()
        res_products_by_location = sorted(dict1+dict2, key=itemgetter('location_id'))
        products_by_location = dict((k, [v['product_id'] for v in itr]) for k, itr in groupby(res_products_by_location, itemgetter('location_id')))

        result = dict([(i, 0.0) for i in ids])
        result.update(dict([(i, 0.0) for i in list(set([aaa['location_id'] for aaa in res_products_by_location]))]))

        currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        currency_obj = self.pool.get('res.currency')
        currency = currency_obj.browse(cr, uid, currency_id, context=context)


        for loc_id, product_ids in products_by_location.items():
            if prod_id:
                product_ids = [prod_id]
            c = (context or {}).copy()
            c['location'] = loc_id
            for prod in product_product_obj.browse(cr, uid, product_ids, context=c):
                    """
                if prod.is_kit:
                    child_prod = []
                    for bom in prod.bom_ids:
                        for line in bom.bom_lines:
                            child_prod.append(line.product_id)
                    child_prod = list(set(child_prod))
                    if not child_prod:
                        continue
                    result[loc_id] += min([p._current_virtual_available for p in child_prod])
                else:
                """
                    if loc_id not in result:
                        result[loc_id] = 0
                    result[loc_id] += prod._current_virtual_available
        return result


    def _product_value(self, cr, uid, ids, field_names, arg, context=None):
        """Computes stock value (real and virtual) for a product, as well as stock qty (real and virtual).
        @param field_names: Name of field
        @return: Dictionary of values
        """
        prod_id = context and context.get('product_id', False)

        if not prod_id:
            return dict([(i, {}.fromkeys(field_names, 0.0)) for i in ids])

        product_product_obj = self.pool.get('product.product')

        cr.execute('select distinct product_id, location_id from stock_move where location_id in %s', (tuple(ids), ))
        dict1 = cr.dictfetchall()
        cr.execute('select distinct product_id, location_dest_id as location_id from stock_move where location_dest_id in %s', (tuple(ids), ))
        dict2 = cr.dictfetchall()
        res_products_by_location = sorted(dict1+dict2, key=itemgetter('location_id'))
        products_by_location = dict((k, [v['product_id'] for v in itr]) for k, itr in groupby(res_products_by_location, itemgetter('location_id')))

        result = dict([(i, {}.fromkeys(field_names, 0.0)) for i in ids])
        result.update(dict([(i, {}.fromkeys(field_names, 0.0)) for i in list(set([aaa['location_id'] for aaa in res_products_by_location]))]))
        #result =  super(stock_location, self)._product_value(cr, uid, ids, field_names, arg, context=context)

        currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        currency_obj = self.pool.get('res.currency')
        currency = currency_obj.browse(cr, uid, currency_id, context=context)
        for loc_id, product_ids in products_by_location.items():
            if prod_id:
                product_ids = [prod_id]
            c = (context or {}).copy()
            c['location'] = loc_id
            for prod in product_product_obj.browse(cr, uid, product_ids, context=c):
                #Issue 203
                if prod.is_kit:
                    child_prod = []
                    for bom in prod.bom_ids:
                        #bom type is phantom
                        #TODO take care of the valid date of the components
                        #if bom.type == 'phantom':
                        for line in bom.bom_lines:
                            child_prod.append(line.product_id)
                    child_prod = list(set(child_prod))
                    if not child_prod:
                        continue
                    for f in field_names:
                        if f == 'stock_real':
                            if loc_id not in result:
                                result[loc_id] = {}
                            result[loc_id][f] += min([p.qty_available for p in child_prod])
                        elif f == 'stock_virtual':
                            result[loc_id][f] += prod.virtual_available
                            result[loc_id][f] += min([p.virtual_available for p in child_prod])
                        elif f == 'stock_real_value':
                            result[loc_id][f] += min([currency_obj.round(cr, uid, currency, p.qty_available * p.standard_price) for p in child_prod])
                        elif f == 'stock_virtual_value':
                            result[loc_id][f] += min([currency_obj.round(cr, uid, currency, p.virtual_available * p.standard_price) for p in child_prod])
                else:
                    for f in field_names:
                        if f == 'stock_real':
                            if loc_id not in result:
                                result[loc_id] = {}
                            result[loc_id][f] += prod.qty_available
                        elif f == 'stock_virtual':
                            result[loc_id][f] += prod.virtual_available
                        elif f == 'stock_real_value':
                            amount = prod.qty_available * prod.standard_price
                            amount = currency_obj.round(cr, uid, currency, amount)
                            result[loc_id][f] += amount
                        elif f == 'stock_virtual_value':
                            amount = prod.virtual_available * prod.standard_price
                            amount = currency_obj.round(cr, uid, currency, amount)
                            result[loc_id][f] += amount
    
        return result

    _columns = {
        'stock_ats': fields.function(_product_value_ats, type='float', string='ATS Stock',),
        'stock_real': fields.function(_product_value, type='float', string='Real Stock', multi="stock"),
        'stock_virtual': fields.function(_product_value, type='float', string='Virtual Stock', multi="stock"),
        'stock_real_value': fields.function(_product_value, type='float', string='Real Stock Value', multi="stock", digits_compute=dp.get_precision('Account')),
        'stock_virtual_value': fields.function(_product_value, type='float', string='Virtual Stock Value', multi="stock", digits_compute=dp.get_precision('Account')),
    }

class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def _crm_claim(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = {
                    'if_claim':False,
                    'claim_id':False,
                    }
            if picking.sale_id:
                claim_id = self.pool.get('crm.claim').search(cr, uid, [('sale_id','=',picking.sale_id.id)])
                if claim_id and claim_id[0]:
                    res[picking.id] = {
                            'if_claim':True,
                            'claim_id':claim_id[0],
                            }
        return res

    _columns = {
        #'if_notification': fields.boolean('Email DO Notification', help="Send DO Notification Auto"),
        #'auto_email': fields.many2one('auto.email.int', "Auto Email Template"),
        'auto_email': fields.many2one('auto.email.do', "Auto Email Template"),
        'shipping_method':fields.related('sale_id','shipping_method',type='selection',selection=[
                ('collection','Collection'), 
                ('post','Post'), 
                ('courier','Courier'), 
                ('free','Free Shipping'), 
                ('transport','Own Transport'),
                ('freight','Freight')
             ],readonly='1',string='Shipping Method'),
        'is_preorder':fields.related('sale_id','is_preorder',type='boolean',readonly='1',string='If prepay order'),
        'control' : fields.char('3PL Inward Control #', size=32, select=True),
        'date_order': fields.related('purchase_id','date_order',string='ETD',readonly=True,type="date"),
        'minimum_planned_date': fields.related('purchase_id','minimum_planned_date',string='Expected Date',readonly=True,type="date"),
        'partner_ref': fields.related('purchase_id','partner_ref',string='Supplier Reference',readonly=True,type="char"),
        #Issue350
        'is_seconds': fields.boolean('Is Seconds'),
        'seconds': fields.selection((
                ('missing','Missing Parts'), 
                ('fully','Fully Damaged')),'Seconds'),
        'seconds_lines': fields.one2many('seconds.line', 'picking_id', string='Seconds Lines'),
        'if_claim': fields.function(_crm_claim, type='boolean', string='If Claim', multi='claim'),
        'claim_id': fields.function(_crm_claim, type='many2one', relation='crm.claim', string='Claim ID', multi='claim'), #Issue349
    }

    _defaults = {
            #'if_notification': True,
            }

    #Issue267
    def create(self, cr, uid, vals, context=None):
        auto_email = self.pool.get('auto.email.do').search(cr, uid, 
            [('company_id', '=', self.pool.get('res.users').browse(cr, uid, uid).company_id.id)],
            limit=1)
        if auto_email:
            vals.update({'auto_email': auto_email[0]})
        return super(stock_picking, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if ((context and not context.get('from stock')) or not context):
            for picking in self.browse(cr, uid, ids):
                if 'note' in vals:
                    self.pool.get('sale.order').write(cr, uid, picking.sale_id.id, {'note':vals['note']}, context={'from stock':True})
                    for p in picking.sale_id.picking_ids:
                        self.write(cr, uid, p.id, {'note':vals['note']}, context={'from stock':True})
                #Issue266
                if 'carrier_id' in vals:
                    if picking.sale_id:
                        for picking_id in picking.sale_id.picking_ids:
                            if picking_id.type == 'out' and (not picking_id.carrier_id or picking_id.carrier_id == picking.carrier_id):
                                self.write(cr, uid, picking_id.id, {'carrier_id':vals['carrier_id']}, context={'from stock':True})
                if 'carrier_tracking_ref' in vals:
                    if picking.sale_id:
                        for picking_id in picking.sale_id.picking_ids:
                            if picking_id.type == 'out' and (not picking_id.carrier_tracking_ref or picking_id.carrier_tracking_ref == picking.carrier_tracking_ref):
                                self.write(cr, uid, picking_id.id, {'carrier_tracking_ref':vals['carrier_tracking_ref']}, context={'from stock':True})
        return super(stock_picking, self).write(cr, uid, ids, vals, context=context)


    def action_view_so(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'sale', 'action_orders')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #sale order
        picking = self.browse(cr, uid, ids[0], context=context)
        if picking and picking.sale_id:
            res = mod_obj.get_object_reference(cr, uid, 'sale', 'view_order_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = picking.sale_id.id
        return result

    def action_view_do(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'stock', 'action_picking_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #sale order
        picking = self.browse(cr, uid, ids[0], context=context)
        if picking and picking.sale_id:
            for picking_id in picking.sale_id.picking_ids:
                if picking_id.type == 'out':
                    res = mod_obj.get_object_reference(cr, uid, 'stock', 'view_picking_out_form')
                    result['views'] = [(res and res[1] or False, 'form')]
                    result['res_id'] = picking_id.id
                    return result
        return True


    def action_done(self, cr, uid, ids, context=None):
        for picking in self.browse(cr, uid, ids, context=context):
            #issue119
            if picking.type == 'in' and picking.company_id.id in (4,5,7) and picking.purchase_id and picking.purchase_id.related_so:
                so = self.pool.get('sale.order').browse(cr, 86, int(picking.purchase_id.related_so))
                #if not so.invoiced:
                #    raise osv.except_osv('Invalid Action!', 'The %s has not been paid! Please check it!'%so.name)
                for p in so.picking_ids:
                    if p.type == 'internal' and p.state != 'done':
                        raise osv.except_osv('Invalid Action!', 'The INT %s has not been delivered! Please check it!'%p.name)
                    if p.type == 'out':
                        wf_service = netsvc.LocalService('workflow')
                        #self.action_confirm_zx(cr, 86, p.id, context=context)
                        res = wf_service.trg_validate(86, 'stock.picking', p.id, 'button_confirm', cr)
                        res = wf_service.trg_validate(86, 'stock.picking', p.id, 'button_done', cr)
            if picking.type == 'internal' and picking.company_id.id == 8 and picking.sale_id and picking.sale_id.related_po:
                po = self.pool.get('purchase.order').browse(cr, 1, int(picking.sale_id.related_po))
                if po.company_id.id == 5:
                    self.pool.get('res.users').write(cr, 1, 48, {'company_id':5}, context=context)
                
                    #send   purchase@mactrends.com
                    ir_model_data = self.pool.get('ir.model.data')
                    try:
                        template_id = ir_model_data.get_object_reference(cr, 48, 'purchase_enhance','email_template_purchase_confirm')[1]
                    except ValueError:
                        template_id = False
                    if template_id:
                        template_obj = self.pool.get('email.template')
                        template_obj.write(cr, 1, [template_id], {'email_to':'purchase@mactrends.com'})
                        mail_id = template_obj.send_mail(cr, 48, template_id, po.id, True)

        result = super(stock_picking, self).action_done(cr, uid, ids, context=context)
        for picking in self.browse(cr, uid, ids, context=context):
            #issue150
            if picking.type == 'out' and picking.sale_id:
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_validate(uid, 'sale.order', picking.sale_id.id, 'button_done', cr)
                #Issue261
                if picking and picking.partner_id and picking.partner_id.email and picking.state in ('progress','manual'):
                    tmp_ids = []
                    for line in picking.move_lines:
                        if line.product_id.auto_email and line.product_id.auto_email.is_send_do:
                            for template_id in line.product_id.auto_email.templates_do:
                                tmp_ids.append(template_id.id)
                        elif line.product_id.categ_id.auto_email and line.product_id.categ_id.auto_email.is_send_do:
                            for template_id in line.product_id.categ_id.auto_email.templates_do:
                                tmp_ids.append(template_id.id)
                    for tmp_id in list(set(tmp_ids)): 
                        template_obj.send_mail(cr, uid, tmp_id, picking.id, True)
        return result

    def action_confirm_zx(self, cr, uid, ids, context=None):
        """ Confirm the inventory and writes its finished date
        @return: True
        """
        if context is None:
            context = {}
        # to perform the correct inventory corrections we need analyze stock location by
        # location, never recursively, so we use a special context
        product_context = dict(context, compute_child=False)

        location_obj = self.pool.get('stock.location')
        for inv in self.browse(cr, uid, ids, context=context):
            move_ids = []
            for line in inv.inventory_line_id:
                pid = line.product_id.id
                product_context.update(uom=line.product_uom.id, to_date=inv.date, date=inv.date, prodlot_id=line.prod_lot_id.id)
                amount = location_obj._product_get(cr, uid, line.location_id.id, [pid], product_context)[pid]
                change = line.product_qty - amount
                lot_id = line.prod_lot_id.id
                if change:
                    location_id = line.product_id.property_stock_inventory.id
                    value = {
                        'name': _('INV:') + (line.inventory_id.name or ''),
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'prodlot_id': lot_id,
                        'date': inv.date,
                    }

                    if change > 0:
                        value.update( {
                            'product_qty': change,
                            'location_id': location_id,
                            'location_dest_id': line.location_id.id,
                        })
                    else:
                        value.update( {
                            'product_qty': -change,
                            'location_id': line.location_id.id,
                            'location_dest_id': location_id,
                        })
                    move_ids.append(self._inventory_line_hook(cr, uid, line, value))
            self.write(cr, uid, [inv.id], {'state': 'confirm', 'move_ids': [(6, 0, move_ids)]})
            self.pool.get('stock.move').action_confirm(cr, uid, move_ids, context=context)
        return True

    def action_check(self, cr, uid, ids, *args):
        """ Check qty of product.
            if f == 'qty_available':
                c.update({ 'states': ('done',), 'what': ('in', 'out') })
            if f == 'virtual_available':
                c.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
            if f == 'incoming_qty':
                c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('in',) })
            if f == 'outgoing_qty':
                c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('out',) })
        @return: True
        """
        for picking in self.browse(cr, uid, ids):
            for move in picking.move_lines:
                qty = self.pool.get('stock.location')._product_get_multi_location(cr, uid, [move.location_id.id], product_ids=[move.product_id.id], context={
            'states': ['done'],
            'what': ('in', 'out'),
            'location': [move.location_id.id]
                    })
                if qty.get(move.product_id.id, 0) - move.product_qty < 0:
                    raise osv.except_osv('Invalid Action!', 'The qty of %s is not enough(%s<%s)! Please check it!'%(move.product_id.name_template, qty.get(move.product_id.id, 0), move.product_qty))
        return self.action_assign(cr, uid, ids, *args)

    #Issue363
    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        invoice_vals = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
        if 'return' in picking.name:
            invoice_vals.update({
                'product_return': True,
                'refund_picking_id': picking.id,
                #'if_returned': picking.state == 'done' and True or False
                })
        if picking.claim_id:
            invoice_vals.update({
                'claim_id': picking.claim_id.id
                })
        return invoice_vals

    #Issue349
    def action_invoice_create(self, cr, uid, ids, journal_id=False,
            group=False, type='out_invoice', context=None):
        """ Creates invoice based on the invoice state selected for picking.
        @param journal_id: Id of journal
        @param group: Whether to create a group invoice or not
        @param type: Type invoice to be created
        @return: Ids of created invoices for the pickings
        """
        if context is None:
            context = {}

        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        partner_obj = self.pool.get('res.partner')
        invoices_group = {}
        res = {}
        inv_type = type
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.invoice_state != '2binvoiced':
                continue
            partner = self._get_partner_to_invoice(cr, uid, picking, context=context)
            if isinstance(partner, int):
                partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
            if not partner:
                raise osv.except_osv(_('Error, no partner!'),
                    _('Please put a partner on the picking list if you want to generate invoice.'))

            if not inv_type:
                inv_type = self._get_invoice_type(picking)

            if group and partner.id in invoices_group:
                invoice_id = invoices_group[partner.id]
                invoice = invoice_obj.browse(cr, uid, invoice_id)
                invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
                invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
            else:
                invoice_vals = self._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
                invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
                invoices_group[partner.id] = invoice_id
            res[picking.id] = invoice_id
            #Issue349
            if not picking.sale_id:
                for move_line in picking.move_lines:
                    if move_line.state == 'cancel':
                        continue
                    if move_line.scrapped:
                        # do no invoice scrapped products
                        continue
                    vals = self._prepare_invoice_line(cr, uid, group, picking, move_line,
                                    invoice_id, invoice_vals, context=context)
                    if vals:
                        invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
                        self._invoice_line_hook(cr, uid, move_line, invoice_line_id)
            else:
                for move_line in picking.sale_id.order_line:
                    if move_line.state == 'cancel':
                        continue
                    vals = self._prepare_invoice_line_sale(cr, uid, group, picking, move_line,
                                    invoice_id, invoice_vals, context=context)
                    if vals:
                        invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
                        move_line.write({'invoice_lines': [(4, invoice_line_id)]})


            invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
                    set_total=(inv_type in ('in_invoice', 'in_refund')))
            self.write(cr, uid, [picking.id], {
                'invoice_state': 'invoiced',
                }, context=context)
            self._invoice_hook(cr, uid, picking, invoice_id)
        self.write(cr, uid, res.keys(), {
            'invoice_state': 'invoiced',
            }, context=context)
        return res

    def _prepare_invoice_line_sale(self, cr, uid, group, picking, move_line, invoice_id,
        invoice_vals, context=None):
        """ Builds the dict containing the values for the invoice line
            @param group: True or False
            @param picking: picking object
            @param: move_line: move_line object
            @param: invoice_id: ID of the related invoice
            @param: invoice_vals: dict used to created the invoice
            @return: dict that will be used to create the invoice line
        """
        if group:
            name = (picking.name or '') + '-' + move_line.name
        else:
            name = move_line.name
        origin = move_line.order_id.name or ''
        if move_line.order_id.origin:
            origin += ':' + move_line.order_id.origin

        if invoice_vals['type'] in ('out_invoice', 'out_refund'):
            account_id = move_line.product_id.property_account_income.id
            if not account_id:
                account_id = move_line.product_id.categ_id.\
                        property_account_income_categ.id
        else:
            account_id = move_line.product_id.property_account_expense.id
            if not account_id:
                account_id = move_line.product_id.categ_id.\
                        property_account_expense_categ.id
        if invoice_vals['fiscal_position']:
            fp_obj = self.pool.get('account.fiscal.position')
            fiscal_position = fp_obj.browse(cr, uid, invoice_vals['fiscal_position'], context=context)
            account_id = fp_obj.map_account(cr, uid, fiscal_position, account_id)
        # set UoS if it's a sale and the picking doesn't have one
        uos_id = move_line.product_uos and move_line.product_uos.id or False
        if not uos_id and invoice_vals['type'] in ('out_invoice', 'out_refund'):
            uos_id = move_line.product_uom.id

        return {
            'name': name,
            'origin': origin,
            'invoice_id': invoice_id,
            'uos_id': uos_id,
            'product_id': move_line.product_id.id,
            'account_id': account_id,
            'price_unit': self._get_price_unit_invoice_sale(cr, uid, move_line, invoice_vals['type']),
            'discount': move_line.discount,
            'quantity': move_line.product_uos_qty or move_line.product_qty,
            'invoice_line_tax_id': [(6, 0, [x.id for x in move_line.tax_id])],
            'account_analytic_id': self._get_account_analytic_invoice(cr, uid, picking, move_line),
        }

    def _get_price_unit_invoice_sale(self, cursor, user, move_line, type):
        uom_id = move_line.product_id.uom_id.id
        uos_id = move_line.product_id.uos_id and move_line.product_id.uos_id.id or False
        price = move_line.price_unit
        coeff = move_line.product_id.uos_coeff
        if uom_id != uos_id  and coeff != 0:
            price_unit = price / coeff
            return price_unit
        return move_line.price_unit


class stock_picking_out(orm.Model):
    _inherit = 'stock.picking.out'

    def _crm_claim(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = {
                    'if_claim':False,
                    'claim_id':False,
                    }
            if picking.sale_id:
                claim_id = self.pool.get('crm.claim').search(cr, uid, [('sale_id','=',picking.sale_id.id)])
                if claim_id and claim_id[0]:
                    res[picking.id] = {
                            'if_claim':True,
                            'claim_id':claim_id[0],
                            }
        return res

    _columns = {
        #'if_notification': fields.boolean('Email DO Notification', help="Send DO Notification Auto"),
        'auto_email': fields.many2one('auto.email.do', "Auto Email Template"),
        'shipping_method':fields.related('sale_id','shipping_method',type='selection',selection=[
                ('collection','Collection'), 
                ('post','Post'), 
                ('courier','Courier'), 
                ('free','Free Shipping'), 
                ('transport','Own Transport'),
                ('freight','Freight')
             ],readonly='1',string='Shipping Method'),
        'if_claim': fields.function(_crm_claim, type='boolean', string='If Claim', multi='claim'),
        'claim_id': fields.function(_crm_claim, type='many2one', relation='crm.claim', string='Claim ID', multi='claim'), #Issue349
    }

    _defaults = {
            #'if_notification': True,
            }

    #Issue267
    def create(self, cr, uid, vals, context=None):
        auto_email = self.pool.get('auto.email.do').search(cr, uid, 
            [('company_id', '=', self.pool.get('res.users').browse(cr, uid, uid).company_id.id)],
            limit=1)
        if auto_email:
            vals.update({'auto_email': auto_email[0]})
        return super(stock_picking_out, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = super(stock_picking_out, self).write(cr, uid, ids, vals, context=context)
        if 'note' in vals and ((context and not context.get('from stock')) or not context):
            for picking in self.browse(cr, uid, ids, context=context):
                self.pool.get('sale.order').write(cr, uid, picking.sale_id.id, {'note':vals['note']}, context={'from stock':True})
                for p in picking.sale_id.picking_ids:
                    self.pool.get('stock.picking').write(cr, uid, p.id, {'note':vals['note']}, context={'from stock':True})
        return res

    def action_view_so(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'sale', 'action_orders')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #sale order
        picking = self.browse(cr, uid, ids[0], context=context)
        if picking and picking.sale_id:
            res = mod_obj.get_object_reference(cr, uid, 'sale', 'view_order_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = picking.sale_id.id
        return result

    def action_view_int(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'stock', 'action_picking_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #sale order
        picking = self.browse(cr, uid, ids[0], context=context)
        if picking and picking.sale_id:
            for picking_id in picking.sale_id.picking_ids:
                if picking_id.type == 'internal':
                    res = mod_obj.get_object_reference(cr, uid, 'stock', 'view_picking_form')
                    result['views'] = [(res and res[1] or False, 'form')]
                    result['res_id'] = picking_id.id
                    return result
        return True

    #issue 121
    def action_view_claim(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'crm_claim', 'crm_case_categ_claim0')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #crm claim
        picking = self.browse(cr, uid, ids[0], context=context)
        if picking and picking.sale_id:
            res = mod_obj.get_object_reference(cr, uid, 'crm_claim', 'crm_case_claims_form_view')
            result['views'] = [(res and res[1] or False, 'form')]
            claim_id = self.pool.get('crm.claim').search(cr, uid, [('sale_id','=',picking.sale_id.id)])
            if claim_id and claim_id[0]:
                result['res_id'] = claim_id[0]
        return result

    #issue137
    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        if not context:
            context = {}
        if uid != 1:
            company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
            domain.append(['company_id','=',company_id])
        return super(stock_picking_out, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby)


class stock_picking_in(orm.Model):
    _inherit = 'stock.picking.in'

    def _crm_claim(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = {
                    'if_claim':False,
                    'claim_id':False,
                    }
            if picking.sale_id:
                claim_id = self.pool.get('crm.claim').search(cr, uid, [('sale_id','=',picking.sale_id.id)])
                if claim_id and claim_id[0]:
                    res[picking.id] = {
                            'if_claim':True,
                            'claim_id':claim_id[0],
                            }
        return res

    #Issue242
    _columns = {
        'date_order': fields.related('purchase_id','date_order',string='ETD',readonly=True,type="date"),
        'minimum_planned_date': fields.related('purchase_id','minimum_planned_date',string='Expected Date',readonly=True,type="date"),
        'partner_ref': fields.related('purchase_id','partner_ref',string='Supplier Reference',readonly=True,type="char"),
        #Issue350
        'is_seconds': fields.boolean('Is Seconds'),
        'seconds': fields.selection((
                ('missing','Missing Parts'), 
                ('fully','Fully Damaged')),'Seconds'),
        'seconds_lines': fields.one2many('seconds.line', 'picking_id', string='Seconds Lines'),
        #'claim_id': fields.many2one('crm.claim', string='Claim ID'), #Issue349
        'if_claim': fields.function(_crm_claim, type='boolean', string='If Claim', multi='claim'),
        'claim_id': fields.function(_crm_claim, type='many2one', relation='crm.claim', string='Claim ID', multi='claim'), #Issue349
        }

#    def default_get(self, cr, uid, fields, context=None):
#        if context is None:
#            context = {}
#        res = super(stock_picking_in, self).default_get(cr, uid, fields, context=context)
#
#        if 'claim_id' in fields and 'claim_id' in context:
#            res.update({'claim_id': context['claim_id']})
#
#        return res
    #Issue349
    def action_invoice_create(self, cr, uid, ids, journal_id=False,
            group=False, type='out_invoice', context=None):
        """ Creates invoice based on the invoice state selected for picking.
        @param journal_id: Id of journal
        @param group: Whether to create a group invoice or not
        @param type: Type invoice to be created
        @return: Ids of created invoices for the pickings
        """
        if context is None:
            context = {}

        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        partner_obj = self.pool.get('res.partner')
        invoices_group = {}
        res = {}
        inv_type = type
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.invoice_state != '2binvoiced':
                continue
            partner = self._get_partner_to_invoice(cr, uid, picking, context=context)
            if isinstance(partner, int):
                partner = partner_obj.browse(cr, uid, [partner], context=context)[0]
            if not partner:
                raise osv.except_osv(_('Error, no partner!'),
                    _('Please put a partner on the picking list if you want to generate invoice.'))

            if not inv_type:
                inv_type = self._get_invoice_type(picking)

            if group and partner.id in invoices_group:
                invoice_id = invoices_group[partner.id]
                invoice = invoice_obj.browse(cr, uid, invoice_id)
                invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
                invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
            else:
                invoice_vals = self._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
                invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
                invoices_group[partner.id] = invoice_id
            res[picking.id] = invoice_id
            #Issue349
            if not picking.sale_id:
                for move_line in picking.move_lines:
                    if move_line.state == 'cancel':
                        continue
                    if move_line.scrapped:
                        # do no invoice scrapped products
                        continue
                    vals = self._prepare_invoice_line(cr, uid, group, picking, move_line,
                                    invoice_id, invoice_vals, context=context)
                    if vals:
                        invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
                        self._invoice_line_hook(cr, uid, move_line, invoice_line_id)
            else:
                for move_line in picking.sale_id.order_line:
                    if move_line.state == 'cancel':
                        continue
                    vals = self._prepare_invoice_line_sale(cr, uid, group, picking, move_line,
                                    invoice_id, invoice_vals, context=context)
                    if vals:
                        invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
                        move_line.write({'invoice_lines': [(4, invoice_line_id)]})


            invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
                    set_total=(inv_type in ('in_invoice', 'in_refund')))
            self.write(cr, uid, [picking.id], {
                'invoice_state': 'invoiced',
                }, context=context)
            self._invoice_hook(cr, uid, picking, invoice_id)
        self.write(cr, uid, res.keys(), {
            'invoice_state': 'invoiced',
            }, context=context)
        return res


class stock_partial_picking(osv.osv_memory):
    _inherit = "stock.partial.picking"

    def do_partial(self, cr, uid, ids, context={}):
        ret_val = super(stock_partial_picking, self).do_partial(cr, uid, ids, context=context)
        '''    
        if context.get('send_au_ftp_file', False):
            picking_obj.send_freight_file(cr, uid, context['active_ids'], context)
        template = self.pool.get('ir.model.data').get_object(cr, uid, 'picking_notify', 'picking_notify_email_template')
        '''    
        picking_obj = self.pool.get('stock.picking.out')
        email_obj = self.pool.get('email.template')
        for picking in picking_obj.browse(cr, uid, context['active_ids']):
            if picking.type=='out' and picking.auto_email and picking.auto_email.if_notify and picking.partner_id and picking.partner_id.email:
                for move in picking.move_lines:
                    if move.location_dest_id.id == 9:  #客户
                        '''
                        if picking.company_id.id == 5:
                            template_id = 55
                        elif picking.company_id.id == 4:
                            template_id = 27
                        elif picking.company_id.id == 7:
                            template_id = 28
                        else:
                            return ret_val
                        '''
                        template_id = picking.auto_email.template_notify
                        mail_id = email_obj.send_mail(cr, uid, template_id, picking.id, force_send=True)
                        #zhangxue send sms
                        email = self.pool.get('mail.mail').browse(cr, uid, mail_id)
                        if not email:
                            return ret_val
                        if hasattr(email, 'mail_server_id') and (not email.mail_server_id):
                            return ret_val
                        try:
                            template = template_obj.browse(cr, uid, template_id, context=context)
                            if template and template.if_sms and template.sms and template.sms.strip():
                                sms_body = template_obj.render_template(cr, uid, template.sms, template.model, ids[0], context)
                                partner_id = self.browse(cr, uid, ids[0]).partner_id
                                sms_to = partner_id.phone or partner_id.mobile or ''
                                sms_to = sms_to.replace(' ','')
                                if sms_to and sms_body:
                                    if picking.company_id.id == 4:
                                        sms_to = '61' + sms_to[1:]
                                    elif picking.company_id.id == 5:
                                        sms_to = '64' + sms_to[1:]
                                    #url = 'https://www.siptraffic.com/myaccount/sendsms.php?username=mactrends&password=jmfimports2010&from=+001800&to=%s&text=%s'%(sms_to,sms_body)
                                    url = 'http://api.clickatell.com/http/sendmsg?user=mactrends_sms&password=PNKMUaffcWAIeN&api_id=3536862&to=%s&text=%s'%(sms_to,sms_body)
                                    res = requests.get(url)
                        except:
                            pass

                        break
        return ret_val

class product_product(osv.osv):
    _inherit = "product.product"

    def _volume_total(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for pd in self.browse(cr, uid, ids, context=context):
            res[pd.id] = pd.qty_available * pd.volume
        return res

    def _kits_product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        res = {}
        field_names = field_names or []
        context = context or {}
        for id in ids:
            res[id] = {}.fromkeys(field_names, 0.0)
        field_map = {
            'kits_qty_available': 'qty_available',
            'kits_incoming_qty': 'incoming_qty',
            'kits_outgoing_qty': 'outgoing_qty',
            'kits_virtual_available': 'virtual_available'
        }
        for product_record in self.browse(cr, uid, ids, context=context):
            #check if is a kit product.
            so_qty = self._get_sale_quotation_qty(cr, uid, product_record.id, context=context)
            if not self._is_kit(
                cr, uid,
                [product_record.id],
                    context=context).get(product_record.id):

                res[product_record.id] = {
                    'kits_qty_available': 0,
                    'kits_incoming_qty': 0,
                    'kits_virtual_available': 0,
                    'kits_outgoing_qty': 0,
                    'kits_sale_quotation_qty': so_qty
                }
            #product with no bom
            # if not product_record.bom_ids:
            #     raw_res = self._product_available(cr, uid, [product_record.id], field_map.values(), arg, context)
            #     for key, val in field_map.items():
            #         res[product_record.id][key] = raw_res[product_record.id].get(val)

            #TODO how to deal with multi-bom products.
            #now get always get the first bom.
            #product with bom
            else:
                for bom in product_record.bom_ids:
                    #bom type is phantom
                    #TODO take care of the valid date of the components
                    if bom.type == 'phantom':
                        child_product_res = {}
                        for line in bom.bom_lines:
                            child_product_res[line.product_id.id] = {'product_qty': line.product_qty or 0.0}
                        child_product_qtys = self._product_available(cr, uid, child_product_res.keys(), field_map.values(), context=context)
                        res[product_record.id] = {
                            'kits_qty_available': self._get_qty_from_children(child_product_qtys, child_product_res, 'qty_available'),
                            'kits_incoming_qty': self._get_qty_from_children(child_product_qtys, child_product_res, 'incoming_qty'),
                            'kits_virtual_available': self._get_qty_from_children(child_product_qtys, child_product_res, 'virtual_available') - so_qty,
                            'kits_outgoing_qty': self._get_qty_from_children(child_product_qtys, child_product_res, 'outgoing_qty'),
                            'kits_sale_quotation_qty': so_qty
                        }

                    else:
                        raw_res = self._product_available(cr, uid, ids, field_map.values(), arg, context)
                        for key, val in field_map.items():
                            res[product_record.id][key] = raw_res[product_record.id].get(val)

                    #only get the first bom.
                    break
        return res

    def _get_sale_quotation_qty(self, cr, uid, product_id, context=None):
        '''get all qty of the product in all sale quotations (draft, sent)'''
        sol_obj = self.pool.get('sale.order.line')
        domain = [('state', 'in', ('draft', False, None)), ('product_id', '=', product_id)]
        #TODO take care of the uom.
        sol_ids = sol_obj.read_group(cr, uid, domain, ['product_uom_qty', 'product_id'], groupby=['product_id'])
        return sol_ids and sol_ids[0].get('product_uom_qty') or 0.0

    def _get_qty_from_children(self, child_product_qtys, child_product_res, field_name):
        def qty_div(product_total_qty, component_qty):
            return product_total_qty[1].get(field_name) / component_qty[1].get('product_qty')
        # when the bom has no components
        # Alex Duan <alex.duan@elico-corp.com>
        if not child_product_res:
            raise osv.except_osv(
                _('Warning'),
                _('BoM of this product has no components.\n'
                    'To avoid this warning, you might add components for this BoM.\n'))
        return min(map(qty_div, child_product_qtys.iteritems(), child_product_res.iteritems()))

    _columns = {
        'default_code' : fields.char('Internal Reference', size=64, select=True, required=True),
        'volume_total': fields.function(_volume_total, type='float', string='Total Volume', digits_compute=dp.get_precision('Payroll Rate'), help="The volume in m3 * qty_onhand"),
    }

    def _check_ref(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        refs = self.search(cr, uid, [('default_code','=',obj.default_code)], context=context)
        if len(refs)>1:
            raise osv.except_osv('Invalid Action!', 'The product ref %s repeat again! Please check it!'%obj.default_code)
        return True

    _constraints = [
        (_check_ref, 'The internal reference must be unique!', ['default_code'])
        ]

    _sql_constraints = [
        ('uniq_default_code', 'unique(default_code)', "The ref must be unique!"),
        ]


    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context={}
        if not default:
            default = {}
        default = default.copy()
        code = self.read(cr, uid, id, ['default_code'], context=context)['default_code']
        default.update(default_code="%s(copy)" % (code))
        return super(product_product, self).copy(cr, uid, id, default=default, context=context)

product_product()

class stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line"
    _columns = {
        'location_id': fields.many2one('stock.location', 'Location', required=True, states={'confirm': [('readonly', True)], 'done': [('readonly', True)]}),
        'product_id': fields.many2one('product.product', 'Product', required=True, select=True, states={'confirm': [('readonly', True)], 'done': [('readonly', True)]}),
        'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True, states={'confirm': [('readonly', True)], 'done': [('readonly', True)]}),
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), states={'confirm': [('readonly', True)], 'done': [('readonly', True)]}),
        'prod_lot_id': fields.many2one('stock.production.lot', 'Serial Number', domain="[('product_id','=',product_id)]", states={'confirm': [('readonly', True)], 'done': [('readonly', True)]}),
    }
stock_inventory_line()

class stock_warehouse(osv.osv):
    _inherit = "stock.warehouse"

    _columns = {
        'code' : fields.char('Warehouse Code', size=32, select=True),
    }

class seconds_line(orm.Model):
    _name = 'seconds.line'

    _columns = {
        'picking_id': fields.many2one('stock.picking', 'Picking', required=True, select=True, ),
        'product_id': fields.many2one('product.product', 'Product', required=True, select=True, ),
        'qty' : fields.integer('QTY', required=True),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

