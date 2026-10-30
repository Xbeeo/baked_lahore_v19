# -*- coding: utf-8 -*-
from odoo import api, models


class PurchaseLedgerReport(models.AbstractModel):
    _name = 'report.cno_baked_report.report_purchase_ledger'
    _description = 'Purchase Base Ledger Report Parser'

    def _get_moves_domain(self, data):
        domain = [
            ('move_type', '=', 'entry'),
            ('date', '>=', data.get('date_from')),
            ('date', '<=', data.get('date_to')),
            ('state', '=', 'posted'),
            ('ref', 'not ilike', 'INV'),
        ]
        return domain

    def _get_lines_domain(self, data, move_ids):
        domain = [
            ('move_id', 'in', move_ids),
            ('account_id', 'in', data.get('account_ids')),
        ]
        if data.get('partner_id'):
            domain.append(('partner_id', '=', data.get('partner_id')))
        return domain

    def _get_opening_balance(self, data, account_id):
        """Sum of debit - credit for this account (and partner/type filters)
        on entries dated strictly before the date_from."""
        domain = [
            ('move_id.move_type', '=', 'entry'),
            ('move_id.state', '=', 'posted'),
            ('account_id', '=', account_id),
            ('date', '<', data.get('date_from')),
        ]
        if data.get('partner_id'):
            domain.append(('partner_id', '=', data.get('partner_id')))
        lines = self.env['account.move.line'].search(domain)
        return sum(lines.mapped('debit')) - sum(lines.mapped('credit'))

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        wizard = self.env['purchase.ledger.wizard'].browse(data.get('wizard_id'))

        move_domain = self._get_moves_domain(data)
        moves = self.env['account.move'].search(move_domain)

        accounts = self.env['account.account'].browse(data.get('account_ids'))
        partner = self.env['res.partner'].browse(data.get('partner_id')) if data.get('partner_id') else False

        account_blocks = []
        grand_total_debit = 0.0
        grand_total_credit = 0.0

        for account in accounts:
            lines_domain = self._get_lines_domain(data, moves.ids)
            lines_domain.append(('account_id', '=', account.id))
            move_lines = self.env['account.move.line'].search(
                lines_domain, order='date asc, move_id asc, id asc'
            )

            bill_refs = move_lines.mapped('move_id.ref')
            bill_refs = [ref for ref in bill_refs if ref]

            if bill_refs:
                payments = self.env['account.payment'].search([
                    ('state', '=', 'paid'),
                    ('memo', 'in', bill_refs),
                ])
                payment_move_ids = payments.mapped('move_id').ids
                payable_lines = self.env['account.move.line'].search([
                    ('move_id', 'in', payment_move_ids),
                    ('account_id.account_type', '=', 'liability_payable'),
                ])

                move_lines = move_lines | payable_lines

            move_lines = move_lines.sorted(
                key=lambda line: (line.date, line.move_id.id, line.id)
            )



            balance = self._get_opening_balance(data, account.id)
            opening_balance = balance

            report_lines = []
            total_debit = 0.0
            total_credit = 0.0

            for line in move_lines:
                balance += line.debit - line.credit
                total_debit += line.debit
                total_credit += line.credit

                name_parts = [line.move_id.name or '']
                if line.move_id.ref:
                    name_parts.append(line.move_id.ref)
                if line.name:
                    name_parts.append(line.name)

                report_lines.append({
                    'name': ' - '.join(filter(None, name_parts)),
                    'date': line.date,
                    'partner': line.partner_id.name or '',
                    'currency': line.currency_id.name or line.company_currency_id.name or '',
                    'debit': line.debit,
                    'credit': line.credit,
                    'balance': balance,
                })

            grand_total_debit += total_debit
            grand_total_credit += total_credit

            account_blocks.append({
                'account': account,
                'opening_balance': opening_balance,
                'closing_balance': balance,
                'total_debit': total_debit,
                'total_credit': total_credit,
                'lines': report_lines,
            })

        return {
            'doc_ids': docids,
            'doc_model': 'purchase.ledger.wizard',
            'docs': wizard,
            'data': data,
            'account_blocks': account_blocks,
            'partner': partner,
            'grand_total_debit': grand_total_debit,
            'grand_total_credit': grand_total_credit,
            'grand_total_balance': grand_total_debit - grand_total_credit,
        }
