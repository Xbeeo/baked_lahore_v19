from odoo import fields, models, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        related='product_id.vendor_id',
        store=True,
    )

    cost_price = fields.Float(
        string='Cost Price',
        compute='_compute_cost_price',
        store=True,
    )

    adjustment_cost = fields.Float(
        string='Adjustment Cost',
        compute='_compute_adjustment_cost',
        store=True,
    )

    last_move_date = fields.Datetime(
        string='Last Move Date',
        compute='_compute_last_move_info',
    )

    # last_move_quantity = fields.Float(
    #     string='Last Move Quantity',
    #     compute='_compute_last_move_info',
    # )

    last_move_user_id = fields.Many2one(
        'res.users',
        string='Last Move By',
        compute='_compute_last_move_info',
    )

    @api.depends('product_id', 'product_id.standard_price')
    def _compute_cost_price(self):
        for rec in self:
            rec.cost_price = rec.product_id.standard_price

    @api.depends('cost_price', 'inventory_diff_quantity')
    def _compute_adjustment_cost(self):
        for rec in self:
            rec.adjustment_cost = rec.cost_price * rec.inventory_diff_quantity

    def _compute_last_move_info(self):
        for rec in self:
            move_line = self.env['stock.move.line'].search([
                ('product_id', '=', rec.product_id.id),
                ('state', '=', 'done'),
                ('is_inventory', '=', True),
            ], order='date desc', limit=1)

            rec.last_move_date = move_line.date
            rec.last_move_user_id = move_line.create_uid.id

    def action_apply_inventory(self, date=None):
        for quant in self:
            cost_price = quant.product_id.standard_price
            difference = quant.inventory_diff_quantity

            self.env['inventory.adjustment.analysis'].create({
                'quant_id': quant.id,
                'product_id': quant.product_id.id,
                'location_id': quant.location_id.id,
                'company_id': quant.company_id.id,

                'vendor_id': quant.product_id.vendor_id.id,
                'cost_price': cost_price,
                'last_move_user_id': self.env.user.id,
                'last_move_date': fields.Datetime.now(),
                # 'last_move_quantity': quant.last_move_quantity,
                # 'scheduled': quant.inventory_date,
                'on_hand': quant.quantity,
                'counted': quant.inventory_quantity,
                'difference': difference,

                'adjustment_cost': cost_price * difference,
                'adjustment_date': fields.Datetime.now(),
            })
        result = super().action_apply_inventory(date=date)
        return result