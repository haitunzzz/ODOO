#-*- encoding: utf-8 -*-
##################################################################
#author:zhangxue  date:2013.06.06
##################################################################


{
        "name": "stock add item",
        "version": "1.0",
        "author": "zhangxue",
        "depends": ["stock","purchase"],
        'description' : """
Key Functions
------------
* if incoming shipments confirm receipt,product item automatically generated records
* Display sale records in purchase order
    """,
    "data": [
        'stock_view.xml',
        ],
    "active": False,
    "update_xml": [],
    "installable": True
    }
