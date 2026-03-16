from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


from odoo.api import ValuesType, Self
from odoo.exceptions import ValidationError
class KeHoachTaoMoiAbstractModel(models.AbstractModel):
    _name = 'ekids.kehoach_taomoi_abstractmodel'
    _description = 'Can thiệp'
    _abstract = True








