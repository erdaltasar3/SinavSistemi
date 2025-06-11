#!/usr/bin/env bash
# Render.com build script

# Python paketlerini kurma
pip install -r requirements.txt

# Veritabanı migrasyonlarını yapma
python manage.py migrate

# Verileri yükleme (eğer migration başarılı olursa ve veritabanı boşsa)
if [ -f initial_data.json ]; then
    echo "Veritabanı verilerini yüklüyorum..."
    python manage.py loaddata initial_data.json
fi

# Statik dosyaları toplama
python manage.py collectstatic --noinput 