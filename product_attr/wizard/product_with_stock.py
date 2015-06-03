# -*- coding: utf-8 -*-
##############################################################################
# by wgwang(svd.wang@gmail.com)
# http://wgwang.github.com
##############################################################################

import logging
_logger = logging.getLogger(__name__)

import datetime
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _

class product_with_stock(osv.osv_memory):
    _name = "product.with.stock"
    _description = "Product With Stock"
    _columns = {
        'product_ref': fields.char('Reference', size=13),
        'category_id': fields.many2one('product.category', 'Category'),
        'product_brand_id' : fields.many2one('product.brand', 'Brand'),
        'product_model': fields.char('Model', size=32),
        'product_material': fields.char('Material', size=16),
        'product_color': fields.char('Color', size=16),
        'product_size_id' : fields.many2one('product.size', 'Size'),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse'),
        'way_get' : fields.selection([('normal', 'Normal'),('weekly', 'Weekly'),('sort_by_new', 'New Ahead(Slow)')], 'Way', required=True),
        'in_stock_start_date':fields.date('In Stock Start Date'),
        'in_stock_end_date':fields.date('In Stock End Date'),
        'befor_time':fields.date('Befor Time In Stock'),
    }
    _defaults = {
        'way_get': 'normal',
    }
    def default_get(self, cr, uid, fields, context):
        res = super(product_with_stock, self).default_get(cr, uid, fields, context=context)
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id 
        warehouse_id = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', company_id)])
        if warehouse_id:
            res.update(warehouse_id=warehouse_id[0])
        return res

    """get product_id prior to the storage of stock """
    def get_product_id_by_company_id(self,cr,uid,company_id,date):
        #1.get on hand number at this date
        end_date = time.strptime(date,'%Y-%m-%d')
        end_date = datetime.datetime(* end_date[:3])
        end_date = end_date + datetime.timedelta(days=1)
        start_date = date
        stock_warehouse = self.pool.get('stock.warehouse')
        stock_warehouse_ids = stock_warehouse.search(cr,uid,[('company_id','=',company_id)])
        stock_warehouses =  stock_warehouse.browse(cr,uid,stock_warehouse_ids)
        location_ids = []
        for s in stock_warehouses:
            location_ids.append(s.lot_stock_id.id)
        lenght = len(location_ids)
        in_sql = ''
        out_sql = ''
        cnt = 0
        if lenght <= 0:
            return
        for location_id in location_ids:
            in_sql += """
            select product_id,product_qty from stock_move where state = 'done'
            and location_dest_id = %d and location_id != %d and date < '%s'""" %(location_id,location_id,end_date)
            out_sql += """
            select product_id,product_qty from stock_move where state = 'done' 
            and location_dest_id != %d and location_id = %d and date < '%s'""" %(location_id,location_id,end_date)
            cnt += 1
            if cnt <  lenght:
                in_sql += ' union all '
                out_sql += ' union all '
        onhand_sql = """select product_id,sum(product_qty) as number from
                        (%s) as in_stock group by product_id 
                        union all
                        select product_id,sum(product_qty*-1) as number from
                        (%s) as out_stock group by product_id""" %(in_sql,out_sql)
        
        #2.get sale number after this date
        sale_sql = """
        (
        select sum(number)*-1 from
        (
        select product_id,sum(product_qty) as number from stock_move where location_dest_id = 9
        and location_id != 9 and date >= '%s' and state = 'done'  and company_id = %d  group by product_id 
        union all
        select product_id,sum((product_qty*-1)) as number from stock_move where location_id = 9
        and location_dest_id != 9 and date >= '%s' and state = 'done' and company_id = %d  group by product_id 
        ) as sale 
        where product_id = on_hand.product_id
        group by product_id
        having sum(number) >= 0
        ) as sale_number
        """ %(start_date,company_id,start_date,company_id)

        #3.get reslt sql
        sql = """select product_id,sum(number) as number,%s from (%s) as on_hand group by product_id having(sum(number)) > 0""" %(sale_sql,onhand_sql)
        result_sql = """select product_id from (%s) as result where (number+sale_number > 0 or number+sale_number is null)""" %sql
        return result_sql

    def get_view_id(self,cr,uid,view_id):
        models = self.pool.get('ir.model.data')
        result = models.get_object_reference(cr,uid,'product',view_id)
        return result and result[1] or False

    def search_products(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        p = self.browse(cr, user, ids, context=context)
        if not p:
            return
        res_user = self.pool.get('res.users').browse(cr,user,user)
        company_id = res_user.company_id
        p = p[0]
        if p.warehouse_id:
            location_id = p.warehouse_id.lot_stock_id.id
        where_clause = []
        if p.product_ref:
            where_clause.append("default_code = '%s'" %p.product_ref.strip())
        if p.product_brand_id:
            where_clause.append('hx_product_brand_id = %s' %p.product_brand_id.id)
        if p.product_model:
            where_clause.append("hx_model = '%s'" %p.product_model.strip())
        if p.product_material:
            where_clause.append("hx_material = '%s'" %p.product_material.strip())
        if p.product_color:
            where_clause.append("hx_color = '%s'" %p.product_color.strip())
        if p.product_size_id:
            where_clause.append("hx_product_size = '%s'" %p.product_size_id.id)
        if p.category_id:
            cate_left = p.category_id.parent_left
            cate_right = p.category_id.parent_right
            cate_obj = self.pool.get('product.category')
            cate_list = cate_obj.search(cr, user, [('parent_left','>',cate_left),('parent_right','<',cate_right)])
            cate_list.append(p.category_id.id)
            where_clause.append("""product_tmpl_id in (select id from  product_template where categ_id in (%s))"""%','.join(str(i) for i in cate_list))
        if p.befor_time:
                sql = self.get_product_id_by_company_id(cr,user,company_id.id,p.befor_time)
                where_clause.append("""id in (%s)""" %sql)
        if p.warehouse_id:
            where_clause.append("""id in (select product_id from chricar_stock_product_by_location where location_id = %s and name > 0.1)""" %location_id)
        else:
            where_clause.append("""id in (select distinct(product_id) from chricar_stock_product_by_location
                                    where location_id in (select lot_stock_id from stock_warehouse where company_id = %d)  and name > 0.1)""" %company_id)

        sql_cmd = """select id from product_product where %s order by id desc;""" %(' and '.join(where_clause))
        cr.execute(sql_cmd)
        #_logger.info("sql is %s",sql_cmd)
        products = [ i[0] for i in cr.fetchall()]
        if p.way_get in ['sort_by_new', 'weekly']:
            d = 30
            if p.way_get == 'weekly':
                d = 8
            d15 = datetime.date.today()-datetime.timedelta(days=d)
            d15 = d15.strftime('%Y-%m-%d')
            sql_cmd_picking = """select id from stock_picking where  date_done > '%s' and type = 'in' and state='done' and origin ~ 'PO0\d*'""" %(d15)
            if p.warehouse_id:
                sql_cmd = """select product_id from stock_move where location_dest_id = %d and picking_id in (%s) order by date desc;""" %(location_id, sql_cmd_picking)
            else:
                sql_cmd = """select product_id from stock_move where location_dest_id in (select lot_stock_id from stock_warehouse
                             where company_id = %d) and picking_id in (%s) order by date desc;""" %(company_id,sql_cmd_picking)
            cr.execute(sql_cmd)
            products_sort = []
            for i in cr.fetchall():
                i = i[0]
                if i in products:
                    products_sort.append(i)
                    products.remove(i)
            if p.way_get == 'sort_by_new':
                products_sort.extend(products)
            products = products_sort
        context.update(product_with_stock=True)
        name = ''
        if p.warehouse_id:
            name = p.warehouse_id.name
            context.update(location=location_id)
        else:
            name = 'all stock'
        res = {
            'name': _('Products Stock')+ '[%s: %d]' %(name, len(products)),
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'product.product',
            'context':context,
            'domain': ('product_with_stock', products),
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
        return res


product_with_stock()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
