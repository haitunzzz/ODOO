#coding: utf8
# by yangjie yangjie.xt@gmail.com
import logging
_logger = logging.getLogger(__name__)

from openerp.osv import fields, osv
from openerp.tools.translate import _

class product_create_by_sizetype(osv.osv_memory):
    _name = 'product.create.by.sizetype'
    _description = 'Create Product By Size Type'
    _columns = {
            'hx_product_brand_id': fields.many2one('product.brand', 'Brand',required=True),
            'categ_id':fields.many2one('product.category','Category',required=True),
            'hx_model': fields.char('Model', size=32, select=True,required=True),
            'hx_material': fields.char('Material', size=16, select=True),
            'hx_color': fields.char('Color', size=16, select=True),
            'hx_price_cn': fields.float('China Price'),
            'hx_price_eu': fields.float('Europe Price' ),
            'hx_price_hk': fields.float('Hongkong Price'),
            'hx_year_season': fields.char('Year Season', size=8),
            'hx_product_size_type_id' : fields.many2one('product.sizetype','SizeType', select=True,required=True),
            }

    def create_products(self,cr,uid,ids,context=None):
        if context is None:
            context = {}
        lines = self.browse(cr,uid,ids,context=context)
        if not lines:
            return
        line = lines[0]

        hx_model = line.hx_model
        hx_material = line.hx_material
        hx_color = line.hx_color

        hx_product_size_type_id = line.hx_product_size_type_id.id
        size_ids = self.pool.get('product.size').search(cr,uid,[('sizetype_id','=',hx_product_size_type_id)])

        product_obj = self.pool.get('product.product')
        result_id = []
        for size_id in size_ids:
            domain = []
            if hx_model:
                domain.append(['hx_model','=',hx_model])
            if hx_material:
                domain.append(['hx_material','=',hx_material])
            if hx_color:
                domain.append(['hx_color','=',hx_color])
            size = self.pool.get('product.size').browse(cr, uid, size_id, context=context)
            domain.append(['hx_product_size.name','=',size.name])
            products = product_obj.search(cr,uid,domain)
            if len(products) == 0:
                vals = {}
                vals['hx_model'] = hx_model
                vals['hx_price_cn'] = line.hx_price_cn
                vals['hx_price_eu'] = line.hx_price_eu
                vals['hx_price_hk'] = line.hx_price_hk
                vals['hx_product_brand_id'] = line.hx_product_brand_id.id
                vals['categ_id'] = line.categ_id.id
                vals['hx_material'] = hx_material
                vals['hx_color'] = hx_color
                vals['image_medium'] = False
                vals['hx_new_type'] = 'new'
                vals['sale_ok'] = 't'
                vals['hx_product_size'] = size_id
                product_id = product_obj.create(cr,uid,vals,context)
                result_id.append(product_id)
        if len(result_id) == 0:
            raise osv.except_osv(_('Warning!'),_("All Size Have Exists in ERP"))
        context.update({'product_with_stock':True})
        return  {
                'name':_('Create Product By Size Type [%d]' %len(result_id)),
                'view_type':'form',
                'view_mode': 'kanban,tree,form',
                'res_model': 'product.product',
                'context':context,
                'domain':('product_with_stock',result_id),
                'type':'ir.actions.act_window',
                'target':'current',
        }

product_create_by_sizetype()
        
