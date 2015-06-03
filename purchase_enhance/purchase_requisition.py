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
import time
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, orm
import logging
_logger = logging.getLogger(__name__)
from openerp.tools.translate import _

class purchase_target(osv.osv):
    _name = "purchase.target"
    
    _columns = {
            'name': fields.char('name', size=32),
            }
purchase_target()
    

class purchase_requisition(osv.osv):
    _inherit = "purchase.requisition"
    
    def _usd_total(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for req in self.browse(cr, uid, ids):
            res[req.id] = 0
            for line in req.line_ids:
                res[req.id] += line.price_target * line.annualv
        return res

    _columns = {
            'project': fields.selection([('new','New Product Development'),('exist','Existing Product Development')],'Project Type', required=True),
            'partner_id': fields.many2one('res.partner', 'Supplier', domain=[('supplier', '=', True)]),
            'state': fields.selection([('draft','New'),('in_progress','Approved1'),('cancel','Cancelled'),('done','Approved')],
                            'Status', track_visibility='onchange', required=True),
            'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True),
            'pro_description': fields.char('Proposal Description', size=128),

            'target': fields.many2many('purchase.target','purchase_requisition_target','requisition_id','target_id','Target Market'),
            'winning':fields.integer('How many winning features do we have for this proposal?'),
            'note': fields.text('Description of Key Features and Benefits'),
            #Competitor #1
            'annualv_1':fields.float('Annual Volume?', ),
            'monthlya_1':fields.float('Peak Season Monthly Average'),
            'off_monthlya_1':fields.float('Off Peak Season Monthly Average'),
            'models_1': fields.integer('# of Competitor Models'),
            'skus_1': fields.integer('Competitor Total SKUs'),
            'swot_1': fields.text('Competitor SWOT Analysis'),
            #Competitor #2
            'annualv_2':fields.float('Annual Volume?'),
            'monthlya_2':fields.float('Peak Season Monthly Average'),
            'off_monthlya_2':fields.float('Off Peak Season Monthly Average'),
            'models_2': fields.integer('# of Competitor Models'),
            'skus_2': fields.integer('Competitor Total SKUs'),
            'swot_2': fields.text('Competitor SWOT Analysis'),
            #Competitor #3
            'annualv_3':fields.float('Annual Volume?'),
            'monthlya_3':fields.float('Peak Season Monthly Average'),
            'off_monthlya_3':fields.float('Off Peak Season Monthly Average'),
            'models_3': fields.integer('# of Competitor Models'),
            'skus_3': fields.integer('Competitor Total SKUs'),
            'swot_3': fields.text('Competitor SWOT Analysis'),
            #Issue217
            'priority': fields.selection([
                ('highest','Very High'),
                ('high','High'),
                ('normal','Normal'),
                ('low','Low'),
                ('lowest','Very Low'),
                ],'Priority'),
            'usd_total':fields.function(
                _usd_total,
                string='USD Total',
                type='float',
                digits=(16,2),
                ), #Issue 173
            'email_to': fields.many2many('res.users','purchase_requisition_users','requisition_id','user_id','Email To'),
    }

    _defaults = {
            #'company_id': 8, #Visionaer Global Trading Co., Ltd
            }

    def create(self, cr, uid, vals, context=None):
        pr = super(purchase_requisition, self).create(cr, uid, vals, context=context)
        pr_obj = self.browse(cr, uid, pr)
        if pr_obj and pr_obj.company_id.id != 8:
            raise osv.except_osv('Company Error!', 'Please only fill this form in Visionaer Global Trading Co., Ltd!')
        #Issue217
        email_to = ','.join([user.email for user in pr_obj.email_to])
        template_pool = self.pool.get('email.template')
        template = self.pool.get('ir.model.data').get_object(cr, uid, 'purchase_enhance', 'email_template_requisition_user')
        if email_to:
            template_pool.write(cr, uid, template.id, {'email_to': email_to})
            mail_id = template_pool.send_mail(cr, uid, template.id, pr_obj.id, force_send=False)
        return pr

    def tender_done_po(self, cr, uid, ids, context=None):
        for this in self.browse(cr, uid, ids, context=context):
            if this.partner_id:
                if this.line_ids:
                    self. make_purchase_order(cr, uid, [this.id], this.partner_id.id, context=context)
                else:
                    raise osv.except_osv('No Products!', 'The PR %s has not products!'%this.name)
            else:
                raise osv.except_osv('No Supplier!', 'The PR %s has not supplier!'%this.name)
        return self.write(cr, uid, ids, {'state':'done', 'date_end':time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)

    def tender_done_po_approve(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'done', 'date_end':time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)

    def tender_done_po_draft(self, cr, uid, ids, context=None):
        for this in self.browse(cr, uid, ids, context=context):
            if this.partner_id:
                if this.line_ids:
                    self. make_purchase_order(cr, uid, [this.id], this.partner_id.id, context=context)
                else:
                    raise osv.except_osv('No Products!', 'The PR %s has not products!'%this.name)
            else:
                raise osv.except_osv('No Supplier!', 'The PR %s has not supplier!'%this.name)
        return True

    def tender_delete_pro(self, cr, uid, ids, context=None):
        for this in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, [this.id], {'line_ids':[(6,0,[])]}, context=context)
        return True


purchase_requisition()

class purchase_requisition_line(osv.osv):
    _inherit = "purchase.requisition.line"

    _columns = {
            'loading': fields.integer('Container Loading(40FT)'),
            'price_target': fields.float('Target Price(USD)', digits_compute= dp.get_precision('Product Price')),
            'price_nz': fields.float('Selling Price(NZ)', digits_compute= dp.get_precision('Product Price')),
            'price_au': fields.float('Selling Price(AU)', digits_compute= dp.get_precision('Product Price')),
            'price_uk': fields.float('Selling Price(UK)', digits_compute= dp.get_precision('Product Price')),
            'annualv': fields.integer('Targeted Annual Sale Volume'),
            'name': fields.text('Description', required=True),
            'pqty': fields.integer('Promotion Qty'), #Issue362
            'pprice': fields.float('Promotion Price', digits_compute= dp.get_precision('Product Price')), #Issue362
            }

    def onchange_product_id(self, cr, uid, ids, product_id, product_uom_id, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        result =  super(purchase_requisition_line, self).onchange_product_id(cr, uid, ids, product_id, product_uom_id, context=context)
        if product_id:
            product_obj = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context)[0][1]
            result['price_target'] = product_obj.purchase_price_unit
            if product_obj.description_sale:
                result['name'] += '\n'+product_obj.description_sale
        return {'value': result}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

