import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- 1. Ρυθμίσεις Σελίδας ---
st.set_page_config(page_title="Ανάλυση Αντιβιοτικών", layout="wide")
st.title("💊 Πρόγραμμα Ανάλυσης Κατανάλωσης (Wide Format)")

# --- 2. Δεδομένα Πληθυσμού ανά Έτος ---
POPULATION_PER_YEAR = {
    2017: 10768193, 2018: 10732882, 2019: 10724599, 
    2020: 10718565, 2021: 10678632, 2022: 10432481, 
    2023: 10413982, 2024: 10390000, 2025: 10370000, 
    2026: 10350000
}

# --- Συνάρτηση για έξυπνη εύρεση του Έτους από το όνομα της στήλης ---
def extract_year(date_string):
    date_str = str(date_string)
    # Ψάχνει για τετραψήφιο (π.χ. 2018)
    match_4 = re.search(r'(20\d{2})', date_str)
    if match_4:
        return int(match_4.group(1))
    # Ψάχνει για διψήφιο (π.χ. 18, 19)
    match_2 = re.search(r'\b(1[7-9]|2[0-9])\b', date_str)
    if match_2:
        return 2000 + int(match_2.group(1))
    return 2024 # Ασφαλής επιλογή αν δεν βρει κάτι

# --- 3. Φόρτωση Αρχείου ---
uploaded_file = st.file_uploader("Ανέβασε το αρχείο σου (CSV ή Excel) εδώ", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            
        st.success("Το αρχείο διαβάστηκε επιτυχώς!")
        
        with st.expander("👀 Προεπισκόπηση Αρχικών Δεδομένων"):
            st.dataframe(df.head())

        # --- 4. Πλαϊνό Μενού Αντιστοίχισης Στηλών ---
        st.sidebar.header("⚙️ Βασικές Στήλες")
        col_trade = st.sidebar.selectbox("Εμπορική Ονομασία", df.columns)
        col_substance = st.sidebar.selectbox("Δραστική Ουσία", df.columns)
        col_mg_pack = st.sidebar.selectbox("Σύνολο mg / Συσκευασία", df.columns)
        col_ddd_who = st.sidebar.selectbox("DDD WHO (σε mg)", df.columns)

        st.sidebar.header("📅 Στήλες Πωλήσεων (Μήνες)")
        st.sidebar.write("Διάλεξε την αρχή και το τέλος των μηνών:")
        col_first_month = st.sidebar.selectbox("Από (π.χ. ΙΑΝ 2018)", df.columns)
        col_last_month = st.sidebar.selectbox("Έως (π.χ. ΔΕΚ 2024)", df.columns)

        # --- 5. Εκκίνηση Υπολογισμών ---
        if st.button("🚀 Υπολογισμός & Δημιουργία Γραφημάτων"):
            
            # Βρίσκουμε όλες τις στήλες ανάμεσα στον πρώτο και τον τελευταίο μήνα
            idx_start = df.columns.get_loc(col_first_month)
            idx_end = df.columns.get_loc(col_last_month) + 1
            sales_cols = list(df.columns[idx_start:idx_end])

            # Απαραίτητες στήλες αναγνώρισης
            id_cols = [col_trade, col_substance, col_mg_pack, col_ddd_who]
            
            # --- ΜΕΤΑΤΡΟΠΗ: Από Οριζόντια σε Κάθετη μορφή (Melt) ---
            df_long = df[id_cols + sales_cols].melt(
                id_vars=id_cols, 
                value_vars=sales_cols, 
                var_name='Μήνας_Έτος', 
                value_name='Πωλήσεις_Τεμάχια'
            )

            # Καθαρισμός δεδομένων (μετατροπή σε αριθμούς)
            df_long['Πωλήσεις_Τεμάχια'] = pd.to_numeric(df_long['Πωλήσεις_Τεμάχια'], errors='coerce').fillna(0)
            df_long[col_mg_pack] = pd.to_numeric(df_long[col_mg_pack], errors='coerce')
            df_long[col_ddd_who] = pd.to_numeric(df_long[col_ddd_who], errors='coerce')

            # Εύρεση Έτους και Πληθυσμού
            df_long['Έτος'] = df_long['Μήνας_Έτος'].apply(extract_year)
            df_long['Current_Population'] = df_long['Έτος'].map(POPULATION_PER_YEAR).fillna(10432000)

            # --- ΤΕΛΙΚΟΙ ΥΠΟΛΟΓΙΣΜΟΙ DDD ---
            df_long['Total_mg'] = df_long[col_mg_pack] * df_long['Πωλήσεις_Τεμάχια']
            df_long['Total_DDD'] = df_long['Total_mg'] / df_long[col_ddd_who]
            df_long['DDD_per_1000'] = (df_long['Total_DDD'] / df_long['Current_Population']) * 1000

            st.divider()
            st.header("📊 Αποτελέσματα & Γραφήματα")

            # --- ΓΡΑΦΗΜΑ 1: Συνολική κατανάλωση ανά μήνα ---
            st.subheader("1. Συνολική Κατανάλωση Αντιβιοτικών (DDD) ανά Περίοδο")
            df_total_time = df_long.groupby('Μήνας_Έτος', sort=False)['Total_DDD'].sum().reset_index()
            fig1 = px.line(df_total_time, x='Μήνας_Έτος', y='Total_DDD', markers=True, 
                           title="Διακύμανση Συνολικών DDD")
            st.plotly_chart(fig1, use_container_width=True)

            # --- ΓΡΑΦΗΜΑ 2: Κατανάλωση ανά Δραστική Ουσία ---
            st.subheader("2. Διακύμανση ανά Δραστική Ουσία")
            df_substance_time = df_long.groupby(['Μήνας_Έτος', col_substance], sort=False)['Total_DDD'].sum().reset_index()
            fig2 = px.bar(df_substance_time, x='Μήνας_Έτος', y='Total_DDD', color=col_substance,
                           title="Κατανάλωση DDD ανά Δραστική Ουσία (Stacked Bar)")
            st.plotly_chart(fig2, use_container_width=True)

            # --- ΠΙΝΑΚΑΣ 1: DDD ανά 1000 κατοίκους για Εμπορική Ονομασία ---
            st.subheader("3. Πίνακας: Συνολικά DDD ανά 1000 κατοίκους (Εμπορική Ονομασία)")
            # Ομαδοποίηση ανά Έτος (πιο χρήσιμο από το να τα βλέπεις όλα μαζί)
            df_trade_report = df_long.groupby(['Έτος', col_trade])['DDD_per_1000'].sum().reset_index()
            df_trade_report['DDD_per_1000'] = df_trade_report['DDD_per_1000'].round(4)
            st.dataframe(df_trade_report, use_container_width=True)

            # --- ΠΙΝΑΚΑΣ 2: DDD ανά 1000 κατοίκους για Δραστική Ουσία ---
            st.subheader("4. Πίνακας: Συνολικά DDD ανά 1000 κατοίκους (Δραστική Ουσία)")
            df_substance_report = df_long.groupby(['Έτος', col_substance])['DDD_per_1000'].sum().reset_index()
            df_substance_report['DDD_per_1000'] = df_substance_report['DDD_per_1000'].round(4)
            st.dataframe(df_substance_report, use_container_width=True)

    except Exception as e:
        st.error(f"Ωχ! Κάτι πήγε στραβά με τους υπολογισμούς. Λεπτομέρειες σφάλματος: {e}")
