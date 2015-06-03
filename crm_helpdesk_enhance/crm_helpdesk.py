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

from openerp.addons.base_status.base_state import base_state
from openerp.addons.base_status.base_stage import base_stage
from openerp.osv import fields, osv
from openerp.tools.translate import _


class crm_helpdesk(base_state, base_stage, osv.osv):
    _inherit = 'crm.helpdesk'

    _columns = {
            'name': fields.char('Name', size=128, required=True, help='80px'),
    }

    #Issue378
    def create(self, cr, uid, vals, context=None):
        helpdesk_id = super(crm_helpdesk, self).create(cr, uid, vals, context=context)
        helpdesk_obj = self.browse(cr, uid, helpdesk_id)
        ir_model_data = self.pool.get('ir.model.data')
        template_obj = self.pool.get('email.template')
        if helpdesk_obj.partner_id.email:
            template_id = ir_model_data.get_object_reference(cr, uid, 'crm_helpdesk_enhance', 'email_template_helpdesk_create')[1]
            if template_id:
                mail_id = template_obj.send_mail(cr, uid, template_id, helpdesk_id, True)
        if helpdesk_obj.company_id.helpdesk_email:
            template_id = ir_model_data.get_object_reference(cr, uid, 'crm_helpdesk_enhance', 'email_template_helpdesk_create_com')[1]
            if template_id:
                mail_id = template_obj.send_mail(cr, uid, template_id, helpdesk_id, True)
        return helpdesk_id

    def case_close(self, cr, uid, ids, context=None):
        for helpdesk_obj in self.browse(cr, uid, ids):
            if helpdesk_obj.partner_id.email:
                ir_model_data = self.pool.get('ir.model.data')
                template_obj = self.pool.get('email.template')
                template_id = ir_model_data.get_object_reference(cr, uid, 'crm_helpdesk_enhance', 'email_template_helpdesk_close')[1]
                if template_id:
                    mail_id = template_obj.send_mail(cr, uid, template_id, helpdesk_obj.id, True)
        return super(crm_helpdesk, self).case_close(cr, uid, ids, context=context)

    def message_post(self, cr, uid, thread_id, body='', subject=None, type='notification',
                        subtype=None, parent_id=False, attachments=None, context=None,
                        content_subtype='html', **kwargs):
        result = super(crm_helpdesk, self).message_post(cr, uid, thread_id, body=body, subject=subject, type=type, subtype=subtype, parent_id=parent_id, attachments=attachments, context=context, content_subtype=content_subtype, **kwargs)
        helpdesk_obj = self.browse(cr, uid, thread_id)
        if helpdesk_obj.partner_id in helpdesk_obj.message_follower_ids:
            ir_model_data = self.pool.get('ir.model.data')
            template_obj = self.pool.get('email.template')
            template_id = ir_model_data.get_object_reference(cr, uid, 'crm_helpdesk_enhance', 'email_template_helpdesk_notification')[1]
            if template_id:
                mail_id = template_obj.send_mail(cr, uid, template_id, helpdesk_obj.id, True)
        return result

#Issue378
class res_company(osv.osv):
    _inherit = 'res.company'
    _columns = {
            'helpdesk_email': fields.char('HelpDesk Email', size=256),
    }
res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
