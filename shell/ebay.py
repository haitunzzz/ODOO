
import logging
_logger = logging.getLogger(__name__)
from osv import osv, fields
from xml.dom import minidom
from datetime import datetime
from dateutil.relativedelta import relativedelta
import httplib, ConfigParser
import sys, traceback
import pooler
import ecs
import time

name_prefix = 'Ebay'

class ebay_sites(osv.osv):
    _name = 'ebay.sites'
    _columns = {
                    'name'          : fields.char('Name', size=256),
                    'site_id'       : fields.integer('Site ID'),
                    'code'          : fields.char('Code', size=64),
                    'lang'          : fields.char('Lang', size=128),
                    'country_id'    : fields.many2one('res.country','Country'),
                    'url'           : fields.char('URL', size=1024),
    }
    
ebay_sites()

class connect_ebay(osv.osv):

    def call(self, cr, uid, ids, verb, requestXml):
        assert len(ids),1
        sobj = self.browse(cr, uid, ids[0])

        httpHeaders = {
                            "X-EBAY-API-COMPATIBILITY-LEVEL": str("871"),
                            "X-EBAY-API-DEV-NAME": str(sobj.dvp_key),
                            "X-EBAY-API-APP-NAME": str(sobj.app_key),
                            "X-EBAY-API-CERT-NAME": str(sobj.cert_key),
                            "X-EBAY-API-SITEID": str(sobj.site_id.site_id),
                            "X-EBAY-API-CALL-NAME": str(verb),
                            #"X-EBAY-API-DETAIL-LEVEL" : str(0),
                            #"Content-Type": "text/xml; charset=utf-8",
                        }

        requestXml = requestXml.replace(u'{USERTOKEN}', sobj.auth_token)
        requestXml = requestXml.replace('&', '&amp;')

        connection = httplib.HTTPSConnection(sobj.url)
        requestXml = requestXml.encode('utf-8')

        connection.request("POST", sobj.path, requestXml, httpHeaders)
        response = connection.getresponse()

        if response.status != 200:
            print "Error sending request:" + response.reason
            return False
        else:
            data = response.read()
            connection.close()
            print data
            try:
                dom = minidom.parseString(data)
            except:
                return xml
            else:
                return ecs.unmarshal(dom)

    def process_Errors(self, cr, uid, Errors):
        if not isinstance(Errors, list):
            Errors = [Errors]

        err_msg = ""

        for Error in Errors: 
            err_msg += Error.ErrorClassification + "\n"
            err_msg += Error.ErrorCode + "\n"
            if hasattr(Error, 'ErrorParameters'):
                if hasattr(Error.ErrorParameters, 'Value'):
                    err_msg += Error.ErrorParameters.Value + "\n"
            err_msg += Error.LongMessage + "\n"
            err_msg += Error.SeverityCode + "\n"
            err_msg += Error.ShortMessage + "\n"
            err_msg += "\n--"
        return err_msg

    def GeteBayOfficialTime(self, cr, uid, ids):
        request = "<?xml version='1.0' encoding='utf-8'?>"+\
                      "<GeteBayOfficialTimeRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">"+\
                      "<RequesterCredentials><eBayAuthToken>{USERTOKEN}</eBayAuthToken></RequesterCredentials>" + \
                      "</GeteBayOfficialTimeRequest>"

        resp =  self.call(cr, uid, ids, "GeteBayOfficialTime", request)
        
        if resp and resp.GeteBayOfficialTimeResponse.Ack == 'Success':
            return resp.GeteBayOfficialTimeResponse.Timestamp
        else:
            return False
    
    def GetOrders(self, cr, uid, ids, date_from, date_to):
        date_from = '2014-10-01T01:25:26Z'
        request  = "<?xml version='1.0' encoding='utf-8'?>"+\
                     "<GetOrdersRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">"+\
                     "<RequesterCredentials><eBayAuthToken>{USERTOKEN}</eBayAuthToken></RequesterCredentials>" +\
                     "<ModTimeFrom>" + date_from + "</ModTimeFrom>"+\
                     "<ModTimeTo>" + date_to + "</ModTimeTo>"+\
                     "<OrderRole>Seller</OrderRole>"+\
                     "</GetOrdersRequest>"

        #_logger.debug('aaaaaa-----%s    %s'%(date_from,date_to))
        resp =  self.call(cr, uid, ids, "GetOrders", request)
        if resp and resp.GetOrdersResponse.Ack == 'Success':
            return resp.GetOrdersResponse.OrderArray
        elif resp and resp.GetOrdersResponse.Ack == 'Failure':
            self.process_Errors(cr, uid, resp.GetOrdersResponse.Errors)
            return False
        
    def SendInvoice(self, cr, uid, ids):
        request = "<SendInvoiceRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">"+\
                    "<AdjustmentAmount currencyID=\"CurrencyCodeType\"> AmountType (double) </AdjustmentAmount>"+\
                    "<CheckoutInstructions> string </CheckoutInstructions>"+\
                    "<CODCost currencyID=\"CurrencyCodeType\"> AmountType (double) </CODCost>"+\
                    "<EmailCopyToSeller> boolean </EmailCopyToSeller>"+\
                    "<InsuranceFee currencyID=\"CurrencyCodeType\"> AmountType (double) </InsuranceFee>"+\
                    "<InsuranceOption> InsuranceOptionCodeType </InsuranceOption>"+\
                    "<ItemID> ItemIDType (string) </ItemID>"+\
                    "<OrderID> OrderIDType (string) </OrderID>"+\
                    "<OrderLineItemID> string </OrderLineItemID>"+\
                    "<PaymentMethods> BuyerPaymentMethodCodeType </PaymentMethods>"+\
                    "<PayPalEmailAddress> string </PayPalEmailAddress>"+\
                    "<SKU> SKUType (string) </SKU>"+\
                    "<TransactionID> string </TransactionID>"+\
                    "</SendInvoiceRequest>"

    def AddDispute(self, cr, uid, ids, order_line_ebay_id):
        request  = "<?xml version='1.0' encoding='utf-8'?>"+\
                        "<AddDisputeRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">" +\
                            "<RequesterCredentials><eBayAuthToken>{USERTOKEN}</eBayAuthToken></RequesterCredentials>" +\
                            "<ErrorLanguage>en_US</ErrorLanguage>" +\
                            "<WarningLevel>High</WarningLevel>" +\
                            "<DisputeExplanation>BuyerPurchasingMistake</DisputeExplanation>" +\
                            "<DisputeReason>TransactionMutuallyCanceled</DisputeReason>" +\
                            "<OrderLineItemID>" + order_line_ebay_id +"</OrderLineItemID>" +\
                        "</AddDisputeRequest>"
                            #"<ItemID> ItemIDType (string) </ItemID>" +\
                            #"<TransactionID> string </TransactionID>" +\

        resp =  self.call(cr, uid, ids, "AddDisputeRequest", request)
        if resp and resp.AddDisputeResponse.Ack == 'Success':
            return resp.AddDisputeResponse
        elif resp and resp.AddDisputeResponse.Ack == 'Failure':
            self.process_Errors(cr, uid, resp.AddDisputeResponse.Errors)
            return False
    
    def CompleteSale(self, cr, uid, ids, order_line_ebay_id, params):
        request = "<?xml version=\"1.0\" encoding=\"utf-8\"?>" +\
                    "<CompleteSaleRequest xmlns=\"urn:ebay:apis:eBLBaseComponents\">" +\
                        "<RequesterCredentials><eBayAuthToken>{USERTOKEN}</eBayAuthToken></RequesterCredentials>" +\
                        "<ErrorLanguage>en_US</ErrorLanguage>" +\
                        "<WarningLevel>High</WarningLevel>" +\
                        "<OrderLineItemID>" + order_line_ebay_id +"</OrderLineItemID>"

        if params.get('feedback'):
            request += "<FeedbackInfo>"
            request +=   "<CommentText>" + params['feedback']['comment'] + "</CommentText>"
            request +=   "<CommentType>" + params['feedback']['feedback'] + "</CommentType>"
            request +=   "<TargetUser>"  + params['feedback']['user'] + "</TargetUser>"
            request += "</FeedbackInfo>"
        
#         if params.get("paid"):
#             request += "<Paid>true</Paid>"
        
#         if params.get("shipment"):
#             request += "<Shipment><Notes>Shipped USPS Media</Notes></Shipment>"
#             request += "<Shipped>true</Shipped>"
            
        request += "</CompleteSaleRequest>"

        resp =  self.call(cr, uid, ids, "CompleteSaleRequest", request)
        if resp and resp.CompleteSaleResponse.Ack == 'Success':
            return resp.CompleteSaleResponse
        elif resp and resp.CompleteSaleResponse.Ack == 'Failure':
            self.process_Errors(cr, uid, resp.CompleteSaleResponse.Errors)
            return False
            
    _name = 'connect.ebay'
    _columns = {
                    'name' : fields.char('KeySet Name', size=64, required="1"),
                    'url'  : fields.char('Server URL', size=256, readonly=True, states={'draft':[('readonly',False)]}),
                    'path'  : fields.char('API PATH', size=256, readonly=True, states={'draft':[('readonly',False)]}),
                    'auth_token': fields.text('Ebay auth token', help="token key used in Ebay web service request", readonly=True, states={'draft':[('readonly',False)]}),
                    'dvp_key': fields.char('Developer key', size=64, help='Ebay developper key', readonly=True, states={'draft':[('readonly',False)]}),
                    'app_key': fields.char('Application key', size=64, help='Ebay application key', readonly=True, states={'draft':[('readonly',False)]}),
                    'cert_key': fields.char('Certificate key.', size=64, help='Ebay certificate key', readonly=True, states={'draft':[('readonly',False)]}),
                    'site_id' : fields.many2one('ebay.sites', string="Ebay Site", readonly=True, states={'draft':[('readonly',False)]}),
                    
                    
    
                    'state': fields.selection([('draft','Draft'),('connected','Connected'),('error','Error in Connection')], 'State', readonly=True),
                    'shop_id': fields.many2one('sale.shop','Shop', readonly=True, states={'draft':[('readonly',False)]}),
                    'user_id': fields.many2one('res.users', 'Salesman', readonly=True, states={'draft':[('readonly',False)]}),
                    
                    'payment_method_ids': fields.one2many('ebay.payment.method', 'ebay_id', 'Payment Method'),
                    
                    'start_from': fields.date('Start First Import From', readonly=True, states={'draft':[('readonly',False)]})                
                }
    _defaults = {
                    'state'   : lambda *a: 'draft',
                    'url'     : lambda *a: 'api.ebay.com',
                    'path'    : lambda *a: '/ws/api.dll',
    }
    
    def reset(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'draft'})
    
    def test_connection(self, cr, uid, ids, context=None):
        
        sobj = self.browse(cr, uid, ids[0])
        
        companies = []
        
        companies.append(sobj.user_id.company_id.id)
        companies.append(sobj.shop_id.company_id.id)
        
        companies = list(set(companies))
        
        if len(companies) > 1:
            raise osv.except_osv('Company Configuration', "Please make sure that Company are Same, \n User's Company: %s \n Shop's Company: %s" %(sobj.user_id.company_id.name, sobj.shop_id.company_id.name))
        
        if not sobj.shop_id.pricelist_id:
            raise osv.except_osv('Error', 'Please select Price List in Shop: ' + sobj.shop_id.name)
        
        if self.GeteBayOfficialTime(cr, uid, ids):
            return self.write(cr, uid, ids, {'state':'connected'})
        else:
            return self.write(cr, uid, ids, {'state':'error'})

    def import_orders_all(self, cr, uid, ids=[], context=None):
        all_ids = self.search(cr, uid, [('state','=','connected')])
        
        for id in all_ids:
            self.import_orders(cr, uid, [id], context)
        
        return True

        
    def import_orders(self, cr, uid, ids=[], context=None):
        order_pool   = self.pool.get('sale.order')
        prod_pool    = self.pool.get('product.product')
        line_pool    = self.pool.get('sale.order.line')
        partner_pool = self.pool.get('res.partner')
        
        eobj = self.browse(cr, uid, ids[0])
        shop = eobj.shop_id
        user = eobj.user_id
        
        payment_methods = {}

        for pm in eobj.payment_method_ids:
            payment_methods[pm.name.lower()] = pm.payment_method_id
        
        today = datetime.now() - relativedelta(minutes=5)
        next_date = datetime.strptime(eobj.start_from + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        last_update_date = False
        
        while (next_date <= today):
            cr.execute('select max(ebay_last_update) as ebay_last_update from sale_order WHERE ebay_config_id=' + str(eobj.id));
            resp = cr.dictfetchone()
            if resp['ebay_last_update'] and last_update_date != resp['ebay_last_update']:
                last_update_date = resp['ebay_last_update']
                next_date   = datetime.strptime(resp['ebay_last_update'], '%Y-%m-%d %H:%M:%S') + relativedelta(seconds=1)

            next_date_7 = next_date + relativedelta(days=30)
            
            if next_date_7 > datetime.utcnow():
                next_date_7 = datetime.utcnow() - relativedelta(minutes=5)
        
            resp = self.GetOrders(cr, user.id, ids, next_date.strftime('%Y-%m-%dT%H:%M:%SZ'), next_date_7.strftime('%Y-%m-%dT%H:%M:%SZ'))            
            next_date = next_date_7
            
            if resp:
                orders = resp.Order
                if not isinstance(orders, list):
                    orders = [orders]
                
                for order in orders:
                    if not hasattr(order.ShippingAddress, 'AddressID'):
                        continue

                    if isinstance(order.TransactionArray.Transaction, list):
                        tran = order.TransactionArray.Transaction[0]
                    else:
                        tran = order.TransactionArray.Transaction

                    partner_id    = self.get_shipping_address(cr, user.id, ids, order.ShippingAddress, {'shop_id':shop.id, 'email':tran.Buyer.Email, 'ebay_userid':order.BuyerUserID, 'country_id':eobj.site_id.country_id.id}) 
                    
                    transaction = order.TransactionArray.Transaction
                    if isinstance(transaction, list):
                        transaction = transaction[-1]
                    
                    order_vals = {
                                    'ebay_id'             : order.OrderID,
                                    'ebay_order_status'   : order.OrderStatus,
                                    'ebay_payment_method' : order.CheckoutStatus.PaymentMethod,
                                    'ebay_amount_paid'    : order.AmountPaid,
                                    'ebay_order_total'    : order.Total,
                                    'order_total'         : order.Total,
                                    
                                    'ebay_order_time'        : order.CreatedTime,
                                    'date_time'              : order.CreatedTime,
                                    'ebay_invoice_sent_time' : hasattr(transaction, 'InvoiceSentTime') and transaction.InvoiceSentTime or False,
                                    'ebay_paid_time'         : hasattr(order, 'PaidTime') and order.PaidTime or False,
                                    'ebay_shipped_time'      : hasattr(order, 'ShippedTime') and order.ShippedTime or False,
                                    'ebay_last_update'       : order.CheckoutStatus.LastModifiedTime,
                                  
                                    'date_order'          : order.CreatedTime,
                                    'client_order_ref'    : order.BuyerUserID + '-' +name_prefix + order.OrderID,
                                    'shop_id'             : shop.id,
                                    'company_id'          : shop.company_id.id,
                                    'pricelist_id'        : shop.pricelist_id and shop.pricelist_id.id or False,

                                    'partner_id'          : partner_id,
                                    'partner_invoice_id'  : partner_id,
                                    'partner_shipping_id' : partner_id,
                                    'ebay_config_id'      : eobj.id,
                                    
                                    'user_id'             : eobj.user_id and eobj.user_id.id or False
                              }
                    
                    
                    if order_vals['ebay_payment_method'].lower() in payment_methods:
                        payment_method =  payment_methods[order_vals['ebay_payment_method'].lower()]
                        order_vals['payment_method_id']   = payment_method.id
                        
                        if payment_method.workflow_process_id:
                            order_vals['workflow_process_id'] = payment_method.workflow_process_id.id
                        
                        journal = payment_method.journal_id and payment_method.journal_id or False 
                    else:
                        journal = False
                        
                    #_logger.debug('aaaa  email----%s'%tran.Buyer.Email) 
                    order_ids = order_pool.search(cr, user.id, [('ebay_id','=',order_vals['ebay_id'])])
                    if order_ids:
                        order_id = order_ids[0]
                        #Issue 224
                        order_obj = order_pool.browse(cr, user.id, order_id, context=context)
                        #Issue254
                        if order_obj.state != 'draft' or order_obj.if_validated:
                            continue
                        order_pool.write(cr, user.id, [order_id], order_vals)
                    else:
                        order_id = order_pool.create(cr, user.id, order_vals)
 
                    if not isinstance(order.TransactionArray.Transaction, list):
                        transaction_list = [order.TransactionArray.Transaction]
                    else:
                        transaction_list = order.TransactionArray.Transaction
 
                    partner = partner_pool.browse(cr, user.id, partner_id)
                    fiscal_position = partner.property_account_position and partner.property_account_position.id or False
                    fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, user.id, fiscal_position) or False
                         
                    for transaction in transaction_list:
                        prod_ids = prod_pool.search(cr, user.id, [('default_code','=',transaction.Item.SKU)])
                        #Issue #146 by zhangxue
                        if not prod_ids:
                            try:
                                prod_ids = prod_pool.search(cr, user.id, [('default_code','=',transaction.Variation.SKU)])
                                #_logger.debug('Item.SKU(%s) & Variation.SKU(%s) ---------> prod_ids(%s)',transaction.Item.SKU, transaction.Variation.SKU, prod_ids)
                            except:
                                #_logger.debug('Item.SKU(%s) & Variation.SKU ---------> NO prod_ids',transaction.Item.SKU)
 
                        line_vals = {
                                        'order_id'        : order_id,
                                        'product_id'      : prod_ids and prod_ids[0] or False,
                                        'name'            : transaction.Item.Title,
                                        'product_uom_qty' : transaction.QuantityPurchased,
                                        'price_unit'      : transaction.TransactionPrice,
                                        'ebay_id'         : transaction.OrderLineItemID
                         }
 
                        if prod_ids:
                            product_obj = prod_pool.browse(cr, user.id, prod_ids[0])
                            line_vals['tax_id'] = [[6, 0, self.pool.get('account.fiscal.position').map_tax(cr, user.id, fpos, product_obj.taxes_id)]]
                         
                        line_exist = line_pool.search(cr, user.id, [('ebay_id','=',line_vals['ebay_id']),('order_id','=',order_id)])
                        if line_exist:
                            line_pool.write(cr, user.id, line_exist, line_vals)
                        else:
                            line_pool.create(cr, user.id, line_vals)
                    
                    if hasattr(order, 'ShippingServiceSelected'):
                        if hasattr(order.ShippingServiceSelected, 'ShippingServiceCost'):
                            ship_amount = order.ShippingServiceSelected.ShippingServiceCost
                            ship_service = order.ShippingServiceSelected.ShippingService
                            line_vals = {
                                            'order_id'        : order_id,
                                            'name'            : ship_service,
                                            'product_uom_qty' : 1,
                                            'price_unit'      : ship_amount,
                                            'ebay_id'         : order.OrderID + '_shipping'
                             }
                            
                            ship_prod_ids = prod_pool.search(cr, user.id, [('default_code','=','SHIP')])
                            if ship_prod_ids:
                                line_vals['product_id'] = ship_prod_ids and ship_prod_ids[0] or False
                                ship_product_obj = prod_pool.browse(cr, user.id, ship_prod_ids[0])
                                line_vals['tax_id'] = [[6, 0, self.pool.get('account.fiscal.position').map_tax(cr, user.id, fpos, ship_product_obj.taxes_id)]]
                            
                            line_exist = line_pool.search(cr, user.id, [('ebay_id','=',line_vals['ebay_id']),('order_id','=',order_id)])
                            if line_exist:
                                line_pool.write(cr, user.id, line_exist, line_vals)
                            else:
                                line_pool.create(cr, user.id, line_vals)
                    
                    #Make PAYMENT 
                    sale_order = order_pool.browse(cr, user.id, order_id)
                    
                    if journal and float(order.AmountPaid) > 0.1 and float(order.AmountPaid) > sale_order.amount_paid:
                        order_pool._add_payment(cr, user.id, sale_order, journal, float(order.AmountPaid), (hasattr(order, 'PaidTime') and order.PaidTime or order.CheckoutStatus.LastModifiedTime ), sale_order.name)
                        order_pool.write(cr, user.id, order_id, {'has_prepaid': True})
                    
                    cr.commit()
    
    
    def get_shipping_address(self, cr, uid, ids, address, context={}):
        country_ids  = self.pool.get('res.country').search(cr, uid, [('code','=',address.Country)])
        state_ids    = self.pool.get('res.country.state').search(cr, uid, ['|',('name','ilike',address.StateOrProvince),('code','ilike',address.StateOrProvince)])  #by zhangxue

        user = self.pool.get('res.users').browse(cr, uid, uid)
        
        address_vals = {
                            'name'      : address.Name,
                            'shop_id'   : context.get('shop_id'),
                            'street'    : address.Street1,
                            'street2'   : address.Street2,
                            'zip'       : address.PostalCode,
                            'city'      : address.CityName,
                            'phone'     : address.Phone,
                            'email'     : context.get('email'),
                            'ebay_userid': context.get('ebay_userid'),
                            'country_id' : country_ids and country_ids[0] or context.get('country_id', False),
                            'state_id'   : state_ids and state_ids[0] or False,
                            'company_id' : user.company_id.id 
                        }
        partner_pool = self.pool.get('res.partner')
        partner_ids = partner_pool.search(cr, uid, [('email','=',address_vals['email']),('phone','=',address_vals['phone']),('name','=',address_vals['name']),('ebay_userid','=',address_vals['ebay_userid'])])
        if partner_ids:
            partner_id = partner_ids[0]
            partner_pool.write(cr, uid, [partner_id], address_vals)
        else:
            partner_id = partner_pool.create(cr, uid, address_vals)
        return partner_id
    
    
    def import_products(self, cr, uid, ids, context=None, product_ids=[]):
        #GetSellerList
        #http://developer.ebay.com/DevZone/XML/docs/Reference/ebay/GetSellerList.html
        
        date_3month = datetime.today() + relativedelta(days=90) 
        
        prod_sku = ''
        if product_ids:
            prod_sku = "<SKUArray>"
            for prod in self.pool.get('product.product').browse(cr, uid, product_ids):
                prod_sku += "<SKU>" + prod.default_code + "1</SKU>"
            prod_sku += "</SKUArray>"
        
        requestXml = '''
                    <?xml version="1.0" encoding="utf-8"?>
                    <GetSellerListRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                      <RequesterCredentials>
                        <eBayAuthToken>{USERTOKEN}</eBayAuthToken>
                      </RequesterCredentials>
                      <ErrorLanguage>en_US</ErrorLanguage>
                      <WarningLevel>High</WarningLevel>
                      <GranularityLevel>Coarse</GranularityLevel>
                      <DetailLevel>ReturnAll</DetailLevel>
                      <OutputSelector>ItemArray.Item.SKU,ItemArray.Item.Title,ItemArray.Item.ItemID,ItemArray.Item.SellingStatus.CurrentPrice,ItemArray.Item.Variations.Variation.SKU,ItemArray.Item.Variations.Variation.Quantity,ItemArray.Item.Variations.Variation.SellingStatus.QuantitySold,ItemArray.Item.Variations.Variation.StartPrice</OutputSelector> 
                      <IncludeVariations>true</IncludeVariations>
                      <EndTimeFrom>%s</EndTimeFrom>
                      <EndTimeTo>%s</EndTimeTo>
                      %s
                      <IncludeWatchCount>true</IncludeWatchCount> 
                      <Pagination> 
                        <EntriesPerPage>200</EntriesPerPage> 
                      </Pagination> 
                    </GetSellerListRequest>''' %(time.strftime('%Y-%m-%dT%H:%M:%SZ'), date_3month.strftime('%Y-%m-%dT%H:%M:%SZ'), prod_sku);        

        resp =  self.call(cr, uid, "GetSellerList", requestXml)

        if resp and resp.GetSellerListResponse.Ack == 'Failure':
            self.process_Errors(cr, uid, resp.GetSellerListResponse.Errors)
            
        prod_pool = self.pool.get('product.product')

        items = resp.GetSellerListResponse.ItemArray.Item
        
        if not isinstance(items, list):
            items = [items]
            
        for item in items:
            if hasattr(item, 'transaction'):
                name = item.Title
            if hasattr(item, 'Variations'):
                for var in item.Variations.Variation:
                    sku = var.SKU
                    qty = 0
                    price = 0.0
                    sold_qty = 0
                      
                    if hasattr(var, 'Quantity'):
                        qty = var.Quantity
                    if hasattr(var, 'StartPrice'):
                        price = var.StartPrice
                    if hasattr(var, 'SellingStatus'):
                        sold_qty = var.SellingStatus.QuantitySold
                    vals = {
                            'name':item.Title,
                            'default_code' : var.SKU,
                            'list_price' : price,
                            'sold_qty'   : sold_qty
                            }
                    prod_id  = prod_pool.search(cr, uid, [('default_code','=',sku)])
                    if prod_id:
                        prod = prod_pool.browse(cr, uid, prod_id[0])
                        prod_pool.write(cr, uid, [prod_id[0]], vals)
                    else:
                        product_id = prod_pool.create(cr, uid, vals)
             
        cr.commit()
        return True
connect_ebay()

class ebay_payment_method(osv.osv):
    _name = 'ebay.payment.method'
    _columns = {
                    'name': fields.char('Ebay Payment Method', required=True),
                    'payment_method_id': fields.many2one('payment.method', 'Payment Method', required=True),
                    'ebay_id': fields.many2one('connect.ebay', 'Ebay', ondelete='cascade', required=True)
    }
ebay_payment_method()
