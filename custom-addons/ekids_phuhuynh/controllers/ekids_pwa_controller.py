import json
from odoo import http
from odoo.http import request

class EkidsPWAController(http.Controller):

    # Chú ý: Bỏ website=True, thêm csrf=False và cors='*'
    @http.route('/ph/manifest.json', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def pwa_manifest(self):
        manifest_data = {
            "name": "eVDDN - App Phụ Huynh",
            "short_name": "eVDDN-Phụ huynh",
            "description": "Ứng dụng theo dõi học tập cho phụ huynh",
            "scope": "/",
            "start_url": "/ph/home", # Hoặc link trang chủ của anh
            "display": "standalone",
            "background_color": "#E0F2FE",
            "theme_color": "#2563EB",
            "icons": [
                {
                    "src": "/ekids_phuhuynh/static/src/img/icon_192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable" # Giúp icon hiển thị đẹp trên Android
                },
                {
                    "src": "/ekids_phuhuynh/static/src/img/icon_512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
            ]
        }
        return request.make_response(
            json.dumps(manifest_data),
            headers=[('Content-Type', 'application/json; charset=utf-8')]
        )

    # Chú ý: Bỏ website=True, thêm csrf=False và cors='*'
    @http.route('/ph/sw.js', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def pwa_service_worker(self):
        js_content = """
        const CACHE_NAME = 'evddn-cache-v1';
        self.addEventListener('install', (event) => {
            self.skipWaiting();
        });
        self.addEventListener('activate', (event) => {
            event.waitUntil(clients.claim());
        });
        self.addEventListener('fetch', (event) => {
            event.respondWith(fetch(event.request));
        });
        """
        return request.make_response(
            js_content,
            headers=[
                ('Content-Type', 'application/javascript; charset=utf-8'),
                ('Service-Worker-Allowed', '/')
            ]
        )