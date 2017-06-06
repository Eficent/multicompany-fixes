from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    def get_current_company(self):
        self.current_company_id = self.env.user.company_id

    current_company_id = fields.Many2one(
        comodel_name='res.company',
        default=get_current_company,
        compute='get_current_company',
        store=False
    )
