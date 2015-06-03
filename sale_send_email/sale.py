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

from dateutil import relativedelta
from datetime import datetime, timedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc
from openerp import tools

import requests

import logging
_logger = logging.getLogger(__name__)

class sale_shop(osv.osv):
    _inherit = "sale.shop"
    _columns = {
        'active': fields.boolean('Active', help="The active field allows you to hide the shop without removing it."),
    }
    _defaults = {
        'active': True,
    }

sale_shop()


class email_template(osv.osv):
    _inherit = "email.template"

    _columns = {
        'sms': fields.text('SMS', help="send message to customer where send email"),
        'if_sms': fields.boolean('Enable SMS', help="Send Message"),
    }

    _defaults = {
            'if_sms': False,
    }
    """
    def render_sms(self, cr, uid, sms, model, res_id, context=None):
        if not sms:
            return u""
        if context is None:
            context = {}
        try:
            template = tools.ustr(template)
            record = None
            if res_id:
                record = self.pool.get(model).browse(cr, uid, res_id, context=context)
            variables = {
                'object': record,
                'user': user,
                'ctx': context,     # context kw would clash with mako internals
            }
            result = mako_template_env.from_string(template).render(variables)
            if result == u"False":
                result = u""
            return result
        except Exception:
            _logger.exception("failed to render mako template value %r", template)
            return u""
    """


    
class sale_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {
        'amount_paid_lst': fields.float('Paid last time', digits_compute= dp.get_precision('Account'), readonly=True),
        'is_preorder': fields.boolean('Is Preorder', help="If prepay order"),
        'date_done': fields.datetime('Done Date', readonly=True, select=True, help="Date on which sales order is done."),
    }

    _defaults = {
    }

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'date_done': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        return super(sale_order, self).action_done(cr, uid, ids, context=context)

###########################    Email Template    ###############################
    def action_email_send(self, cr, uid, ids, email_template, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'sale_send_email', email_template)[1]
        except ValueError:
            template_id = False
        if template_id:
            template_obj = self.pool.get('email.template')
            mail_id = template_obj.send_mail(cr, uid, template_id, ids[0], True)
            #zhangxue send sms
            email = self.pool.get('mail.mail').browse(cr, uid, mail_id)
            if not email:
                return False
            if hasattr(email, 'mail_server_id') and (not email.mail_server_id):
                return False
            try:
                template = template_obj.browse(cr, uid, template_id, context=context)
                if template and template.if_sms and template.sms and template.sms.strip():
                    sms_body = template_obj.render_template(cr, uid, template.sms, template.model, ids[0], context)
                    partner_id = self.browse(cr, uid, ids[0]).partner_id
                    sms_to = partner_id.phone or partner_id.mobile or ''
                    sms_to = sms_to.replace(' ','')
                    #sms_to = '+8613681856739'
                    if sms_to and sms_body:
                        #Issue 190
                        sale_obj = self.browse(cr, uid, ids[0])
                        if sale_obj.company_id.id == 4:
                            sms_to = '61' + sms_to[1:]
                        elif sale_obj.company_id.id == 5:
                            sms_to = '64' + sms_to[1:]
                        #url = 'https://www.siptraffic.com/myaccount/sendsms.php?username=mactrends&password=jmfimports2010&from=+001800&to=%s&text=%s'%(sms_to,sms_body)
                        url = 'http://api.clickatell.com/http/sendmsg?user=mactrends_sms&password=PNKMUaffcWAIeN&api_id=3536862&to=%s&text=%s'%(sms_to,sms_body)
                        res = requests.get(url)
            except:
                pass
        return True
    
###########################    Email Template    ###############################

    def create(self, cr, uid, vals, context=None):

        sale = super(sale_order, self).create(cr, uid, vals, context=context)
        sale_obj = self.browse(cr, uid, sale)
        #Issue267
        auto_email = self.pool.get('auto.email.so').search(cr, uid, 
            [('company_id', '=', sale_obj.company_id.id)],
            limit=1)
        if auto_email and not sale_obj.auto_email:
            self.write(cr, uid, [sale_obj.id], {'auto_email': auto_email[0]})
        if sale_obj and sale_obj.partner_id and sale_obj.partner_id.email and sale_obj.state in ('draft','sent'):    #Issue 197 Issue267
            template_obj = self.pool.get('email.template')
            if sale_obj.auto_email and sale_obj.auto_email.if_sq_notify:
                template_obj.send_mail(cr, uid, sale_obj.auto_email.template_sq.id, sale_obj.id, True)
            elif auto_email and self.pool.get('auto.email.so').browse(cr, uid, auto_email[0]).if_sq_notify:
                template_obj.send_mail(cr, uid, self.pool.get('auto.email.so').browse(cr, uid, auto_email[0]).template_sq.id, sale_obj.id, True)
            '''
            if sale_obj.company_id.id == 5: #NZ
                self.action_email_send(cr, uid, [sale], 'email_template_edi_sale_sq_nz', context=context)
            elif sale_obj.company_id.id == 4: #AUS
                self.action_email_send(cr, uid, [sale], 'email_template_edi_sale_sq_aus', context=context)
            elif sale_obj.company_id.id == 7: #UK
                self.action_email_send(cr, uid, [sale], 'email_template_edi_sale_sq_uk', context=context)
            '''

        #Issue220
        #if sale_obj and sale_obj.partner_id and sale_obj.partner_id.email and sale_obj.state in ('draft','sent'):
        #    for line in sale_obj.order_line:
        #        if line.product_id.etemplate_id:
        #            tmp_ids.append(line.product_id.etemplate_id.id)
            #Issue261
            tmp_ids = []
            for line in sale_obj.order_line:
                if line.product_id.auto_email and line.product_id.auto_email.is_send_sq:
                    for template_id in line.product_id.auto_email.templates_sq:
                        tmp_ids.append(template_id.id)
                elif line.product_id.categ_id.auto_email and line.product_id.categ_id.auto_email.is_send_sq:
                    for template_id in line.product_id.categ_id.auto_email.templates_sq:
                        tmp_ids.append(template_id.id)
                    '''
                    if line.product_id.template_sq_1:
                        tmp_ids.append(line.product_id.template_sq_1.id)
                    if line.product_id.template_sq_2:
                        tmp_ids.append(line.product_id.template_sq_2.id)
                    if line.product_id.template_sq_3:
                        tmp_ids.append(line.product_id.template_sq_3.id)
                    if line.product_id.template_sq_4:
                        tmp_ids.append(line.product_id.template_sq_4.id)
                    if line.product_id.template_sq_5:
                        tmp_ids.append(line.product_id.template_sq_5.id)
                    if line.product_id.template_sq_6:
                        tmp_ids.append(line.product_id.template_sq_6.id)
                    if line.product_id.template_sq_7:
                        tmp_ids.append(line.product_id.template_sq_7.id)
                    '''
            for tmp_id in list(set(tmp_ids)): 
                mail_id = template_obj.send_mail(cr, uid, tmp_id, sale_obj.id, True)

        return sale


    def action_button_confirm(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        # Issue-147
        for sale_obj in self.browse(cr, uid, ids, context=context):
            if abs(sale_obj.amount_total - sale_obj.amount_paid) > 0.001:
                raise osv.except_osv(_('Invalid Action!'), _('Amount Paid not equal Total'))
        # Issue-128
        if not context.get('mark'):
            for sale_obj in self.browse(cr, uid, ids, context=context):
                dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale_send_email', 'view_sale_order_confirm')
                for line in sale_obj.order_line:
                    # not kits and service
                    #if not line.product_id.is_kit and line.product_id.categ_id.id != 16 and line.product_id.virtual_available < line.product_uom_qty:
                    #Issue 206
                    if ((line.product_id.is_kit and line.product_id.kits_qty_available < line.product_uom_qty) or (not line.product_id.is_kit and line.product_id.virtual_available < line.product_uom_qty)) and ((line.product_id.categ_id and line.product_id.categ_id.id != 16) or not line.product_id.categ_id):
                        return {
                            'name':_("Warning"),
                            'view_mode': 'form',
                            'view_id': view_id,
                            'res_id': line.id,
                            'view_type': 'form',
                            'res_model': 'sale.order.line',
                            'type': 'ir.actions.act_window',
                            'nodestroy': True,
                            'target': 'new',
                            'domain': '[]',
                            'context': {},
                            }
        sale = super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)
        wf_service = netsvc.LocalService("workflow")
        for sale_obj in self.browse(cr, uid, ids, context=context):
            # Issue-128
            wf_service.trg_validate(uid, 'sale.order', sale_obj.id, 'manual_invoice', cr)
            if not context.get('mark'): #Issue 184
                for picking in sale_obj.picking_ids:
                    self.pool.get('stock.picking').force_assign(cr, uid, [picking.id])
            # Issue-126
            if sale_obj.shipping_method != 'collection' and sale_obj.partner_id and (not sale_obj.partner_id.phone) and (not sale_obj.partner_id.mobile):
                for line in sale_obj.order_line:
                    if line.product_id.cubic_weight > 30 or line.product_id.weight_net > 30:
                        raise osv.except_osv(_('Invalid Action!'), _('You must have at least one phone number to validate this order!'))

            if sale_obj and sale_obj.partner_id and sale_obj.partner_id.email and sale_obj.state in ('progress','manual','invoice_except'):    #Issue 197 Issue267
            #if sale_obj and sale_obj.partner_id and sale_obj.partner_id.email and sale_obj.state in ('progress','manual'):
                template_obj = self.pool.get('email.template')
                if sale_obj.auto_email and sale_obj.auto_email.if_con_notify:
                    template_obj.send_mail(cr, uid, sale_obj.auto_email.template_so.id, sale_obj.id, True)
                #Issue261
                tmp_ids = []
                for line in sale_obj.order_line:
                    #if line.product_id.is_send_so:
                        #for template_id in line.product_id.templates_so:
                    if line.product_id.auto_email and line.product_id.auto_email.is_send_so:
                        for template_id in line.product_id.auto_email.templates_so:
                            tmp_ids.append(template_id.id)
                    elif line.product_id.categ_id.auto_email and line.product_id.categ_id.auto_email.is_send_so:
                        for template_id in line.product_id.categ_id.auto_email.templates_so:
                            tmp_ids.append(template_id.id)
                for tmp_id in list(set(tmp_ids)): 
                    template_obj.send_mail(cr, uid, tmp_id, sale_obj.id, True)
                '''
                if sale_obj.company_id.id == 5: #NZ
                    self.action_email_send(cr, uid, [sale_obj.id], 'email_template_edi_sale_con_nz', context=context)
                elif sale_obj.company_id.id == 4: #AUS
                    self.action_email_send(cr, uid, [sale_obj.id], 'email_template_edi_sale_con_aus', context=context)
                elif sale_obj.company_id.id == 7: #UK
                    self.action_email_send(cr, uid, [sale_obj.id], 'email_template_edi_sale_con_uk', context=context)
                        if line.product_id.template_so_1:
                            tmp_ids.append(line.product_id.template_so_1.id)
                        if line.product_id.template_so_2:
                            tmp_ids.append(line.product_id.template_so_2.id)
                        if line.product_id.template_so_3:
                            tmp_ids.append(line.product_id.template_so_3.id)
                        if line.product_id.template_so_4:
                            tmp_ids.append(line.product_id.template_so_4.id)
                        if line.product_id.template_so_5:
                            tmp_ids.append(line.product_id.template_so_5.id)
                        if line.product_id.template_so_6:
                            tmp_ids.append(line.product_id.template_so_6.id)
                        if line.product_id.template_so_7:
                            tmp_ids.append(line.product_id.template_so_7.id)
                '''

            if sale_obj.is_createpq and sale_obj.company_id.id!=8:
                pname = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order', context={'force_company':8})
                qc = list(set([line.product_id.qc_manager and line.product_id.qc_manager.partner_id.name for line in sale_obj.order_line]))
                qc = filter(lambda a: a, qc)
                purchase = {
                        'name': pname,
                        'origin': qc and ' ,'.join(qc) + ':' + sale_obj.name or sale_obj.name,  #Issue #170
                        'notes': sale_obj.shop_id.warehouse_id.name,
                        'date_order': time.strftime('%Y-%m-%d'),
                        'partner_id': 23558,
                        'warehouse_id': 11,
                        'location_id': 65,
                        'pricelist_id': 12,
                        'invoice_method': 'order',
                        'state': 'draft',
                        'company_id': 8,
                        }
                purchase_id = self.pool.get('purchase.order').create(cr, 1, purchase, context=context)
                for line in sale_obj.order_line:
                    purchase_line ={
                            'name': line.product_id.name,
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'date_planned': time.strftime('%Y-%m-%d'),
                            'product_uom': line.product_uom.id,
                            'price_unit': line.price_unit,
                            'order_id': purchase_id,
                            'state': 'draft',
                            'company_id': 8,
                            }
                    self.pool.get('purchase.order.line').create(cr, 1, purchase_line, context=context)
                ir_model_data = self.pool.get('ir.model.data')
                template_id = ir_model_data.get_object_reference(cr, 1, 'sale_send_email', 'email_template_po_qcmanager')[1]
                qc = list(set([line.product_id.qc_manager and line.product_id.qc_manager.partner_id.email for line in sale_obj.order_line]))
                qc = filter(lambda a: a, qc)
                email_to = qc and ','.join(qc) or ''
                if template_id and email_to:
                    template_obj = self.pool.get('email.template')
                    template_obj.write(cr, 1, template_id, {'email_to':email_to})
                    mail_id = template_obj.send_mail(cr, 1, template_id, purchase_id, True)
        return sale

class sale_order_line(osv.osv):

    _inherit = 'sale.order.line'

    _columns = {
        #'purchase_price': fields.related('product_id', 'standard_price', string='Cost Price', digits=(16,2), type='float', readonly=True),
        #'product_uom': fields.many2one('product.uom', 'Unit of Measure ', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'product_uom': fields.related('product_id', 'uom_id', string='Unit of Measure', type='many2one', relation='product.uom', store=True, readonly=True),
        }

    def do_confirm(self, cr, uid, ids, context=None):
        # Issue-128
        if context is None:
            context = {}
        context.update({'mark':'mark'})
        for line in self.browse(cr, uid, ids, context=context):
            self.pool.get('sale.order').action_button_confirm(cr, uid, [line.order_id.id], context=context)
            return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
