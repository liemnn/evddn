FROM python:3.9

# Cài các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libffi-dev \
    pkg-config \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpq-dev \
    fonts-dejavu-core \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    xfonts-75dpi \
    xfonts-base \
    && rm -rf /var/lib/apt/lists/*

# Cài wkhtmltopdf từ file .deb
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.jammy_amd64.deb \
    && apt install -y ./wkhtmltox_0.12.6-1.jammy_amd64.deb \
    && rm wkhtmltox_0.12.6-1.jammy_amd64.deb



# Cài các thư viện Python bổ sung
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install mysql-connector-python lunardate sympy pandas pdfminer.six PyJWT psycopg2 werkzeug pypeg2 openpyxl numpy google-auth beautifulsoup4

# Tạo user odoo
RUN useradd -m -d /opt/odoo/erp -U -r -s /bin/bash odoo

# Copy mã nguồn Odoo vào image
COPY ./erp /opt/odoo/erp

WORKDIR /opt/odoo/erp

# Cài đặt Python dependencies từ requirements.txt
RUN pip3 install -r requirements.txt

# Copy file cấu hình
COPY ./odoo.conf /etc/odoo.conf

# Phân quyền
RUN chown -R odoo:odoo /opt/odoo/erp

USER odoo
CMD ["python3", "/opt/odoo/erp/odoo-bin", "-c", "/etc/odoo.conf"]
