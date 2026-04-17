import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. Ρυθμίσεις Σελίδας ---
st.set_page_config(page_title="Ανάλυση Αντιβιοτικών", layout="wide")
st.title("💊 Πρόγραμμα Ανάλυσης Κατανάλωσης Αντιβιοτικών (DDD)")

# --- 2. Δεδομένα Πληθυσμού ανά Έτος ---
POPULATION_PER_YEAR = {
    2017: 10768193, 
    2018: 10732882,
    2019: 10724599,
    2020: 10718565,
    2021: 10678632,
    2022: 10432481,
    2023: 10413982,
    2024: 10390000,
    2025: 10370000,
    2026: 10350000
}

st.markdown("""
Καλώς ήρθες! Ανέβασε το αρχείο σου (σε μορφή **CSV ή Excel**) για να δούμε την κατανάλωση. 
*Βεβαιώσου ότι το αρχείο σου έχει στήλες για: Μήνα/Έτος, Εμπορική Ονομασία, Δραστική, mg ανά συσκευασία, Τεμάχια Πωλήσεων και το DDD WHO.*
""")

# --- 3. Φόρτωση Αρχείου (Υποστηρίζει πλέον CSV και XLSX) ---
uploaded_file = st.file_uploader("Ανέβασε το αρχείο σου (CSV ή Excel) εδώ", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        # Διαβάζουμε το αρχείο ανάλογα με τον τύπο του
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            
        st.success("Το αρχείο ανέβηκε και διαβάστηκε επιτυχώς!")
        
        with st.expander("👀 Δες τα πρώτα δεδομένα του αρχείου σου (Προεπισκόπηση)"):
            st.dataframe(df.head())

        # --- 4. Πλαϊνό Μενού για Αντιστοίχιση Στηλών ---
        st.sidebar.header("⚙️ Ρυθμίσεις Στηλών")
        st.sidebar.write("Επειδή τα αρχεία διαφέρουν, πες στο πρόγραμμα ποια στήλη είναι ποια:")
        
        col_date = st.sidebar.selectbox("Ημερομηνία / Μήνας", df.columns)
        col_trade = st.sidebar.selectbox("Εμπορική Ονομασία", df.columns)
        col_substance = st.sidebar.selectbox("Δραστική Ουσία", df.columns)
        col_mg_pack = st.sidebar.selectbox("Σύνολο mg / Συσκευασία", df.columns)
        col_units = st.sidebar.selectbox("Πωλήσεις (Τεμάχια)", df.columns)
        col_ddd_who = st.sidebar.selectbox("DDD WHO (σε mg)", df.columns)

        # --- 5. Κουμπί Εκκίνησης Υπολογισμών ---
        if st.button("🚀 Υπολογισμός & Δημιουργία Γραφημάτων"):
            
            # --- ΜΑΘΗΜΑΤΙΚΟΙ ΥΠΟΛΟΓΙΣΜΟΙ ---
            
            # Α. Καθαρισμός δεδομένων (μετατροπή σε αριθμούς για αποφυγή λαθών)
            df[col_mg_pack] = pd.to_numeric(df[col_mg_pack], errors='coerce')
            df[col_units] = pd.to_numeric(df[col_units], errors='coerce')
            df[col_ddd_who] = pd.to_numeric(df[col_ddd_who], errors='coerce')

            # Β. Εύρεση του Έτους από τη στήλη Ημερομηνίας
            df['Datetime'] = pd.to_datetime(df[col_date], errors='coerce')
            df['Year'] = df['Datetime'].dt.year

            # Γ. Αντιστοίχιση του σωστού πληθυσμού ανάλογα με τη χρονιά
            # Αν δεν βρει χρονιά, βάζει τον μέσο όρο (10.432.000) για ασφάλεια
            df['Current_Population'] = df['Year'].map(POPULATION_PER_YEAR).fillna(10432000)

            # Δ. Υπολογισμός συνολικών mg και DDD
            df['Total_mg'] = df[col_mg_pack] * df[col_units]
            df['Total_DDD'] = df['Total_mg'] / df[col_ddd_who]
            
            # Ε. Υπολογισμός DDD ανά 1000 κατοίκους (με τον δυναμικό πληθυσμό!)
            df['DDD_per_1000'] = (df['Total_DDD'] / df['Current_Population']) * 1000

            st.divider()
            st.header("📊 Αποτελέσματα & Γραφήματα")

            # --- ΓΡΑΦΗΜΑ 1: Συνολική κατανάλωση ανά μήνα ---
            st.subheader("1. Συγκριτικό Γράφημα: Συνολική Κατανάλωση Αντιβιοτικών (DDD) ανά Μήνα/Έτος")
            df_total_time = df.groupby(col_date)['Total_DDD'].sum().reset_index()
            fig1 = px.line(df_total_time, x=col_date, y='Total_DDD', markers=True, 
                           title="Διακύμανση Συνολικών DDD στον χρόνο")
            st.plotly_chart(fig1, use_container_width=True)

            # --- ΓΡΑΦΗΜΑ 2: Κατανάλωση ανά Δραστική Ουσία ---
            st.subheader("2. Συγκριτικό Γράφημα: Διακύμανση ανά Δραστική Ουσία")
            df_substance_time = df.groupby([col_date, col_substance])['Total_DDD'].sum().reset_index()
            fig2 = px.bar(df_substance_time, x=col_date, y='Total_DDD', color=col_substance,
                           title="Κατανάλωση DDD ανά Δραστική Ουσία (Stacked Bar)")
            st.plotly_chart(fig2, use_container_width=True)

            # --- ΠΙΝΑΚΑΣ 1: DDD ανά 1000 κατοίκους για Εμπορική Ονομασία ---
            st.subheader("3. Πίνακας: DDD ανά 1000 κατοίκους ανά Εμπορική Ονομασία")
            df_trade_report = df.groupby([col_date, col_trade, col_mg_pack])['DDD_per_1000'].sum().reset_index()
            df_trade_report['DDD_per_1000'] = df_trade_report['DDD_per_1000'].round(4) # Στρογγυλοποίηση
            st.dataframe(df_trade_report, use_container_width=True)

            # --- ΠΙΝΑΚΑΣ 2: DDD ανά 1000 κατοίκους για Δραστική Ουσία ---
            st.subheader("4. Πίνακας: DDD ανά 1000 κατοίκους ανά Δραστική Ουσία")
            df_substance_report = df.groupby([col_date, col_substance])['DDD_per_1000'].sum().reset_index()
            df_substance_report['DDD_per_1000'] = df_substance_report['DDD_per_1000'].round(4) # Στρογγυλοποίηση
            st.dataframe(df_substance_report, use_container_width=True)

    except Exception as e:
        st.error(f"Ωχ! Κάτι πήγε στραβά με το αρχείο ή τις στήλες. Το σφάλμα είναι: {e}")
