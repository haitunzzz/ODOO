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
    'name': 'Sale Send Email',
    'version': '1.0',
    'category': 'Sales Management',
    'sequence': 20,
    'summary': 'Send email',
    'description': """
Send Email after save
Send Email after prepay
    """,
    'author': 'Zhang Xue',
    'depends': ['sale_prepayment','email_template'],
    'data': [
        'wizard/prepay_wizard_view.xml',
        'security/ir.model.access.csv',
        'edi/sale_order_action_send_email.xml',
        'edi/so_done_email.xml',
        'edi/product_so_email.xml',
        'edi/so_auto_email.xml',
        'auto_email_view.xml',
        'sale_report.xml',
        'sale_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
