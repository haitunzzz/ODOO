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
{
    'name' : 'Account Enhance',
    'version' : '1.0',
    'author' : 'ZhangXue',
    'category' : 'Accounting & Finance',
    'description' : """
Accounting and Financial Management.
====================================

Financial and accounting module that covers:
--------------------------------------------
    * Post account entries selected

    """,
    'depends' : ['account', 'crm_claim'],
    'data': [
        'account_data.xml',
        'security/ir.model.access.csv',
        'security/account_enhance_security.xml',
        'edi/invoice_confirm_email.xml',
        'account_view.xml',
        'account_validate_move_view.xml',
        'partner_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
