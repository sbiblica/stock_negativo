# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import openerp.addons.decimal_precision
from openerp.tools.translate import _
import logging
 

class pos_order(osv.osv):
    _inherit = 'pos.order'

    def _default_journal(self, cr, uid, context=None):
        session_ids = self._default_session(cr, uid, context)
        if session_ids:
            session_record = self.pool.get('pos.session').browse(cr, uid, session_ids, context=context)
            return session_record.config_id.journal_id and session_record.config_id.journal_id.id or False
        return False

    def _default_location(self, cr, uid, context=None):
        session_ids = self._default_session(cr, uid, context)
        if session_ids:
            session_record = self.pool.get('pos.session').browse(cr, uid, session_ids, context=context)
            return session_record.config_id.stock_location_id and session_record.config_id.stock_location_id.id or False
        return False

    _columns = {
        'sale_journal': fields.many2one('account.journal', 'Sale Journal', readonly=True, states={'draft': [('readonly', False)]}),
        'location_id': fields.many2one('stock.location', 'Location', readonly=True, states={'draft': [('readonly', False)]}),
    }

    _defaults = {
        'sale_journal': _default_journal,
        'location_id': _default_location,
    }

    def sbg_onchange_session(self, cr, uid, ids, session_id, context=None):

        logging.warn('----')

        result = {}
        if not session_id:
            return result

        result['value'] = {}
        session_record = self.pool.get('pos.session').browse(cr, uid, session_id, context=context)
        if session_record.config_id.journal_id:
            result['value']['sale_journal'] = session_record.config_id.journal_id.id

        if session_record.config_id.stock_location_id:
            result['value']['location_id'] = session_record.config_id.stock_location_id.id

        return result
 

pos_order()

        

class sbg_pos_order_line(osv.osv):
    _inherit = 'pos.order.line'

    def sbg_onchange_product_id(self, cr, uid, ids, pricelist, product_id, qty=0, partner_id=False, location_id=None, context=None):
        result = super(sbg_pos_order_line, self).onchange_product_id(cr, uid, ids, pricelist, product_id, qty, partner_id, context)

        if not product_id:
            return result

        context = context or {}
        ctx = context.copy()
        ctx.update({'location': location_id})

        producto = self.pool.get('product.product').browse(cr, uid, product_id, context=ctx)
        if (producto.type=='product') and (producto.virtual_available < qty):
            warning = {
                'title': _('Not enough stock !'),
                'message': _('You plan to sell %.2f but you only have %.2f available !') % (qty, producto.virtual_available)
            }
            result['warning'] = warning
            result['value']['qty'] = None
        if (producto.type=='consu'):

            domain = ' e.bodega = %s'
            args = (location_id,)
            domain += ' and p.id = %s'
            args += (product_id,)
            _warning = ''

            cr.execute('Select e.bodega,b.complete_name,p.id product_lista,t.type,l.id '\
                       'lista_id,l.code,l.product_tmpl_id,ll.product_id,ll.product_qty,e.existencia,pl.default_code '\
	               'from mrp_bom l '\
 	               'join product_template t '\
	               'on l.product_tmpl_id = t.id '\
	               'join mrp_bom_line ll '\
	               'ON l.id = ll.bom_id '\
                       'join "SBG_inventario_por_bodega_virtual" e '\
                       'on ll.product_id = e.id '\
                       'join product_product pl '\
                       'on ll.product_id = pl.id '\
                       'join product_product p '\
                       'on p.product_tmpl_id = t.id '\
                       'Join stock_location b '\
                       'on b.id = e.bodega '\
                       'where'+domain
            , args)

            for line in cr.dictfetchall():
                _total_qty = line['product_qty']*qty
                if _total_qty > line['existencia']:

                    _warning = str(line['existencia']) +' of code '+str(line['default_code'])+' location '+str(line['complete_name'])

                    warning = {

                        'title': _('Not enough stock !'),
                        'message': _('You plan to sell "%d" but you not have available "%s"') % (_total_qty,_warning)

                    }

                    result['warning'] = warning

                    result['value']['qty'] = None




        return result

    def sbg_onchange_qty(self, cr, uid, ids, product_id, discount, qty, price_unit, location_id, context=None):
        result = super(sbg_pos_order_line, self).onchange_qty(cr, uid, ids, product_id, discount, qty, price_unit, context)

        if not product_id:
            return result

        context = context or {}
        ctx = context.copy()
        ctx.update({'location': location_id})

        producto = self.pool.get('product.product').browse(cr, uid, product_id, context=ctx)
        if (producto.type=='product') and (producto.virtual_available < qty):
            warning = {
                'title': _('Not enough stock !'),
                'message': _('You plan to sell %.2f but you only have %.2f available !') % (qty, producto.virtual_available)
            }
            result['warning'] = warning
            result['value']['qty'] = None

        if (producto.type=='consu'):

            domain = ' e.bodega = %s'
            args = (location_id,)
            domain += ' and p.id = %s'
            args += (product_id,)
            _warning = ''

            cr.execute('Select e.bodega,b.complete_name,p.id product_lista,t.type,l.id '\
                       'lista_id,l.code,l.product_tmpl_id,ll.product_id,ll.product_qty,e.existencia,pl.default_code '\
	               'from mrp_bom l '\
 	               'join product_template t '\
	               'on l.product_tmpl_id = t.id '\
	               'join mrp_bom_line ll '\
	               'ON l.id = ll.bom_id '\
                       'join "SBG_inventario_por_bodega_virtual" e '\
                       'on ll.product_id = e.id '\
                       'join product_product pl '\
                       'on ll.product_id = pl.id '\
                       'join product_product p '\
                       'on p.product_tmpl_id = t.id '\
                       'Join stock_location b '\
                       'on b.id = e.bodega '\
                       'where'+domain
            , args)

            for line in cr.dictfetchall():
                _total_qty = line['product_qty']*qty
                if _total_qty > line['existencia']:

                    _warning = str(line['existencia']) +' of code '+str(line['default_code'])+' location '+str(line['complete_name'])

                    warning = {

                        'title': _('Not enough stock !'),
                        'message': _('You plan to sell "%d" but you not have available "%s"') % (_total_qty,_warning)

                    }

                    result['warning'] = warning

                    result['value']['qty'] = None



        return result
 

sbg_pos_order_line()


class sbg_pos_session(osv.osv):
    _inherit = 'pos.session'

    def conciliar(self, cr, uid, ids, context=None):
        """
        Conciliar todas las facturas con sus pagos
        """
        if context is None:
            context = dict()

        for s in self.browse(cr, uid, ids, context=context):
            for o in s.order_ids:

                lineas = []
                cuenta = o.invoice_id.account_id.id
                conciliado = False

                for l in o.invoice_id.move_id.line_id:
                    self.pool.get('account.move.line').write(cr, uid, l.id, {'partner_id':o.partner_id.id}, context=context)
                    if l.account_id.id == cuenta:
                        lineas.append(l.id)
                        if l.reconcile_id or l.reconcile_partial_id:
                            conciliado = True

                for st in o.statement_ids:
                    for l in st.journal_entry_id.line_id:
                        self.pool.get('account.move.line').write(cr, uid, l.id, {'partner_id':o.partner_id.id}, context=context)
                        if l.account_id.id == cuenta:
                            lineas.append(l.id)
                            if l.reconcile_id or l.reconcile_partial_id:
                                conciliado = True

                if o.amount_total != o.amount_paid:
                    continue

                if not o.invoice_id or not o.invoice_id.move_id:
                    continue

                if not conciliado:
                    self.pool.get('account.move.line').reconcile(cr, uid, lineas, context=context)

        return True

sbg_pos_session()
 
