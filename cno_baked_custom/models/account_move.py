# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    vendor_settlement_entry = fields.Boolean(string='Vendor Settlement Entry')
    expenses_voucher_id = fields.Many2one(comodel_name='expenses.voucher',string='Expenses Voucher')
    def action_post(self):
        self = self.with_context(disable_abnormal_invoice_detection=True)
        res = super().action_post()
        for move in self:
            if move.move_type != 'in_invoice':
                continue

            if not move.invoice_line_ids:
                continue

            misc_journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)

            lines = []

            for line in move.invoice_line_ids:
                product = line.product_id

                credit_line = move.line_ids.filtered(lambda l: l.credit > 0.0)[:1]
                if credit_line and product and product.account_credit_id and product.payable_suppl_2221001_id:
                    amount = line.price_subtotal

                    payable_account = credit_line.account_id

                    lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'account_id': product.payable_suppl_2221001_id.id,
                        'debit': amount,
                        'credit': 0.0,
                        'name': 'Revsl/'+ move.name,
                        'partner_id': move.partner_id.id,
                    }))

                    lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'account_id': product.account_credit_id.id,
                        'debit': 0.0,
                        'credit': amount,
                        'name': product.name,
                        'partner_id': move.partner_id.id,
                    }))

            if lines:
                move_obj = self.env['account.move'].create({
                    'ref': move.name,
                    'journal_id': misc_journal.id,
                    'move_type': 'entry',
                    'line_ids': lines,
                })
                move_obj.action_post()

        return res

    def _get_accounting_date(self, invoice_date, has_tax):
        # not related, just ensuring normal flow untouched
        return super()._get_accounting_date(invoice_date, has_tax)

    def _sync_dynamic_lines(self, container):
        res = super()._sync_dynamic_lines(container)
        for move in self:
            if move.move_type in ('in_invoice', 'in_refund', 'out_invoice', 'out_refund'):
                analytic_distribution = {}
                for l in move.invoice_line_ids:
                    if l.analytic_distribution:
                        analytic_distribution.update(l.analytic_distribution)
                if analytic_distribution:
                    term_lines = move.line_ids.filtered(
                        lambda l: l.display_type == 'payment_term'
                    )
                    term_lines.analytic_distribution = analytic_distribution
        return res


