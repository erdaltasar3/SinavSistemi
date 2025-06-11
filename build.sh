#!/usr/bin/env bash
# Render.com build script

# Python paketlerini kurma
pip install -r requirements.txt

# Veritabanı migrasyonlarını yapma
python manage.py migrate

# Verileri yükleme (eğer migration başarılı olursa ve veritabanı boşsa)
if [ -f initial_data.json ]; then
    echo "Veritabanı verilerini yüklüyorum..."
    # Önce dosyayı UTF-8'e dönüştürelim
    iconv -f ISO-8859-9 -t UTF-8 initial_data.json > initial_data_utf8.json
    python manage.py loaddata initial_data_utf8.json
fi

# Statik dosyaları toplama
python manage.py collectstatic --noinput 