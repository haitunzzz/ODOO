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

class auto_email_so(osv.osv):
    _name = "auto.email.so"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'if_sq_notify': fields.boolean('Email SQ Notification', help="Send SQ Notification Auto"),
        'template_sq': fields.many2one('email.template','SQ Template', domain=[('model', '=', 'sale.order')]),
        'if_prepay_notify': fields.boolean('Email Prepay Notification', help="Send Prepat Notification Auto"),
        'template_prepay': fields.many2one('email.template','Prepay Template', domain=[('model', '=', 'sale.order')]),
        'if_con_notify': fields.boolean('Email SO Confirmation', help="Send Confirmation Notification Auto"),
        'template_so': fields.many2one('email.template','SO Template', domain=[('model', '=', 'sale.order')]),
        'company_id': fields.many2one('res.company','Company'),
    }
    _defaults = {
            'if_sq_notify': True,
            'if_prepay_notify': True,
            'if_con_notify': True,
    }

    _sql_constraints = [
        ('company_uniq', 'unique(company_id)', 'Default Automated Email Template mast be unique per company!'),
    ]
auto_email_so()

class auto_email_pro(osv.osv):
    _name = "auto.email.pro"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'templates_sq':fields.many2many('email.template', 'products_templates_sq','pro_id','template_id',string='SQ Template', domain=[('model', '=', 'sale.order')]),
        'is_send_sq': fields.boolean('Send with SQ'),
        'templates_so':fields.many2many('email.template', 'products_templates_so','pro_id','template_id',string='SO Template', domain=[('model', '=', 'sale.order')]),
        'is_send_so': fields.boolean('Send with SO'),
        'templates_do':fields.many2many('email.template', 'products_templates_do','pro_id','template_id',string='DO Template', domain=[('model', '=', 'stock.picking.out')]),
        'is_send_do': fields.boolean('Send with DO'),
    }

auto_email_pro()

class auto_email_do(osv.osv):
    _name = "auto.email.do"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'if_notify': fields.boolean('Email DO Notification', help="Send DO Notification Auto"),
        'template_notify': fields.many2one('email.template','DO Template', domain=[('model', '=', 'stock.picking.out')]),
        'company_id': fields.many2one('res.company','Company'),
    }
    _defaults = {
            'if_notify': True,
    }

    _sql_constraints = [
        ('company_uniq', 'unique(company_id)', 'Default Automated Email Template mast be unique per company!'),
    ]

class auto_email_int(osv.osv):
    _name = "auto.email.int"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'if_notify': fields.boolean('Email INT Notification', help="Send INT Notification Auto"),
        'template_notify': fields.many2one('email.template','INT Template', intmain=[('model', '=', 'stock.picking')]),
        'company_id': fields.many2one('res.company','Company'),
    }
    _defaults = {
            'if_notify': True,
    }

    _sql_constraints = [
        ('company_uniq', 'unique(company_id)', 'Default Automated Email Template mast be unique per company!'),
    ]

class product_product(osv.osv):
    _inherit = 'product.product'
    _columns = {
        'auto_email': fields.property(
            'auto.email.pro',
            type='many2one',
            relation='auto.email.pro',
            string="Auto Email Template",
            view_load=True),
    }

class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = {
        'auto_email': fields.property(
            'auto.email.pro',
            type='many2one',
            relation='auto.email.pro',
            string="Auto Email Template",
            view_load=True),
    }


class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
#        'auto_email': fields.property(
#            'auto.email.so',
#            type='many2one',
#            relation='auto.email.so',
#            string="Auto Email Template",
#            view_load=True),
        'auto_email': fields.many2one('auto.email.so', "Auto Email Template"),
    }


