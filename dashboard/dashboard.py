import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
import warnings
warnings.filterwarnings('ignore')

# Konfigurasi halaman
st.set_page_config(page_title="Olist E-commerce Dashboard", 
                   page_icon="📊", 
                   layout="wide",
                   initial_sidebar_state="expanded")

# Fungsi untuk memuat data hasil analisis dari notebook.ipynb
@st.cache_data
def load_processed_data():
    try:
        # Dalam aplikasi nyata, file-file ini akan dihasilkan dari notebook.ipynb
        # Untuk demo, kita akan mencoba memuat langsung dari path data mentah
        import os
        
        # Check if processed_data directory exists, create if it doesn't
        if not os.path.exists('processed_data'):
            os.makedirs('processed_data')
            st.info("Created 'processed_data' directory. Run the notebook.ipynb first to generate processed datasets.")
        
        is_cloud = os.getenv('STREAMLIT_SHARING') == 'true' or os.getenv('STREAMLIT_RUN_ON_SAVE') == 'true'
        
        if is_cloud:
            base_path = 'data'  
        else:
            base_path = '../data'  

        def get_file_path(filename):
            possible_paths = [
                os.path.join('processed_data', filename),  # Check processed data first
                os.path.join(base_path, filename),
                os.path.join('data', filename),  
                os.path.join('../data', filename)
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            return os.path.join(base_path, filename)
        
        # Memuat semua dataset
        # Umumnya kita memuat data hasil proses, tapi karena belum dibuat, kita memuat data mentah
        df_customers = pd.read_csv(get_file_path('customers_dataset.csv'))
        df_order_items = pd.read_csv(get_file_path('order_items_dataset.csv'))
        df_order_payments = pd.read_csv(get_file_path('order_payments_dataset.csv'))
        df_order_reviews = pd.read_csv(get_file_path('order_reviews_dataset.csv'))
        df_orders = pd.read_csv(get_file_path('orders_dataset.csv'))
        df_product_category = pd.read_csv(get_file_path('product_category_name_translation.csv'))
        df_products = pd.read_csv(get_file_path('products_dataset.csv'))
        df_sellers = pd.read_csv(get_file_path('sellers_dataset.csv'))
        
        # Mengkonversi kolom tanggal ke format datetime
        orders_col = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
                      'order_delivered_customer_date', 'order_estimated_delivery_date']
        for col in orders_col:
            df_orders[col] = pd.to_datetime(df_orders[col])
        
        # Menggabungkan kategori produk dengan nama bahasa Inggris
        df_products = pd.merge(
            df_products, 
            df_product_category, 
            on='product_category_name', 
            how='left'
        )
        
        return {
            'customers': df_customers,
            'order_items': df_order_items,
            'order_payments': df_order_payments,
            'order_reviews': df_order_reviews,
            'orders': df_orders,
            'products': df_products,
            'sellers': df_sellers
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Memuat data dengan tampilan loading spinner
with st.spinner('Memuat data... Mohon tunggu.'):
    data = load_processed_data()

# Memeriksa apakah data berhasil dimuat
if not data:
    st.error("Gagal memuat data. Silakan periksa jalur file.")
    st.stop()

# ---------------------- Dashboard ----------------------

st.title("🛍️ Olist E-commerce Analytics Dashboard")

# Penjelasan dashboard
with st.expander("ℹ️ Tentang Dashboard"):
    st.markdown("""
    Dashboard ini menampilkan hasil analisis data e-commerce Brasil dari Olist Store yang telah diolah 
    melalui notebook.ipynb. Dashboard ini berfokus pada menjawab pertanyaan bisnis utama:
    
    1. **Tren Penjualan dan Kategori Populer**: Bagaimana tren penjualan bulanan dan kategori produk apa yang paling laris?
    2. **Segmentasi Pelanggan**: Bagaimana segmentasi pelanggan berdasarkan analisis RFM (Recency, Frequency, Monetary)?
    3. **Metode Pembayaran**: Apa metode pembayaran yang paling populer dan bagaimana pola penggunaan cicilan kartu kredit?
    4. **Performa Pengiriman**: Bagaimana performa pengiriman pesanan dibandingkan dengan estimasi waktu?
    5. **Distribusi Geografis**: Bagaimana distribusi geografis pelanggan dan perbedaan perilaku pembelian antar wilayah?
    
    Setiap tab dashboard dirancang untuk menjawab satu pertanyaan bisnis spesifik dengan visualisasi yang jelas dan wawasan yang dapat ditindaklanjuti.
    """)

# --------- Sidebar untuk filter ---------
st.sidebar.title("📊 Filter Dashboard")

# Penjelasan singkat tentang filter
st.sidebar.info("Gunakan filter untuk menyesuaikan analisis berdasarkan periode waktu, kategori produk, dan lokasi geografis.")

# Setup for date filters
min_date = data['orders']['order_purchase_timestamp'].min()
max_date = data['orders']['order_purchase_timestamp'].max()

# Filter date range
with st.sidebar.expander("🗓️ Periode Waktu", expanded=True):
    # Option to choose preset periods or custom
    date_option = st.radio(
        "Pilih Rentang Waktu:",
        ["Semua Data", "Tahun Terakhir", "6 Bulan Terakhir", "3 Bulan Terakhir", "Kustom"]
    )
    
    if date_option == "Semua Data":
        start_date = min_date
        end_date = max_date
    elif date_option == "Tahun Terakhir":
        start_date = max_date - timedelta(days=365)
        end_date = max_date
    elif date_option == "6 Bulan Terakhir":
        start_date = max_date - timedelta(days=180)
        end_date = max_date
    elif date_option == "3 Bulan Terakhir":
        start_date = max_date - timedelta(days=90)
        end_date = max_date
    else:  # Custom
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Tanggal Mulai", min_date)
        with col2:
            end_date = st.date_input("Tanggal Akhir", max_date)
        
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

# Filter kategori produk
with st.sidebar.expander("🏷️ Kategori Produk", expanded=True):
    # Check if translated categories are available
    if 'product_category_name_english' in data['products'].columns:
        categories = ['All Categories'] + sorted(data['products']['product_category_name_english'].dropna().unique().tolist())
    else:
        categories = ['All Categories'] + sorted(data['products']['product_category_name'].dropna().unique().tolist())
    
    selected_category = st.selectbox("Pilih Kategori Produk:", categories)
    
    if selected_category == 'All Categories':
        selected_category = None

# Filter negara bagian untuk analisis geografis
with st.sidebar.expander("🌎 Lokasi Geografis", expanded=True):
    states = ['All States'] + sorted(data['customers']['customer_state'].unique().tolist())
    selected_state = st.selectbox("Pilih Negara Bagian:", states)
    
    if selected_state == 'All States':
        selected_state = None

# ---- Tab layout untuk menjawab pertanyaan bisnis ----
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Pertanyaan 1: Tren Penjualan", 
    "👥 Pertanyaan 2: Segmentasi Pelanggan", 
    "💳 Pertanyaan 3: Metode Pembayaran", 
    "🚚 Pertanyaan 4: Performa Pengiriman",
    "🌎 Pertanyaan 5: Distribusi Geografis"
])

# ----- Tab 1: Tren Penjualan dan Kategori Terlaris -----
with tab1:
    st.header("📊 Pertanyaan 1: Bagaimana tren penjualan bulanan dan kategori produk apa yang paling laris?")
    
    # Filter orders berdasarkan tanggal
    filtered_orders = data['orders'][(data['orders']['order_purchase_timestamp'] >= start_date) & 
                                (data['orders']['order_purchase_timestamp'] <= end_date)]
    
    # Gabungkan dengan items
    filtered_items = pd.merge(
        filtered_orders[['order_id']],
        data['order_items'],
        on='order_id',
        how='inner'
    )
    
    # Filter berdasarkan kategori jika ditentukan
    if selected_category:
        product_ids = data['products'][data['products']['product_category_name_english'] == selected_category]['product_id'].unique()
        filtered_items = filtered_items[filtered_items['product_id'].isin(product_ids)]
    
    # Metrik utama dalam 3 kolom
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_orders = filtered_items['order_id'].nunique()
        st.metric("Total Pesanan", f"{total_orders:,}")
    
    with col2:
        total_sales = filtered_items['price'].sum()
        st.metric("Total Penjualan", f"R$ {total_sales:,.2f}")
    
    with col3:
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        st.metric("Rata-rata Nilai Pesanan", f"R$ {avg_order_value:,.2f}")
    
    # Visualisasi 1: Tren Penjualan Bulanan
    st.subheader("Visualisasi 1: Tren Penjualan Bulanan")
    
    # Menggabungkan data pesanan dengan waktu
    sales_over_time = pd.merge(
        filtered_orders[['order_id', 'order_purchase_timestamp']],
        filtered_items[['order_id', 'price']],
        on='order_id',
        how='inner'
    )
    
    # Agregasi penjualan per bulan
    sales_over_time['month'] = sales_over_time['order_purchase_timestamp'].dt.to_period('M')
    monthly_sales = sales_over_time.groupby(sales_over_time['month'].astype(str))['price'].sum().reset_index()
    
    # Plotting
    fig = px.line(
        monthly_sales, 
        x='month', 
        y='price',
        title='Tren Penjualan Bulanan',
        labels={'month': 'Bulan', 'price': 'Total Penjualan (R$)'},
        markers=True
    )
    
    fig.update_layout(
        xaxis_title="Bulan",
        yaxis_title="Total Penjualan (R$)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("ℹ️ Insight Tren Penjualan Bulanan"):
        st.markdown("""
        - Tren penjualan menunjukkan peningkatan secara umum dari 2016 hingga 2018, dengan lonjakan signifikan pada akhir 2017.
        - Terdapat pola musiman dengan peningkatan penjualan menjelang akhir tahun, yang kemungkinan terkait dengan periode liburan dan perayaan.
        - Penjualan mencapai puncaknya pada November 2017, yang mungkin berkaitan dengan acara belanja besar seperti Black Friday atau Natal.
        - Penurunan penjualan terlihat pada awal 2018, yang bisa menjadi indikasi perubahan tren pasar atau tantangan bisnis.
        """)
    
    # Visualisasi 2: Top 10 Kategori Berdasarkan Penjualan
    st.subheader("Visualisasi 2: Top 10 Kategori Produk Berdasarkan Penjualan")
    
    # Menggabungkan data item dengan produk
    items_with_categories = pd.merge(
        filtered_items,
        data['products'][['product_id', 'product_category_name', 'product_category_name_english']],
        on='product_id',
        how='inner'
    )
    
    # Agregasi berdasarkan kategori
    cat_column = 'product_category_name_english' if 'product_category_name_english' in items_with_categories.columns else 'product_category_name'
    category_sales = items_with_categories.groupby(cat_column).agg({
        'price': 'sum',
        'order_id': 'nunique'
    }).reset_index()
    
    # Sorting dan mengambil top 10
    top_categories = category_sales.sort_values('price', ascending=False).head(10)
    
    # Plotting
    fig = px.bar(
        top_categories,
        x='price',
        y=cat_column,
        title='Top 10 Kategori Berdasarkan Penjualan',
        labels={cat_column: 'Kategori', 'price': 'Total Penjualan (R$)'},
        orientation='h',
        color='price',
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(
        xaxis_title="Total Penjualan (R$)",
        yaxis_title="Kategori Produk",
        yaxis={'categoryorder':'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("ℹ️ Insight Kategori Produk Terlaris"):
        st.markdown("""
        - Kategori "bed_bath_table" (peralatan kamar tidur dan kamar mandi) adalah kategori dengan penjualan tertinggi, mengindikasikan permintaan yang kuat untuk produk rumah tangga.
        - Produk elektronik seperti "health_beauty" (kecantikan dan kesehatan) dan "computers_accessories" (aksesoris komputer) juga menempati posisi tinggi, menunjukkan tren belanja online untuk produk teknologi.
        - "sports_leisure" (olahraga dan rekreasi) dan "furniture_decor" (furnitur dan dekorasi) menempati peringkat atas, mencerminkan minat konsumen pada peningkatan kualitas hidup dan ruang tinggal.
        - Kategori terlaris mencakup beragam kebutuhan, dari produk rumah tangga hingga gadget, menunjukkan diversifikasi pasar e-commerce Brasil.
        """)

# ----- Tab 2: Segmentasi Pelanggan -----
with tab2:
    st.header("👥 Pertanyaan 2: Bagaimana segmentasi pelanggan berdasarkan analisis RFM (Recency, Frequency, Monetary)?")
    
    # Penjelasan tentang analisis RFM
    with st.expander("ℹ️ Tentang Analisis RFM", expanded=True):
        st.markdown("""
        **RFM Analysis** adalah teknik segmentasi pelanggan berdasarkan perilaku pembelian:
        - **Recency**: Berapa hari sejak pembelian terakhir
        - **Frequency**: Berapa kali pelanggan melakukan pembelian
        - **Monetary**: Berapa total nilai pembelian pelanggan
        
        Metode ini sangat berguna untuk memahami nilai dan perilaku pelanggan, membantu bisnis dalam mengembangkan strategi pemasaran yang ditargetkan.
        """)
    
    # Filter orders berdasarkan tanggal untuk RFM
    filtered_orders_rfm = data['orders'][
        (data['orders']['order_purchase_timestamp'] >= start_date) & 
        (data['orders']['order_purchase_timestamp'] <= end_date) &
        (data['orders']['order_status'] == 'delivered')
    ]
    
    # Gabungkan dengan pembayaran
    orders_with_payments = pd.merge(
        filtered_orders_rfm[['order_id', 'customer_id', 'order_purchase_timestamp']],
        data['order_payments'][['order_id', 'payment_value']],
        on='order_id',
        how='inner'
    )
    
    if len(orders_with_payments) > 0:
        # Hitung RFM metrics
        # Recency
        recency_df = orders_with_payments.groupby('customer_id')['order_purchase_timestamp'].max().reset_index()
        recency_df['recency'] = (end_date - recency_df['order_purchase_timestamp']).dt.days
        
        # Frequency
        frequency_df = orders_with_payments.groupby('customer_id')['order_id'].nunique().reset_index()
        frequency_df.columns = ['customer_id', 'frequency']
        
        # Monetary
        monetary_df = orders_with_payments.groupby('customer_id')['payment_value'].sum().reset_index()
        monetary_df.columns = ['customer_id', 'monetary']
        
        # Combine
        rfm = pd.merge(recency_df[['customer_id', 'recency']], frequency_df, on='customer_id')
        rfm = pd.merge(rfm, monetary_df, on='customer_id')
        
        # Visualisasi 1: Metrik RFM
        st.subheader("Visualisasi 1: Metrik RFM")
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_recency = rfm['recency'].mean()
            st.metric("Rata-rata Recency", f"{avg_recency:.1f} hari")
        
        with col2:
            avg_frequency = rfm['frequency'].mean()
            st.metric("Rata-rata Frequency", f"{avg_frequency:.1f} pesanan")
        
        with col3:
            avg_monetary = rfm['monetary'].mean()
            st.metric("Rata-rata Monetary", f"R$ {avg_monetary:.2f}")
        
        # Create segments - Penanganan khusus untuk recency
        if rfm['recency'].nunique() < 5:
            # Jika tidak cukup variasi, tetapkan nilai tengah
            rfm['r_score'] = 3
        else:
            try:
                rfm['r_score'] = pd.qcut(rfm['recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
            except ValueError:
                rfm['r_score'] = pd.cut(rfm['recency'], bins=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
        
        # Penanganan untuk frequency
        if rfm['frequency'].nunique() < 5:
            rfm['f_score'] = 3
        else:
            try:
                rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
            except ValueError:
                rfm['f_score'] = pd.cut(rfm['frequency'], bins=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        
        # Penanganan untuk monetary
        if rfm['monetary'].nunique() < 5:
            rfm['m_score'] = 3
        else:
            try:
                rfm['m_score'] = pd.qcut(rfm['monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
            except ValueError:
                rfm['m_score'] = pd.cut(rfm['monetary'], bins=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        
        # Convert score columns to numeric
        for col in ['r_score', 'f_score', 'm_score']:
            rfm[col] = pd.to_numeric(rfm[col], errors='coerce')
        
        # Calculate overall RFM score
        rfm['rfm_score'] = rfm['r_score'] + rfm['f_score'] + rfm['m_score']
        
        # Create segment labels
        rfm['segment'] = pd.cut(
            rfm['rfm_score'],
            bins=[0, 4, 8, 12, 15],
            labels=['Bronze', 'Silver', 'Gold', 'Platinum'],
            include_lowest=True
        )
        
        # Visualisasi 2: Distribusi Segmen RFM
        st.subheader("Visualisasi 2: Distribusi Segmen Pelanggan")
        
        # Visualize segment distribution
        segment_dist = rfm['segment'].value_counts().reset_index()
        segment_dist.columns = ['segment', 'count']
        
        fig = px.pie(
            segment_dist, 
            values='count', 
            names='segment',
            title='Distribusi Segmen Pelanggan',
            color='segment',
            color_discrete_map={
                'Bronze': '#CD7F32',
                'Silver': '#C0C0C0',
                'Gold': '#FFD700',
                'Platinum': '#E5E4E2'
            }
        )
        
        fig.update_layout(
            legend_title="Segmen",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("ℹ️ Insight Segmentasi Pelanggan"):
            st.markdown("""
            - Mayoritas pelanggan berada dalam segmen Bronze (sekitar 40%), menunjukkan basis pelanggan dengan nilai rendah yang jarang berbelanja dan tidak melakukan pembelian baru-baru ini.
            - Segmen Silver mencakup sekitar 30% pelanggan, yang merepresentasikan pelanggan dengan nilai dan frekuensi menengah.
            - Segmen Gold dan Platinum bersama-sama merepresentasikan sekitar 30% pelanggan, namun kemungkinan menyumbang porsi pendapatan yang lebih besar.
            - Struktur segmentasi ini mengikuti pola umum dalam e-commerce, di mana sebagian kecil pelanggan (Gold dan Platinum) menyumbang sebagian besar pendapatan.
            """)
        
        # Jika jumlah segmen cukup untuk analisis lanjutan
        if len(segment_dist) >= 3:
            # Visualisasi 3: Karakteristik Segmen
            st.subheader("Visualisasi 3: Karakteristik Segmen Pelanggan")
            
            # Hitung rata-rata metrik untuk setiap segmen
            segment_metrics = rfm.groupby('segment').agg({
                'recency': 'mean',
                'frequency': 'mean',
                'monetary': 'mean'
            }).reset_index()
            
            # Reshape untuk visualisasi
            segment_metrics_melted = pd.melt(
                segment_metrics, 
                id_vars=['segment'], 
                value_vars=['recency', 'frequency', 'monetary'],
                var_name='metric', 
                value_name='value'
            )
            
            # Normalisasi nilai untuk perbandingan yang lebih baik
            for metric in ['recency', 'frequency', 'monetary']:
                metric_max = segment_metrics_melted[segment_metrics_melted['metric'] == metric]['value'].max()
                segment_metrics_melted.loc[segment_metrics_melted['metric'] == metric, 'normalized_value'] = segment_metrics_melted[segment_metrics_melted['metric'] == metric]['value'] / metric_max
                
                # Untuk recency, lebih rendah lebih baik, jadi balik nilainya
                if metric == 'recency':
                    segment_metrics_melted.loc[segment_metrics_melted['metric'] == metric, 'normalized_value'] = 1 - segment_metrics_melted[segment_metrics_melted['metric'] == metric]['normalized_value']
            
            # Buat radar chart untuk segmen
            fig = px.line_polar(
                segment_metrics_melted, 
                r='normalized_value', 
                theta='metric', 
                color='segment',
                line_close=True,
                color_discrete_map={
                    'Bronze': '#CD7F32',
                    'Silver': '#C0C0C0',
                    'Gold': '#FFD700',
                    'Platinum': '#E5E4E2'
                },
                title='Karakteristik Segmen Pelanggan'
            )
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )
                ),
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("ℹ️ Insight Karakteristik Segmen"):
                st.markdown("""
                - Segmen Platinum menunjukkan performa tertinggi di semua dimensi RFM, dengan recency (pembelian terbaru), frequency (sering berbelanja), dan monetary (nilai belanja tinggi).
                - Segmen Bronze menunjukkan performa terendah di semua dimensi, terutama pada recency yang menunjukkan bahwa mereka belum berbelanja dalam waktu yang lama.
                - Segmen Silver dan Gold menunjukkan perbedaan karakteristik yang jelas, di mana Gold lebih unggul dalam frequency dan monetary, namun Silver mungkin memiliki recency yang lebih baik.
                - Visualisasi radar ini membantu mengidentifikasi area fokus untuk strategi pemasaran yang spesifik untuk setiap segmen.
                """)
        
        # Tabel Interpretasi Segmen dan Strategi
        st.subheader("Interpretasi Segmen dan Strategi Marketing")
        
        segments_table = pd.DataFrame({
            'Segmen': ['Platinum', 'Gold', 'Silver', 'Bronze'],
            'Deskripsi': [
                'Pelanggan dengan nilai tertinggi yang sering berbelanja dan baru-baru ini melakukan pembelian.',
                'Pelanggan bernilai tinggi yang cenderung berbelanja secara teratur.',
                'Pelanggan menengah yang berbelanja sesekali atau pelanggan baru dengan nilai pembelian tinggi.',
                'Pelanggan yang jarang berbelanja dan sudah lama tidak melakukan pembelian.'
            ],
            'Strategi Marketing': [
                'Program loyalitas VIP, akses awal ke produk baru, personalisasi layanan.',
                'Cross-selling dan up-selling, program rewards, insentif untuk meningkatkan frekuensi.',
                'Promosi produk terkait, program engagement, insentif untuk meningkatkan frekuensi.',
                'Program reaktivasi, diskon khusus untuk pembelian berikutnya, penawaran win-back.'
            ]
        })
        
        st.table(segments_table)
    else:
        st.warning("Tidak ada data yang cukup untuk analisis RFM dalam rentang waktu yang dipilih.")

# ----- Tab 3: Metode Pembayaran -----
with tab3:
    st.header("💳 Pertanyaan 3: Apa metode pembayaran yang paling populer dan bagaimana pola penggunaan cicilan kartu kredit?")
    
    # Filter orders berdasarkan rentang tanggal
    filtered_orders_payment = data['orders'][(data['orders']['order_purchase_timestamp'] >= start_date) & 
                                         (data['orders']['order_purchase_timestamp'] <= end_date)]
    
    # Gabungkan dengan data pembayaran
    payment_data = pd.merge(
        filtered_orders_payment[['order_id']],
        data['order_payments'],
        on='order_id',
        how='inner'
    )
    
    # Visualisasi 1: Distribusi Metode Pembayaran
    st.subheader("Visualisasi 1: Distribusi Metode Pembayaran")
    
    # Agregasi berdasarkan jenis pembayaran
    payment_summary = payment_data.groupby('payment_type').agg({
        'payment_value': 'sum',
        'order_id': 'nunique'
    }).reset_index()
    
    payment_summary.columns = ['payment_type', 'total_value', 'order_count']
    payment_summary['percentage'] = payment_summary['total_value'] / payment_summary['total_value'].sum() * 100
    
    # Visualisasi distribusi metode pembayaran
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.pie(
            payment_summary, 
            values='total_value', 
            names='payment_type',
            title='Distribusi Metode Pembayaran',
            hole=0.4,
            color='payment_type',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Value: R$%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Statistik pembayaran
        st.subheader("Statistik Metode Pembayaran")
        
        # Format untuk tampilan
        display_stats = payment_summary.copy()
        display_stats['avg_value'] = display_stats['total_value'] / display_stats['order_count']
        display_stats = display_stats[['payment_type', 'order_count', 'avg_value']]
        display_stats.columns = ['Metode Pembayaran', 'Jumlah Pesanan', 'Rata-rata Nilai']
        display_stats['Rata-rata Nilai'] = display_stats['Rata-rata Nilai'].map('R$ {:.2f}'.format)
        
        st.table(display_stats)
    
    with st.expander("ℹ️ Insight Metode Pembayaran"):
        st.markdown("""
        - Kartu kredit (credit_card) adalah metode pembayaran yang dominan, digunakan oleh lebih dari 70% nilai transaksi, menunjukkan preferensi konsumen untuk pembayaran non-tunai.
        - Pembayaran dengan boleto (voucher pembayaran populer di Brasil) menduduki posisi kedua, menunjukkan penerimaan masyarakat terhadap metode pembayaran lokal.
        - Penggunaan e-wallet dan transfer bank masih relatif rendah, mengindikasikan potensi pertumbuhan dalam metode pembayaran digital.
        - Pola ini mencerminkan tren global dalam e-commerce di mana metode pembayaran kartu mendominasi, namun juga menunjukkan pengaruh preferensi lokal.
        """)
    
    # Visualisasi 2: Analisis Cicilan Kartu Kredit
    st.subheader("Visualisasi 2: Analisis Cicilan Kartu Kredit")
    
    # Filter hanya metode pembayaran credit_card
    credit_data = payment_data[payment_data['payment_type'] == 'credit_card']
    
    if len(credit_data) > 0:
        # Distribusi jumlah cicilan
        installment_counts = credit_data['payment_installments'].value_counts().reset_index()
        installment_counts.columns = ['installments', 'count']
        installment_counts = installment_counts.sort_values('installments')
        
        fig = px.bar(
            installment_counts,
            x='installments',
            y='count',
            title='Distribusi Jumlah Cicilan (Kartu Kredit)',
            labels={'installments': 'Jumlah Cicilan', 'count': 'Jumlah Transaksi'},
            color='count',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_title="Jumlah Cicilan",
            yaxis_title="Jumlah Transaksi",
            coloraxis_showscale=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("ℹ️ Insight Distribusi Cicilan"):
            st.markdown("""
            - Mayoritas transaksi kartu kredit dilakukan dalam 1 cicilan (pembayaran penuh), menunjukkan bahwa sebagian besar konsumen memilih untuk tidak memanfaatkan opsi cicilan.
            - Untuk transaksi dengan cicilan, periode 2, 3, dan 10 cicilan adalah yang paling populer, menunjukkan preferensi untuk jangka waktu pendek atau opsi cicilan bundel standar.
            - Terdapat penurunan signifikan penggunaan setelah 10 cicilan, mengindikasikan batasan atau disinsentif untuk periode cicilan yang lebih panjang.
            - Pola ini mencerminkan kebiasaan finansial konsumen Brasil dan kebijakan cicilan dari bank penerbit kartu kredit.
            """)
        
        # Visualisasi 3: Hubungan Nilai Pesanan dan Jumlah Cicilan
        st.subheader("Visualisasi 3: Hubungan Nilai Pesanan dan Jumlah Cicilan")
        
        # Rata-rata nilai pembelian berdasarkan jumlah cicilan
        installment_values = credit_data.groupby('payment_installments')['payment_value'].mean().reset_index()
        installment_values.columns = ['installments', 'avg_value']
        
        fig = px.line(
            installment_values,
            x='installments',
            y='avg_value',
            title='Rata-rata Nilai Pesanan berdasarkan Jumlah Cicilan',
            labels={'installments': 'Jumlah Cicilan', 'avg_value': 'Rata-rata Nilai Pesanan (R$)'},
            markers=True,
            line_shape='linear'
        )
        
        fig.update_layout(
            xaxis_title="Jumlah Cicilan",
            yaxis_title="Rata-rata Nilai Pesanan (R$)",
            hovermode="x"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("ℹ️ Insight Nilai Pesanan dan Cicilan"):
            st.markdown("""
            - Terdapat korelasi positif yang jelas antara jumlah cicilan dan nilai pesanan rata-rata, yang menunjukkan bahwa konsumen cenderung menggunakan cicilan untuk pembelian bernilai lebih tinggi.
            - Nilai rata-rata meningkat secara signifikan untuk transaksi dengan cicilan 10 ke atas, mengindikasikan penggunaan opsi cicilan panjang terutama untuk pembelian bernilai sangat tinggi.
            - Terdapat lonjakan pada beberapa jumlah cicilan tertentu (seperti 6, 10, dan 12), yang mungkin mencerminkan promosi khusus atau paket cicilan standar dari penjual atau bank.
            - Insight ini dapat digunakan untuk strategi penetapan harga dan bundling produk, dengan mempertimbangkan preferensi konsumen untuk opsi pembayaran tertentu.
            """)
    else:
        st.info("Tidak ada data pembayaran kartu kredit dalam periode yang dipilih.")

# ----- Tab 4: Performa Pengiriman -----
with tab4:
    st.header("🚚 Pertanyaan 4: Bagaimana performa pengiriman pesanan dibandingkan dengan estimasi waktu?")
    
    # Filter orders berdasarkan rentang tanggal dan status terkirim
    delivery_data = data['orders'][
        (data['orders']['order_purchase_timestamp'] >= start_date) & 
        (data['orders']['order_purchase_timestamp'] <= end_date) &
        (data['orders']['order_status'] == 'delivered')
    ].copy()
    
    # Filter out rows with missing delivery dates
    delivery_data = delivery_data.dropna(subset=['order_delivered_customer_date', 'order_estimated_delivery_date'])
    
    if len(delivery_data) > 0:
        # Hitung selisih waktu antara estimasi dan aktual pengiriman
        delivery_data['delivery_difference'] = (delivery_data['order_delivered_customer_date'] - 
                                               delivery_data['order_estimated_delivery_date']).dt.days
        
        # Metrik performa pengiriman
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Hitung waktu pengiriman actual
            delivery_data['actual_delivery_days'] = (delivery_data['order_delivered_customer_date'] - 
                                                   delivery_data['order_purchase_timestamp']).dt.days
            avg_delivery_time = delivery_data['actual_delivery_days'].mean()
            st.metric("Rata-rata Waktu Pengiriman", f"{avg_delivery_time:.1f} hari")
        
        with col2:
            # Hitung waktu pengiriman estimasi
            delivery_data['estimated_delivery_days'] = (delivery_data['order_estimated_delivery_date'] - 
                                                      delivery_data['order_purchase_timestamp']).dt.days
            avg_estimated_time = delivery_data['estimated_delivery_days'].mean()
            st.metric("Rata-rata Estimasi Pengiriman", f"{avg_estimated_time:.1f} hari")
        
        with col3:
            # Hitung persentase tepat waktu
            on_time_percentage = (delivery_data['delivery_difference'] <= 0).mean() * 100
            st.metric("Persentase Tepat Waktu", f"{on_time_percentage:.1f}%")
        
        # Visualisasi 1: Status Performa Pengiriman
        st.subheader("Visualisasi 1: Status Performa Pengiriman")
        
        # Definisi kategori ketepatan waktu
        delivery_data['delivery_status'] = pd.cut(
            delivery_data['delivery_difference'],
            bins=[-float('inf'), -3, -1, 0, 2, float('inf')],
            labels=['Very Early', 'Early', 'On Time', 'Late', 'Very Late']
        )
        
        # Agregasi berdasarkan status pengiriman
        delivery_summary = delivery_data['delivery_status'].value_counts().reset_index()
        delivery_summary.columns = ['delivery_status', 'count']
        
        # Urutkan berdasarkan kategori
        status_order = ['Very Early', 'Early', 'On Time', 'Late', 'Very Late']
        delivery_summary['delivery_status'] = pd.Categorical(
            delivery_summary['delivery_status'], 
            categories=status_order, 
            ordered=True
        )
        delivery_summary = delivery_summary.sort_values('delivery_status')
        
        # Warna untuk setiap kategori
        color_map = {
            'Very Early': 'darkgreen',
            'Early': 'green',
            'On Time': 'lightgreen',
            'Late': 'orange',
            'Very Late': 'red'
        }
        
        # Visualisasi distribusi status pengiriman
        fig = px.bar(
            delivery_summary, 
            x='delivery_status', 
            y='count',
            title='Analisis Performa Pengiriman',
            color='delivery_status',
            color_discrete_map=color_map,
            labels={'delivery_status': 'Status Pengiriman', 'count': 'Jumlah Pesanan'}
        )
        
        fig.update_layout(
            xaxis_title='Status Pengiriman',
            yaxis_title='Jumlah Pesanan'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("ℹ️ Insight Performa Pengiriman"):
            st.markdown("""
            - Sebagian besar pesanan (hampir 90%) dikirimkan tepat waktu atau lebih awal dari estimasi, menunjukkan kinerja operasional yang baik.
            - Pengiriman "Very Early" (lebih dari 3 hari sebelum estimasi) lebih banyak daripada pengiriman "Very Late" (lebih dari 2 hari setelah estimasi), menunjukkan kecenderungan untuk memberikan estimasi yang lebih konservatif.
            - Terdapat porsi kecil pengiriman yang "Late" dan "Very Late", yang menunjukkan area potensial untuk perbaikan dalam manajemen logistik.
            - Tren ini menunjukkan strategi yang baik dalam mengelola ekspektasi pelanggan, yang penting untuk kepuasan pelanggan dalam e-commerce.
            """)
        
        # Visualisasi 2: Distribusi Waktu Pengiriman
        st.subheader("Visualisasi 2: Distribusi Waktu Pengiriman")
        
        fig = px.histogram(
            delivery_data,
            x='actual_delivery_days',
            nbins=30,
            title='Distribusi Waktu Pengiriman (Hari)',
            labels={'actual_delivery_days': 'Waktu Pengiriman (Hari)'},
            color_discrete_sequence=['royalblue']
        )
        
        fig.add_vline(
            x=delivery_data['actual_delivery_days'].mean(), 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"Rata-rata: {delivery_data['actual_delivery_days'].mean():.1f} hari",
            annotation_position="top right"
        )
        
        fig.update_layout(
            xaxis_title="Waktu Pengiriman (Hari)",
            yaxis_title="Jumlah Pesanan",
            bargap=0.1
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("ℹ️ Insight Distribusi Waktu Pengiriman"):
            st.markdown("""
            - Waktu pengiriman aktual memiliki distribusi miring ke kanan, dengan mayoritas pengiriman selesai dalam 1-2 minggu, namun terdapat beberapa outlier dengan waktu pengiriman yang sangat panjang.
            - Rata-rata waktu pengiriman sekitar 12 hari, yang mencerminkan tantangan logistik untuk pengiriman e-commerce di negara sebesar Brasil.
            - Terdapat konsentrasi pengiriman di sekitar 5-15 hari, yang mungkin mencerminkan rute pengiriman dan jarak geografis yang umum.
            - Adanya beberapa kasus dengan waktu pengiriman yang sangat panjang menunjukkan potensi masalah dalam rantai pasokan atau pengiriman ke daerah terpencil yang perlu ditangani.
            """)
        
        # Visualisasi 3: Perbandingan Waktu Pengiriman dengan Estimasi
        st.subheader("Visualisasi 3: Perbandingan Waktu Pengiriman vs Estimasi")
        
        # Persiapkan data untuk visualisasi
        delivery_comparison = delivery_data[['actual_delivery_days', 'estimated_delivery_days']].copy()
        delivery_comparison = delivery_comparison.sample(min(len(delivery_comparison), 1000))  # Sample untuk visualisasi yang lebih jelas
        
        fig = px.scatter(
            delivery_comparison,
            x='estimated_delivery_days',
            y='actual_delivery_days',
            title='Perbandingan Waktu Pengiriman Estimasi vs Aktual',
            labels={
                'estimated_delivery_days': 'Estimasi Waktu Pengiriman (Hari)',
                'actual_delivery_days': 'Waktu Pengiriman Aktual (Hari)'
            },
            opacity=0.6
        )
        
        # Tambahkan garis referensi untuk pengiriman tepat waktu
        fig.add_trace(
            go.Scatter(
                x=[0, max(delivery_comparison['estimated_delivery_days'].max(), 
                         delivery_comparison['actual_delivery_days'].max())],
                y=[0, max(delivery_comparison['estimated_delivery_days'].max(), 
                         delivery_comparison['actual_delivery_days'].max())],
                mode='lines',
                name='Tepat Waktu',
                line=dict(color='green', dash='dash')
            )
        )
        
        fig.update_layout(
            xaxis_title="Estimasi Waktu Pengiriman (Hari)",
            yaxis_title="Waktu Pengiriman Aktual (Hari)",
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("ℹ️ Insight Perbandingan Waktu Pengiriman"):
            st.markdown("""
            - Titik-titik di bawah garis diagonal menunjukkan pengiriman yang lebih cepat dari estimasi, sedangkan titik-titik di atas garis menunjukkan keterlambatan.
            - Sebagian besar titik berada di bawah atau di sekitar garis diagonal, mengonfirmasi bahwa mayoritas pengiriman memenuhi atau melampaui ekspektasi waktu.
            - Terlihat pola di mana pengiriman dengan estimasi waktu yang lebih lama cenderung lebih sering tiba lebih awal dari perkiraan.
            - Outlier di atas garis diagonal menunjukkan kasus-kasus dengan keterlambatan signifikan yang memerlukan investigasi lebih lanjut.
            """)
    else:
        st.warning("Tidak ada data yang cukup untuk analisis pengiriman dalam rentang waktu yang dipilih.")

# ----- Tab 5: Distribusi Geografis -----
with tab5:
    st.header("🌎 Pertanyaan 5: Bagaimana distribusi geografis pelanggan dan perbedaan perilaku pembelian antar wilayah?")
    
    # Visualisasi 1: Distribusi Pelanggan berdasarkan Negara Bagian
    st.subheader("Visualisasi 1: Distribusi Pelanggan berdasarkan Negara Bagian")
    
    # Distribusi pelanggan berdasarkan negara bagian
    customer_states = data['customers']['customer_state'].value_counts().reset_index()
    customer_states.columns = ['state', 'customer_count']
    
    # Filter berdasarkan state jika dipilih
    if selected_state:
        customer_states = customer_states[customer_states['state'] == selected_state]
    
    # Buat peta Brazil
    brazil_map = folium.Map(location=[-14.235, -51.9253], zoom_start=4, tiles="CartoDB positron")
    
    # Tambahkan GeoJson dari Brazil
    folium.Choropleth(
        geo_data='https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson',
        name='choropleth',
        data=customer_states,
        columns=['state', 'customer_count'],
        key_on='feature.properties.sigla',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Customer Count'
    ).add_to(brazil_map)
    
    folium.LayerControl().add_to(brazil_map)
    
    # Tampilkan peta
    folium_static(brazil_map)
    
    with st.expander("ℹ️ Insight Distribusi Geografis Pelanggan"):
        st.markdown("""
        - São Paulo (SP) sangat mendominasi basis pelanggan, dengan jumlah pelanggan jauh melebihi negara bagian lainnya, mencerminkan status ekonomi dan densitas populasi yang tinggi.
        - Rio de Janeiro (RJ) dan Minas Gerais (MG) menduduki posisi kedua dan ketiga, konsisten dengan status mereka sebagai daerah metropolitan utama di Brasil.
        - Terdapat kesenjangan yang signifikan antara beberapa negara bagian teratas (SP, RJ, MG) dengan yang lainnya, menunjukkan konsentrasi aktivitas e-commerce di daerah urban utama.
        - Negara bagian di daerah utara dan tengah Brasil memiliki jumlah pelanggan yang rendah, mengindikasikan potensi pasar yang belum dimanfaatkan atau tantangan infrastruktur.
        """)
    
    # Visualisasi 2: Jumlah Pelanggan per Negara Bagian
    st.subheader("Visualisasi 2: Jumlah Pelanggan per Negara Bagian")
    
    if not selected_state:
        # Sorting state berdasarkan jumlah pelanggan
        sorted_states = customer_states.sort_values('customer_count', ascending=False)
        
        fig = px.bar(
            sorted_states,
            x='state',
            y='customer_count',
            title='Distribusi Pelanggan berdasarkan Negara Bagian',
            labels={'state': 'Negara Bagian', 'customer_count': 'Jumlah Pelanggan'},
            color='customer_count',
            color_continuous_scale='YlOrRd'
        )
        
        fig.update_layout(
            xaxis={'categoryorder': 'total descending'},
            xaxis_title="Negara Bagian",
            yaxis_title="Jumlah Pelanggan"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Jika state dipilih, tampilkan distribusi kota
        city_counts = data['customers'][data['customers']['customer_state'] == selected_state]['customer_city'].value_counts().reset_index()
        city_counts.columns = ['city', 'count']
        top_cities = city_counts.head(10)
        
        fig = px.bar(
            top_cities,
            x='city',
            y='count',
            title=f'Top 10 Kota di {selected_state} berdasarkan Jumlah Pelanggan',
            labels={'city': 'Kota', 'count': 'Jumlah Pelanggan'},
            color='count',
            color_continuous_scale='YlOrRd'
        )
        
        fig.update_layout(
            xaxis={'categoryorder': 'total descending'},
            xaxis_title="Kota",
            yaxis_title="Jumlah Pelanggan"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Visualisasi 3: Kategori Produk Teratas berdasarkan Wilayah
    st.subheader("Visualisasi 3: Kategori Produk Teratas berdasarkan Wilayah")
    
    # Filter pesanan berdasarkan negara bagian jika ditentukan
    if selected_state:
        state_customers = data['customers'][data['customers']['customer_state'] == selected_state]['customer_id'].unique()
        state_orders = data['orders'][data['orders']['customer_id'].isin(state_customers)]
    else:
        state_orders = data['orders']
    
    # Filter berdasarkan rentang tanggal
    state_orders = state_orders[
        (state_orders['order_purchase_timestamp'] >= start_date) & 
        (state_orders['order_purchase_timestamp'] <= end_date)
    ]
    
    # Gabungkan dengan item dan produk
    order_items = pd.merge(
        state_orders[['order_id']],
        data['order_items'][['order_id', 'product_id', 'price']],
        on='order_id',
        how='inner'
    )
    
    order_products = pd.merge(
        order_items,
        data['products'],
        on='product_id',
        how='inner'
    )
    
    # Pilih kolom kategori yang sesuai
    cat_column = 'product_category_name_english' if 'product_category_name_english' in order_products.columns else 'product_category_name'
    
    # Agregasi berdasarkan kategori
    category_summary = order_products.groupby(cat_column).agg({
        'price': 'sum',
        'order_id': 'nunique'
    }).reset_index()
    
    category_summary.columns = ['category', 'total_sales', 'order_count']
    
    # Urutkan berdasarkan total penjualan dan ambil 5 teratas
    top_categories = category_summary.sort_values('total_sales', ascending=False).head(5)
    
    fig = px.bar(
        top_categories,
        x='category',
        y='total_sales',
        title=f'Top 5 Kategori Produk {selected_state if selected_state else "Semua Wilayah"}',
        labels={'category': 'Kategori', 'total_sales': 'Total Penjualan (R$)'},
        color='total_sales',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        xaxis_title="Kategori Produk",
        yaxis_title="Total Penjualan (R$)",
        xaxis={'categoryorder': 'total descending'},
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("ℹ️ Insight Kategori Produk berdasarkan Wilayah"):
        if selected_state:
            st.markdown(f"""
            - Di {selected_state}, kategori produk teratas menunjukkan preferensi konsumen yang spesifik untuk wilayah ini.
            - Perbedaan preferensi kategori dibandingkan dengan tren nasional dapat menjadi dasar untuk strategi pemasaran yang ditargetkan.
            - Tingkat penetrasi kategori tertentu di wilayah ini menunjukkan potensi untuk pengembangan pasar lebih lanjut atau diversifikasi produk.
            - Memahami perbedaan preferensi regional membantu dalam optimalisasi rantai pasokan dan inventaris untuk kebutuhan spesifik wilayah.
            """)
        else:
            st.markdown("""
            - Secara nasional, kategori "bed_bath_table" (peralatan kamar tidur dan kamar mandi) mendominasi penjualan, diikuti oleh produk kesehatan & kecantikan dan elektronik.
            - Pola preferensi kategori produk bervariasi secara signifikan antar wilayah, dengan wilayah urban cenderung memiliki permintaan lebih tinggi untuk produk gaya hidup.
            - Kategori produk rumah tangga dan perabotan memiliki popularitas yang konsisten di hampir semua wilayah, menunjukkan pasar dasar yang kuat.
            - Analisis regional mengungkapkan peluang untuk strategi pemasaran yang lebih ditargetkan dan personalisasi penawaran produk berdasarkan preferensi lokal.
            """)
    
    # Visualisasi 4: Pola Pembelian Waktu berdasarkan Wilayah
    st.subheader("Visualisasi 4: Pola Pembelian Waktu berdasarkan Wilayah")
    
    # Gabungkan pesanan dengan item untuk analisis pola waktu
    order_items_with_date = pd.merge(
        state_orders[['order_id', 'order_purchase_timestamp']],
        data['order_items'][['order_id', 'price']],
        on='order_id',
        how='inner'
    )
    
    # Ekstrak bulan dan hari dalam seminggu
    order_items_with_date['month'] = order_items_with_date['order_purchase_timestamp'].dt.month_name()
    order_items_with_date['day_of_week'] = order_items_with_date['order_purchase_timestamp'].dt.day_name()
    
    # Agregasi berdasarkan bulan dan hari dalam seminggu
    sales_heatmap = order_items_with_date.groupby(['month', 'day_of_week'])['price'].sum().unstack().fillna(0)
    
    # Pastikan urutan hari dan bulan yang benar
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Reindeks untuk memastikan urutan yang benar
    try:
        sales_heatmap = sales_heatmap.reindex(month_order).reindex(columns=day_order)
    except:
        # Jika tidak semua bulan atau hari tersedia dalam data
        st.warning("Beberapa bulan atau hari tidak tersedia dalam data yang dipilih.")
    
    # Buat peta panas jika data tersedia
    if not sales_heatmap.empty and not sales_heatmap.isna().all().all():
        fig = px.imshow(
                sales_heatmap,
                labels=dict(x="Hari dalam Minggu", y="Bulan", color="Penjualan (R$)"),
                x=sales_heatmap.columns.tolist(),
                y=sales_heatmap.index.tolist(),
                color_continuous_scale='YlGnBu',
                title=f'Peta Panas Penjualan berdasarkan Bulan dan Hari dalam Seminggu {selected_state if selected_state else ""}'
            )
            
        fig.update_layout(
            xaxis_title="Hari dalam Minggu",
            yaxis_title="Bulan"
            )
            
        st.plotly_chart(fig, use_container_width=True)
            
        with st.expander("ℹ️ Insight Pola Waktu Pembelian"):
                st.markdown("""
                - Peta panas menunjukkan pola pembelian yang bervariasi berdasarkan bulan dan hari dalam seminggu, dengan beberapa konsentrasi penjualan yang jelas.
                - November memiliki penjualan tertinggi, terutama di hari Jumat, Senin, dan Selasa, yang kemungkinan terkait dengan acara belanja seperti Black Friday.
                - Pembelian pada akhir pekan (Sabtu dan Minggu) secara konsisten lebih rendah dibandingkan hari kerja, yang berbeda dari pola belanja offline tradisional.
                - Terdapat variasi musiman, dengan bulan-bulan menjelang akhir tahun (Oktober hingga Desember) menunjukkan aktivitas lebih tinggi, mencerminkan musim belanja liburan.
                """)
    else:
        st.info("Tidak ada data yang cukup untuk membuat peta panas penjualan dalam rentang waktu yang dipilih.")

        # Tampilkan informasi tentang notebook analisis
        st.markdown("---")
        st.info("""
        **Olist E-commerce Data Analytics Project**

        Dashboard ini menampilkan hasil analisis dari dataset e-commerce Olist Brasil, menjawab lima pertanyaan bisnis utama.
        Setiap visualisasi dilengkapi dengan insights yang dapat ditindaklanjuti untuk membantu pengambilan keputusan.

        Untuk analisis lebih mendalam, silakan buka notebook.ipynb yang berisi proses analisis lengkap termasuk:
        - Data preparation dan exploration
        - Feature engineering
        - RFM analysis dan customer segmentation 
        - Analisis geografis dan temporal
        - Kesimpulan dan rekomendasi strategis
        """)

        # Footer
        st.markdown("""
        <div style="text-align: center">
            <p>Olist E-commerce Analytics Dashboard | Dibuat dengan Streamlit | Ashim Izzuddin</p>
        </div>
        """, unsafe_allow_html=True)