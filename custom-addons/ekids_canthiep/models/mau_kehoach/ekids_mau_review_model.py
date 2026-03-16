from odoo import models, fields, api, exceptions


class MauKeHoachReview(models.Model):
    _name = "ekids.mau_kehoach_review"
    _description = "Đánh giá"

    mau_kehoach_id = fields.Many2one(
        "ekids.mau_kehoach",
        string="Mẫu kế hoạch",
        required=True,
        ondelete="cascade"
    )
    rating = fields.Selection([
        ("1", "1 Star"), ("2", "2 Star"), ("3", "3 Star"), ("4", "4 Star"), ("5", "5 Star")
    ], string="Số Star đánh giá", required=True)
    comment = fields.Text("Nhận xét")
    user_id = fields.Many2one("res.users", string="Người đánh giá", default=lambda self: self.env.uid)

    _sql_constraints = [
        ('unique_rating', 'unique(mau_kehoach_id, user_id)', 'Mỗi người chỉ được đánh giá một lần!'),
    ]



