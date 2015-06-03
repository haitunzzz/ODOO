# -*- encoding: utf-8 -*-
#################################################################################
# by wgwang svd.wang@gmail.com
###################################################################################
{
    'name': 'Product Attributes',
    'version': '0.1',
    'category': 'Product',
    'description': """
Product Attributes, include several prices, material, color etc.
    """,
    'author': 'wgwang',
    'website': 'http://wgwang.github.com',
    'depends': ['product', 'purchase', 'stock' ],
    'init_xml': [],
    'update_xml': [
        'product_item_view.xml',
        'product_view.xml', 
        'product_brand_view.xml',
        'product_size_view.xml',
        'product_item_sequence.xml',
        'product_brand_sequence.xml',
        'wizard/product_with_stock_view.xml',
        'security/ir.model.access.csv',
        'security/product_item_security.xml',
    ],
    'data':[
    ],
    'demo_xml': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
