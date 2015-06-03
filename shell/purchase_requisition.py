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


class purchase_requisition(osv.osv):
    _inherit = "purchase.requisition"
    
    _columns = {
            'target': fields.selection((
                ('nz','New Zealand'), 
                ('au','Australia'), 
                ('uk','United Kingdom'), 
                ),'Target Market'),
            'winning':fields.integer('How many winning features do we have for this proposal?'),
            'note': fields.text('Description of Key Features and Benefits'),
            #Competitor #1
            'annualv_1':fields.integer('Annual Volume?'),
            'monthlya_1':fields.integer('Peak Season Monthly Average'),
            'off_monthlya_1':fields.integer('Off Peak Season Monthly Average'),
            'models_1': fields.char('# of Competitor Models', size=32),
            'skus_1': fields.char('Competitor Total SKUs', size=32),
            'swot_1': fields.text('Competitor SWOT Analysis'),
            #Competitor #2
            'annualv_2':fields.integer('Annual Volume?'),
            'monthlya_2':fields.integer('Peak Season Monthly Average'),
            'off_monthlya_2':fields.integer('Off Peak Season Monthly Average'),
            'models_2': fields.char('# of Competitor Models', size=32),
            'skus_2': fields.char('Competitor Total SKUs', size=32),
            'swot_2': fields.text('Competitor SWOT Analysis'),
            #Competitor #3
            'annualv_3':fields.integer('Annual Volume?'),
            'monthlya_3':fields.integer('Peak Season Monthly Average'),
            'off_monthlya_3':fields.integer('Off Peak Season Monthly Average'),
            'models_3': fields.char('# of Competitor Models', size=32),
            'skus_3': fields.char('Competitor Total SKUs', size=32),
            'swot_3': fields.text('Competitor SWOT Analysis'),
    }

    _defaults = {
            }

purchase_requisition()

class purchase_requisition_line(osv.osv):
    _inherit = "purchase.requisition.line"

    _columns = {
            'loading': fields.float('Container Loading(40FT)', digits_compute= dp.get_precision('Product Price')),
            'price_target': fields.float('Target Price(USD)', digits_compute= dp.get_precision('Product Price')),
            'price_nz': fields.float('Selling Price(NZ)', digits_compute= dp.get_precision('Product Price')),
            'price_au': fields.float('Selling Price(AU)', digits_compute= dp.get_precision('Product Price')),
            'price_uk': fields.float('Selling Price(UK)', digits_compute= dp.get_precision('Product Price')),
            'annualv': fields.float('Targeted Annual Sale Volume', digits_compute= dp.get_precision('Product Price')),
            }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

