# -*- encoding: utf-8 -*-
#################################################################################
# by wgwang svd.wang@gmail.com
# http://wgwang.github.com
#################################################################################
from openerp.osv.orm import Model
from openerp.osv import fields 
from openerp.addons.product.product import sanitize_ean13
import openerp.addons.decimal_precision as dp

class product_item(Model):
    _name = 'product.item'
    _columns = {
        'product_id':fields.many2one('product.product', 'Product', select=True),
        'iid':fields.char('Item id', size=13, readonly=True, select=True),
        'uuid': fields.char('UUID', size=13),
        'auuid': fields.char('Aux-UUID', size=32),
        'size': fields.many2one('product.size', string='Product Size'),
        'new_type': fields.selection([('new', 'New'), ('second_hand_new', 'Second-hand New'), ('second_hand_like_new', 'Second-hand Like New'), ('second_hand_A', 'Second-hand A'), ('second_hand_B', 'Second-hand B'), ('second_hand_C', 'Second-hand C')], 'New/Secondhand Type'),
        'status':fields.selection([('on_hand', 'item in the stock'), ('saled', 'item is sold'), ('return', 'returned to supplier'),('tmp','item printed')], 'Status'),
        'create_date': fields.datetime('Create Date' , readonly=True),
        'write_date': fields.datetime('Update Date' , readonly=True),
        'in_stock_date': fields.datetime('Purchased Date' , readonly=True),
        'out_stock_date': fields.datetime('Saled Date'),
        'purchase_order_id':fields.many2one('purchase.order', 'Purchase Order'),
        'stock_location_id': fields.many2one('stock.location', 'Stock Location'),
        'note': fields.text('Notes'),
	    'price_unit': fields.float('Purchase Price', required=True, digits_compute= dp.get_precision('Product Price')),
        'in_currency': fields.many2one('res.currency', string="Purchase in Currency"),
        'out_currency': fields.many2one('res.currency', string="Sale out Currency"),
        'sale_order_id':fields.many2one('sale.order', 'Sale Order'),
        'sale_id':fields.many2many('sale.order','sale_history_id','items_id','sale_id', 'Sale Order History'),
        'pos_order_id':fields.many2one('pos.order', 'Pos Order'),
        'pos_id':fields.many2many('pos.order','pos_history_id','items_id','pos_id', 'Pos Order History'),
        'stock_move_id':fields.many2one('stock.move', 'Stock Move'),
        'stock_move_ids':fields.many2many('stock.move','move_history_item_ids','items_id','move_id', 'Stock Move History'),
	    'price_sale': fields.float('Sales Price', digits_compute= dp.get_precision('Product Price')),
        'company_id': fields.related('stock_location_id','company_id',relation='res.company',type='many2one',string='Company',store=True,readonly=True,select=1),
    }
    _defaults = {
        'status':'on_hand',
        #'iid': lambda self,cr,uid,context: sanitize_ean13(self.pool.get('ir.sequence').get(cr, uid, 'product.item')),
        'iid': '0000000000000',
        'new_type': 'new',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'product.item', context=c),
    }
    _order = 'iid desc'
    _sql_constraints = [ 
        ('uniq_iid', 'unique(iid)', "The iid must be unique"),
    ]

    def create(self, cr, uid, vals, context=None):
        if not 'iid' in vals or vals['iid'] == '0000000000000':
            vals['iid'] = sanitize_ean13(self.pool.get('ir.sequence').get(cr, uid, 'product.item'))
        return super(product_item, self).create(cr, uid, vals, context)

    def copy(self, cr, uid, id, default={}, context=None):
        default.update({
            'iid': sanitize_ean13(self.pool.get('ir.sequence').get(cr, uid, 'product.item')),
        })  
        return super(product_item, self).copy(cr, uid, id, default, context)

product_item()
