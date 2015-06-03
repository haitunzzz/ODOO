#coding: utf8
# by wgwang svd.wang@gmail.com
# http://wgwang.github.com
#

from osv import fields, osv

class ProductSizetype(osv.osv):
    _name = 'product.sizetype'
    _description = 'Product Size Type'
    _columns = {
        'name': fields.char('Product Size Type', size=8,
            help='The name of the Product Size Type.', required=True),
        'description': fields.char('Description', size=64,
            help='The description of size type.'),
    }
    _sql_constraints = [
        ('name_uniq', 'unique (name)',
            'The name of the size type must be unique !'),
    ]

ProductSizetype()


class ProductSize(osv.osv):
    _description="Product Size"
    _name = 'product.size'
    _columns = {
        'sizetype_id': fields.many2one('product.sizetype', 'Product Size Type', required=True),
        'name': fields.char('Product Size', size=8, required=True),
        'description': fields.char('Description', size=64),
    }
    _sql_constraints = [
        ('name_type_uniq', 'unique (name, sizetype_id)',
            'The name of the size with same type must be unique !'),
    ]

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if not context:
            context={}
        ids = self.search(cr, user, [('sizetype_id.name', 'ilike', name)] + args, limit=limit, context=context)
        ids += self.search(cr, user, [('name', operator, name)] + args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context)
    _order = 'sizetype_id, name'

ProductSize()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

