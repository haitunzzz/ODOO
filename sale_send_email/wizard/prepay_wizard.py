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
from openerp.osv import orm, fields, osv
import openerp.addons.decimal_precision as dp
import time
import logging
_logger = logging.getLogger(__name__)



class sale_prepayment(orm.TransientModel):
    _inherit = 'sale.prepayment'
    _name = 'sale.prepayment'

    _columns = {
        #Issue341
        'reference': fields.char('Ref #', size=64, help="Transaction reference number."),
        'name':fields.char('Memo', size=256,),
        'period_id': fields.many2one('account.period', 'Period', required=True,),
        'date':fields.date('Date', select=True, help="Effective date for accounting entries"),
        }

    _defaults={
            'date': time.strftime('%Y-%m-%d'),
            }

    def act_prepayment(self, cr, uid, ids, context=None):
        '''do the prepayment '''
        sale_obj = self.pool.get('sale.order')
        sale_id = context and context.get('active_id', False)
        sale = sale_obj.browse(cr, uid, sale_id, context=context)
        date = time.strftime('%Y-%m-%d')
        for prepay in self.browse(cr, uid, ids, context=context):
            journal = prepay.journal_id
            amount = prepay.amount
            is_prepayment = prepay.is_prepayment
            if is_prepayment is True:
                if not sale.partner_id.property_account_prepayable:
                    raise osv.except_osv(
                        'Warning',
                        "Please set this partner's payable account!")
            if amount <= 0:
                raise osv.except_osv('Warning', 'The amount must be positive!')
            #Issue341
            #ref->move.name, memo->line.name
            context.update({
                'ref': prepay.reference,
                'memo': prepay.name,
                'period_id': prepay.period_id.id,
                })
            date = prepay.date

        if sale.payment_method_id:
            sale.payment_method_id.is_prepayment = is_prepayment
            sale.payment_method_id.journal_id = journal
        sale_obj._add_payment(
            cr, uid, sale, journal,
            amount, date, context.get('ref') or sale.name, context=context)
        #write back the field is_prepayment
        sale_obj.write(cr, uid, sale_id, {'has_prepaid': True})

        #send email
        #sale_obj = self.pool.get('sale.order')
        #sale_id = context and context.get('active_id', False)
        #sale = sale_obj.browse(cr, uid, sale_id, context=context)
        prepay = self.browse(cr, uid, ids, context=context)[0]
        sale_obj.write(cr, uid, [sale_id], {'amount_paid_lst':prepay.amount})
        if sale and sale.partner_id and sale.partner_id.email and sale.state in ('draft','sent'):    #Issue 197 Issue267
            template_obj = self.pool.get('email.template')
            if sale.auto_email and sale.auto_email.if_prepay_notify:
                template_obj.send_mail(cr, uid, sale.auto_email.template_prepay.id, sale.id, True)
            '''
            if sale.company_id.id == 5:
                sale_obj.action_email_send(cr, uid, [sale_id], 'email_template_edi_sale_payment_nz', context=context)
            elif sale.company_id.id == 4:
                sale_obj.action_email_send(cr, uid, [sale_id], 'email_template_edi_sale_payment_aus', context=context)
            elif sale.company_id.id == 7:
                sale_obj.action_email_send(cr, uid, [sale_id], 'email_template_edi_sale_payment_uk', context=context)
            '''
        return True

    #Issue341
    def onchange_date(self, cr, uid, ids, date, context=None):
        if context is None:
            context ={}
        res = {'value': {}}
        #set the period of the prepay
        period_pool = self.pool.get('account.period')
        ctx = context.copy()
        pids = period_pool.find(cr, uid, date, context=ctx)
        if pids:
            res['value'].update({'period_id':pids[0]})
        return res
