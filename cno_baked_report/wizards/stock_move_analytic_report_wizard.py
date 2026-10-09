import io
import base64
import logging
from datetime import datetime, time
from collections import defaultdict
import xlsxwriter

_logger = logging.getLogger(__name__)

from odoo import api, fields, models


class StockMoveAnalyticReportWizard(models.TransientModel):
    _name = "stock.move.analytic.report.wizard"
    _description = "Stock Move Analytic Excel Report Wizard"

    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True)
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        domain="[('plan_id.is_pos_plan', '=', True)]",
    )

    def action_print_report(self):
        self.ensure_one()

        _logger.info("=== [ANALYTIC REPORT DEBUG] START ===")
        _logger.info(
            "date_from=%s date_to=%s analytic_account_id=%s",
            self.date_from,
            self.date_to,
            self.analytic_account_id
        )

        if self.analytic_account_id:
            accounts = self.analytic_account_id
        else:
            accounts = self.env["account.analytic.account"].with_context(
                active_test=False
            ).search([("plan_id.is_pos_plan", "=", True)])

        _logger.info(
            "Accounts fetched (%s): %s",
            len(accounts),
            [(a.id, a.name) for a in accounts]
        )

        date_from = self.date_from
        date_to = self.date_to

        if date_to and not isinstance(date_to, datetime):
            date_to = datetime.combine(date_to, time(23, 59, 59))

        if date_from and not isinstance(date_from, datetime):
            date_from = datetime.combine(date_from, time(0, 0, 0))

        _logger.info(
            "Normalized date_from=%s date_to=%s",
            date_from,
            date_to
        )

        scraps = self.env["stock.scrap"].search([
            ("create_date", ">=", date_from),
            ("create_date", "<=", date_to),
        ])

        move_ids = scraps.mapped("move_ids").ids

        domain = [
            ("id", "in", move_ids),
            ("state", "=", "done"),
            ("analytic_distribution", "!=", False),
        ]

        _logger.info(
            "Stock move search domain (filtered by scrap create_date): %s",
            domain
        )

        moves = self.env["stock.move"].search(domain)

        _logger.info("Moves found: %s", len(moves))

        for m in moves:
            _logger.info(
                "Move id=%s expiry_date=%s state=%s product=%s analytic_distribution=%s",
                m.id,
                m.expiry_date,
                m.state,
                m.product_id.display_name,
                m.analytic_distribution
            )

        if not moves:
            _logger.warning(
                "No stock moves matched the domain at all — check date range/state/"
                "analytic_distribution presence before looking at per-account matching."
            )

        account_product_data = {}
        product_info = {}
        product_order = []

        for account in accounts:
            account_id_str = str(account.id)

            _logger.info(
                "--- Matching moves for account: %s (id=%s / id_str=%r) ---",
                account.name,
                account.id,
                account_id_str
            )

            product_data = defaultdict(
                lambda: {
                    "qty": 0.0,
                    "returned": 0.0,
                    "loss": 0.0,
                    "vendor": ""
                }
            )

            for move in moves:
                if not move.analytic_distribution:
                    continue

                for key, percentage in move.analytic_distribution.items():

                    account_ids_in_key = [
                        k.strip() for k in key.split(",")
                    ]

                    if account_id_str not in account_ids_in_key:
                        _logger.info(
                            "  NO MATCH: move %s key %r did not contain account_id %r",
                            move.id,
                            key,
                            account_id_str
                        )
                        continue

                    _logger.info(
                        "  MATCH: move %s matched account %s via key %r (pct=%s)",
                        move.id,
                        account.id,
                        key,
                        percentage
                    )

                    product = move.product_id

                    vendor = (
                        product.seller_ids[:1].partner_id.name
                        if product.seller_ids
                        else ""
                    )

                    ratio = percentage / 100.0
                    qty = move.Qty * ratio

                    list_price = product.list_price
                    expiration_per = (
                        product.expiration_per or 0.0
                    ) / 100.0

                    loss_amount = (
                        qty * expiration_per * list_price
                    )

                    returned_amount = (
                        qty * (1 - expiration_per) * list_price
                    )

                    pid = product.id

                    if pid not in product_info:
                        product_info[pid] = {
                            "display_name": product.display_name,
                            "vendor": vendor,
                        }

                        product_order.append(pid)

                    product_data[pid]["qty"] += qty
                    product_data[pid]["returned"] += returned_amount
                    product_data[pid]["loss"] += loss_amount

                    if vendor:
                        product_data[pid]["vendor"] = vendor

                    _logger.info(
                        "  Accumulated for account=%s product=%s: qty=%s returned=%s loss=%s",
                        account.name,
                        product.display_name,
                        product_data[pid]["qty"],
                        product_data[pid]["returned"],
                        product_data[pid]["loss"]
                    )

                    break

            if product_data:
                account_product_data[account.id] = product_data

                _logger.info(
                    "Account %s (%s): %s distinct products matched",
                    account.name,
                    account.id,
                    len(product_data)
                )

            else:
                _logger.info(
                    "Account %s (%s) has NO matched data — excluding it from the report",
                    account.name,
                    account.id
                )

        accounts_with_data = accounts.filtered(
            lambda a: a.id in account_product_data
        )

        _logger.info(
            "Accounts with data (%s): %s",
            len(accounts_with_data),
            [(a.id, a.name) for a in accounts_with_data]
        )

        _logger.info(
            "Global product order (%s products): %s",
            len(product_order),
            [product_info[p]["display_name"] for p in product_order]
        )

        # ==============================================================
        # EXCEL
        # ==============================================================

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {"in_memory": True}
        )

        # ==============================================================
        # PREMIUM COLOR SCHEME
        # ==============================================================

        DARK_BLUE = "#17365D"
        MEDIUM_BLUE = "#4F7194"
        LIGHT_BLUE = "#EAF0F6"
        VERY_LIGHT_BLUE = "#F5F8FB"
        BORDER = "#D8E0E6"
        TEXT = "#263238"
        MUTED = "#78909C"
        WHITE = "#FFFFFF"

        # ==============================================================
        # FORMATS
        # ==============================================================

        title_fmt = workbook.add_format({
            "bold": True,
            "font_size": 20,
            "font_color": DARK_BLUE,
            "align": "left",
            "valign": "vcenter",
        })

        subtitle_fmt = workbook.add_format({
            "font_size": 10,
            "font_color": MUTED,
            "align": "left",
            "valign": "vcenter",
        })

        date_label_fmt = workbook.add_format({
            "bold": True,
            "font_size": 9,
            "font_color": MUTED,
            "bg_color": VERY_LIGHT_BLUE,
            "border": 1,
            "border_color": BORDER,
            "align": "center",
            "valign": "vcenter",
        })

        date_value_fmt = workbook.add_format({
            "bold": True,
            "font_size": 10,
            "font_color": TEXT,
            "bg_color": VERY_LIGHT_BLUE,
            "border": 1,
            "border_color": BORDER,
            "align": "center",
            "valign": "vcenter",
        })

        header_fmt = workbook.add_format({
            "bold": True,
            "bg_color": DARK_BLUE,
            "font_color": WHITE,
            "border": 1,
            "border_color": DARK_BLUE,
            "align": "center",
            "valign": "vcenter",
            "font_size": 10,
        })

        header_left_fmt = workbook.add_format({
            "bold": True,
            "bg_color": DARK_BLUE,
            "font_color": WHITE,
            "border": 1,
            "border_color": DARK_BLUE,
            "align": "left",
            "valign": "vcenter",
            "font_size": 10,
        })

        cell_fmt = workbook.add_format({
            "border": 1,
            "border_color": BORDER,
            "font_color": TEXT,
            "valign": "vcenter",
        })

        cell_alt_fmt = workbook.add_format({
            "border": 1,
            "border_color": BORDER,
            "font_color": TEXT,
            "bg_color": "#FAFBFC",
            "valign": "vcenter",
        })

        number_fmt = workbook.add_format({
            "border": 1,
            "border_color": BORDER,
            "font_color": TEXT,
            "num_format": '#,##0.00',
            "align": "right",
            "valign": "vcenter",
        })

        number_alt_fmt = workbook.add_format({
            "border": 1,
            "border_color": BORDER,
            "font_color": TEXT,
            "bg_color": "#FAFBFC",
            "num_format": '#,##0.00',
            "align": "right",
            "valign": "vcenter",
        })

        # ==============================================================
        # WORKSHEET
        # ==============================================================

        sheet = workbook.add_worksheet("Product Expiry Report")

        sheet.hide_gridlines(2)

        # Row heights
        sheet.set_row(0, 30)
        sheet.set_row(1, 20)
        sheet.set_row(2, 24)

        # ==============================================================
        # REPORT HEADING
        # ==============================================================

        sheet.merge_range(
            0,
            0,
            0,
            4,
            "Product Expiry Report",
            title_fmt
        )

        sheet.merge_range(
            0,
            5,
            0,
            7,
            "Inventory & Expiry Analysis",
            subtitle_fmt
        )

        # ==============================================================
        # DATE INFORMATION
        # ==============================================================

        sheet.merge_range(
            1,
            0,
            1,
            1,
            "REPORT PERIOD",
            date_label_fmt
        )

        sheet.merge_range(
            1,
            2,
            1,
            3,
            f"{self.date_from.strftime('%d-%b-%Y')}  →  "
            f"{self.date_to.strftime('%d-%b-%Y')}",
            date_value_fmt
        )

        # ==============================================================
        # MAIN TABLE HEADER
        # ==============================================================

        sheet.merge_range(
            2,
            0,
            3,
            0,
            "Item Name",
            header_left_fmt
        )

        sheet.merge_range(
            2,
            1,
            3,
            1,
            "Vendor Name",
            header_left_fmt
        )

        sheet.set_column(0, 0, 40)
        sheet.set_column(1, 1, 25)

        col = 2
        account_col_start = {}

        for account in accounts_with_data:

            start = col
            end = col + 2

            sheet.merge_range(
                2,
                start,
                2,
                end,
                account.name,
                header_fmt
            )

            sheet.write(
                3,
                start,
                "Qty",
                header_fmt
            )

            sheet.write(
                3,
                start + 1,
                "Returned Amount",
                header_fmt
            )

            sheet.write(
                3,
                start + 2,
                "Loss Amount",
                header_fmt
            )

            sheet.set_column(
                start,
                end,
                16
            )

            account_col_start[account.id] = start

            col = end + 1

        # ==============================================================
        # AGGREGATED
        # ==============================================================

        total_col_start = col

        sheet.merge_range(
            2,
            total_col_start,
            2,
            total_col_start + 2,
            "Aggregated",
            header_fmt
        )

        sheet.write(
            3,
            total_col_start,
            "Total Qty",
            header_fmt
        )

        sheet.write(
            3,
            total_col_start + 1,
            "Total Returned Amt",
            header_fmt
        )

        sheet.write(
            3,
            total_col_start + 2,
            "Total Loss Amt",
            header_fmt
        )

        sheet.set_column(
            total_col_start,
            total_col_start + 2,
            18
        )

        _logger.info(
            "Account column start positions: %s",
            account_col_start
        )

        _logger.info(
            "Total (aggregated) column start position: %s",
            total_col_start
        )

        # ==============================================================
        # DATA
        # ==============================================================

        row = 4

        for row_index, pid in enumerate(product_order):

            info = product_info[pid]

            is_alt = row_index % 2 == 1

            current_cell_fmt = (
                cell_alt_fmt if is_alt else cell_fmt
            )

            current_number_fmt = (
                number_alt_fmt if is_alt else number_fmt
            )

            sheet.write(
                row,
                0,
                info["display_name"],
                current_cell_fmt
            )

            sheet.write(
                row,
                1,
                info["vendor"],
                current_cell_fmt
            )

            total_qty = 0.0
            total_returned = 0.0
            total_loss = 0.0

            for account in accounts_with_data:

                start = account_col_start[account.id]

                data = account_product_data[
                    account.id
                ].get(pid)

                if data:

                    sheet.write(
                        row,
                        start,
                        data["qty"],
                        current_number_fmt
                    )

                    sheet.write(
                        row,
                        start + 1,
                        data["returned"],
                        current_number_fmt
                    )

                    sheet.write(
                        row,
                        start + 2,
                        data["loss"],
                        current_number_fmt
                    )

                    total_qty += data["qty"]
                    total_returned += data["returned"]
                    total_loss += data["loss"]

                else:

                    sheet.write(
                        row,
                        start,
                        "",
                        current_cell_fmt
                    )

                    sheet.write(
                        row,
                        start + 1,
                        "",
                        current_cell_fmt
                    )

                    sheet.write(
                        row,
                        start + 2,
                        "",
                        current_cell_fmt
                    )

            sheet.write(
                row,
                total_col_start,
                total_qty,
                current_number_fmt
            )

            sheet.write(
                row,
                total_col_start + 1,
                total_returned,
                current_number_fmt
            )

            sheet.write(
                row,
                total_col_start + 2,
                total_loss,
                current_number_fmt
            )

            row += 1

        # ==============================================================
        # CLOSE
        # ==============================================================

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(
            output.read()
        )

        output.close()

        attachment = self.env["ir.attachment"].create({
            "name": "Product_Expiry_Report.xlsx",
            "type": "binary",
            "datas": file_data,
            "res_model": self._name,
            "res_id": self.id,
        })

        _logger.info(
            "=== [ANALYTIC REPORT DEBUG] END, attachment id=%s ===",
            attachment.id
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }

