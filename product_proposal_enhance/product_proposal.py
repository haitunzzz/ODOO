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


class product_proposal(osv.osv):
    _name = "product.proposal"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Product Proposal"
    _order = "name desc"
    
    _columns = {
        'name': fields.char('Name', size=16, readonly=True, required=True),
        'project_name': fields.char('Project Name', size=64, required=True),
        'product_id': fields.many2many('product.product', 'proposal_product', 'proposal_id', 'product_id', string='Product',  domain=[('type','<>','service')],states={'done': [('readonly', True)]}),
        'budget': fields.float('Budget', required=True),
        'state': fields.selection([('draft', 'New'),
                                   ('cancel', 'Cancelled'),
                                   ('invest', 'Investigation'),
                                   ('done', 'Accepted'),
                                   ], 'Status', readonly=True, select=True, required=True),
        'date': fields.date('Date', select=True, required=True),
        'expected_date': fields.date('Estimated Completion Date', select=True),
        'user_id': fields.many2one('res.users', 'Responsible', required=True, change_default=True, select=True, track_visibility='always'),
        'feature': fields.text('Improvement Requests', required=True),
        'comment_yes': fields.text('Comment - What can be achieved'),
        'comment_no': fields.text('Comment - What can not be achieved'),
    }

    _defaults = {
        'date': fields.date.context_today,
        'state': 'draft',
        'name': lambda obj, cr, uid, context: '/',
        #'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.order', context=c),
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Order Reference must be unique per Company!'),
    ]

    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'product.proposal') or '/'
        order =  super(product_proposal, self).create(cr, uid, vals, context=context)
        return order

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('user_id'):
            self.write(cr, uid, ids, {'message_follower_ids':[(4,self.pool.get('res.users').browse(cr, uid, vals['user_id']).partner_id.id)]})
        return  super(product_proposal, self).write(cr, uid, ids, vals, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state':'draft',
            'name': self.pool.get('ir.sequence').get(cr, uid, 'product.proposal'),
        })
        return super(product_proposal, self).copy(cr, uid, id, default, context)

    def tender_cancel(self, cr, uid, ids, context=None):
        #purchase_order_obj = self.pool.get('purchase.order')
        #for purchase in self.browse(cr, uid, ids, context=context):
        #    for purchase_id in purchase.purchase_ids:
        #        if str(purchase_id.state) in('draft'):
        #            purchase_order_obj.action_cancel(cr,uid,[purchase_id.id])
        return self.write(cr, uid, ids, {'state': 'cancel'})

    def tender_invest(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'invest'} ,context=context)

    def tender_reset(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'})

    def tender_done(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'done'}, context=context)

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        pass


product_proposal()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

