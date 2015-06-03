#!/usr/bin/env python
# coding: utf8
# by zhangxue
#
from openerp.osv import fields, osv
import time
import logging
_logger = logging.getLogger(__name__)
from openerp import netsvc, tools
from openerp.tools.translate import _
from datetime import datetime


class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def _crm_claim(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        for inv in self.browse(cr, uid, ids, context=context):
            res[inv.id] = False
            cr.execute("select order_id from sale_order_invoice_rel where invoice_id=%s" % inv.id)
            sale_id = cr.fetchall()
            if sale_id and sale_id[0]:
                claim_id = self.pool.get('crm.claim').search(cr, uid, [('sale_id', '=', sale_id[0][0])])
                if claim_id and claim_id[0]:
                    res[inv.id] = True
        return res

    # Issue207
    def _if_confirm(self, cr, uid, ids, name, arg, context=None):
        res = dict.fromkeys(ids, False)
        for inv in self.browse(cr, uid, ids, context=context):
            # if inv.refund_reason in ('Change of Mind', 'Others'):
            if inv.refund_reason and inv.refund_reason.name in ('Change of Mind', 'Others'):
                res[inv.id] = True
                continue

            #resps = inv.department_ids and [d.manager_id and d.manager_id.id for d in inv.department_ids] or []
            resps = list(set([d.manager_id and d.manager_id.id for d in inv.department_ids] + [d.id for d in inv.resp_ids]))
            resps = filter(lambda x: x, resps)

            # if resps.sort() == eval('['+str(inv.resps and inv.resps or '')+'].sort()'):
            # Issue326
            #_logger.info('resps1 %s resps2 %s',resps, inv.resps)
            if cmp(sorted(resps), eval('sorted([' + str(inv.resps and inv.resps or '') + '])')) == 0:
                res[inv.id] = True
        return res

    # Issue315
    def _if_inner_partner(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for invoice_obj in self.browse(cr, uid, ids, context=context):
            res[invoice_obj.id] = False
            if invoice_obj.partner_id and invoice_obj.type == 'out_invoice':
                cr.execute("select partner_id from res_company")
                inner_partners = cr.fetchall()
                if inner_partners and invoice_obj.partner_id.id in [p[0] for p in inner_partners]:
                    res[invoice_obj.id] = True
        return res

    # Issue363
    def _if_returned(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for invoice_obj in self.browse(cr, uid, ids, context=context):
            res[invoice_obj.id] = False
            if invoice_obj.refund_picking_id and invoice_obj.refund_picking_id.state == 'done':
                #    cr.execute("select id from stock_picking where name like '%s'"%("%-"+invoice_obj.refund_picking_id.name+"-return",))
                #    returns = cr.fetchall()
                #    if returns:
                res[invoice_obj.id] = True
        return res

    _columns = {
        'if_confirmed': fields.boolean('Confirm'),
        'if_confirmed_manager': fields.boolean('Confirmed'),
        'if_payment': fields.boolean('Payment has been made'),
        #        'refund_reason': fields.selection((
        #                ('10 day money back guarantee','10 day money back guarantee'),
        #                ('Warranty Claim','Warranty Claim'),
        # ('Item Damaged / Lost during transit','Item Damaged / Lost during transit'),
        #                ('Freight Claim (Item Damaged)','Freight Claim (Item Damaged)'),
        #                ('Freight Claim (Item Lost)','Freight Claim (Item Lost)'),
        # ('Freight Damage due to own faults','Freight Damage due to own faults'), #Issue285
        #                ('Wrong item shipped','Wrong item shipped'),
        #                ('Change of Mind','Change of Mind'),
        #                ('Out of Stock','Out of Stock'),
        #                ('Customer Service Issue','Customer Service Issue'),
        #                ('Others','Others')),'Refund Reason'),
        'refund_reason': fields.many2one('account.refund.reason', string='Refund Reason'),  # Issue285
        'if_claim': fields.function(_crm_claim, type='boolean', string='If Claim',),
        'create_date': fields.datetime('Creation Date', readonly=True, select=True),
        'department_ids': fields.many2many('hr.department', 'invoice_department', 'invoice_id', 'department_id', string='Responsible Department'),  # Issue 207
        'resp_ids': fields.many2many('hr.employee', 'invoice_employee', 'invoice_id', 'employee_id', string='Responsible Person'),  # Issue 207
        'resps': fields.char(size=128, string='Responsible Persons'),
        'if_confirmed_cus': fields.function(_if_confirm, type='boolean', string='Confirm by all'),
        'if_autopay': fields.boolean('Is Direct Debit Payment'),  # Issue274
        'claim_id': fields.many2one('crm.claim', string='Claim ID'),  # Issue285
        'followup': fields.text('Follow Up Action'),  # Issue285
        'endresult': fields.text('End Result'),  # Issue285
        # Issue302
        'recovery_amount': fields.float('Recovery Amount'),
        'recovered': fields.boolean('Recovered'),
        # Issue316
        'invoice_user_id': fields.related('partner_id', 'invoice_user_id', type="many2one", relation='res.users', string='Invoice Responsible', readonly=True, help='The internal user that is in charge of confirm invoice'),
        # 'if_inner_partner': fields.boolean('Is Inter-company Sales'), #Issue315
        'if_inner_partner': fields.function(
            _if_inner_partner,
            string='Is Inter-company Sales',
            readonly=True,
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['partner_id'], 10),
            },
            type='boolean',
            help="Issue315"),
        'product_return': fields.boolean('Products Return'),  # Issue363
        # 'refund_picking_id': fields.many2one('stock.picking.out', string='Original DO', domain=[('type','=','out')]), #Issue363
        'refund_picking_id': fields.many2one('stock.picking', string='Original DO'),  # Issue363
        'if_returned': fields.function(
            _if_returned,
            string='Returned',
            readonly=True,
            type='boolean',
            help="Issue363"),
    }

    # Issue355
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        types = {
            'out_invoice': _('Invoice'),
            'in_invoice': _('Supplier Invoice'),
            'out_refund': _('Refund'),
            'in_refund': _('Supplier Refund'),
        }
        return [(r['id'], '%s %s' % (r['number'] or types[r['type']], r['origin'] and str(r['name']) + ' [' + r['origin'] + ']' or r['name'])) for r in self.read(cr, uid, ids, ['type', 'number', 'name', 'origin'], context, load='_classic_write')]

    # Issue 286
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(account_invoice, self).default_get(cr, uid, fields, context=context)

        if 'claim_id' in fields and 'claim_id' in context:
            res.update({'claim_id': context['claim_id']})
        # Issue349
        if 'partner_id' in fields and 'partner_id' in context:
            res.update({'partner_id': context['partner_id']})
        if 'origin' in fields and 'origin' in context:
            res.update({'origin': context['origin']})
        if 'name' in fields and 'name' in context:
            res.update({'name': context['name']})

        return res

    # Issue 182
    def send_conf_email(self, cr, uid, ids, context=None):
        invoice_obj = self.browse(cr, uid, ids[0])
        if invoice_obj and invoice_obj.partner_id and invoice_obj.partner_id.invoice_user_id and invoice_obj.partner_id.invoice_user_id.email:
            ir_model_data = self.pool.get('ir.model.data')
            try:
                template_id = ir_model_data.get_object_reference(cr, uid, 'account_enhance', 'email_template_edi_supplier_invoice_create')[1]
            except ValueError:
                template_id = False
            if template_id:
                template_obj = self.pool.get('email.template')
                mail_id = template_obj.send_mail(cr, uid, template_id, ids[0], True, context=context)
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        # Issue #172
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.partner_id.invoice_user_id.id != uid and not self.pool.get('ir.model.access').check_groups(cr, uid, "account.group_account_manager"):
                raise osv.except_osv('Invalid Action!', 'You have not right to confirm this invoice!')
        self.write(cr, uid, ids, {'if_confirmed': True}, context=context)

        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'account_enhance',
                                                             'email_template_edi_supplier_invoice_confirm')[1]
        except ValueError:
            template_id = False
        if template_id:
            template_obj = self.pool.get('email.template')
            template_obj.send_mail(cr, uid, template_id, ids[0], True)

        for inv in self.browse(cr, uid, ids, context=context):
            values = {
                'subject': "Invoice confirmed",
                'body': "",
                'model': self._name,
                'record_name': inv.name,
                'res_id': inv.id,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'author_id': self.pool.get('res.users').browse(cr, uid, uid).partner_id.id,
                'type': "notification",
            }
            self.pool.get('mail.message').create(cr, uid, values, context=context)

            if inv.amount_total < 2000 or inv.partner_id.if_autopay == True:
                self.write(cr, uid, [inv.id], {'if_confirmed_manager': True}, context=context)

        return True

    def action_confirm_manager(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids, context=context):
            values = {
                'subject': "Invoice confirmed by manager",
                'body': "",
                'model': self._name,
                'record_name': inv.name,
                'res_id': inv.id,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'author_id': self.pool.get('res.users').browse(cr, uid, uid).partner_id.id,
                'type': "notification",
            }
            self.pool.get('mail.message').create(cr, uid, values, context=context)

        self.write(cr, uid, ids, {'if_confirmed_manager': True}, context=context)
        return True

    def create(self, cr, uid, vals, context=None):
        invoice = super(account_invoice, self).create(cr, uid, vals, context=context)
        invoice_obj = self.browse(cr, uid, invoice)
        # issue 94
        self.send_conf_email(cr, uid, [invoice], context=context)
        # Issue274
        if invoice_obj.partner_id and invoice_obj.partner_id.if_autopay:
            self.write(cr, uid, [invoice_obj.id], {"if_autopay": True})
        return invoice

    # Issue315
    def action_create_partner_invoice(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids, context=context):
            cr.execute("select id from res_company where partner_id = %s" % inv.partner_id.id)
            partner_company_id = cr.fetchall()[0][0]
            cr.execute("select id from res_users where login like '%s' and company_id = %s limit 1" % ('admin%', partner_company_id))
            user_id = cr.fetchall()[0][0]
            #_logger.info('zhangxue----- %s  %s',partner_company_id,user_id)

            #p = self.pool.get('res.users').browse(cr, user_id, user_id).company_id.partner_id
            #p = inv.company_id.partner_id
            p = self.pool.get('res.partner').browse(cr, user_id, inv.company_id.partner_id.id)
            '''
            journal_id
            '''
            journal_obj = self.pool.get('account.journal')
#            domain = [('company_id', '=', partner_company_id),('type', '=', 'purchase'),('currency','=',p.property_account_payable.currency_id.id)]
            journal_id = journal_obj.search(cr, user_id, [('company_id', '=', partner_company_id), ('type', '=', 'purchase'), ('currency', '=', p.property_account_payable.currency_id.id)], limit=1)
            #_logger.info('zhangxue-----journal_id %s account_id %s',journal_id,p.property_account_payable.id)

            new_invoice_id = self.create(cr, user_id, {
                'partner_id': p.id,
                'account_id': p.property_account_payable.id,
                'payment_term': p.property_supplier_payment_term and p.property_supplier_payment_term.id or False,
                'fiscal_position': p.property_account_position and p.property_account_position.id or False,
                'origin': inv.name,
                'journal_id': journal_id and journal_id[0],
                'currency_id': p.property_account_payable.currency_id and p.property_account_payable.currency_id.id or p.property_account_payable.company_id.currency_id.id,
                #'type':'in_invoice',
                #'company_id':partner_company_id,
            }, context={
                'default_type': "in_invoice",
                'journal_type': "purchase",
                'type': "in_invoice",
            })
            for line in inv.invoice_line:
                self.pool.get('account.invoice.line').create(cr, user_id, {
                    'invoice_id': new_invoice_id,
                    'name': line.name or line.product_id.name,
                    'product_id': line.product_id.id,
                    'price_unit': line.price_unit,
                    'quantity': line.quantity,
                    'account_id': p.property_account_payable.id,
                })
        return new_invoice_id

    def invoice_validate(self, cr, uid, ids, context=None):
        invoice = super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
        for inv in self.browse(cr, uid, ids, context=context):
            # issue119
            if inv.type == 'in_invoice' and inv.company_id.id in (4, 5, 7) and inv.origin:
                po = self.pool.get('purchase.order').search(cr, uid, [('name', '=', inv.origin)])
                if po and po[0]:
                    related_so = self.pool.get('purchase.order').browse(cr, uid, po[0]).related_so
                    so = self.pool.get('sale.order').browse(cr, 86, int(related_so))
                    if so:
                        for invoice in so.invoice_ids:
                            wf_service = netsvc.LocalService('workflow')
                            wf_service.trg_validate(86, 'account.invoice', invoice.id, 'invoice_open', cr)
        return invoice

    def action_confirm_cus(self, cr, uid, ids, context=None):
        # Issue 207
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.type != 'out_refund':
                continue
            emps = inv.department_ids and [d.manager_id for d in inv.department_ids] or []
            emps.extend(inv.resp_ids)
            users = [emp.user_id and emp.user_id.id for emp in emps]
            if uid not in users:
                raise osv.except_osv('Invalid Action!', 'You have not right to confirm this invoice!')
            else:
                for e in self.pool.get('res.users').browse(cr, uid, uid).employee_ids:
                    if inv.resps and str(e.id) in inv.resps.split(','):
                        raise osv.except_osv('Invalid Action!', 'You have confirmed this invoice!')
                resps = ','.join([str(e.id) for e in self.pool.get('res.users').browse(cr, uid, uid).employee_ids])
                self.write(cr, uid, [inv.id], {'resps': inv.resps and inv.resps + ',' + resps or resps})
                partner = self.pool.get('res.users').browse(cr, uid, uid).partner_id
                values = {
                    'subject': "%s has confirmed to be responsible" % partner.name,
                    'body': '',
                    'model': self._name,
                    'record_name': inv.name,
                    'res_id': inv.id,
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'author_id': partner.id,
                    'type': "notification",
                }
                self.pool.get('mail.message').create(cr, uid, values, context=context)
        return True

    def write(self, cr, uid, ids, vals, context=None):
        for inv in self.browse(cr, uid, ids, context=context):
            # Issue 207
            emails = []
            if vals.get('department_ids'):
                old = inv.department_ids and [d.id for d in inv.department_ids] or []
                new = vals.get('department_ids') and vals.get('department_ids')[0][-1] or []
                ans = set(new) - set(old)
                for depart in ans:
                    manager = self.pool.get('hr.department').browse(cr, uid, depart).manager_id
                    if manager and manager.work_email:
                        emails.append(manager.work_email)
            if vals.get('resp_ids'):
                old = inv.resp_ids and [d.id for d in inv.resp_ids] or []
                new = vals.get('resp_ids') and vals.get('resp_ids')[0][-1] or []
                ans = set(new) - set(old)
                for employee in ans:
                    emp = self.pool.get('hr.employee').browse(cr, uid, employee)
                    if emp.work_email:
                        emails.append(emp.work_email)
            emails = list(set(emails))
            if emails:
                ir_model_data = self.pool.get('ir.model.data')
                try:
                    template_id = ir_model_data.get_object_reference(cr, uid, 'account_enhance',
                                                                     'email_template_edi_customer_invoice_confirm')[1]
                except ValueError:
                    template_id = False
                if template_id:
                    template_obj = self.pool.get('email.template')
                    template_obj.write(cr, 1, template_id, {'email_to': ','.join(emails)})
                    template_obj.send_mail(cr, uid, template_id, ids[0], True)

        if vals.get('if_payment'):
            for inv in self.browse(cr, uid, ids, context=context):
                values = {
                    'subject': "Payment has been made",
                    'body': '',
                    'model': self._name,
                    'record_name': inv.name,
                    'res_id': inv.id,
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'author_id': self.pool.get('res.users').browse(cr, uid, uid).partner_id.id,
                    'type': "notification",
                }
                self.pool.get('mail.message').create(cr, uid, values, context=context)
        result = super(account_invoice, self).write(cr, uid, ids, vals, context=context)
        # Issue345
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.if_confirmed and not inv.if_confirmed_manager and inv.amount_total < 2000:
                cr.execute("update account_invoice set if_confirmed_manager = True where id=%s" % inv.id)
        return result

    # issue 148
    def action_view_claim(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'crm_claim', 'crm_case_categ_claim0')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        # crm claim
        cr.execute("select order_id from sale_order_invoice_rel where invoice_id=%s" % ids[0])
        sale_id = cr.fetchall()
        if sale_id and sale_id[0]:
            res = mod_obj.get_object_reference(cr, uid, 'crm_claim', 'crm_case_claims_form_view')
            result['views'] = [(res and res[1] or False, 'form')]
            claim_id = self.pool.get('crm.claim').search(cr, uid, [('sale_id', '=', sale_id[0][0])])
            if claim_id and claim_id[0]:
                result['res_id'] = claim_id[0]
        return result

    def refund(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None, context=None):
        new_ids = []
        for invoice in self.browse(cr, uid, ids, context=context):
            invoice_data = self._prepare_refund(cr, uid, invoice,
                                                date=date,
                                                period_id=period_id,
                                                description=description,
                                                journal_id=journal_id,
                                                context=context)
            # create the new invoice
            inv_id = self.create(cr, uid, invoice_data, context=context)
            new_ids.append(inv_id)
            # zhangxue issue 166
            if invoice.origin and invoice.origin.find('SO') > 0:
                sale_obj = self.pool.get('sale.order')
                sale_id = sale_obj.search(cr, uid, [('name', '=', invoice.origin)])
                sale_obj.write(cr, uid, sale_id, {'invoice_ids': [(4, inv_id)]}, context=context)
            # zhangxue issue 166

        return new_ids

    # Issue 304
    def on_change_supplier_invoice_number(self, cr, uid, ids, supplier_invoice_number):
        #_logger.info('supplier_invoice_number--- %s',supplier_invoice_number)
        if supplier_invoice_number:
            exist = self.search(cr, uid, [('supplier_invoice_number', '=', supplier_invoice_number)])
            #_logger.info('2supplier_invoice_number--- %s',exist)
            if exist:
                return {'warning': {
                    'title': _("Warning"),
                    'message': _("This invoice number already exist, are you sure wish to continue?"),
                }
                }
        return True

    # issue 323
    def duedate_urgent(self, cr, uid, ids, context=None):
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.state == 'draft' and type == 'in_invoice' and not invoice.if_confirmed and invoice.due_date and invoice.partner_id and invoice.partner_id.invoice_user_id and invoice.partner_id.invoice_user_id.email:
                due_date = datetime.strptime(invoice.due_date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
                if (datetime.today() - due_date).days > 6:
                    ir_model_data = self.pool.get('ir.model.data')
                    try:
                        template_id = ir_model_data.get_object_reference(cr, uid, 'account_enhance', 'email_template_edi_supplier_invoice_due')[1]
                    except ValueError:
                        template_id = False
                    if template_id:
                        template_obj = self.pool.get('email.template')
                        mail_id = template_obj.send_mail(cr, uid, template_id, ids[0], True, context=context)
        return True

account_invoice()


class account_refund_reason(osv.osv):
    _name = "account.refund.reason"

    _columns = {
        'name': fields.char(size=128, string='Name', required=True),
        'active': fields.boolean('Active'),
    }

    _defaults = {
        'active': True
    }

'''
class account_move_line(osv.osv):
    _inherit = "account.move.line"

    def create(self, cr, uid, vals, context=None):
        # issue 335
        if vals.get('statement_id') and 'debit' in vals and 'credit' in vals:
            vals.update({
                'debit':vals['credit'],
                'credit':vals['debit'],
                'amount_currency':vals.get('amount_currency') and -vals['amount_currency'] or 0,
                })
        return super(account_move_line, self).create(cr, uid, vals, context=context)
'''


class account_move(osv.osv):
    _inherit = "account.move"

    def _client_order_ref(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        sale_id = []
        for move in self.browse(cr, uid, ids, context=context):
            if move.ref:
                cr.execute("select client_order_ref from sale_order where name='%s' and client_order_ref is not null" % move.ref)
                sale_id = cr.fetchall()
                #_logger.info('zx----%s--%s',move.id,sale_id)
            res[move.id] = ""
            if sale_id and sale_id[0] and sale_id[0][0]:
                res[move.id] = str(sale_id[0][0])
        return res

    _columns = {
        'client_order_ref': fields.function(_client_order_ref, type='char', size=64, string='Customer Reference'),  # Issue377
    }
