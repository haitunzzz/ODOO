# -*- encoding: utf-8 -*-
#################################################################################
# by wgwang svd.wang@gmail.com                                                                              #
#################################################################################

from osv import osv, fields

from openerp.addons.product.product import sanitize_ean13

class product_brand(osv.osv):
    _name = 'product.brand'
    _columns = {
        'name': fields.char('Brand Name', size=64),
        'reference': fields.char('Reference', size=13, readonly=True),
        'logo': fields.binary('Logo File'),
        'headquarter': fields.many2one('res.country', 'Head Quarter'),
        'partner_id' : fields.many2one('res.partner','partner', help='Select a partner for this brand if it exist'),
        'story': fields.text('Brand Story'),
        'description': fields.text('Description'),
    }
    _defaults = {
        'reference': '0000000000000',
    }

    _sql_constraints = [ 
            ('uniq_reference', 'unique(reference)', "The reference must be unique"),
    ]   

    def create(self, cr, uid, vals, context=None):
        if not 'reference' in vals or vals['reference'] == '0000000000000':
            vals['reference'] = sanitize_ean13(self.pool.get('ir.sequence').get(cr, uid, 'product.brand'))
        return super(product_brand, self).create(cr, uid, vals, context)

    def copy(self, cr, uid, id, default={}, context=None):
        default.update({
            'reference': sanitize_ean13(self.pool.get('ir.sequence').get(cr, uid, 'product.brand')),
        })  
        return super(product_brand, self).copy(cr, uid, id, default, context)


product_brand()


