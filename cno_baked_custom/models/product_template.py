# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    business_type = fields.Selection([('commission', 'Commission'),('trading', 'Trading'),('manufacturing', 'Manufacturing')],string='Business Type', required=True)
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor')
    product_owner_id = fields.Many2one(comodel_name='res.partner', string='Product Owner')
    cogs_basis_id = fields.Many2one(comodel_name='cogs.basis', string='COGS Basis')
    profit_classification_id = fields.Many2one(comodel_name='profit.classification', string='Profit Classification')
    stream = fields.Char(string='Stream')
    brand = fields.Char(string='Brands')
    payable_suppl_2221001_id = fields.Many2one(comodel_name='account.account', string='2221001 Payable to Supplier (Dr.)')
    stock_hand_1125001_id = fields.Many2one(comodel_name='account.account', string='1125001 Stock in Hand (Cr.)')
    account_debit_id = fields.Many2one(comodel_name='account.account', string='2223002 Inventory held on b/f Vendors (Dr.)')
    account_credit_id = fields.Many2one(comodel_name='account.account', string='2223006 Commission based Vendor C/A (Cr.)')
    commission_based_sale = fields.Many2one(comodel_name='account.account', string='3111001 Commission Based Sale (Dr.)')
    commission_asset_cr = fields.Many2one(comodel_name='account.account', string='1125001 Stock In Hand (Dr.)')
    commission_cgs = fields.Many2one(comodel_name='account.account', string='2223006 Commission based Vendor C/A (Dr.)')
    payable_to_supplier_cr = fields.Many2one(comodel_name='account.account', string='2221001 Payable to Supplier (Cr.)')
    inventory_vendor_cr = fields.Many2one(comodel_name='account.account', string='2223002 Inventory held on b/f Vendors (Cr.)')
    cost_of_goods_cr = fields.Many2one(comodel_name='account.account', string='4111003 Cost of Goods Sold (Cr.)')
    commission_income = fields.Many2one(comodel_name='account.account', string='3111001 Commission Income')
    commission_tax = fields.Many2one(comodel_name='account.account', string='2221008 Commission Tax')
    cost_of_goods_exp_adjustment = fields.Many2one(comodel_name='account.account', string='4111003 Cost of Goods Sold (Dr.)')
    commission_exp_adjustment = fields.Many2one(comodel_name='account.account', string='2223006 Commission based Vendor C/A (Dr.)')
    inventory_vendor_exp_Adjustment_cr = fields.Many2one(comodel_name='account.account',string='2223002 Inventory held on b/f Vendors (Cr.)')
    expiration_per = fields.Float(string='Expiration %')
    commission_per = fields.Float(string='Commission %')
    margin_percent = fields.Float(
        string='Margin %',
        compute='_compute_margin_percent',
        store=True
    )

    @api.constrains('name')
    def _check_duplicate_name(self):
        for rec in self:
            if rec.name:
                duplicate = self.search([
                    ('id', '!=', rec.id),
                    ('name', '=ilike', rec.name.strip()),
                ], limit=1)

                if duplicate:
                    raise ValidationError(
                        _("Product name '%s' already exists.") % rec.name
                    )

    @api.constrains('default_code')
    def _check_duplicate_default_code(self):
        for rec in self:
            if rec.default_code:
                duplicate = self.search([
                    ('id', '!=', rec.id),
                    ('default_code', '=ilike', rec.default_code.strip()),
                ], limit=1)

                if duplicate:
                    raise ValidationError(
                        _("Default_code '%s' already exists.") % rec.name
                    )

    @api.depends('list_price', 'standard_price')
    def _compute_margin_percent(self):
        for rec in self:
            if rec.standard_price > 0 and rec.list_price > 0:
                rec.margin_percent = ((rec.list_price - rec.standard_price)/rec.list_price) * 100
            else:
                rec.margin_percent = 0.0

    @api.onchange('list_price', 'standard_price')
    def onchange_standard_price(self):
        for rec in self:
            if rec.list_price and rec.standard_price and rec.list_price < rec.standard_price:
                raise ValidationError(
                    _("Sale Price should not be less than Cost Price.")
                )

