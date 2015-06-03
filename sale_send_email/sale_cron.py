from osv import osv, fields
import cStringIO
import base64
import time
from tools.translate import _

from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)


class res_company(osv.osv):
    _inherit = 'res.company'
    
    _columns = {
        'weekly_claim_report_sent': fields.datetime('Last Claim Report Sent On'),
        'weekly_doneso_report_sent': fields.datetime('Last Done SO Report Sent On'),
    }

    def send_open_claims_notification(self, cr, uid, ids, context=None):

        if not context:
            context = {}
        template_pool = self.pool.get('email.template')
        mail_pool     = self.pool.get('mail.mail')
        attach_pool   = self.pool.get('ir.attachment')
        user_pool     = self.pool.get('res.users')
        sale_pool    = self.pool.get('sale.order')
        inv_pool    = self.pool.get('account.invoice')

        template = self.pool.get('ir.model.data').get_object(cr, uid, 'sale_send_email', 'email_template_all_so_weekly')
        template1 = self.pool.get('ir.model.data').get_object(cr, uid, 'sale_send_email', 'email_template_refund_inv_weekly')
        
        for sobj in self.browse(cr, uid, ids):
            so_ids = sale_pool.search(cr, uid, [('company_id','=',sobj.id),('date_done', '>=', sobj.weekly_claim_report_sent)], order='id')
            if so_ids:
                buf=cStringIO.StringIO()
                headers = '"SO Name","SO Confirm Date","Product Code","Product Name","Subtotal","Cost Price","Margin","Margin%"'+ '\n'
                buf.write(headers)
                for so_obj in sale_pool.browse(cr, uid, so_ids):
                    cc = 0
                    for line in so_obj.order_line:
                        vals = []
                        if cc == 0:
                            for fld in [so_obj.name, so_obj.date_confirm, line.product_id.default_code, line.product_id.name, line.price_subtotal, line.purchase_price, line.price_subtotal-line.purchase_price, line.price_subtotal and round((line.price_subtotal-line.purchase_price)/line.price_subtotal*100, 2) or 0]:
                                vals.append( '"' + str(fld and fld or " ") + '"' )
                                cc = 1
                        else:
                            for fld in ["", "", line.product_id.default_code, line.product_id.name, line.price_subtotal, line.purchase_price, line.price_unit-line.purchase_price, line.price_subtotal and round((line.price_subtotal-line.purchase_price)/line.price_subtotal*100, 2) or 0]:
                                vals.append( '"' + str(fld and fld or " ") + '"' )
                        line = ','.join(vals) + "\n"
                        buf.write(line)
                report_file = base64.b64encode(buf.getvalue())
                report_name = 'Weekly SO Report_' + time.strftime('%Y-%m-%d_%H%M') + '.csv'
                mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, sobj.id, force_send=False)
                attach_id = attach_pool.create(cr, uid, {'name':report_name, 'datas_fname':report_name, 'datas': report_file, 'res_model':'mail.mail', 'res_id': mail_id})
                mail_pool.write(cr, uid, [mail_id], {'attachment_ids':[[6, 0, [attach_id]]]}, context)
            
            #issue 149
            inv_ids = inv_pool.search(cr, uid, [('company_id','=',sobj.id),('create_date', '>=', sobj.weekly_claim_report_sent),('type','=','out_refund')], order='id')
            if inv_ids:
                buf=cStringIO.StringIO()
                headers = '"Refund Date","Customer Name","SO Name","Product Code","Product Name","Price","Refund","Reason","Claim"'+ '\n'
                buf.write(headers)
                for inv_obj in inv_pool.browse(cr, uid, inv_ids):
                    claim_name = ""
                    sale_id = sale_pool.search(cr, uid, [('name','=',inv_obj.origin)], order='id')
                    if sale_id and sale_id[0]:
                        claim_id = self.pool.get('crm.claim').search(cr, uid, [('sale_id','=',sale_id[0])])
                        if claim_id and claim_id[0]:
                            claim_name = self.pool.get('crm.claim').browse(cr, uid, claim_id[0]).name
    
                    cc = 0 
                    for line_obj in inv_obj.invoice_line:
                        vals = []
                        price = 0
                        if sale_id and sale_id[0] and line_obj.product_id.id:
                            cr.execute("select price_unit from sale_order_line where order_id=%s and product_id=%s",(sale_id[0], line_obj.product_id.id))
                            
                            price = cr.fetchall()
                            if price and price[0]:
                                price = price[0][0]
                        if cc == 0:
                            for fld in [inv_obj.create_date, inv_obj.partner_id.name, inv_obj.origin, line_obj.product_id.default_code, line_obj.product_id.name, price, line_obj.price_unit, inv_obj.refund_reason, claim_name]: 
                                vals.append( '"' + str(fld and fld or " ") + '"' )
                                cc = 1
                        else:
                            for fld in [inv_obj.create_date, "", "", line_obj.product_id.default_code, line_obj.product_id.name, price, line_obj.price_unit, "", ""]:
                                vals.append( '"' + str(fld and fld or " ") + '"' )
                        line = ','.join(vals) + "\n"
                        buf.write(line)
                report_file = base64.b64encode(buf.getvalue())
                report_name = 'Weekly Refund SO Report_' + time.strftime('%Y-%m-%d_%H%M') + '.csv'
                mail_id = self.pool.get('email.template').send_mail(cr, uid, template1.id, sobj.id, force_send=False)
                attach_id = attach_pool.create(cr, uid, {'name':report_name, 'datas_fname':report_name, 'datas': report_file, 'res_model':'mail.mail', 'res_id': mail_id})
                mail_pool.write(cr, uid, [mail_id], {'attachment_ids':[[6, 0, [attach_id]]]}, context)
        return super(res_company, self).send_open_claims_notification(cr, uid, ids, context=context)

    #Issue371
    def send_doneso_price_notification(self, cr, uid, ids, context=None):

        if not context:
            context = {}
        template_pool = self.pool.get('email.template')
        mail_pool     = self.pool.get('mail.mail')
        attach_pool   = self.pool.get('ir.attachment')
        user_pool     = self.pool.get('res.users')
        sale_pool    = self.pool.get('sale.order')

        template = self.pool.get('ir.model.data').get_object(cr, uid, 'sale_send_email', 'email_template_doneso_price_weekly')
        email_to = [] 
        orders = []
        for sobj in self.browse(cr, uid, ids):
            so_ids = sale_pool.search(cr, uid, [('company_id','=',sobj.id),('date_done', '>=', sobj.weekly_doneso_report_sent)], order='id')
            if so_ids:
                buf=cStringIO.StringIO()
                headers = '"SO Name","Product Code","Product Name","Sale Price","Unit Price"'+ '\n'
                buf.write(headers)
                for so_obj in sale_pool.browse(cr, uid, so_ids):
                    cc = 0
                    for line in so_obj.order_line:
                        if line.product_id.list_price - line.price_unit > 0.001:
                            orders.append(so_obj)
                            vals = []
                            if line.product_id.qc_manager and line.product_id.qc_manager.email:
                                email_to.append(line.product_id.qc_manager.email)
                            if cc == 0:
                                for fld in [so_obj.name, line.product_id.default_code, line.product_id.name, line.product_id.list_price, line.price_unit]:
                                    vals.append( '"' + str(fld and fld or " ") + '"' )
                                    cc = 1
                            else:
                                for fld in ["", line.product_id.default_code, line.product_id.name, line.product_id.list_price, line.price_unit]:
                                    vals.append( '"' + str(fld and fld or " ") + '"' )
                            line = ','.join(vals) + "\n"
                            buf.write(line)

                report_file = base64.b64encode(buf.getvalue())
                report_name = 'Weekly DONE SO Report_' + time.strftime('%Y-%m-%d_%H%M') + '.csv'
                template_pool.write(cr, uid, template.id, {"email_to":','.join(list(set(email_to))), "body_html":template.body_html.replace('func_body','Sales Total:%s<br/>SO#%s'%(sum([s.amount_total for s in list(set(orders))]),','.join([s.name for s in list(set(orders))])))})
                mail_id = self.pool.get('email.template').send_mail(cr, uid, template.id, sobj.id, force_send=False)
                attach_id = attach_pool.create(cr, uid, {'name':report_name, 'datas_fname':report_name, 'datas': report_file, 'res_model':'mail.mail', 'res_id': mail_id})
                mail_pool.write(cr, uid, [mail_id], {'attachment_ids':[[6, 0, [attach_id]]]}, context)
        return True
            

res_company()

