import io
import base64
import xlsxwriter
from datetime import timedelta

from odoo import fields, models


class ScrapReportWizard(models.TransientModel):
    _name = 'scrap.report.wizard'
    _description = 'Scrap Report Wizard'

    date_from = fields.Datetime(string='Date From', required=True)
    date_to = fields.Datetime(string='Date To', required=True)

    def _pk(self, value):
        if not value:
            return ''
        dt = fields.Datetime.to_datetime(value) + timedelta(hours=5)
        return dt.strftime('%d-%m-%Y %I:%M %p')

    def action_print_report(self):
        self.ensure_one()
        scraps = self.env['stock.scrap'].search([
            ('state', '=', 'done'),
            ('date_done', '>=', self.date_from),
            ('date_done', '<=', self.date_to),
        ], order='date_done, id')

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = wb.add_worksheet('Scrap Report')
        sheet.hide_gridlines(2)
        sheet.freeze_panes(5, 0)
        sheet.set_zoom(90)

        DARK, BORDER, TEXT, MUTED, WHITE = '#17365D', '#D8E0E6', '#263238', '#78909C', '#FFFFFF'
        LIGHT, TOTAL = '#F5F8FB', '#DCE6F1'

        def fmt(**kw):
            base = {'valign': 'vcenter'}
            base.update(kw)
            return wb.add_format(base)

        bordered = {'border': 1, 'border_color': BORDER, 'font_color': TEXT}
        num = {'num_format': '#,##0.00', 'align': 'right'}
        title_f = fmt(bold=True, font_size=20, font_color=WHITE, bg_color=DARK)
        sub_f = fmt(font_size=10, font_color=MUTED, italic=True)
        lbl_f = fmt(bold=True, font_size=9, font_color=MUTED, bg_color=LIGHT,
                    border=1, border_color=BORDER, align='center')
        val_f = fmt(bold=True, font_size=10, font_color=DARK, bg_color=LIGHT,
                    border=1, border_color=BORDER, align='center')
        head = dict(bold=True, font_size=10, font_color=WHITE, bg_color=DARK,
                    border=1, border_color=WHITE, text_wrap=True)
        head_c, head_l = fmt(align='center', **head), fmt(align='left', **head)
        cell = [fmt(**bordered), fmt(bg_color='#FAFBFC', **bordered)]
        numf = [fmt(**bordered, **num), fmt(bg_color='#FAFBFC', **bordered, **num)]
        tot = dict(bold=True, font_color=DARK, bg_color=TOTAL, border=1, border_color=BORDER)
        tot_l, tot_n = fmt(align='left', **tot), fmt(**tot, **num)

        for c, w in enumerate([21, 38, 25, 24, 14, 16, 30, 26]):
            sheet.set_column(c, c, w)

        last = 7
        sheet.set_row(0, 36)
        sheet.merge_range(0, 0, 0, last, 'Scrap Report', title_f)
        sheet.set_row(1, 22)
        sheet.merge_range(1, 0, 1, last, 'Inventory | Done Scrap Orders', sub_f)
        sheet.set_row(2, 25)
        sheet.merge_range(2, 0, 2, 1, 'REPORT PERIOD', lbl_f)
        sheet.merge_range(2, 2, 2, 5, '{}  to  {}'.format(
            self._pk(self.date_from), self._pk(self.date_to)), val_f)
        sheet.write(2, 6, 'STATE', lbl_f)
        sheet.write(2, 7, 'Done', val_f)

        headers = ['Scrap Date', 'Product', 'Vendor', 'Source Document',
                   'Quantity', 'Value', 'Scrap Reason', 'Company']
        sheet.set_row(4, 34)
        for c, h in enumerate(headers):
            sheet.write(4, c, h, head_l if c in (1, 2, 3, 6, 7) else head_c)

        row, tot_qty, tot_val = 5, 0.0, 0.0
        for i, s in enumerate(scraps):
            k = i % 2
            seller = s.product_id.seller_ids[:1]
            qty = s.scrap_qty or 0.0
            value = s.scrap_value or 0.0
            sheet.write(row, 0, self._pk(s.date_done), cell[k])
            sheet.write(row, 1, s.product_id.display_name or '', cell[k])
            sheet.write(row, 2, seller.partner_id.name or '', cell[k])
            sheet.write(row, 3, s.origin or '', cell[k])
            sheet.write_number(row, 4, qty, numf[k])
            sheet.write_number(row, 5, value, numf[k])
            sheet.write(row, 6, ', '.join(s.scrap_reason_tag_ids.mapped('name')), cell[k])
            sheet.write(row, 7, s.company_id.name or '', cell[k])
            tot_qty += qty
            tot_val += value
            sheet.set_row(row, 22)
            row += 1

        sheet.set_row(row, 28)
        sheet.merge_range(row, 0, row, 3, 'GRAND TOTAL', tot_l)
        sheet.write_number(row, 4, tot_qty, tot_n)
        sheet.write_number(row, 5, tot_val, tot_n)
        sheet.merge_range(row, 6, row, 7, '', tot_l)

        if row > 5:
            sheet.autofilter(4, 0, row - 1, last)
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_margins(0.25, 0.25, 0.5, 0.5)
        sheet.repeat_rows(4)

        wb.close()
        output.seek(0)
        att = self.env['ir.attachment'].create({
            'name': 'Scrap_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        output.close()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(att.id),
            'target': 'self',
        }