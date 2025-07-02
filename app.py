import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, timedelta
from db_ops import (
    create_table, insert_activity, fetch_by_user,
    update_activity, delete_activity
)
from auth import create_user_table, add_user, login_user

# Inisialisasi tabel database jika belum ada
create_table()
create_user_table()

# ==================== SIDEBAR LOGIN ====================
st.sidebar.title("🔐 Autentikasi")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    auth_menu = st.sidebar.radio("Login / Daftar", ["Login", "Daftar Akun"])

    st.markdown("""
        <div style='padding: 20px; background-color: #f0f2f6; border-radius: 10px; color: black;'>
            <h3>🔒 Silakan login terlebih dahulu untuk menggunakan aplikasi.</h3>
            <p>Jika belum memiliki akun, silakan daftar terlebih dahulu melalui menu di samping kiri.</p>
        </div>
    """, unsafe_allow_html=True)

    if auth_menu == "Login":
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")

            if login_btn:
                user = login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Selamat datang, {username} 👋")
                    st.rerun()
                else:
                    st.error("Username atau password salah.")

    elif auth_menu == "Daftar Akun":
        with st.form("signup_form"):
            new_user = st.text_input("Buat Username")
            new_pass = st.text_input("Buat Password", type="password")
            daftar_btn = st.form_submit_button("Daftar")

            if daftar_btn:
                add_user(new_user, new_pass)
                st.success("Akun berhasil dibuat. Silakan login.")

else:
    st.sidebar.success(f"👤 Login sebagai: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ==================== MAIN APP ====================
if st.session_state.logged_in:
    st.title("🧠 Rekam Jejak Digital")
    st.markdown("Catat, lacak, dan refleksikan aktivitas digitalmu setiap hari.")

    menu = st.sidebar.radio("📌 Menu", ["📅 Input Aktivitas", "📊 Lihat Ringkasan", "📈 Dashboard Statistik", "⬇️ Export Data"])

    kategori_opsi = ["Sosial Media", "Belajar", "Baca Artikel", "Coding", "Hiburan", "Olahraga", "Lainnya"]

    if menu == "📅 Input Aktivitas":
        st.header("📝 Tambah Aktivitas")
        tanggal = st.date_input("Tanggal", date.today())
        kategori = st.selectbox("Kategori", kategori_opsi)
        deskripsi = st.text_area("Deskripsi")
        durasi = st.slider("Durasi (menit)", 1, 300)

        if st.button("✅ Simpan Aktivitas"):
            insert_activity(st.session_state.username, tanggal.strftime("%Y-%m-%d"), kategori, deskripsi, durasi)
            st.success("Aktivitas berhasil disimpan!")

    elif menu == "📊 Lihat Ringkasan":
        st.header("📈 Ringkasan Aktivitas")
        df = fetch_by_user(st.session_state.username)

        if not df.empty:
            st.dataframe(df)

            st.markdown(f"**Total Waktu:** {df['durasi'].sum()} menit")

            chart_type = st.selectbox("Pilih jenis grafik", ["Bar Chart", "Pie Chart", "Trendline"])
            chart_color = st.color_picker("Pilih warna chart", "#FF5733")
            pie_display = st.radio("Tampilkan pada Pie Chart", ["Persentase", "Jumlah"], horizontal=True)
            chart = df.groupby("kategori")["durasi"].sum().reset_index()

            if chart_type == "Bar Chart":
                fig, ax = plt.subplots()
                ax.bar(chart["kategori"], chart["durasi"], color=chart_color)
                ax.set_ylabel("Durasi (menit)")
                ax.set_title("Bar Chart Aktivitas")
                st.pyplot(fig)

            elif chart_type == "Pie Chart":
                fig, ax = plt.subplots()
                if pie_display == "Persentase":
                    autopct = "%1.1f%%"
                else:
                    total = chart["durasi"].sum()
                    autopct = lambda p: f"{p * total / 100:.0f}"

                wedges, texts, autotexts = ax.pie(
                    chart["durasi"],
                    labels=chart["kategori"],
                    autopct=autopct,
                    startangle=140,
                    colors=[chart_color] * len(chart),
                    wedgeprops={'linewidth': 1, 'edgecolor': 'black'}
                )
                ax.axis("equal")
                ax.set_title("Pie Chart Aktivitas")
                st.pyplot(fig)

            elif chart_type == "Trendline":
                df["tanggal"] = pd.to_datetime(df["tanggal"])
                df = df.sort_values("tanggal")
                kategori_list = df["kategori"].unique()

                st.subheader("📈 Trendline per Kategori")
                for kategori in kategori_list:
                    df_kat = df[df["kategori"] == kategori]
                    df_grouped = df_kat.groupby("tanggal")["durasi"].sum().reset_index()

                    if len(df_grouped) >= 2:
                        x = np.arange(len(df_grouped))
                        y = df_grouped["durasi"].values

                        coef = np.polyfit(x, y, 1)
                        trend = np.poly1d(coef)

                        fig, ax = plt.subplots()
                        ax.plot(df_grouped["tanggal"], y, label="Aktual", marker='o', color=chart_color)
                        ax.plot(df_grouped["tanggal"], trend(x), label="Trendline", linestyle='--', color='gray')
                        ax.set_title(f"Kategori: {kategori}")
                        ax.set_ylabel("Durasi (menit)")
                        ax.set_xlabel("Tanggal")
                        ax.legend()
                        plt.xticks(rotation=30)
                        st.pyplot(fig)
                    else:
                        st.info(f"Kategori '{kategori}' belum punya cukup data untuk trendline.")

            # Edit / Hapus
            st.subheader("✏️ Edit / 🗑️ Hapus Aktivitas")
            selected_id = st.selectbox("Pilih ID Aktivitas", df["id"])
            selected_row = df[df["id"] == selected_id].iloc[0]

            new_kategori = st.selectbox("Edit Kategori", kategori_opsi, index=kategori_opsi.index(selected_row["kategori"]))
            new_deskripsi = st.text_input("Edit Deskripsi", value=selected_row["deskripsi"])
            new_durasi = st.slider("Edit Durasi", 1, 300, selected_row["durasi"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Simpan Edit"):
                    update_activity(selected_id, new_kategori, new_deskripsi, new_durasi)
                    st.success("Aktivitas berhasil diperbarui!")
                    st.rerun()

            with col2:
                if st.button("🗑️ Hapus"):
                    delete_activity(selected_id)
                    st.warning("Aktivitas berhasil dihapus.")
                    st.rerun()
        else:
            st.info("Belum ada data aktivitas.")

    elif menu == "📈 Dashboard Statistik":
        st.header("📊 Statistik Aktivitas")
        df = fetch_by_user(st.session_state.username)
        if not df.empty:
            df["tanggal"] = pd.to_datetime(df["tanggal"])
            pilihan_range = st.selectbox("Pilih Rentang Waktu", ["Mingguan", "Bulanan"])
            chart_type = st.selectbox("Pilih jenis grafik", ["Area Chart", "Bar Chart"])
            chart_color = st.color_picker("Warna grafik", "#00ccff")

            if pilihan_range == "Mingguan":
                start_date = date.today() - timedelta(days=6)
            else:
                start_date = date.today() - timedelta(days=29)

            df_filtered = df[df["tanggal"] >= pd.to_datetime(start_date)]
            summary = df_filtered.groupby(["tanggal", "kategori"]).sum().reset_index()
            pivot = summary.pivot(index="tanggal", columns="kategori", values="durasi").fillna(0)

            if chart_type == "Area Chart":
                st.area_chart(pivot)
            elif chart_type == "Bar Chart":
                st.bar_chart(pivot)
        else:
            st.info("Belum ada data untuk ditampilkan di dashboard.")

    elif menu == "⬇️ Export Data":
        st.header("📄 Export Data")
        df = fetch_by_user(st.session_state.username)
        if not df.empty:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, f"{st.session_state.username}_aktivitas.csv", "text/csv")
        else:
            st.warning("Belum ada data untuk diekspor.")
else:
    st.info("Silakan login terlebih dahulu untuk menggunakan aplikasi.")
