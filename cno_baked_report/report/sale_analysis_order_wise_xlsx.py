# -*- coding: utf-8 -*-

from odoo import models
from datetime import timedelta
from odoo.exceptions import UserError


class SaleAnalysisOrderWiseXlsx(models.AbstractModel):
    _name = 'report.cno_baked_report.sale_analysis_order_wise_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Sale Analysis Order Wise XLSX Report'

    def generate_xlsx_report(self, workbook, data, report):
        sheet = workbook.add_worksheet('Sale Analysis Report')

        center = workbook.add_format({
            'align': 'center'
        })

        center_left = workbook.add_format({
            'align': 'left'
        })

        center_right = workbook.add_format({
            'align': 'right'
        })

        bold = workbook.add_format({
            'bold': True,
            'align': 'center'
        })

        date_style_1 = workbook.add_format({
            'text_wrap': True,
            'num_format': 'dd-mm-yyyy',
            'align': 'center',
            'font_size': 10,
            'bold': True,
        })

        format3_colored = workbook.add_format({
            'align': 'center',
            'bg_color': '#87CEEB',
            'bold': True,
            'font_color': 'white'
        })

        sheet.set_column('A:AH', 20)

        r = 1
        co = 0
        row = 3

        # ==========================
        # DATE
        # ==========================

        f_date = (
            report.date_from + timedelta(hours=5)
        ).strftime("%d-%m-%Y %H:%M:%S")

        t_date = (
            report.date_to + timedelta(hours=5)
        ).strftime("%d-%m-%Y %H:%M:%S")

        sheet.merge_range(
            r,
            co,
            r,
            co + 6,
            'Sale Analysis Order Wise Report',
            bold
        )

        r += 1

        sheet.merge_range(
            r,
            co,
            r,
            co + 6,
            f'Date From: {f_date}  Date To: {t_date}',
            date_style_1
        )

        # ==========================
        # POS ORDER DOMAIN
        # ==========================

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
            raise UserError(
                "No POS orders found in the specified date range."
            )

        # ==========================
        # HEADERS
        # ==========================

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
        sheet.write(row, 10, 'Order', format3_colored)
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

        # ==========================
        # ONE ROW PER ORDER
        # ==========================

        for order in pos_orders:

            # --------------------------
            # DATE / TIME
            # --------------------------

            date = (
                order.date_order + timedelta(hours=5)
            ).strftime("%d-%m-%Y")

            time = (
                order.date_order + timedelta(hours=5)
            ).strftime("%H:%M")

            # --------------------------
            # PAYMENT METHODS
            # --------------------------

            payment_methods = []

            for pay in order.payment_ids:
                if pay.payment_method_id:
                    payment_methods.append(
                        pay.payment_method_id.name
                    )

            payment_methods_str = ', '.join(
                payment_methods
            )

            # --------------------------
            # ORDER LINES
            # --------------------------

            lines = order.lines

            # Quantity
            total_quantity = sum(
                line.qty for line in lines
            )

            # Gross Sales
            gross_sales = sum(
                line.qty * line.price_unit
                for line in lines
            )

            # Discount Amount
            discount_amt = sum(
                (
                    line.discount *
                    (line.qty * line.price_unit)
                ) / 100
                for line in lines
            )

            # Net Sales
            net_sale = gross_sales - discount_amt

            # COGS
            cost_goods = sum(
                line.qty * line.product_id.standard_price
                for line in lines
            )

            # Gross Profit
            gross_profit = net_sale - cost_goods

            # Tax
            taxes = sum(
                line.price_subtotal_incl -
                line.price_subtotal
                for line in lines
            )

            if order.amount_total < 0:
                taxes = -1 * taxes

            # Commission
            commission_income = sum(
                (
                    line.qty * line.price_unit
                ) *
                (
                    line.product_id.commission_per / 100
                )
                for line in lines
            )

            # Vendor Basis
            vendor_basis = gross_profit - commission_income

            # --------------------------
            # DISCOUNT NAME
            # --------------------------

            discount_names = []

            for line in lines:
                if line.custom_discount_reason:
                    discount_names.append(
                        line.custom_discount_reason
                    )

            discount_name = ', '.join(
                list(dict.fromkeys(discount_names))
            )

            # --------------------------
            # DISCOUNT %
            # --------------------------

            discount_percentages = []

            for line in lines:
                if line.discount:
                    discount_percentages.append(
                        str(line.discount)
                    )

            discount_percentage = ', '.join(
                list(dict.fromkeys(discount_percentages))
            )

            # --------------------------
            # TAX RATE
            # --------------------------

            tax_rates = []

            for line in lines:
                for tax in line.tax_ids_after_fiscal_position:
                    tax_rates.append(
                        f"{tax.amount}%"
                    )

            tax_rate = ', '.join(
                list(dict.fromkeys(tax_rates))
            )

            # --------------------------
            # COMMISSION RATE
            # --------------------------

            commission_rates = []

            for line in lines:
                commission_rates.append(
                    f"{line.product_id.commission_per}%"
                )

            commission_rate = ', '.join(
                list(dict.fromkeys(commission_rates))
            )

            # --------------------------
            # PRODUCT INFORMATION
            # --------------------------
            #
            # Since this is ORDER WISE,
            # there is no individual product.
            #
            # We keep these columns blank
            # except Item = order.name.
            #

            vendor_names = list(dict.fromkeys(
                line.product_id.vendor_id.name
                for line in lines
                if line.product_id.vendor_id
            ))

            streams = list(dict.fromkeys(
                line.product_id.stream
                for line in lines
                if line.product_id.stream
            ))

            brands = list(dict.fromkeys(
                line.product_id.brand
                for line in lines
                if line.product_id.brand
            ))

            categories = list(dict.fromkeys(
                line.product_id.categ_id.name
                for line in lines
                if line.product_id.categ_id
            ))

            skus = list(dict.fromkeys(
                line.product_id.default_code
                for line in lines
                if line.product_id.default_code
            ))

            cogs_bases = list(dict.fromkeys(
                line.product_id.cogs_basis_id.name
                for line in lines
                if line.product_id.cogs_basis_id
            ))

            profit_classifications = list(dict.fromkeys(
                line.product_id.profit_classification_id.name
                for line in lines
                if line.product_id.profit_classification_id
            ))

            # --------------------------
            # CUSTOMER
            # --------------------------

            customer_name = (
                order.partner_id.name
                if order.partner_id
                else ''
            )

            customer_contact = (
                order.partner_id.phone
                if order.partner_id
                else ''
            )

            # --------------------------
            # RECEIPT TYPE
            # --------------------------

            receipt_type = (
                'Refund'
                if order.amount_total < 0
                else 'Sale'
            )

            # --------------------------
            # PROFIT MARGIN
            # --------------------------

            profit_margin = (
                (gross_profit / net_sale) * 100
                if net_sale
                else 0
            )

            # --------------------------
            # WRITE ONE ORDER ROW
            # --------------------------

            sheet.write(row, 0, date, center_left)
            sheet.write(row, 1, time, center_left)
            sheet.write(
                row, 2,
                order.session_id.name,
                center_left
            )
            sheet.write(
                row, 3,
                order.name,
                center_left
            )
            sheet.write(
                row, 4,
                receipt_type,
                center_left
            )
            sheet.write(
                row, 5,
                ', '.join(vendor_names),
                center_left
            )
            sheet.write(
                row, 6,
                ', '.join(streams),
                center_left
            )
            sheet.write(
                row, 7,
                ', '.join(brands),
                center_left
            )
            sheet.write(
                row, 8,
                ', '.join(categories),
                center_left
            )
            sheet.write(
                row, 9,
                ', '.join(skus),
                center_left
            )

            # IMPORTANT:
            # Item = POS ORDER NAME
            sheet.write(
                row, 10,
                order.name,
                center_left
            )

            sheet.write(
                row, 11,
                total_quantity,
                center_right
            )
            sheet.write(
                row, 12,
                gross_sales,
                center_right
            )
            sheet.write(
                row, 13,
                discount_name,
                center_left
            )
            sheet.write(
                row, 14,
                discount_percentage,
                center_right
            )
            sheet.write(
                row, 15,
                discount_amt,
                center_right
            )
            sheet.write(
                row, 16,
                net_sale,
                center_right
            )

            # No single product cost in order-wise report.
            # We use total COGS / total quantity as average unit cost.
            unit_cost = (
                cost_goods / total_quantity
                if total_quantity
                else 0
            )

            sheet.write(
                row, 17,
                unit_cost,
                center_right
            )
            sheet.write(
                row, 18,
                cost_goods,
                center_right
            )
            sheet.write(
                row, 19,
                gross_profit,
                center_right
            )
            sheet.write(
                row, 20,
                f"{round(profit_margin)}%",
                center_right
            )
            sheet.write(
                row, 21,
                tax_rate,
                center_right
            )
            sheet.write(
                row, 22,
                taxes,
                center_right
            )
            sheet.write(
                row, 23,
                commission_rate,
                center_right
            )
            sheet.write(
                row, 24,
                commission_income,
                center_right
            )
            sheet.write(
                row, 25,
                vendor_basis,
                center_right
            )
            sheet.write(
                row, 26,
                ', '.join(cogs_bases),
                center_left
            )
            sheet.write(
                row, 27,
                ', '.join(profit_classifications),
                center_left
            )
            sheet.write(
                row, 28,
                order.invoice_number or '',
                center_left
            )
            sheet.write(
                row, 29,
                payment_methods_str,
                center_left
            )
            sheet.write(
                row, 30,
                order.session_id.config_id.name,
                center_left
            )
            sheet.write(
                row, 31,
                order.user_id.name,
                center_left
            )
            sheet.write(
                row, 32,
                customer_name,
                center_left
            )
            sheet.write(
                row, 33,
                customer_contact,
                center_left
            )

            # IMPORTANT:
            # Only move to next row.
            # No order total.
            # No grand total.
            row += 1
