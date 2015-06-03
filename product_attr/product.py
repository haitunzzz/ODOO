# -*- coding: utf-8 -*-
##############################################################################
# by wgwang svd.wang@gmail.com
# http://wgwang.github.com
##############################################################################
import logging
_logger = logging.getLogger(__name__)
from osv import osv, fields
from openerp.tools.translate import _

default_url = 'http://img.hxpop.com/media/default.jpg'

class product_product(osv.osv):
    def _image_url_from_attr(self, product, isize):
        pbid =  product.hx_product_brand_id.id
        pmodel = product.hx_model
        pmaterial = product.hx_material
        pcolor = product.hx_color
        if not pbid:
            return default_url
        pmodel = pmodel and pmodel.strip().lstrip('%').lstrip('$') or ''
        pmaterial = pmaterial and pmaterial.strip() or ''
        pcolor = pcolor and pcolor.strip() or ''
        url = 'http://img.hxpop.com/pimg/p%s/%d/m%s/m%s/c%s.jpg' %(isize, pbid, pmodel, pmaterial, pcolor)
        return url.lower()
    def _image_url(self, cr, uid, ids, fields, arg, context=None):
        res = {}
        for pd in self.browse(cr, uid, ids, context=context):
            res[pd.id] = self._image_url_from_attr(pd, 'l')
        return res
    def _image_url_medium(self, cr, uid, ids, fields, arg, context=None):
        res = {}
        for pd in self.browse(cr, uid, ids, context=context):
            res[pd.id] = self._image_url_from_attr(pd, 'm')
        return res
    def _image_url_small(self, cr, uid, ids, fields, arg, context=None):
        res = {}
        for pd in self.browse(cr, uid, ids, context=context):
            res[pd.id] = self._image_url_from_attr(pd, 't')
        return res

    _inherit = 'product.product'
    _columns = {
            'hx_price_cn': fields.float('China Price' ),
            'hx_price_eu': fields.float('Europe Price' ),
            'hx_price_hk': fields.float('Hongkong Price'),
            'hx_gender' : fields.selection([('general','General'),('male','Male'),('female', 'Female')], 'Gender'),
            'hx_color': fields.char('Color', size=16, select=True),
            'hx_material': fields.char('Material', size=16, select=True),
            'hx_model': fields.char('Model', size=32, select=True),
            'hx_origin': fields.many2one('res.country', 'Origin Country'),
            'hx_new_type': fields.selection([('new', 'New'), ('second_hand_new', 'Second-hand New'), ('second_hand_like_new', 'Second-hand Like New'), ('second_hand_A', 'Second-hand A'), ('second_hand_B', 'Second-hand B'), ('second_hand_C', 'Second-hand C')], 'New/Secondhand Type'),
            'hx_year_season': fields.char('Year Season', size=8),
            'hx_product_size': fields.many2one('product.size', string='Product Size'),
            'hx_product_item_ids' : fields.one2many('product.item', 'product_id', 'Product Items', help='Items of product in stock.'),
            'hx_product_brand_id' : fields.many2one('product.brand','Brand', select=True, help='Select a brand for this product'),
            'hx_product_size_type_id' : fields.many2one('product.sizetype','SizeType', select=True),
            'image_medium': fields.function(_image_url_medium, type="char", string='Medium Image'),
            'image': fields.function(_image_url, type="char", string='Medium Image'),
            'image_small': fields.function(_image_url_small, type="char", string='Medium Image'),
            }
    _sql_constraints = [ 
            ('uniq_brand_model_material_color_size', 'unique(hx_model,hx_material,hx_color,hx_product_brand_id,hx_product_size)', "The brand_model_material_color must be unique"),
            ]
    _defaults = {
            'hx_gender':'general',
            'name': 'DefaultNameForAutoGenerating'
            }
#    _order = 'name_template'

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context={}
        if not 'name' in vals or vals['name'] == 'DefaultNameForAutoGenerating':
            if 'hx_product_brand_id' in vals and vals['hx_product_brand_id']:
                brand = self.pool.get('product.brand').browse(cr, uid, vals['hx_product_brand_id'], context=context)
                if not brand:
                    raise osv.except_osv(_('Warning!'),_("Auto Generating name must have brand!"))
                vals['name'] =  brand.name 
            else:
                raise osv.except_osv(_('Warning!'),_("Auto Generating name must have brand!"))
            is_hx_new_type = ['second_hand_new','second_hand_like_new','second_hand_A','second_hand_B','second_hand_C']
            if vals['hx_new_type'] in is_hx_new_type:
                vals['hx_model'] = '%_SN ' + vals['hx_model']
            if vals['hx_model']:
                vals['hx_model'] = vals['hx_model'].strip()
                vals['name'] += ' ' + vals['hx_model']
            if vals['hx_material']:
                vals['hx_material'] = vals['hx_material'].strip()
                vals['name'] += ' ' + vals['hx_material']
            if vals['hx_color']:
                vals['hx_color'] = vals['hx_color'].strip()
                vals['name'] += ' ' + vals['hx_color']
            if vals['hx_product_size']:
                size = self.pool.get('product.size').browse(cr, uid, vals['hx_product_size'], context=context)
                if size:
                    vals['name'] += ' ' + size.name
        return super(product_product, self).create(cr, uid, vals, context)

    def get_domain(self,cr,uid,vals):
        domain = []
        hx_model = vals['hx_model']
        hx_material = vals['hx_material']
        hx_color = vals['hx_color']
        if hx_model:
            domain.append(['hx_model','=',hx_model]);
        if hx_material:
            domain.append(['hx_material','=',hx_material])
        if hx_color:
            domain.append(['hx_color','=',hx_color])
        return domain

    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context={}
        if not default:
            default = {}
        product = self.read(cr, uid, id, ['hx_model'], context=context)
        default = default.copy()
        default.update(hx_model="%s__COPY" % (product['hx_model']))
        default.update(hx_product_item_ids = False)
        return super(product_product, self).copy(cr, uid, id, default=default, context=context)
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        #_logger.info('wgwang: args: %s', args)
        if context and context.get('product_with_stock', False):
            if args[0]=='product_with_stock':
                if len(args) > 2:
                    domain = args[:]
                    domain[1] = ['sale_ok','=',1]
                    del domain[0]
                    domain.append(['id','in',args[1]])
                    product_ids = super(product_product,self).search(cr,uid,domain,context=context)
                    args[1] = product_ids
                if count:
                    return len(args[1])
                if not limit:
                    return args[1][offset:]
                return args[1][offset:offset+limit]
        return super(product_product, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

product_product()
