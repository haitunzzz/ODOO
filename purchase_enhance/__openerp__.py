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

{
    'name': 'Purchase Enhance',
    'version': '1.0',
    'category': 'Purchase Management',
    'sequence': 32,
    'summary': 'purchase enhance',
    'description': """
purchase securty
    """,
    'author': 'Zhang Xue',
    'depends': ['purchase_landed_costs'],
    'data': [
        'security/ir.model.access.csv',
        #'security/purchase_security.xml',
        'purchase_report.xml',
        'purchase_view.xml',
        #'wizard/purchase_confirm_view.xml',
        'purchase_requisition_view.xml',
        'purchase_data.xml',
        'edi/purchase_confirm.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: