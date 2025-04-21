```markdown
# Dashboard Analitik E-commerce Olist

Dashboard ini menyediakan analisis komprehensif untuk data e-commerce Brasil dari Olist, yang mencakup berbagai aspek bisnis:
- **Analisis Pola Pembelian Geografis**: Mengeksplorasi tren pembelian berdasarkan lokasi pelanggan
- **Analisis Performa Penjual**: Evaluasi kinerja penjual berdasarkan penjualan dan ulasan
- **Analisis Metode Pembayaran**: Analisis preferensi metode pembayaran dan pola cicilan
- **Segmentasi Pelanggan (RFM)**: Pengelompokan pelanggan berdasarkan Recency, Frequency, dan Monetary value

## Demo
Dashboard ini tersedia secara online pada Streamlit Cloud: [Olist E-commerce Dashboard](https://dashboard-olist-e-commerce.streamlit.app/)

## Struktur Repositori
```
├── dashboard/
│   └── dashboard.py          # File utama aplikasi Streamlit
│
├── notebook/
│   └── notebook.ipynb        # Notebook untuk analisis data mendalam
│
├── data/                     # Direktori data
│   ├── customers_dataset.csv
│   ├── geolocation_dataset.csv
│   ├── order_items_dataset.csv
│   ├── order_payments_dataset.csv
│   ├── order_reviews_dataset.csv
│   ├── orders_dataset.csv
│   ├── product_category_name_translation.csv
│   ├── products_dataset.csv
│   └── sellers_dataset.csv
│
├── processed_data/           # Data yang telah diproses dari notebook
│
├── README.md                 # Dokumentasi proyek
├── requirements.txt          # Daftar dependensi
└── url.txt                   # URL repository
```

## Petunjuk Penggunaan
### Prasyarat
- Python 3.10 atau lebih tinggi
- Pip package manager

### Instalasi
1. Clone repositori ini:
```
git clone https://github.com/Koerentji/dashboard-olist-e-commerce.git
```

2. Pindah ke direktori proyek:
```
cd dashboard-olist-e-commerce
```

3. Buat virtual environment (direkomendasikan):
```
python -m venv venv
```

4. Aktifkan virtual environment:
   - Windows:
   ```
   venv\Scripts\activate
   ```
   - macOS/Linux:
   ```
   source venv/bin/activate
   ```

5. Pasang paket yang diperlukan:
```
pip install -r requirements.txt
```

### Menjalankan Aplikasi
1. Jalankan notebook.ipynb terlebih dahulu untuk menghasilkan data yang diproses:
```
jupyter notebook notebook/notebook.ipynb
```

2. Setelah notebook selesai dijalankan, jalankan dashboard:
```
cd dashboard
streamlit run dashboard.py
```

Aplikasi akan terbuka di browser Anda secara otomatis, biasanya di `http://localhost:8501`.

## Fitur
### Notebook Analisis
- Analisis mendalam tentang data e-commerce
- Pengolahan data dan pembuatan model RFM (Recency, Frequency, Monetary)
- Clustering pelanggan berdasarkan perilaku pembelian
- Visualisasi lanjutan untuk insight bisnis

### Dashboard Interaktif
#### Tren Penjualan
- Analisis tren penjualan dari waktu ke waktu
- Performa kategori produk
- Visualisasi pola musiman

#### Analisis Pelanggan
- Segmentasi RFM (Recency, Frequency, Monetary)
- Profil kluster pelanggan
- Strategi pemasaran untuk setiap segmen

#### Metode Pembayaran
- Distribusi metode pembayaran
- Analisis pola cicilan kartu kredit
- Korelasi nilai transaksi dengan metode pembayaran

#### Performa Pengiriman
- Analisis ketepatan waktu pengiriman
- Distribusi waktu pengiriman aktual
- Tren performa pengiriman

#### Analisis Geografis
- Distribusi pelanggan berdasarkan negara bagian
- Analisis kategori produk populer per wilayah
- Peta panas distribusi pelanggan

## Sumber Data
Dataset yang digunakan adalah data publik dari Olist, marketplace e-commerce Brasil. Dataset berisi informasi tentang 100.000 pesanan dari 2016 hingga 2018. Data ini mencakup berbagai aspek operasional e-commerce seperti informasi pesanan, pembayaran, produk, pelanggan, dan penjual.

## Teknologi yang Digunakan
- **Jupyter Notebook**: Analisis data eksploratori dan pemrosesan data
- **Streamlit**: Kerangka kerja untuk membangun aplikasi web interaktif
- **Pandas & NumPy**: Manipulasi dan analisis data
- **Plotly & Matplotlib**: Visualisasi data interaktif dan statis
- **Folium**: Visualisasi peta geografis
- **Seaborn**: Visualisasi statistik lanjutan

## Tentang Proyek
Proyek ini dibuat sebagai bagian dari tugas akhir kursus Data Science. Tujuannya adalah untuk menunjukkan kemampuan dalam menganalisis data e-commerce dan menghasilkan dashboard yang interaktif dan informatif untuk pengambilan keputusan bisnis.
```