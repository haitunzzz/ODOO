########################################################
#author:zhangfan  date:2013.04.19
#author:zhangxue  date:2013.06.06
########################################################


from openerp.osv.orm import Model
import time
from datetime import datetime
from osv import osv,fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class stock_move(osv.osv):
    _inherit = 'stock.move'
    _description = 'stock add item'
    _name = 'stock.move'
        
    _columns = {
        'item_ids':fields.many2many('product.item','move_history_item_ids','move_id','items_id', 'Items',readonly=True),
        }

    def action_done(self, cr, uid, ids, context=None):
        super(stock_move,self).action_done(cr, uid, ids, context=context)
        product_item_obj = self.pool.get('product.item')
        for move in self.browse(cr, uid, ids, context=context):
            move_id = move.id
            price = move.price_unit
            pick_type = move.picking_id.type
            qty = int(move.product_qty)
            prod_id = move.product_id.id
            po_id =  move.picking_id.purchase_id.id
            sale_id = move.picking_id.sale_id.id
            pos_id =  move.picking_id.pos_id.id
            from_id = move.location_id.id
            to_id = move.location_dest_id.id
            cc = 0
            move_time = time.strftime('%Y-%m-%d %H:%M:%S')
            if qty == 0:
                if pick_type == 'in' and po_id!= False:
                    #zhangxue delete print items    
                    for item in move.item_ids:
                        if item.status == 'tmp':
                            self.pool.get('product.item').unlink(cr,uid,item.id)
                continue
            # In  --  Purchase
            if pick_type == 'in' and po_id!= False:
                po_curr = move.picking_id.purchase_id.pricelist_id.currency_id.id
                cr.execute(
                        'SELECT *'
                        'FROM product_item '
                        'WHERE stock_move_id = %s '
                        'AND purchase_order_id = %s '
                        "AND status = 'tmp' "
                        'ORDER BY id DESC',
                        (move_id,po_id))
                res1 = cr.dictfetchall()
                old_qty = len(res1)
                creat_qty = qty-old_qty
                #1 zhangxue no old 
                if old_qty == 0:
                    for i in range(0,qty):
                        #product_item_obj.create(cr,uid,{'product_id':prod_id,'price_unit':price,'purchase_order_id':po_id,'status':'on_hand','stock_location_id':to_id,'stock_move_id':move_id,'in_currency':po_curr},context=context)
                        product_item_obj.create(cr,uid,{'product_id':prod_id,'price_unit':price,'purchase_order_id':po_id,'status':'on_hand','stock_location_id':to_id,'stock_move_id':move_id,'stock_move_ids':[(4,move_id)],'in_currency':po_curr,'in_stock_date':move_time},context=context)
                    continue
                for res in res1:
                    if prod_id <> res['product_id']:
                    #2 zhangxue new product
                    #zhangxue delete print items    
                        for item in move.item_ids:
                            if item.status == 'tmp' and item.product_id.id == res['product_id']:
                                self.pool.get('product.item').unlink(cr,uid,item.id)
                        for i in range(0,qty):
                            product_item_obj.create(cr,uid,{'product_id':prod_id,'price_unit':price,'purchase_order_id':po_id,'status':'on_hand','stock_location_id':to_id,'stock_move_id':move_id,'stock_move_ids':[(4,move_id)],'in_currency':po_curr,'in_stock_date':move_time},context=context)
                        cc = 1
                        break
                if cc ==1:
                    cc=0
                    continue
                for res in res1:
                    if creat_qty <= 0 :
                    #3 zhangxue old_qty > new_qty 
                        cr.execute(
                                'UPDATE product_item '
                                "SET status = 'on_hand', "
                                'stock_move_id = %s, '
                                'price_unit = %s, '
                                'in_currency = %s, '
                                'stock_location_id = %s, '
                                'product_id = %s, '
                                'in_stock_date = %s '
                                'WHERE id = %s ',
                                (move_id,price,po_curr,to_id,prod_id,move_time,res['id']))
                        qty -= 1
                        if qty == 0:
                        #zhangxue delete print items    
                            for item in move.item_ids:
                                if creat_qty == 0:
                                    break
                                if item.status == 'tmp' and item.product_id.id == res['product_id']:
                                    self.pool.get('product.item').unlink(cr,uid,item.id)
                                    creat_qty +=1
                            break
                    else:
                        cr.execute(
                                'UPDATE product_item '
                                "SET status = 'on_hand', "
                                'stock_move_id = %s, '
                                'price_unit = %s, '
                                'in_currency = %s, '
                                'stock_location_id = %s, '
                                'product_id = %s, '
                                'in_stock_date = %s '
                                'WHERE id = %s ',
                                (move_id,price,po_curr,to_id,prod_id,move_time,res['id']))
                        qty -= 1
                        if qty == 1:
                            for i in range(0,creat_qty):
                                product_item_obj.create(cr,uid,{'product_id':prod_id,'price_unit':price,'purchase_order_id':po_id,'status':'on_hand','stock_location_id':to_id,'stock_move_id':move_id,'stock_move_ids':[(4,move_id)],'in_currency':po_curr,'in_stock_date':move_time},context=context)
                            break
            # Out  --  Purchase Return
            elif pick_type == 'out' and po_id!= False:
                cr.execute(
                        'SELECT * '
                        'FROM product_item '
                        'WHERE stock_location_id = %s '
                        'AND purchase_order_id = %s '
                        'AND product_id = %s '
                        'AND status = %s '
                        'ORDER BY id DESC ',
                        (from_id,po_id) + (prod_id,'on_hand'))
                res1 = cr.dictfetchall()
                for res in res1:
                    cr.execute(
                        'UPDATE product_item '
                        "SET status = 'return', "
                        'stock_move_id = %s, '
                        'out_stock_date = %s '
                        'WHERE id = %s ',
                        (move_id,move_time,res['id']))
                    product_item_obj.write(cr, uid, res['id'], {'stock_move_ids':[(4,move_id)]}, context=context)
                    qty -= 1
                    if qty == 0:
                        break
            # Internal
            elif pick_type == 'internal':
                cr.execute(
                        'SELECT *'
                        'FROM product_item '
                        'WHERE stock_location_id = %s '
                        'AND product_id = %s '
                        "AND status = 'on_hand' "
                        'ORDER BY id DESC',
                        (from_id,prod_id))
                res1 = cr.dictfetchall()
                for res in res1:
                    cr.execute(
                        'UPDATE product_item '
                        'SET stock_move_id = %s, '
                        'stock_location_id = %s '
                        'WHERE id = %s ',
                        (move_id,to_id,res['id']))
                    product_item_obj.write(cr, uid, res['id'], {'stock_move_ids':[(4,move_id)]}, context=context)
                    qty -= 1
                    if qty == 0:
                        break
            # Out  --  Sale
            elif pick_type == 'out' and sale_id!= False:
                so_curr = move.picking_id.sale_id.pricelist_id.currency_id.id
                cr.execute(
                        'select sum(product_qty), product_id '
                        'from stock_move '
                        'where location_id <> %s '
                        'and location_dest_id = %s '
                        'and product_id = %s '
                        "and state = 'done' "
                        'group by product_id',
                        (from_id,from_id) + (prod_id,))
                res_in = cr.dictfetchall()
                cr.execute(
                        'select sum(product_qty), product_id '
                        'from stock_move '
                        'where location_id = %s '
                        'and location_dest_id <> %s '
                        'and product_id = %s '
                        "and state = 'done' "
                        'group by product_id',
                        (from_id,from_id) + (prod_id,))
                res_out = cr.dictfetchall()
                stock_qty = res_in[0]['sum']-res_out[0]['sum'] 
                cr.execute(
                        'SELECT * '
                        'FROM product_item '
                        'WHERE stock_location_id = %s '
                        'AND product_id = %s '
                        "AND status = 'on_hand'"
                        'ORDER BY id DESC',
                        (from_id,prod_id))
                res1 = cr.dictfetchall()
                for res in res1:
                    if stock_qty <= 0:
                        cr.execute(
                                'UPDATE product_item '
                                "SET status = 'saled', "
                                'stock_move_id = %s, '
                                'price_sale = %s, '
                                'out_currency = %s, '
                                'sale_order_id = %s, '
                                'out_stock_date = %s '
                                'WHERE id = %s ',
                                (move_id,price,so_curr,sale_id,move_time,res['id']))
                        product_item_obj.write(cr, uid, res['id'], {'sale_id':[(4,sale_id)],'stock_move_ids':[(4,move_id)]}, context=context)
                        qty -= 1
                    stock_qty -= 1
                    if qty == 0:
                        break
            # Out  --  Pos
            elif pick_type == 'out' and pos_id!= False:
                pos_curr = move.picking_id.pos_id.pricelist_id.currency_id.id
                cr.execute(
                        'select sum(product_qty), product_id '
                        'from stock_move '
                        'where location_id <> %s '
                        'and location_dest_id = %s '
                        'and product_id = %s '
                        "and state = 'done' "
                        'group by product_id',
                        (from_id,from_id) + (prod_id,))
                res_in = cr.dictfetchall()
                cr.execute(
                        'select sum(product_qty), product_id '
                        'from stock_move '
                        'where location_id = %s '
                        'and location_dest_id <> %s '
                        'and product_id = %s '
                        "and state = 'done' "
                        'group by product_id',
                        (from_id,from_id) + (prod_id,))
                res_out = cr.dictfetchall()
                stock_qty = res_in[0]['sum']-res_out[0]['sum'] 
                cr.execute(
                        'SELECT *'
                        'FROM product_item '
                        'WHERE stock_location_id = %s '
                        'AND product_id = %s'
                        "AND status = 'on_hand'"
                        'ORDER BY id DESC',
                        (from_id,prod_id))
                res1 = cr.dictfetchall()
                for res in res1:
                    if stock_qty <= 0:
                        cr.execute(
                                'UPDATE product_item '
                                "SET status = 'saled',"
                                'stock_move_id = %s, '
                                'price_sale = %s, '
                                'out_currency = %s, '
                                'pos_order_id = %s, '
                                'out_stock_date = %s '
                                'WHERE id = %s ',
                                (move_id,price,pos_curr,pos_id,move_time,res['id']))
                        product_item_obj.write(cr, uid, res['id'], {'pos_id':[(4,pos_id)],'stock_move_ids':[(4,move_id)]}, context=context)
                        qty -= 1
                    stock_qty -= 1
                    if qty == 0:
                        break
            # In  --  Sale Return
            elif pick_type == 'in' and sale_id!= False:
                cr.execute(
                        'SELECT *'
                        'FROM product_item '
                        'WHERE stock_location_id = %s '
                        'AND sale_order_id = %s '
                        'AND product_id = %s '
                        "AND status = 'saled'"
                        'ORDER BY id DESC',
                        (to_id,sale_id,prod_id))
                res1 = cr.dictfetchall()
                if res1:
                    for res in res1:
                        cr.execute(
                                'UPDATE product_item '
                                "SET status = 'on_hand', "
                                "sale_order_id = NULL, "
                                'stock_move_id = %s '
                                'WHERE id = %s ',
                                (move_id,res['id']))
                        product_item_obj.write(cr, uid, res['id'], {'stock_move_ids':[(4,move_id)]}, context=context)
                        qty -= 1
                        if qty == 0:
                            break
                else:
                    cr.execute(
                        'SELECT *'
                        'FROM product_item '
                        'WHERE product_id = %s '
                        "AND status = 'saled' "
                        "AND sale_order_id is NULL "
                        'AND (stock_location_id = %s OR stock_location_id is NULL) '
                        'ORDER BY id DESC',
                        (prod_id,to_id))
                    res2 = cr.dictfetchall()
                    for res in res2:
                        cr.execute(
                        'UPDATE product_item '
                        "SET status = 'on_hand', "
                        'stock_move_id = %s, '
                        'stock_location_id = %s '
                        'WHERE id = %s ',
                        (move_id,to_id,res['id']))
                        product_item_obj.write(cr, uid, res['id'], {'stock_move_ids':[(4,move_id)]}, context=context)
                        qty -= 1
                        if qty == 0:
                            break
            # In  --  Pos Return
            elif pick_type == 'in' and pos_id!= False:
                cr.execute(
                        'SELECT * '
                        'FROM product_item '
                        'WHERE stock_location_id = %s '
                        'AND pos_order_id = %s '
                        'AND product_id = %s '
                        "AND status = 'saled'"
                        'ORDER BY id DESC',
                        (to_id,move.picking_id.pos_id.old_order_id.id,prod_id))
                res1 = cr.dictfetchall()
                if res1:
                    for res in res1:
                        product_item_obj.write(cr, uid, res['id'], {'pos_id':[(4,pos_id)],'stock_move_ids':[(4,move_id)]}, context=context)
                        cr.execute(
                                'UPDATE product_item '
                                "SET status = 'on_hand', "
                                "pos_order_id = NULL, "
                                'stock_move_id = %s '
                                'WHERE id = %s ',
                                (move_id,res['id']))
                        qty -= 1
                        if qty == 0:
                            break
                else:
                    cr.execute(
                            'SELECT *'
                            'FROM product_item '
                            'WHERE product_id = %s '
                            "AND status = 'saled' "
                            "AND pos_order_id is NULL "
                            'AND (stock_location_id = %s OR stock_location_id is NULL) '
                            'ORDER BY id DESC',
                            (prod_id,to_id))
                    res2 = cr.dictfetchall()
                    for res in res2:
                        product_item_obj.write(cr, uid, res['id'], {'pos_id':[(4,pos_id)],'stock_move_ids':[(4,move_id)]}, context=context)
                        cr.execute(
                                'UPDATE product_item '
                                "SET status = 'on_hand', "
                                'stock_move_id = %s, '
                                'stock_location_id = %s '
                                'WHERE id = %s ',
                                (move_id,to_id,res['id']))
                        qty -= 1
                        if qty == 0:
                            break
        return True 

stock_move()
            
class stock_picking_in(osv.osv):
    _inherit = "stock.picking.in"
    _name = "stock.picking.in"

    def print_item(self, cr, uid, ids, context=None):
        product_item_obj = self.pool.get('product.item')
        for pick in self.browse(cr, uid, ids, context=context):
            if not pick.purchase_id.id :
                raise osv.except_osv(_('Invalid Action!'), _('You can only print product items of Purchase Order'))
            for move in pick.move_lines:
                move_id = move.id
                price = move.price_unit
                po_curr = move.picking_id.purchase_id.pricelist_id.currency_id.id
                pick_type = move.picking_id.type
                qty = int(move.product_qty)
                prod_id = move.product_id.id
                po_id =  move.picking_id.purchase_id.id
                to_id = move.location_dest_id.id
                # In  --  Purchase   Print item
                if pick_type == 'in' and po_id!= False:
                    cr.execute(
                        'SELECT *'
                        'FROM product_item '
                        'WHERE stock_move_id = %s '
                        'AND purchase_order_id = %s '
                        'ORDER BY id DESC',
                        (move_id,po_id))
                    """
                    cr.execute(
                        'SELECT *'
                        'FROM move_history_item_ids '
                        'WHERE move_id = %s '
                        'ORDER BY id DESC',
                        (move_id,))
                    """
                    res1 = cr.dictfetchall()
                    if len(res1)>0:
                        raise osv.except_osv(_('Invalid Action!'), _('You have printed product items of Purchase Order'))

                    for i in range(0,qty):
                        product_item_obj.create(cr,uid,{'product_id':prod_id,'price_unit':price,'purchase_order_id':po_id,'status':'tmp','stock_location_id':to_id,'stock_move_id':move_id,'stock_move_ids':[(4,move_id)],'in_currency':po_curr},context=context)
                else:
                    raise osv.except_osv(_('Invalid Action!'), _('You can only print product items of Purchase Order'))
        return True 
stock_picking_in()

class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = "purchase.order"
    _description = "Purchase Order"
    _columns = {
        'item_ids': fields.one2many('product.item', 'purchase_order_id','Product Items', readonly=True),
        }
purchase_order()

class sale_order(osv.osv):
    _name = "sale.order"
    _inherit = "sale.order"
    _description = "Sale Order"
    _columns = {
        'item_ids': fields.one2many('product.item', 'sale_order_id','Product Items', readonly=True),
        #'item_id':fields.many2many('product.item','sale_history_id','sale_id','items_id', 'Items'),
        }
sale_order()

class pos_order(osv.osv):
    _name = "pos.order"
    _inherit = "pos.order"
    _description = "Pos Order"
    _columns = {
        'item_ids': fields.one2many('product.item', 'pos_order_id','Product Items', readonly=True),
        }
pos_order()
