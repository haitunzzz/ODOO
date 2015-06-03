from osv import osv, fields
import cStringIO
import base64
import time
from tools.translate import _

from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)

#Issue272
class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    
    _columns = {
        'if_csvdown': fields.boolean('If CSV Downloaded'),
    }

    _defaults = {
        'if_csvdown': False,
    }

class stock_warehouse(osv.osv):
    _inherit = "stock.warehouse"

    _columns = {
        'email' : fields.char('Email', size=32, select=True),
        'cutoff1' : fields.datetime('Automated Email Cut-Off Time #1', select=True),
        'cutoff2' : fields.datetime('Automated Email Cut-Off Time #2', select=True),
        'email_active': fields.boolean('Email Active'),
    }

    _defaults = {
        'email_active': False,
    }

    def send_int_csv(self, cr, uid, ids, context=None):
        """
        delivered int pickings(not downloaded yet) 
        send email attach csv
        """
        if context is None: context = {}
        if 'int_key' not in context:
            context.update({'int_key':'cutoff1'})
        template_pool = self.pool.get('email.template')
        mail_pool     = self.pool.get('mail.mail')
        attach_pool   = self.pool.get('ir.attachment')
        stock_pool    = self.pool.get('stock.picking')
        for warehouse in self.browse(cr, uid, ids):
            int_ids = []
            #_logger.info("zhangxue----  %s  (%s,%s,%s)",warehouse.email,warehouse.lot_input_id.id, warehouse.lot_output_id.id, warehouse.lot_stock_id.id)
            if warehouse.email and warehouse.email_active:
                cr.execute("select sm.picking_id from stock_move as sm where sm.location_id in (%s,%s,%s) \
                        and sm.picking_id in (select sp.id from stock_picking as sp where sp.if_csvdown=False \
                        and sp.state = 'done' and sp.type='internal' and sp.name not like '%s')",(warehouse.lot_input_id.id, warehouse.lot_output_id.id, warehouse.lot_stock_id.id,'%-return'))
#                int_ids = stock_pool.search(cr, uid, [('if_csvdown','=',False),('state','=','done')])
#                self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', int_ids),('location_id','in',(warehouse.lot_input_id.id, warehouse.lot_output_id.id, warehouse.lot_stock_id.id)])
                int_ids = list(set([ids and ids[0] for ids in cr.fetchall()]))

                if int_ids:
                    file_data = cStringIO.StringIO()
                    try:
                        if_header = True
                        for picking in stock_pool.browse(cr, uid, int_ids, context=context):
                            if if_header:
                                head = stock_pool._translate_header_uk(cr, uid, picking.company_id.id, ',')
                                file_data.writelines(head + '\n')
                                if_header = False

                            linenumber = 1
                            for line in picking.move_lines:
                                body_line = stock_pool._translate_line_uk(cr, uid, line, linenumber, ',')
                                file_data.writelines(body_line + '\n')
                                linenumber += 1
                        
                        report_file = base64.b64encode(file_data.getvalue())
                        report_name = 'Daily INT Report_' + time.strftime('%Y-%m-%d_%H%M') + '.csv'
                        template = self.pool.get('ir.model.data').get_object(cr, uid, 'stock_enhance', 'email_template_int_daily')
                        mail_id = template_pool.send_mail(cr, uid, template.id, warehouse.id, force_send=False)
                        attach_id = attach_pool.create(cr, uid, {'name':report_name, 'datas_fname':report_name, 'datas': report_file, 'res_model':'mail.mail', 'res_id': mail_id})
                        mail_pool.write(cr, uid, [mail_id], {'attachment_ids':[[6, 0, [attach_id]]]}, context)
                        stock_pool.write(cr, uid, int_ids, {"if_csvdown":True})
                    finally:
                        file_data.close()
                else:
                    template = self.pool.get('ir.model.data').get_object(cr, uid, 'stock_enhance', 'email_template_int_daily_null')
                    mail_id = template_pool.send_mail(cr, uid, template.id, warehouse.id, force_send=False)
            #_logger.info("zhangxue----  %s  %s",warehouse.id, context)
            next_time = datetime.strptime(eval("warehouse.%s"%context['int_key']), '%Y-%m-%d %H:%M:%S') + relativedelta(days=1)
            self.write(cr, uid, [warehouse.id], {context['int_key']: next_time})
        return True
