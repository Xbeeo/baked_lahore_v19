# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import timedelta, date, datetime
from odoo.exceptions import ValidationError
from collections import defaultdict
from datetime import datetime , time , timedelta
from pytz import timezone, UTC
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from collections import defaultdict


class SaleAnalysisReport(models.TransientModel):
    _name = "sale.analysis.report"

    date_from = fields.Datetime(string='Date From', required= True)
    date_to = fields.Datetime(string='Date To', required= True)
    allowed_pos = fields.Many2many(
        comodel_name='pos.config',
        string='Allowed POS',
        help='Select POS configurations. Leave empty for all POS.',
    )

    report_type = fields.Selection(
        [
            ('product', 'Product Wise'),
            ('order', 'Order Wise'),
        ],
        string='Report Type',
        required=True,
        default='product',
    )

    def action_print(self):
        self.ensure_one()

        data = {
            'form': self.read()[0],
        }

        if self.report_type == 'product':
            report = self.env.ref(
                'cno_baked_report.sale_analysis_report_xlsx_details'
            )
        else:
            report = self.env.ref(
                'cno_baked_report.sale_analysis_order_wise_xlsx'
            )

        return report.report_action(self, data=data)


