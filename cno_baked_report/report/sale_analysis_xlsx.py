import base64
import io
import os
from odoo import models
from datetime import timedelta
from odoo.exceptions import UserError

dirname = os.path.dirname(__file__)


class SaleAnalysisXlsx(models.AbstractModel):
    _name = 'report.cno_baked_report.sale_analysis_report_id_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, report):
        sheet = workbook.add_worksheet('Sale Analysis Report')
        center = workbook.add_format({'align': 'center'})
        center_left = workbook.add_format({'align': 'left'})
        center_right = workbook.add_format({'align': 'right'})
        bold = workbook.add_format({'bold': True, 'align': 'center'})
        bold_left = workbook.add_format({'bold': True, 'align': 'left'})
        bold_right = workbook.add_format({'bold': True, 'align': 'right'})
        date_style_1 = workbook.add_format(
            {'text_wrap': True, 'num_format': 'dd-mm-yyyy', 'align': 'center', 'font_size': 10, 'bold': True, })
        date_style = workbook.add_format(
            {'num_format': 'dd-mm-yyyy', 'align': 'center', })
        format3_colored = workbook.add_format(
            {'align': 'center', 'bg_color': '#87CEEB', 'bold': True, 'font_color': 'white'})
        format3_colored_left = workbook.add_format(
            {'align': 'left', 'bg_color': '#87CEEB', 'bold': True, 'font_color': 'white'})
        format3_colored_right = workbook.add_format(
            {'align': 'right', 'bg_color': '#87CEEB', 'bold': True, 'font_color': 'white'})

        res_company = self.env.user.company_id
        sheet.set_column('A:V', 20)

        r = 1
        co = 0
        row = 3

        # Formatting the date from and to
        f_date = ((report.date_from) + timedelta(hours=5)).strftime("%d-%m-%Y %H:%M:%S")
        t_date = ((report.date_to) + timedelta(hours=5)).strftime("%d-%m-%Y %H:%M:%S")



        sheet.merge_range(r, co, r, co + 6, 'Sale Analysis Report', bold)
        r += 1
        sheet.merge_range(r, co, r, co + 6, f'Date From:  {f_date}  Date To:  {t_date}', date_style_1)

        # Query pos.orders within the specified date range
        domain = [
            ('date_order', '>=', report.date_from),
            ('date_order', '<=', report.date_to),
        ]

        if report.allowed_pos:
            domain.append(
                ('session_id.config_id', 'in', report.allowed_pos.ids)
            )

        pos_orders = self.env['pos.order'].search(
            domain,
            order='date_order asc'
        )

        if not pos_orders:
            raise UserError("No POS orders found in the specified date range.")

        # Column headers for the report
        r += 2
        sheet.write(row, 0, 'Date', format3_colored)
        sheet.write(row, 1, 'Time', format3_colored)
        sheet.write(row, 2, 'POS Session', format3_colored)
        sheet.write(row, 3, 'Receipt Number', format3_colored)
        sheet.write(row, 4, 'Receipt Type', format3_colored)
        sheet.write(row, 5, 'Vendor', format3_colored)
        sheet.write(row, 6, 'Stream', format3_colored)
        sheet.write(row, 7, 'Brands', format3_colored)
        sheet.write(row, 8, 'Category', format3_colored)
        sheet.write(row, 9, 'SKU', format3_colored)
        sheet.write(row, 10, 'Item', format3_colored)
        sheet.write(row, 11, 'Quantity', format3_colored)
        sheet.write(row, 12, 'Gross sales', format3_colored)
        sheet.write(row, 13, 'Discount Name', format3_colored)
        sheet.write(row, 14, 'Discount %', format3_colored)
        sheet.write(row, 15, 'Discount Amt', format3_colored)
        sheet.write(row, 16, 'Net sales', format3_colored)
        sheet.write(row, 17, 'Unit Cost/Vendor Cost', format3_colored)
        sheet.write(row, 18, 'COGS/Vendor Cost', format3_colored)
        sheet.write(row, 19, 'Item Gross Profit', format3_colored)
        sheet.write(row, 20, 'Item Profit Margin %', format3_colored)
        sheet.write(row, 21, 'Tax Rate (POS)', format3_colored)
        sheet.write(row, 22, 'Tax Amount', format3_colored)
        sheet.write(row, 23, 'Commission Rate', format3_colored)
        sheet.write(row, 24, 'Commission Income', format3_colored)
        sheet.write(row, 25, 'Vendor Basis', format3_colored)
        sheet.write(row, 26, 'COGS Basis', format3_colored)
        sheet.write(row, 27, 'Profit Classification', format3_colored)
        sheet.write(row, 28, 'Invoice QR', format3_colored)
        sheet.write(row, 29, 'MOP', format3_colored)
        sheet.write(row, 30, 'Store', format3_colored)
        sheet.write(row, 31, 'Cashier Name', format3_colored)
        sheet.write(row, 32, 'Customer Name', format3_colored)
        sheet.write(row, 33, 'Customer Contacts', format3_colored)
        row += 1

        # Loop through the pos orders and display the corresponding order lines
        for order in pos_orders:
            payment_methods = []
            # Loop through the payment methods and collect their names
            for pay in order.payment_ids:
                mop = pay.payment_method_id.name
                payment_methods.append(mop)  # Add the payment method name to the list
            # Join the payment method names with a comma separator
            payment_methods_str = ', '.join(payment_methods)

            for line in order.lines:
                date = ((order.date_order) + timedelta(hours=5)).strftime("%d-%m-%Y")
                time = ((order.date_order) + timedelta(hours=5)).strftime("%H:%M")
                vendor_name = line.product_id.vendor_id.name if line.product_id.vendor_id else ''
                cogs_b = line.product_id.cogs_basis_id.name if line.product_id.cogs_basis_id else ''
                pro_classi = line.product_id.profit_classification_id.name if line.product_id.profit_classification_id else ''
                customer_name = order.partner_id.name if order.partner_id else ''
                customer_contact = order.partner_id.phone if order.partner_id else ''
                receipt_type = 'Refund' if order.amount_total < 0 else 'Sale'
                dic = (line.discount * (line.qty*line.price_unit))/100
                net_sale = (line.qty*line.price_unit) - dic
                cost_goods = line.qty * line.product_id.standard_price
                gross_pro = net_sale - cost_goods
                taxes = line.price_subtotal_incl - line.price_subtotal
                if order.amount_total < 0:
                    taxes = -1 * taxes
                tax_per = ', '.join(
                    f"{tax.amount}%"
                    for tax in line.tax_ids_after_fiscal_position
                )
                sheet.write(row, 0, date, center_left)
                sheet.write(row, 1, time, center_left)
                sheet.write(row, 2, order.session_id.name, center_left)
                sheet.write(row, 3, order.name, center_left)
                sheet.write(row, 4, receipt_type, center_left)
                sheet.write(row, 5, vendor_name, center_left)
                sheet.write(row, 6, line.product_id.stream, center_left)
                sheet.write(row, 7, line.product_id.brand, center_left)
                sheet.write(row, 8, line.product_id.categ_id.name, center_left)
                sheet.write(row, 9, line.product_id.default_code, center_left)
                sheet.write(row, 10, line.product_id.name, center_left)
                sheet.write(row, 11, line.qty, center_right)
                sheet.write(row, 12, line.qty*line.price_unit, center_right)
                sheet.write(row, 13, line.custom_discount_reason, center_left)
                sheet.write(row, 14, line.discount, center_right)
                sheet.write(row, 15, dic, center_right)
                sheet.write(row, 16, net_sale, center_right)
                sheet.write(row, 17, line.product_id.standard_price, center_right)
                sheet.write(row, 18, cost_goods, center_right)
                sheet.write(row, 19, net_sale-cost_goods, center_right)
                sheet.write(row, 20, f"{round(((net_sale - cost_goods) / net_sale) * 100) if net_sale else 0}%", center_right)
                sheet.write(row, 21, tax_per, center_right)
                sheet.write(row, 22, taxes, center_right)
                sheet.write(row, 23, f"{line.product_id.commission_per}%", center_right)
                sheet.write(row, 24, (line.qty*line.price_unit)*(line.product_id.commission_per/100), center_right)
                sheet.write(row, 25, (net_sale-cost_goods) - ((net_sale-cost_goods)*(line.product_id.commission_per/100)), center_right)
                sheet.write(row, 26, cogs_b, center_right)
                sheet.write(row, 27, pro_classi, center_right)
                sheet.write(row, 28, order.invoice_number, center_right)
                sheet.write(row, 29, payment_methods_str, center_left)
                sheet.write(row, 30, order.session_id.config_id.name, center_left)
                sheet.write(row, 31, order.user_id.name, center_left)
                sheet.write(row, 32, customer_name, center_left)
                sheet.write(row, 33, customer_contact, center_left)
                row += 1