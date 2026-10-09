import io
import base64
import xlsxwriter
from datetime import timedelta

from odoo import fields, models


class QuantReportWizard(models.TransientModel):
    _name = 'quant.report.wizard'
    _description = 'Stock Quant Report Wizard'

    date_from = fields.Datetime(
        string='Date From',
        required=True,
    )
    date_to = fields.Datetime(
        string='Date To',
        required=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
    )

    def _format_pakistan_datetime(self, value):
        if not value:
            return ''

        dt = fields.Datetime.to_datetime(value)

        # Odoo UTC -> Pakistan time (+5 hours)
        dt = dt + timedelta(hours=5)

        return dt.strftime('%d-%m-%Y %I:%M %p')

    def action_print_report(self):
        self.ensure_one()

        domain = [
            ('adjustment_date', '>=', self.date_from),
            ('adjustment_date', '<=', self.date_to),
            ('location_id.usage', 'in', ['internal', 'transit']),
        ]

        if self.location_id:
            domain.append(
                ('location_id', '=', self.location_id.id)
            )

        quants = self.env[
            'inventory.adjustment.analysis'
        ].search(domain, order='adjustment_date, id')

        # --------------------------------------------------
        # WORKBOOK
        # --------------------------------------------------

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True}
        )

        sheet = workbook.add_worksheet(
            'Inventory Adjustment Report'
        )

        sheet.hide_gridlines(2)
        sheet.freeze_panes(5, 0)
        sheet.set_zoom(90)

        # --------------------------------------------------
        # COLORS
        # --------------------------------------------------

        DARK_BLUE = '#17365D'
        MEDIUM_BLUE = '#4F7194'
        LIGHT_BLUE = '#EAF0F6'
        VERY_LIGHT_BLUE = '#F5F8FB'
        BORDER = '#D8E0E6'
        TEXT = '#263238'
        MUTED = '#78909C'
        WHITE = '#FFFFFF'
        TOTAL_BG = '#DCE6F1'

        # --------------------------------------------------
        # FORMATS
        # --------------------------------------------------

        title_fmt = workbook.add_format({
            'bold': True,
            'font_size': 20,
            'font_color': WHITE,
            'bg_color': DARK_BLUE,
            'align': 'left',
            'valign': 'vcenter',
        })

        subtitle_fmt = workbook.add_format({
            'font_size': 10,
            'font_color': MUTED,
            'italic': True,
            'align': 'left',
            'valign': 'vcenter',
        })

        date_label_fmt = workbook.add_format({
            'bold': True,
            'font_size': 9,
            'font_color': MUTED,
            'bg_color': VERY_LIGHT_BLUE,
            'border': 1,
            'border_color': BORDER,
            'align': 'center',
            'valign': 'vcenter',
        })

        date_value_fmt = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font_color': DARK_BLUE,
            'bg_color': VERY_LIGHT_BLUE,
            'border': 1,
            'border_color': BORDER,
            'align': 'center',
            'valign': 'vcenter',
        })

        header_fmt = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font_color': WHITE,
            'bg_color': DARK_BLUE,
            'border': 1,
            'border_color': WHITE,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        header_left_fmt = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font_color': WHITE,
            'bg_color': DARK_BLUE,
            'border': 1,
            'border_color': WHITE,
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        cell_fmt = workbook.add_format({
            'border': 1,
            'border_color': BORDER,
            'font_color': TEXT,
            'valign': 'vcenter',
        })

        cell_alt_fmt = workbook.add_format({
            'border': 1,
            'border_color': BORDER,
            'font_color': TEXT,
            'bg_color': '#FAFBFC',
            'valign': 'vcenter',
        })

        number_fmt = workbook.add_format({
            'border': 1,
            'border_color': BORDER,
            'font_color': TEXT,
            'num_format': '#,##0.00',
            'align': 'right',
            'valign': 'vcenter',
        })

        number_alt_fmt = workbook.add_format({
            'border': 1,
            'border_color': BORDER,
            'font_color': TEXT,
            'bg_color': '#FAFBFC',
            'num_format': '#,##0.00',
            'align': 'right',
            'valign': 'vcenter',
        })

        total_label_fmt = workbook.add_format({
            'bold': True,
            'font_color': DARK_BLUE,
            'bg_color': TOTAL_BG,
            'border': 1,
            'border_color': BORDER,
            'align': 'left',
            'valign': 'vcenter',
        })

        total_number_fmt = workbook.add_format({
            'bold': True,
            'font_color': DARK_BLUE,
            'bg_color': TOTAL_BG,
            'border': 1,
            'border_color': BORDER,
            'num_format': '#,##0.00',
            'align': 'right',
            'valign': 'vcenter',
        })

        # --------------------------------------------------
        # COLUMN WIDTHS
        # --------------------------------------------------

        widths = {
            0: 21,   # Adjustment Date
            1: 32,   # Location
            2: 25,   # Vendor
            3: 38,   # Product
            4: 24,   # Last Move By
            5: 16,   # Cost Price
            6: 16,   # On Hand
            7: 16,   # Counted
            8: 16,   # Difference
            9: 20,   # Adjustment Cost
        }

        for col, width in widths.items():
            sheet.set_column(col, col, width)

        # --------------------------------------------------
        # REPORT HEADING
        # --------------------------------------------------

        sheet.set_row(0, 36)
        sheet.merge_range(
            0, 0, 0, 9,
            'Inventory Adjustment Report',
            title_fmt,
        )

        sheet.set_row(1, 22)
        sheet.merge_range(
            1, 0, 1, 9,
            'Physical Inventory | Adjustment Summary',
            subtitle_fmt,
        )

        # --------------------------------------------------
        # DATE AND LOCATION INFORMATION
        # --------------------------------------------------

        sheet.set_row(2, 25)

        sheet.merge_range(
            2, 0, 2, 1,
            'REPORT PERIOD',
            date_label_fmt,
        )

        sheet.merge_range(
            2, 2, 2, 4,
            '{}  to  {}'.format(
                self._format_pakistan_datetime(self.date_from),
                self._format_pakistan_datetime(self.date_to),
            ),
            date_value_fmt,
        )

        sheet.write(
            2, 5,
            'LOCATION',
            date_label_fmt,
        )

        sheet.merge_range(
            2, 6, 2, 9,
            self.location_id.complete_name
            if self.location_id else 'All Internal / Transit Locations',
            date_value_fmt,
        )

        # --------------------------------------------------
        # TABLE HEADER
        # --------------------------------------------------

        headers = [
            'Adjustment Date',
            'Location',
            'Vendor',
            'Product',
            'Last Move By',
            'Cost Price',
            'On Hand',
            'Counted',
            'Difference',
            'Adjustment Cost',
        ]

        header_row = 4
        sheet.set_row(header_row, 34)

        for col, header in enumerate(headers):
            if col in (1, 2, 3, 4):
                fmt = header_left_fmt
            else:
                fmt = header_fmt

            sheet.write(
                header_row,
                col,
                header,
                fmt,
            )

        # --------------------------------------------------
        # DATA AND TOTALS
        # --------------------------------------------------

        row = header_row + 1

        total_on_hand = 0.0
        total_counted = 0.0
        total_difference = 0.0
        total_adjustment_cost = 0.0

        for index, quant in enumerate(quants):
            is_alt = index % 2 == 1

            text_fmt = (
                cell_alt_fmt if is_alt else cell_fmt
            )
            num_fmt = (
                number_alt_fmt if is_alt else number_fmt
            )

            # Adjustment Date
            if quant.adjustment_date:
                sheet.write(
                    row,
                    0,
                    self._format_pakistan_datetime(
                        quant.adjustment_date
                    ),
                    text_fmt,
                )
            else:
                sheet.write(row, 0, '', text_fmt)

            sheet.write(
                row, 1,
                quant.location_id.complete_name or '',
                text_fmt,
            )
            sheet.write(
                row, 2,
                quant.vendor_id.name or '',
                text_fmt,
            )
            sheet.write(
                row, 3,
                quant.product_id.display_name or '',
                text_fmt,
            )
            sheet.write(
                row, 4,
                quant.last_move_user_id.name or '',
                text_fmt,
            )

            cost_price = quant.cost_price or 0.0
            on_hand = quant.on_hand or 0.0
            counted = quant.counted or 0.0
            difference = quant.difference or 0.0
            adjustment_cost = quant.adjustment_cost or 0.0

            sheet.write_number(
                row, 5, cost_price, num_fmt
            )
            sheet.write_number(
                row, 6, on_hand, num_fmt
            )
            sheet.write_number(
                row, 7, counted, num_fmt
            )
            sheet.write_number(
                row, 8, difference, num_fmt
            )
            sheet.write_number(
                row, 9, adjustment_cost, num_fmt
            )

            total_on_hand += on_hand
            total_counted += counted
            total_difference += difference
            total_adjustment_cost += adjustment_cost

            sheet.set_row(row, 22)
            row += 1

        # --------------------------------------------------
        # GRAND TOTAL ROW
        # --------------------------------------------------

        sheet.set_row(row, 28)

        sheet.merge_range(
            row, 0, row, 5,
            'GRAND TOTAL',
            total_label_fmt,
        )

        sheet.write_number(
            row, 6,
            total_on_hand,
            total_number_fmt,
        )
        sheet.write_number(
            row, 7,
            total_counted,
            total_number_fmt,
        )
        sheet.write_number(
            row, 8,
            total_difference,
            total_number_fmt,
        )
        sheet.write_number(
            row, 9,
            total_adjustment_cost,
            total_number_fmt,
        )

        # --------------------------------------------------
        # AUTOFILTER AND PRINT SETTINGS
        # --------------------------------------------------

        if row > header_row + 1:
            sheet.autofilter(
                header_row,
                0,
                row - 1,
                len(headers) - 1,
            )

        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_margins(0.25, 0.25, 0.5, 0.5)
        sheet.repeat_rows(header_row)

        # --------------------------------------------------
        # CREATE DOWNLOAD
        # --------------------------------------------------

        workbook.close()

        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'Inventory_Adjustment_Report.xlsx',
            'type': 'binary',
            'datas': file_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': (
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet'
            ),
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(
                attachment.id
            ),
            'target': 'self',
        }