# -*- coding: utf-8 -*-
from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id()
        if self.partner_id:
            self.fiscal_position_id = \
                self.env['account.fiscal.position'].with_context(
                    force_company=self.company_id.id).get_fiscal_position(
                    self.partner_id.id)
            self.payment_term_id = self.partner_id.\
                with_context(force_company=self.company_id.id).\
                property_supplier_payment_term_id.id
            self.currency_id = self.partner_id.\
                with_context(force_company=self.company_id.id).\
                property_purchase_currency_id.id or self.env.user.company_id.\
                currency_id.id
        for line in self.order_line:
            line.onchange_product_id()
        return res

    @api.multi
    def action_view_invoice(self):
        result = super(PurchaseOrder, self).action_view_invoice()
        result['context']['default_company_id'] = self.company_id.id
        return result

    @api.multi
    @api.constrains('partner_id', 'company_id')
    def _check_partner_company(self):
        for rec in self:
            if (rec.partner_id and rec.partner_id.company_id and
                    rec.partner_id.company_id != rec.company_id):
                raise ValidationError(_('Configuration error\n'
                                        'The Company of the Partner '
                                        'must match with that of the '
                                        'RFQ/Purchase order'))

    @api.multi
    @api.constrains('payment_term_id', 'company_id')
    def _check_payment_term_company(self):
        for rec in self:
            if (rec.payment_term_id and rec.payment_term_id.company_id and
                    rec.payment_term_id.company_id != rec.company_id):
                raise ValidationError(_('Configuration error\n'
                                        'The Company of the Payment Term '
                                        'must match with that of the '
                                        'RFQ/Purchase order'))

    @api.multi
    @api.constrains('fiscal_position_id', 'company_id')
    def _check_fiscal_position_company(self):
        for rec in self:
            if (rec.fiscal_position_id and
                    rec.fiscal_position_id.company_id and
                    rec.fiscal_position_id.company_id != rec.company_id):
                raise ValidationError(_('Configuration error\n'
                                        'The Company of the fiscal position '
                                        'must match with that of the '
                                        'quote/sales order'))


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id', 'company_id')
    def onchange_product_id(self):
        if not self.company_id:
            self.company_id = self.order_id.company_id
        result = super(PurchaseOrderLine, self).onchange_product_id()

        fpos = self.order_id.fiscal_position_id or self.order_id.\
            with_context(force_company=self.company_id.id).\
            partner_id.property_account_position_id
        taxes = self.product_id.supplier_taxes_id.filtered(
            lambda r: not self.company_id or r.company_id == self.company_id)
        self.taxes_id = fpos.map_tax(
            taxes, self.product_id, self.order_id.partner_id) if \
            fpos else taxes
        self._suggest_quantity()
        self._onchange_quantity()

        return result

    @api.multi
    @api.constrains('tax_id', 'company_id')
    def _check_tax_company(self):
        for rec in self.sudo():
            if (rec.tax_id.company_id and rec.tax_id.company_id !=
                    rec.company_id):
                raise ValidationError(_('Configuration error\n'
                                        'The Company of the tax %s '
                                        'must match with that of the '
                                        'quote/sales order') % rec.tax_id.name)

    @api.multi
    @api.constrains('product_id', 'company_id')
    def _check_product_company(self):
        for rec in self.sudo():
            if (rec.product_id.company_id and
                    rec.product_id.company_id != rec.company_id):
                raise ValidationError(_('Configuration error\n'
                                        'The Company of the product '
                                        'must match with that of the '
                                        'order line %s') % rec.name)
