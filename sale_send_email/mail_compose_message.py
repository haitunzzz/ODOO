# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp import tools
from openerp.osv import osv, fields
import logging
_logger = logging.getLogger(__name__)

class mail_compose_message(osv.TransientModel):
    _inherit = 'mail.compose.message'

    def generate_email_for_composer(self, cr, uid, template_id, res_id, context=None):
        """ Call email_template.generate_email(), get fields relevant for
            mail.compose.message, transform email_cc and email_to into partner_ids """
        template_values = self.pool.get('email.template').generate_email(cr, uid, template_id, res_id, context=context)
        # filter template values
        fields = ['body_html', 'subject', 'email_to', 'email_recipients', 'email_cc', 'attachment_ids', 'attachments']
        values = dict((field, template_values[field]) for field in fields if template_values.get(field))
        values['body'] = values.pop('body_html', '')

        # transform email_to, email_cc into partner_ids
        partner_ids = []
        mails = tools.email_split(values.pop('email_to', '') + ' ' + values.pop('email_cc', ''))
        ctx = dict((k, v) for k, v in (context or {}).items() if not k.startswith('default_'))
        for mail in mails:
            partner_id = self.pool.get('res.partner').search(cr, uid, [('email','=', mail)], context=ctx)
            partner_ids.extend(partner_id)
            _logger.info('pppppp-----  %s   %s',mail, partner_ids)
        email_recipients = values.pop('email_recipients', '')
        if email_recipients:
            for partner_id in email_recipients.split(','):
                if partner_id:  # placeholders could generate '', 3, 2 due to some empty field values
                    partner_ids.append(int(partner_id))
        # legacy template behavior: void values do not erase existing values and the
        # related key is removed from the values dict
        if partner_ids:
            values['partner_ids'] = list(set(partner_ids))

        return values


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
