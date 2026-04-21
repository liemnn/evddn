import html
from odoo import http, models
from odoo.http import request


class EkidsChatController(http.Controller):

    # 1. RENDER TRANG GIAO DIỆN CHAT
    @http.route('/ph/chat', type='http', auth='user', website=True)
    def render_chat_page(self, **kwargs):
        user = request.env.user
        qcontext = {}
        if user:
            hocsinh = request.env['ekids.hocsinh'].sudo().search([('user_id', '=', user.id)], limit=1)
            if hocsinh:
                # Tìm tài khoản của Cơ sở (Nếu không có thì đẩy về Admin hệ thống)
                target_partner = request.env.ref('base.partner_admin')
                if hocsinh.coso_id and hocsinh.coso_id.user_id:
                    target_partner = hocsinh.coso_id.user_id.partner_id

                qcontext['target_partner_id'] = target_partner.id
                qcontext['ten_nguoi_nhan'] = hocsinh.coso_id.name if hocsinh.coso_id else 'Trường trung tâm'

        return request.render('ekids_phuhuynh.chat_page', qcontext)

    # --- HÀM ẨN: TẠO PHÒNG CHAT THỦ CÔNG CHỐNG LỖI ODOO 18 ---
    def _get_or_create_dm_channel(self, target_partner_id):
        target_id = int(target_partner_id)
        my_id = request.env.user.partner_id.id

        # Tìm xem 2 người đã từng có kênh chat riêng chưa
        channel = request.env['discuss.channel'].sudo().search([
            ('channel_type', '=', 'chat'),
            ('channel_partner_ids', 'in', [target_id]),
            ('channel_partner_ids', 'in', [my_id])
        ], limit=1)

        # Nếu chưa có thì tự động tạo mới
        if not channel:
            channel = request.env['discuss.channel'].sudo().create({
                'channel_type': 'chat',
                'name': f'Chat {my_id} & {target_id}',
                'channel_partner_ids': [(4, my_id), (4, target_id)]
            })
        return channel

    # 2. API LẤY LỊCH SỬ TIN NHẮN
    @http.route('/ph/chat/history', type='json', auth='user', methods=['POST'])
    def get_chat_history(self, target_partner_id):
        if not target_partner_id:
            return []

        channel = self._get_or_create_dm_channel(target_partner_id)

        # Lấy 100 tin nhắn (comment) mới nhất
        messages = request.env['mail.message'].sudo().search([
            ('model', '=', 'discuss.channel'),
            ('res_id', '=', channel.id),
            ('message_type', '=', 'comment')
        ], order='id asc', limit=100)

        chat_data = []
        my_partner_id = request.env.user.partner_id.id

        for msg in messages:
            chat_data.append({
                'id': msg.id,
                'author': msg.author_id.name or 'Nhà trường',
                'body': msg.body,
                'date': msg.date.strftime("%H:%M %d/%m"),
                'is_me': msg.author_id.id == my_partner_id
            })
        return chat_data

    # 3. API GỬI TIN NHẮN
    @http.route('/ph/chat/send', type='json', auth='user', methods=['POST'])
    def send_chat_message(self, target_partner_id, message_body):
        if not target_partner_id or not message_body:
            return {'success': False}

        channel = self._get_or_create_dm_channel(target_partner_id)

        # Đăng tin nhắn vào kênh chat dưới quyền của user đang đăng nhập
        msg = channel.with_user(request.env.user).message_post(
            body=html.escape(message_body),
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )
        return {'success': True, 'msg_id': msg.id}