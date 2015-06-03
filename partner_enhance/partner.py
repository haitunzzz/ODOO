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

from openerp.osv import fields, osv
import time


class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _columns = {
        'country_id': fields.many2one('res.country', 'Country', required=True),
        'if_autopay': fields.boolean('Is Direct Debit Payment'),#Issue274
        'manufacturer': fields.boolean('Manufacturer'),#Issue294
        'lead': fields.integer('Lead Time'),#Issue294
    }


    def write(self, cr, uid, ids, vals, context=None):
        if 'lead' in vals:
            partner = self.browse(cr, uid, ids[0])
            values = {
                        'subject': "Lead Time has been modified",
                        'body': str(partner.lead) + ' -> ' + str(vals['lead']),
                        'model': self._name,
                        'record_name':partner.name,
                        'res_id': partner.id,
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'author_id':self.pool.get('res.users').browse(cr, uid, uid).partner_id.id,
                        'type': "notification",
                        }
            self.pool.get('mail.message').create(cr, uid, values, context=context)
        return super(res_partner, self).write(cr, uid, ids, vals, context=context)

    def _display_address(self, cr, uid, address, without_company=False, context=None):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''

        # get the information that will be injected into the display format
        # get the address format
        address_format = address.country_id and address.country_id.address_format or \
              "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
        address_format += "\n%(phone)s %(mobile)s"
        args = {
            'state_code': address.state_id and address.state_id.code or '',
            'state_name': address.state_id and address.state_id.name or '',
            'country_code': address.country_id and address.country_id.code or '',
            'country_name': address.country_id and address.country_id.name or '',
            'company_name': address.parent_id and address.parent_id.name or '',
            'phone': address.phone or '',
            'mobile': address.mobile or '',
        }
        for field in self._address_fields(cr, uid, context=context):
            args[field] = getattr(address, field) or ''
        if without_company:
            args['company_name'] = ''
        elif address.parent_id:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args


res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

