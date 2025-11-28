import streamlit as st
import pandas as pd
from sqlalchemy import text

# Database connection
def get_db_connection():
    # Supabase connection
    conn = st.connection("supabase", type="sql")
    return conn

def get_all_symptoms():
    conn = get_db_connection()
    # Fetch symptoms
    df = conn.query('SELECT * FROM symptoms ORDER BY name', ttl=0)
    return df.to_dict('records')

def get_diseases_rules():
    conn = get_db_connection()
    # Fetch diseases
    diseases_df = conn.query('SELECT * FROM diseases', ttl=0)
    diseases = diseases_df.to_dict('records')
    
    disease_rules = []
    for d in diseases:
        # Fetch rules
        rules_df = conn.query('''
            SELECT s.name, r.weight
            FROM rules r 
            JOIN symptoms s ON r.symptom_id = s.id 
            WHERE r.disease_id = :id
        ''', params={"id": d['id']}, ttl=0)
        
        rules = rules_df.to_dict('records')
        
        disease_rules.append({
            'id': d['id'],
            'name': d['name'],
            'description': d['description'],
            'suggestion': d['suggestion'],
            'min_symptoms': d['min_symptoms'],
            'rules': [{'name': r['name'], 'weight': r['weight']} for r in rules]
        })
    
    return disease_rules

def diagnose(selected_symptoms):
    disease_rules = get_diseases_rules()
    results = []

    for disease in disease_rules:
        rules = disease['rules']
        matched_weight = 0
        total_weight = 0
        match_count = 0
        
        for rule in rules:
            total_weight += rule['weight']
            if rule['name'] in selected_symptoms:
                matched_weight += rule['weight']
                match_count += 1
        
        # Calculate percentage
        if total_weight > 0:
            percentage = (matched_weight / total_weight) * 100
        else:
            percentage = 0
            
        # Check minimum requirement
        if match_count >= disease['min_symptoms']:
            results.append({
                'disease': disease,
                'percentage': percentage,
                'match_count': match_count
            })

    # Sort results
    results.sort(key=lambda x: x['percentage'], reverse=True)
    return results

def main():
    st.set_page_config(page_title="Expert System Diagnosa Penyakit", page_icon="🏥")
    
    st.title("🏥 Expert System Diagnosa Penyakit Berat")
    st.write("Silakan pilih gejala yang Anda alami di bawah ini:")

    # Get symptoms
    symptoms = get_all_symptoms()
    
    # Symptom selection
    selected_symptoms = []
    
    # Layout symptoms
    cols = st.columns(3)
    for i, symptom in enumerate(symptoms):
        col = cols[i % 3]
        if col.checkbox(symptom['name'], key=symptom['id']):
            selected_symptoms.append(symptom['name'])

    st.markdown("---")
    
    if st.button("Diagnosa", type="primary"):
        if not selected_symptoms:
            st.warning("Silakan pilih minimal satu gejala untuk melakukan diagnosa.")
        else:
            results = diagnose(selected_symptoms)
            
            if results:
                top_result = results[0]
                disease = top_result['disease']
                
                st.success(f"Hasil Diagnosa: **{disease['name']}**")
                st.metric(label="Tingkat Kecocokan (Berdasarkan Bobot)", value=f"{top_result['percentage']:.1f}%")
                
                st.subheader("Deskripsi")
                st.write(disease['description'])
                
                st.subheader("Saran")
                st.info(disease['suggestion'])
                
                # Show alternatives
                if len(results) > 1:
                    with st.expander("Kemungkinan Penyakit Lain"):
                        for res in results[1:]:
                            st.write(f"- **{res['disease']['name']}**: {res['percentage']:.1f}%")
            else:
                st.error("Tidak ditemukan penyakit yang cocok dengan gejala yang dipilih.")
                st.write("Saran: Segera konsultasi dengan dokter untuk mendapatkan diagnosa yang tepat.")

if __name__ == "__main__":
    main()
