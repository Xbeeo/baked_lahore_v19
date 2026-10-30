import io
import base64
import xlsxwriter

from collections import defaultdict
from datetime import datetime
import pytz
from odoo import fields, models, _
from odoo.exceptions import UserError


class ConsolidatedInventoryReportWizard(models.TransientModel):
    _name = 'consolidated.inventory.report.wizard'
    _description = 'Consolidated Inventory Report Wizard'

    company_ids = fields.Many2many(
        'res.company',
        string='Companies / Branches',
        required=True,
    )

    # --------------------------------------------------
    # GET COMPANY WAREHOUSE INTERNAL LOCATIONS
    # --------------------------------------------------

    def _get_company_internal_locations(self, company):
        Warehouse = self.env['stock.warehouse'].with_company(company)
        Location = self.env['stock.location'].with_company(company)

        warehouses = Warehouse.search([
            ('company_id', '=', company.id),
        ])

        if not warehouses:
            return Location.browse()

        location_ids = set()

        for warehouse in warehouses:
            if not warehouse.view_location_id:
                continue

            locations = Location.search([
                ('id', 'child_of', warehouse.view_location_id.id),
                ('usage', '=', 'internal'),
                '|',
                ('company_id', '=', company.id),
                ('company_id', '=', False),
            ])

            location_ids.update(locations.ids)

        return Location.browse(list(location_ids))

    # --------------------------------------------------
    # GET COMPANY PRODUCT STOCK AND COST
    # --------------------------------------------------

    def _get_company_stock_data(self, company):
        Quant = self.env['stock.quant'].with_company(company)

        locations = self._get_company_internal_locations(company)

        stock_data = defaultdict(lambda: {
            'qty': 0.0,
            'value': 0.0,
        })

        if not locations:
            return stock_data

        quants = Quant.search([
            ('company_id', '=', company.id),
            ('location_id', 'in', locations.ids),
            ('location_id.usage', '=', 'internal'),
            ('quantity', '!=', 0),
        ])

        for quant in quants:
            if not quant.product_id:
                continue

            product_id = quant.product_id.id
            qty = quant.quantity or 0.0
            unit_cost = quant.cost_price or 0.0

            stock_data[product_id]['qty'] += qty
            stock_data[product_id]['value'] += qty * unit_cost

        return stock_data

    # --------------------------------------------------
    # EXCEL REPORT
    # --------------------------------------------------

    def action_print_report(self):
        self.ensure_one()

        companies = self.company_ids.sorted(
            key=lambda company: company.id
        )

        if not companies:
            raise UserError(_(
                'Please select at least one company.'
            ))

        # ----------------------------------------------
        # COLLECT STOCK FOR ALL COMPANIES
        # ----------------------------------------------

        stock_by_company = {}
        product_ids = set()

        for company in companies:
            company_stock = self._get_company_stock_data(company)

            stock_by_company[company.id] = company_stock

            product_ids.update(
                product_id
                for product_id, stock_info in company_stock.items()
                if stock_info['qty'] != 0
            )

        if not product_ids:
            raise UserError(_(
                'No on-hand inventory was found in the selected '
                'companies internal warehouse locations.'
            ))

        products = self.env['product.product'].browse(
            sorted(product_ids)
        ).exists()

        # ----------------------------------------------
        # WORKBOOK
        # ----------------------------------------------

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {'in_memory': True},
        )

        sheet = workbook.add_worksheet(
            'Consolidated Inventory'
        )

        sheet.hide_gridlines(2)
        sheet.freeze_panes(6, 2)
        sheet.set_zoom(90)

        # ----------------------------------------------
        # COLORS
        # ----------------------------------------------

        DARK_BLUE = '#17365D'
        MEDIUM_BLUE = '#4F7194'
        VERY_LIGHT_BLUE = '#F5F8FB'
        BORDER = '#D8E0E6'
        TEXT = '#263238'
        MUTED = '#78909C'
        WHITE = '#FFFFFF'
        TOTAL_BG = '#DCE6F1'

        # ----------------------------------------------
        # FORMATS
        # ----------------------------------------------

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

        info_label_fmt = workbook.add_format({
            'bold': True,
            'font_size': 9,
            'font_color': MUTED,
            'bg_color': VERY_LIGHT_BLUE,
            'border': 1,
            'border_color': BORDER,
            'align': 'center',
            'valign': 'vcenter',
        })

        info_value_fmt = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font_color': DARK_BLUE,
            'bg_color': VERY_LIGHT_BLUE,
            'border': 1,
            'border_color': BORDER,
            'align': 'left',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        group_header_fmt = workbook.add_format({
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

        header_fmt = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font_color': WHITE,
            'bg_color': MEDIUM_BLUE,
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

        # ----------------------------------------------
        # DYNAMIC COLUMNS
        # Product | Vendor
        # Company: Qty | Unit Cost | Total Value
        # Grand Total: Qty | Total Value
        # ----------------------------------------------

        company_count = len(companies)

        total_start_col = 2 + (company_count * 3)
        last_col = total_start_col + 1

        sheet.set_column(0, 0, 38)  # Product
        sheet.set_column(1, 1, 28)  # Vendor

        for index, company in enumerate(companies):
            start_col = 2 + (index * 3)

            sheet.set_column(start_col, start_col, 15)
            sheet.set_column(start_col + 1, start_col + 1, 15)
            sheet.set_column(start_col + 2, start_col + 2, 19)

        sheet.set_column(total_start_col, total_start_col, 16)
        sheet.set_column(total_start_col + 1, total_start_col + 1, 20)

        # ----------------------------------------------
        # REPORT HEADING
        # ----------------------------------------------

        sheet.set_row(0, 36)

        sheet.merge_range(
            0, 0, 0, last_col,
            'Consolidated Inventory Report',
            title_fmt,
        )

        sheet.set_row(1, 22)

        pakistan_tz = pytz.timezone('Asia/Karachi')
        print_datetime = datetime.now(pytz.utc).astimezone(pakistan_tz)

        sheet.merge_range(
            1, 0, 1, last_col,
            (
                'Company-wise Stock Quantity | Unit Cost | Inventory Valuation'
                f'                        Printed On: {print_datetime.strftime("%d-%m-%Y %I:%M:%S %p")}'
            ),
            subtitle_fmt,
        )

        # ----------------------------------------------
        # SELECTED COMPANIES INFORMATION
        # ----------------------------------------------

        sheet.set_row(2, 32)

        sheet.merge_range(
            2, 0, 2, 1,
            'SELECTED COMPANIES',
            info_label_fmt,
        )

        company_names = ', '.join(companies.mapped('name'))

        sheet.merge_range(
            2, 2, 2, last_col,
            company_names,
            info_value_fmt,
        )

        # ----------------------------------------------
        # TWO-LEVEL TABLE HEADER
        # ----------------------------------------------

        group_row = 4
        subheader_row = 5

        sheet.set_row(group_row, 30)
        sheet.set_row(subheader_row, 28)

        sheet.merge_range(
            group_row, 0,
            subheader_row, 0,
            'Product',
            header_left_fmt,
        )

        sheet.merge_range(
            group_row, 1,
            subheader_row, 1,
            'Vendor',
            header_left_fmt,
        )

        for index, company in enumerate(companies):
            start_col = 2 + (index * 3)

            sheet.merge_range(
                group_row, start_col,
                group_row, start_col + 2,
                company.name,
                group_header_fmt,
            )

            sheet.write(subheader_row, start_col, 'Qty', header_fmt)
            sheet.write(subheader_row, start_col + 1, 'Unit Cost', header_fmt)
            sheet.write(subheader_row, start_col + 2, 'Total Value', header_fmt)

        sheet.merge_range(
            group_row, total_start_col,
            group_row, total_start_col + 1,
            'Grand Total',
            group_header_fmt,
        )

        sheet.write(subheader_row, total_start_col, 'Qty', header_fmt)
        sheet.write(subheader_row, total_start_col + 1, 'Total Value', header_fmt)

        # ----------------------------------------------
        # DATA AND TOTALS
        # ----------------------------------------------

        row = subheader_row + 1

        grand_total_qty = 0.0
        grand_total_value = 0.0

        company_totals = {
            company.id: {
                'qty': 0.0,
                'value': 0.0,
            }
            for company in companies
        }

        for index, product in enumerate(products):
            is_alt = index % 2 == 1

            text_fmt = cell_alt_fmt if is_alt else cell_fmt
            num_fmt = number_alt_fmt if is_alt else number_fmt

            sheet.set_row(row, 23)

            sheet.write(
                row, 0,
                product.display_name or '',
                text_fmt,
            )

            sheet.write(
                row, 1,
                ', '.join(product.vendor_id.mapped('name'))
                if product.vendor_id else '',
                text_fmt,
            )

            product_total_qty = 0.0
            product_total_value = 0.0

            for company_index, company in enumerate(companies):
                start_col = 2 + (company_index * 3)

                stock_info = stock_by_company[company.id].get(
                    product.id,
                    {'qty': 0.0, 'value': 0.0},
                )

                qty = stock_info['qty']
                value = stock_info['value']

                # Weighted average unit cost
                unit_cost = value / qty if qty else 0.0

                sheet.write_number(row, start_col, qty, num_fmt)
                sheet.write_number(row, start_col + 1, unit_cost, num_fmt)
                sheet.write_number(row, start_col + 2, value, num_fmt)

                company_totals[company.id]['qty'] += qty
                company_totals[company.id]['value'] += value

                product_total_qty += qty
                product_total_value += value

            sheet.write_number(
                row, total_start_col,
                product_total_qty,
                num_fmt,
            )

            sheet.write_number(
                row, total_start_col + 1,
                product_total_value,
                num_fmt,
            )

            grand_total_qty += product_total_qty
            grand_total_value += product_total_value

            row += 1

        # ----------------------------------------------
        # GRAND TOTAL ROW
        # ----------------------------------------------

        sheet.set_row(row, 30)

        sheet.write(row, 0, 'GRAND TOTAL', total_label_fmt)
        sheet.write(row, 1, '   ' , total_label_fmt)
        for company_index, company in enumerate(companies):
            start_col = 2 + (company_index * 3)

            sheet.write_number(
                row,
                start_col,
                company_totals[company.id]['qty'],
                total_number_fmt,
            )

            sheet.write_blank(
                row,
                start_col + 1,
                None,
                total_label_fmt,
            )

            sheet.write_number(
                row,
                start_col + 2,
                company_totals[company.id]['value'],
                total_number_fmt,
            )

        sheet.write_number(
            row, total_start_col,
            grand_total_qty,
            total_number_fmt,
        )

        sheet.write_number(
            row, total_start_col + 1,
            grand_total_value,
            total_number_fmt,
        )

        # ----------------------------------------------
        # AUTOFILTER AND PRINT SETTINGS
        # ----------------------------------------------

        if products:
            sheet.autofilter(
                subheader_row,
                0,
                row - 1,
                last_col,
            )

        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_margins(0.25, 0.25, 0.5, 0.5)
        sheet.repeat_rows(group_row, subheader_row)

        # ----------------------------------------------
        # CREATE DOWNLOAD
        # ----------------------------------------------

        workbook.close()

        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'Consolidated_Inventory_Report.xlsx',
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