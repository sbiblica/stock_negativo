# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import openerp.addons.decimal_precision
from openerp.tools.translate import _
import logging

class pos_order(osv.osv):
    _inherit = 'pos.order'

    def validar_inventario(self, cr, uid, product_id, qty, context=None):
        producto = self.pool.get('product.product').browse(cr, uid, product_id, context=context)

        if producto.type=='product':

            if producto.virtual_available < qty:
                return producto

        elif producto.type=='consu':

            boms = self.pool.get('mrp.bom').search(cr, uid, [('type','=','phantom'), ('product_tmpl_id','=',producto.product_tmpl_id.id)], context=context)
            for b in self.pool.get('mrp.bom').browse(cr, uid, boms, context=context):

                for l in b.bom_line_ids:

                    sub_producto = self.pool.get('product.product').browse(cr, uid, l.product_id.id, context=context)
                    if sub_producto.virtual_available < l.product_qty * qty:
                        return sub_producto

        return None

    def add_payment(self, cr, uid, order_id, data, context=None):
        for o in self.browse(cr, uid, order_id, context=context):
            context = context or {}
            ctx = context.copy()
            ctx.update({'location': o.location_id.id})

            for l in o.lines:
                producto = self.validar_inventario(cr, uid, l.product_id.id, l.qty, context=ctx)
                if producto:
                    raise osv.except_osv(_('Not enough stock !'), _('You plan to sell %.2f but you only have %.2f available !') % (l.qty, producto.virtual_available))

        return super(pos_order, self).add_payment(cr, uid, order_id, data, context)

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

        producto = self.pool.get('pos.order').validar_inventario(cr, uid, product_id, qty, context=ctx)

        if producto:
            warning = {
                'title': _('Not enough stock !'),
                'message': _('You plan to sell %.2f but you only have %.2f available !') % (qty, producto.virtual_available)
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

        producto = self.pool.get('pos.order').validar_inventario(cr, uid, product_id, qty, context=ctx)

        if producto:
            warning = {
                'title': _('Not enough stock !'),
                'message': _('You plan to sell %.2f but you only have %.2f available !') % (qty, producto.virtual_available)
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
