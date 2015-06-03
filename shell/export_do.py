from openerp.osv import fields, osv

import StringIO
import base64

class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    
    def _check_length(self, val, max):
        if len(val)>max:
            return val[:max]
        return val
    
    def delimeter(self, c='~', max=1):
        if not max:
            max = 1
        res = ''
        for num in range(0,max):
            res += c
        return res
    
    def _translate_line(self, cr, uid, line, linenumber=1, delimeter='~'):
        record = []
        if line.picking_id.partner_id:
            partner = line.picking_id.partner_id
            street  = (partner.street and partner.street or '') + (partner.street2 and partner.street2 or '')
            if linenumber == 1:
               record = [line.picking_id.name , line.product_id.name , line.product_id.default_code , line.product_qty , partner.name , partner.street , partner.city , partner.state_id and partner.state_id.name , partner.zip , partner.phone or partner.mobile , partner.email, line.product_id.weight , line.picking_id.note ]
            else:
               record = ['', line.product_id.name , line.product_id.default_code , line.product_qty , partner.name , partner.street , partner.city , partner.state_id and partner.state_id.name , partner.zip , partner.phone or partner.mobile, partner.email, line.product_id.weight , '']
        else:
            if linenumber == 1:
                record = [line.picking_id.name , line.product_id.name , line.product_id.default_code , line.product_qty , '', '', '', '', '', '', line.product_id.weight , line.picking_id.note ]
            else:
                record = ['', line.product_id.name , line.product_id.default_code , line.product_qty , '', '', '', '', '', '', line.product_id.weight , '']
        
        result = self.delimeter(delimeter).join([r and str(r) or '' for r in record])
        #result += self.delimeter(delimeter)
        return result
        """
        #0 M 3A Record Type
        result = 'SOL' + self.delimeter(delimeter)
        #1 M 8N Client Order Line Number
        result += str(linenumber) + self.delimeter(delimeter)
        #2 M 1 A Spare
        result += self.delimeter(delimeter)
        #3 M 30 A Product Code
        result += line.product_id.default_code or 'PRODUCT CODE' 
        result += self.delimeter(delimeter)
        #4 O 80 A Product Description
        result += line.product_id.name or '' + self.delimeter(delimeter)
        #5-9
        result += self.delimeter(delimeter, 5)
        #10
        result += str(0) + self.delimeter(delimeter)
        #11
        result += str(line.product_qty or 0) + self.delimeter(delimeter)
        #12
        result += str(line.product_uom.name or '') + self.delimeter(delimeter)
        #13-14
        result += self.delimeter(delimeter, 2)
        #15 Product Unit Standard / Recommended Price
        result += '0' + self.delimeter(delimeter)
        #16 Product Unit Discount % 
        result += '0' + self.delimeter(delimeter)
        #17 Product Unit Discount Amount 
        result += '0' + self.delimeter(delimeter)
        #18 Product Unit Price After Discount Applied 
        result += '0' + self.delimeter(delimeter)
        #19 Product Extended Price 
        result += '0' + self.delimeter(delimeter)
        #20-21
        result += self.delimeter(delimeter, 2)
        #22-27
        result += self.delimeter(delimeter, 6)
        #28-52
        result += self.delimeter(delimeter, 25)
        #53-64
        result += self.delimeter(delimeter, 12)                
        """
        
    
    def _translate_header(self, cr, uid, do, delimeter='~'):
        header = ['Order #', 'Product(s) Name(s)',  'SKU(s)',  'Qnty',   'Ship to Name',    'Ship to Street',  'Ship to City', 'Ship to State', 'Shipping Postcode', 'Contact Phone', 'Customer Email', 'WEIGHT',  'SPECIAL NOTES']
        result = self.delimeter(delimeter).join(header)
        #result += self.delimeter(delimeter)
        return result
        
        """
        #M 3A Record Type
        result = 'SOH' + self.delimeter(delimeter)
        #M 3A Record Structure and Version
        result += '1.0' + self.delimeter(delimeter)
        
        #M 128 A Sending Parties URL / Email
        #result += do.company_id.email or 'mike@mactrends.com'
        result += do.partner_id.email or '' + self.delimeter(delimeter)

        #M 35 A Order Number
        result += do.origin or '00001'
        result += self.delimeter(delimeter)
        #O 35 A Customer Reference
        result += do.partner_id.name or 'CUSTOMER REF' 
        result += self.delimeter(delimeter)
        # 1 A Spare
        result += self.delimeter(delimeter)
        #O 3 A Order Type
        result += 'ORD' + self.delimeter(delimeter)
        #O 3 A Pick Type
        result += 'SOP' + self.delimeter(delimeter)
        #O 8 D Date Required
        str_dt = str(do.min_date)
        result += str_dt[0:10].replace('-','') + self.delimeter(delimeter)
        # 1 A Spare
        result += self.delimeter(delimeter)
        # 1 A Spare
        result += self.delimeter(delimeter)
        # 1 A Spare
        result += self.delimeter(delimeter)
        #M 3A Warehouse Code   
        result += 'DEM' + self.delimeter(delimeter)
        #O 8,2 N Total BillTo Invoice Amount 
        result += '0' + self.delimeter(delimeter)
        # 1 A Spare
        result += self.delimeter(delimeter)
        # 1 A Spare
        result += self.delimeter(delimeter)
        #O 35 A Transport Co Ref
        result += self.delimeter(delimeter)
        #O 3 A Transport Service Level
        result += self.delimeter(delimeter)
        # 1 A Spare
        result += self.delimeter(delimeter)
        #O 10 A Total Units
        result += self.delimeter(delimeter)
        #20-32 1 A Spare
        result += self.delimeter(delimeter, 13)
        #33 GM 25 Client Code A Spare
        result += 'CUSTOMER' + self.delimeter(delimeter)
        #34 GM 50 A Client Contact
        result += do.partner_id.name or '' 
        result += self.delimeter(delimeter)
        #35 Client Company Name
        companyname = do.partner_id.name
        if do.partner_id.is_company:
            companyname = do.partner_id.name
        elif do.partner_id.company_id:
            companyname = do.partner_id.company_id.name
        #result += companyname + self.delimeter(delimeter)
        result += '' + self.delimeter(delimeter)
        #36 Client Address 1
        result += do.partner_id.street or '' + self.delimeter(delimeter)
        #37 Client Address 2 
        result += do.partner_id.street2 or '' 
        result += self.delimeter(delimeter)
        #38 Client City 
        result += do.partner_id.city or '' + self.delimeter(delimeter)
        #39 Client State 
        result += do.partner_id.state_id.name or '' 
        result += self.delimeter(delimeter)
        #40 Client PostCode 
        result += do.partner_id.zip or '' + self.delimeter(delimeter)
        #41 Client ISO Country Code 
        #result += do.partner_id.country_id.code or '' + self.delimeter(delimeter)
        result += self.delimeter(delimeter)
        #42 Client Country Name 
        #result += do.partner_id.country_id.name or '' + self.delimeter(delimeter)
        result += self.delimeter(delimeter)
        #43 Client UNLOCO 
        #result += do.partner_id.country_id.code or '' + self.delimeter(delimeter)
        result += self.delimeter(delimeter)
        #44 Client Phone 
        result += do.partner_id.phone or '' 
        result += self.delimeter(delimeter)
        #45 Client Email Address 
        result += do.partner_id.email or '' 
        result += self.delimeter(delimeter)
        #46-47
        result += self.delimeter(delimeter, 2)
        #48-60 M
        result += self.delimeter(delimeter, 13)
        #61-62
        result += self.delimeter(delimeter, 2)
        #63-75
        result += self.delimeter(delimeter, 13)
        #76-77
        result += self.delimeter(delimeter, 2)
        #78-90
        result += self.delimeter(delimeter, 13)
        #91-92
        result += self.delimeter(delimeter, 2)
        #93-105
        result += self.delimeter(delimeter, 13)
        #106-107
        result += self.delimeter(delimeter, 2)
        #108 Goods Handling Notes 
        result += do.note or '' + self.delimeter(delimeter)
        #109 DG Additional Handling Notes 
        result += self.delimeter(delimeter)
        #110 Delivery Instructions 
        result += self.delimeter(delimeter)        
        """
    
    def export_do(self, cr, uid, ids, context=None):

        if context is None: context = {}
        if context.get('active_ids'):
            do_ids = context.get('active_ids') or []
        if context.get('active_model') != self._name:
            context.update(active_ids=ids, active_model=self._name)
        file_data = StringIO.StringIO()
        try:
            str = self._translate_header(cr, uid, 'zhangxue', '~')
            file_data.writelines(str + '\n')
            for do in self.browse(cr, uid, do_ids, context=context):
                linenumber = 1
                for line in do.move_lines:
                    str = self._translate_line(cr, uid, line, linenumber, '~')
                    file_data.writelines(str + '\n')
                    linenumber += 1
            #writer = DoUnicodeWriter(file_data)
            
            #writer.writerows(rows)
            file_value = file_data.getvalue()
            partial_id = self.pool.get("do.csv.export").create(cr, uid, {'data': base64.encodestring(file_value)}, context=context)
        finally:
            file_data.close()
        
        return {
            'name':"Download CSV File",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'do.csv.export',
            'res_id': partial_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }
        
    def export_do1(self, cr, uid, ids, context=None):

        if context is None: context = {}
        if context.get('active_ids'):
            do_ids = context.get('active_ids') or []
        if context.get('active_model') != self._name:
            context.update(active_ids=ids, active_model=self._name)
        file_data = StringIO.StringIO()
        try:
            str = self._translate_header(cr, uid, 'zhangxue', ',')
            file_data.writelines(str + '\n')
            for do in self.browse(cr, uid, do_ids, context=context):
                linenumber = 1
                for line in do.move_lines:
                    str = self._translate_line(cr, uid, line, linenumber, ',')
                    file_data.writelines(str + '\n')
                    linenumber += 1
            #writer = DoUnicodeWriter(file_data)
            
            #writer.writerows(rows)
            file_value = file_data.getvalue()
            partial_id = self.pool.get("do.csv.export").create(cr, uid, {'data': base64.encodestring(file_value)}, context=context)
        finally:
            file_data.close()
        
        return {
            'name':"Download CSV File",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'do.csv.export',
            'res_id': partial_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }
    
stock_picking_out()
