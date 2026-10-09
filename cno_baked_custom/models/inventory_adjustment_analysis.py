# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InventoryAdjustmentAnalysis(models.Model):
    _name = 'inventory.adjustment.analysis'
    _description = 'Inventory Adjustment Analysis'
    _order = 'adjustment_date desc, id desc'

    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        readonly=True,
    )

    location_id = fields.Many2one('stock.location', 'Location')

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        readonly=True,
        required=True,
    )

    last_move_date = fields.Datetime(
        string='Last Move Date',
        readonly=True,
    )

    last_move_quantity = fields.Float(
        string='Last Move Quantity',
        readonly=True,
    )

    last_move_user_id = fields.Many2one(
        'res.users',
        string='Last Move By',
        readonly=True,
    )

    cost_price = fields.Float(
        string='Cost Price',
        readonly=True,
    )

    scheduled = fields.Date(
        string='Scheduled',
        readonly=True,
    )

    on_hand = fields.Float(
        string='On Hand',
        readonly=True,
    )

    counted = fields.Float(
        string='Counted',
        readonly=True,
    )

    difference = fields.Float(
        string='Difference',
        readonly=True,
    )

    adjustment_cost = fields.Float(
        string='Adjustment Cost',
        readonly=True,
    )

    adjustment_date = fields.Datetime(
        string='Adjustment Date',
        readonly=True,
        default=fields.Datetime.now,
    )

    quant_id = fields.Many2one(
        'stock.quant',
        string='Stock Quant',
        readonly=True,
        ondelete='set null',
        index=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        default=lambda self: self.env.company,
    )