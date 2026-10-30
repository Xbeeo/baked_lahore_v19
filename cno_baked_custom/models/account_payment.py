# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    receiver_id = fields.Many2one(comodel_name='res.partner',string="Receiver")