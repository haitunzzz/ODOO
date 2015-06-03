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
from openerp.tools.translate import _

class validate_account_move_zx(osv.osv_memory):
    _name = "validate.account.move.zx"
    _description = "Validate Account Move"
    _columns = {
    }

    def validate_moves(self, cr, uid, ids, context=None):
        obj_move = self.pool.get('account.move')
        if context is None:
            context = {}
        ids_move = []
        data = obj_move.browse(cr, uid, context['active_ids'], context=context)
        for move in data:
            if move.state == 'draft':
                ids_move.append(move.id)
        if not ids_move:
            raise osv.except_osv(_('Warning!'), _('Selected Entries does not in draft state.'))
        obj_move.button_validate(cr, uid, ids_move, context=context)
        return {'type': 'ir.actions.act_window_close'}

validate_account_move_zx()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
