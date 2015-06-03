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

from openerp.osv import osv, fields
import logging
_logger = logging.getLogger(__name__)
from openerp.tools.translate import _


class sale_crm_lead(osv.Model):
    _inherit = 'crm.lead'

    def create(self, cr, uid, vals, context=None):
        res = super(sale_crm_lead, self).create(cr, uid, vals, context=context)
        lead = self.browse(cr, uid, res)
        #Issue139
        ir_model_data = self.pool.get('ir.model.data')
        if lead.user_id and lead.user_id.email:
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'crm_claim_enhance', 'email_template_crm_lead_notify')[1]
                if template_id:
                    template_obj = self.pool.get('email.template')
                    mail_id = template_obj.send_mail(cr, uid, template_id, res, True)
            except ValueError:
                template_id = False
        return res

sale_crm_lead()

class crm_claim(osv.Model):
    _inherit = 'crm.claim'

    def _parts_cost(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for claim in self.browse(cursor, user, ids, context=context):
            res[claim.id] = 0
            for pro in claim.parts_code:
                res[claim.id] += pro.standard_price;
        return res

    '''
    def _qc_manager(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for claim in self.browse(cursor, user, ids, context=context):
            res[claim.id] = 'null'
            if claim.type == 'Warranty' and claim.sale_id:
                qc_manager_ids = []
                for line in claim.sale_id.order_line:
                    if line.product_id.qc_manager:
                        qc_manager_ids.append(str(line.product_id.qc_manager.id))
                res[claim.id] = ','.join(set(qc_manager_ids))
        return res
    '''

    _columns = {
        #Issue256
        'parts_code':fields.many2many('product.product', 'claim_partproduct','claim_id','product_id',string='Parts Code'),
        'parts_cost': fields.function(
            _parts_cost,
            string='Parts Cost',
            type='float',
            #store=True
            ),
        'fixing_cost': fields.float('Fixing Cost'),
        'fixing_cost_desc': fields.text('Fixing Cost Description'),
        'reso_actions': fields.selection((
                ('partial refund','Partial Refund'), 
                ('full refund','Full Refund'), 
                ('replacement','Replacement'), 
                ('repair','Repair')),'Resolution actions'),
#        'qc_manager': fields.function(
#            _qc_manager,
#            string='QC Manager',
#            type='char',
#            size=128,
#            ),
        'warranty_id': fields.char('Warranty ID#', size=32),
        #Issue279
        'product_purchase_ids':fields.many2many('product.product', 'claim_product_purchase','claim_id','product_id',string='Product Purchase'),
        'department_ids': fields.many2many('hr.department', 'claim_department', 'claim_id', 'department_id', string='Root Responsible Department'),    #Issue 287
        'resp_ids': fields.many2many('hr.employee', 'claim_employee', 'claim_id', 'employee_id',string='Root Responsible Person'),    #Issue 287
        'pre_action': fields.text('Prevention Action'), #Issue287
        'co_action': fields.text('Correction Action'), #Issue287
        'if_final': fields.boolean('If Final Settled'),#Issue287
        'youtube_url':fields.char('YouTube URL', size=128),#Issue321
        'youtube_url_fd':fields.char('YouTube URL', size=128),#Issue321
        'youtube_url_wc':fields.char('YouTube URL', size=128),#Issue321
        }

    #Issue340
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = str(record.number) + '-' + str(record.name)
            if record.sale_id:
                name += '-' + str(record.sale_id.name)
            if record.partner_id:
                name += '-' + str(record.partner_id.name)
            res.append((record.id, name))
        return res


    def write(self, cr, uid, ids, vals, context=None):
        #Issue 287
        if ('department_ids' in vals or 'resp_ids' in vals) and not self.pool.get('ir.model.access').check_groups(cr, uid, "base.group_sale_manager"):
            raise  osv.except_osv(_('Error!'), _('The Root Responsible Person and Root Responsible Department must be modified by Sales Manager!'))

        for claim in self.browse(cr, uid, ids, context=context):
            users = []
            new_em_emails = []
            if 'resp_ids' in vals:
                old = claim.resp_ids and [d.id for d in claim.resp_ids] or []
                new = vals.get('resp_ids') and vals.get('resp_ids')[0][-1] or []
                for employee in new:
                    em = self.pool.get('hr.employee').browse(cr, uid, employee)
                    if em.user_id:
                        users.append(em.user_id.id)
                ans = set(new) - set(old)
                for employee in ans:
                    em = self.pool.get('hr.employee').browse(cr, uid, employee)
                    if em.work_email:
                        new_em_emails.append(str(em.work_email))
            else:
                for em in claim.resp_ids:
                    if em.user_id:
                        users.append(em.user_id.id)
            #_logger.info('vals ---- %s  users %s new_em_emails %s',vals,users,new_em_emails)

            if ((users and uid not in users) and (not self.pool.get('ir.model.access').check_groups(cr, uid, "base.group_sale_manager"))) and ('department_ids' in vals or 'resp_ids' in vals or 'cause' in vals):
                raise  osv.except_osv(_('Error!'), _('The Root must be modified by Root Responsible Person or Sales Manager!'))
            # The sale manager can modify department_ids,resp_ids.
            if new_em_emails:
                try:
                    ir_model_data = self.pool.get('ir.model.data')
                    template_id = ir_model_data.get_object_reference(cr, uid, 'crm_claim_enhance', 'email_template_crm_claim_responsible')[1]
                    if template_id:
                        template_obj = self.pool.get('email.template')
                        template_obj.write(cr, uid, [template_id], {'email_to': ','.join(new_em_emails)})
                        template_obj.send_mail(cr, uid, template_id, claim.id, True)
                except ValueError:
                    template_id = False

        return super(crm_claim, self).write(cr, uid, ids, vals, context=context)


    #Issue 286
    def action_create_refund_invoice(self, cr, uid, ids, context=None):
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_enhance', 'invoice_form_inh_cus')
        claim_obj = self.browse(cr, uid, ids[0])
        return {
                'name': "Create",
                'view_mode': 'form',
                'view_id': view_id,
                #'res_id': order_id,
                'view_type': 'form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                #'target': 'new',
                'domain': '[]',
                'context': {
                    "default_type": "out_refund",
                    "journal_type": "sale_refund",
                    "claim_id": ids and ids[0],
                    "partner_id": claim_obj.partner_id.id,
                    "origin": claim_obj.number +'+' + claim_obj.sale_id.name,
                    "name": claim_obj.number +'+' + claim_obj.sale_id.name,
                    },
                }

    def action_create_order(self, cr, uid, ids, context=None):
        sale_obj = self.pool.get("sale.order")
        line_obj = self.pool.get("sale.order.line")
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'view_order_form')
        for claim in self.browse(cr ,uid, ids, context=context):
            so_name = self.pool.get('ir.sequence').get(cr, uid, 'sale.order', context=context)
            order_id = sale_obj.create(cr ,uid, {
                'name': so_name,
                'partner_id': claim.partner_id.id,
                'origin': claim.name,
                'partner_invoice_id': claim.partner_id.id,
                'partner_shipping_id': claim.partner_id.id,
                'pricelist_id': claim.partner_id.property_product_pricelist and claim.partner_id.property_product_pricelist.id or False
                }, context=context)
            for product_id in claim.parts_code:
                line_vals = {
                            'order_id': order_id,
                            'name': product_id.name,
                            'product_id': product_id.id,
                            'price_unit': product_id.list_price,
                            'product_uom_qty': 1,
                            'product_uom': product_id.uom_id.id,
                            }
                line_obj.create(cr, uid, line_vals, context=context)
            #return  osv.except_osv(_('Info!'), _('%s created successfully!'%so_name))
            return {
                'name': "Create Success",
                'view_mode': 'form',
                'view_id': view_id,
                'res_id': order_id,
                'view_type': 'form',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                #'target': 'new',
                'domain': '[]',
                'context': {},
                }


    #Issue 287
    def case_close(self, cr, uid, ids, context=None):
        result =  super(crm_claim, self).case_close(cr, uid, ids, context)
        for claim in self.browse(cr ,uid, ids, context=context):
            if not claim.co_action:
                raise osv.except_osv(_('Missing Data'),_('Please Fill Customer Service Resolutions'))

            #CRM - Channel OP Team
            crm = []
            for em in self.pool.get('res.users').browse(cr, uid, uid).employee_ids:
                if em.department_id.id == 16 or (em.department_id.name and em.department_id.name.upper().startswith('CRM')):
                    crm.append(em.user_id.id)

            if uid != claim.user_id.id and not self.pool.get('ir.model.access').check_groups(cr, uid, "base.group_sale_manager") and uid not in crm:
                raise  osv.except_osv(_('Error!'), _('This claim must be comfired by Responsible or Sale Manager or Employee(CRM - Channel OP Team)!'))
                #raise  osv.except_osv(_('Error!'), _('This claim must be comfired by QC manager!'))
            #Final Settle
            if claim.if_final:
                self.write(cr, uid, [claim.id], {'stage_id':12})
        return result

    #Issue287
    def case_close_final(self, cr, uid, ids, context=None):
        for claim in self.browse(cr ,uid, ids, context=context):
            if not claim.department_ids or not claim.resp_ids or not claim.cause:
                raise  osv.except_osv(_('Error!'), _('The Root Responsible Department and Root Responsible Person and  Root Causes can not be NULL!'))
            users = []
            for em in claim.resp_ids:
                if em.user_id:
                    users.append(em.user_id.id)
            if (users and uid not in users) and not self.pool.get('ir.model.access').check_groups(cr, uid, "base.group_sale_manager"):
                raise  osv.except_osv(_('Error!'), _('This claim must be comfired by Responsible or Sale Manager!'))
            self.write(cr, uid, [claim.id], {'if_final':True})
            #Final Settle
            if claim.state == 'done':
                self.write(cr, uid, [claim.id], {'stage_id':12})
        return True

    '''
    def action_comfirm_byqc(self, cr, uid, ids, context=None):
        context = context or {}
        for claim in self.browse(cr ,uid, ids, context=context):
            if claim.qc_manager and str(uid) not in claim.qc_manager:
                raise  osv.except_osv(_('Error!'), _('You have not right to confirm this claim!'))
            else:
                context.update({"force_close":True})
                return self.case_close(cr, uid, [claim.id], context=context)
        return
    '''

    #Issue328
    def create(self, cr, uid, vals, context=None):
        res = super(crm_claim, self).create(cr, uid, vals, context=context)
        claim = self.browse(cr, uid, res)
        email_to = list(set([product.supplier_resp and product.supplier_resp.email for product in claim.product_purchase_ids] + [product.qc_manager and product.qc_manager.partner_id.email for product in claim.product_purchase_ids]))#Issue356 
        email_to = list(set(filter(lambda x: x,email_to)))
        
        if email_to:
            template = self.pool.get('ir.model.data').get_object(cr, uid, 'crm_claim_mactrends', 'email_template_claim')
            template_obj = self.pool.get('email.template')
            old_email_to = template_obj.browse(cr, uid, template.id).email_to
            template_obj.write(cr, uid, [template.id], {'email_to':','.join(email_to)})
            mail_id = template_obj.send_mail(cr, uid, template.id, claim.id, True)
            if old_email_to:
                template_obj.write(cr, uid, [template.id], {'email_to':old_email_to})
        return res

    #Issue349
    def action_create_refund_picking(self, cr, uid, ids, context=None):
        cr.execute("select id from stock_picking where sale_id in (select sale_id from crm_claim where id= %s) and type='in'"%ids[0])
        pickings = cr.fetchall()
        #_logger.info('pp------ %s',pickings)
        if pickings:
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock_enhance', 'view_picking_in_form_inh')
            result = {
                'name': "Exist!",
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'stock.picking.in',
                'res_id': pickings[0][0],
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'domain': '[]',
                'context': {
                    "type": "in",
                    "claim_id": ids and ids[0]
                    }}
            return result

        cr.execute("select id from stock_picking where sale_id in (select sale_id from crm_claim where id= %s) and type='out'"%ids[0])
        pickings = cr.fetchall()
        if pickings:
            dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_stock_return_picking_form')
            result = {
                    'name': "Create",
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'stock.return.picking',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': "new",
                    'domain': '[]',
                    'context': {
                        "type": "in",
                        "active_id":pickings[0][0],
                        "claim_id": ids and ids[0]
                        },}
            return result

crm_claim()
