FROM odoo:16.0

USER root

# 1. Khóa setuptools và bộ 3 bảo mật chống crash Base
RUN python3 -m pip install --no-cache-dir --upgrade pip wheel && \
    python3 -m pip install --no-cache-dir "setuptools==52.0.0" && \
    python3 -m pip install --no-cache-dir "cryptography==3.4.8" "pyOpenSSL==20.0.1" "urllib3<2.0.0"

# 2. Cài đặt đúng 100% phiên bản theo danh sách của bạn
RUN python3 -m pip install --no-cache-dir \
    "mysql-connector-python==9.4.0" \
    "lunardate==0.2.2" \
    "sympy==1.14.0" \
    "pandas" \
    "pdfminer.six==20200726" \
    "PyJWT==2.10.1" \
    "psycopg2-binary==2.8.6" \
    "werkzeug==1.0.1" \
    "pypeg2==2.15.2" \
    "openpyxl==3.1.5" \
    "numpy==2.0.2" \
    "google-auth==2.43.0" \
    "beautifulsoup4==4.9.3" \
    "gevent" \
    "gevent-websocket" \
    "greenlet" \
    "zope.interface==5.5.2" \
    "zope.event==4.5.0"

# 3. Cưỡng chế giữ vững cryptography 3.4.8 để tránh bị google-auth ghi đè
RUN python3 -m pip install --no-cache-dir "cryptography==3.4.8"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER odoo

ENTRYPOINT ["/entrypoint.sh"]
CMD ["-c", "/etc/odoo/odoo.conf"]