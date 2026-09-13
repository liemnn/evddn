FROM odoo:16.0
# Ensure correct permissions for Odoo data and config
USER root

RUN pip3 install mysql-connector-python
RUN pip3 install lunardate sympy pandas pdfminer.six PyJWT psycopg2 werkzeug pypeg2 openpyxl numpy google-auth beautifulsoup4 setuptools
RUN pip3 install --no-cache-dir gevent gevent-websocket greenlet


#COPY ./base_custom /opt/odoo/odoo
#WORKDIR /opt/odoo/odoo

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ***ĐIỂM QUAN TRỌNG NHẤT***
ENTRYPOINT ["/entrypoint.sh"]
CMD ["-c", "/etc/odoo/odoo.conf"]

# Switch back to odoo user
USER odoo




