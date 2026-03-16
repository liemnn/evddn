from odoo import models, fields

class ModelA(models.Model):
    _name = 'model.a'
    _description = 'Model A'

    name = fields.Char(string="Name")
    stage = fields.Selection([
        ('X', 'X'),
        ('O', 'O'),
        ('A', 'A'),
    ], string='Stage',default="X")
