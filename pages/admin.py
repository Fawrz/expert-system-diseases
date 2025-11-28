import streamlit as st
from sqlalchemy import text
import pandas as pd

def check_login(username, password):
    return username == "admin" and password == "admin123"

def admin_page():
    st.title("Admin Dashboard 🛠️")
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        
    if not st.session_state.logged_in:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
        return

    # Logout
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.title("Menu Admin")
    menu = st.sidebar.radio("Pilih Menu", ["Penyakit", "Gejala", "Aturan (Rules)"])
    
    conn = st.connection("supabase", type="sql")
    
    if menu == "Penyakit":
        st.header("Kelola Penyakit")
        
        # Add disease
        with st.expander("Tambah Penyakit Baru"):
            with st.form("add_disease"):
                new_name = st.text_input("Nama Penyakit")
                new_desc = st.text_area("Deskripsi")
                new_sugg = st.text_area("Saran")
                new_min = st.number_input("Minimum Gejala", min_value=1, value=1)
                submitted = st.form_submit_button("Simpan")
                
                if submitted and new_name:
                    with conn.session as s:
                        s.execute(
                            text('INSERT INTO diseases (name, description, suggestion, min_symptoms) VALUES (:name, :desc, :sugg, :min)'),
                            {'name': new_name, 'desc': new_desc, 'sugg': new_sugg, 'min': new_min}
                        )
                        s.commit()
                    st.success("Penyakit berhasil ditambahkan!")
                    st.rerun()
        
        # List diseases
        diseases_df = conn.query('SELECT * FROM diseases', ttl=0)
        diseases = diseases_df.to_dict('records')
        st.dataframe(diseases_df)
        
        st.subheader("Edit/Hapus Penyakit")
        selected_disease_id = st.selectbox("Pilih Penyakit", [d['id'] for d in diseases], format_func=lambda x: next(d['name'] for d in diseases if d['id'] == x))
        
        if selected_disease_id:
            disease = next(d for d in diseases if d['id'] == selected_disease_id)
            with st.form("edit_disease"):
                edit_name = st.text_input("Nama Penyakit", value=disease['name'])
                edit_desc = st.text_area("Deskripsi", value=disease['description'])
                edit_sugg = st.text_area("Saran", value=disease['suggestion'])
                edit_min = st.number_input("Minimum Gejala", min_value=1, value=disease['min_symptoms'])
                
                col1, col2 = st.columns(2)
                with col1:
                    update = st.form_submit_button("Update")
                with col2:
                    delete = st.form_submit_button("Hapus", type="primary")
                
                if update:
                    with conn.session as s:
                        s.execute(
                            text('UPDATE diseases SET name=:name, description=:desc, suggestion=:sugg, min_symptoms=:min WHERE id=:id'),
                            {'name': edit_name, 'desc': edit_desc, 'sugg': edit_sugg, 'min': edit_min, 'id': selected_disease_id}
                        )
                        s.commit()
                    st.success("Data berhasil diupdate!")
                    st.rerun()
                    
                if delete:
                    with conn.session as s:
                        # Delete rules first
                        s.execute(text('DELETE FROM rules WHERE disease_id=:id'), {'id': selected_disease_id})
                        s.execute(text('DELETE FROM diseases WHERE id=:id'), {'id': selected_disease_id})
                        s.commit()
                    st.success("Data berhasil dihapus!")
                    st.rerun()

    elif menu == "Gejala":
        st.header("Kelola Gejala")
        
        # Add symptom
        with st.expander("Tambah Gejala Baru"):
            with st.form("add_symptom"):
                new_name = st.text_input("Nama Gejala")
                submitted = st.form_submit_button("Simpan")
                
                if submitted and new_name:
                    try:
                        with conn.session as s:
                            s.execute(text('INSERT INTO symptoms (name) VALUES (:name)'), {'name': new_name})
                            s.commit()
                        st.success("Gejala berhasil ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        # List symptoms
        symptoms_df = conn.query('SELECT * FROM symptoms ORDER BY name', ttl=0)
        symptoms = symptoms_df.to_dict('records')
        st.dataframe(symptoms_df)
        
        st.subheader("Edit/Hapus Gejala")
        selected_symptom_id = st.selectbox("Pilih Gejala", [s['id'] for s in symptoms], format_func=lambda x: next(s['name'] for s in symptoms if s['id'] == x))
        
        if selected_symptom_id:
            symptom = next(s for s in symptoms if s['id'] == selected_symptom_id)
            with st.form("edit_symptom"):
                edit_name = st.text_input("Nama Gejala", value=symptom['name'])
                
                col1, col2 = st.columns(2)
                with col1:
                    update = st.form_submit_button("Update")
                with col2:
                    delete = st.form_submit_button("Hapus", type="primary")
                
                if update:
                    try:
                        with conn.session as s:
                            s.execute(text('UPDATE symptoms SET name=:name WHERE id=:id'), {'name': edit_name, 'id': selected_symptom_id})
                            s.commit()
                        st.success("Data berhasil diupdate!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                    
                if delete:
                    with conn.session as s:
                        # Delete rules first
                        s.execute(text('DELETE FROM rules WHERE symptom_id=:id'), {'id': selected_symptom_id})
                        s.execute(text('DELETE FROM symptoms WHERE id=:id'), {'id': selected_symptom_id})
                        s.commit()
                    st.success("Data berhasil dihapus!")
                    st.rerun()

    elif menu == "Aturan (Rules)":
        st.header("Kelola Aturan & Bobot")
        
        diseases_df = conn.query('SELECT * FROM diseases', ttl=0)
        diseases = diseases_df.to_dict('records')
        
        symptoms_df = conn.query('SELECT * FROM symptoms ORDER BY name', ttl=0)
        symptoms = symptoms_df.to_dict('records')
        
        selected_disease_id = st.selectbox("Pilih Penyakit untuk Edit Rules", [d['id'] for d in diseases], format_func=lambda x: next(d['name'] for d in diseases if d['id'] == x))
        
        if selected_disease_id:
            st.subheader(f"Rules untuk: {next(d['name'] for d in diseases if d['id'] == selected_disease_id)}")
            
            # Fetch rules
            current_rules_df = conn.query('''
                SELECT r.*, s.name as symptom_name 
                FROM rules r 
                JOIN symptoms s ON r.symptom_id = s.id 
                WHERE r.disease_id = :id
            ''', params={'id': selected_disease_id}, ttl=0)
            current_rules = current_rules_df.to_dict('records')
            
            # Display rules
            if current_rules:
                st.write("Gejala saat ini:")
                rules_data = []
                for r in current_rules:
                    rules_data.append({
                        "Gejala": r['symptom_name'],
                        "Bobot": r['weight'],
                        "Action": "Delete" # Placeholder
                    })
                st.dataframe(pd.DataFrame(rules_data))
                
                # Delete rule
                with st.form("delete_rule"):
                    rule_to_delete = st.selectbox("Hapus Gejala dari Penyakit ini", [r['symptom_id'] for r in current_rules], format_func=lambda x: next(r['symptom_name'] for r in current_rules if r['symptom_id'] == x))
                    delete_btn = st.form_submit_button("Hapus Rule")
                    
                    if delete_btn:
                        with conn.session as s:
                            s.execute(text('DELETE FROM rules WHERE disease_id=:did AND symptom_id=:sid'), {'did': selected_disease_id, 'sid': rule_to_delete})
                            s.commit()
                        st.success("Rule dihapus!")
                        st.rerun()

            st.markdown("---")
            st.subheader("Tambah/Update Rule")
            
            with st.form("add_rule"):
                symptom_to_add = st.selectbox("Pilih Gejala", [s['id'] for s in symptoms], format_func=lambda x: next(s['name'] for s in symptoms if s['id'] == x))
                weight = st.slider("Bobot (Weight)", 0.0, 1.0, 0.5, 0.1)
                
                submit_rule = st.form_submit_button("Simpan Rule")
                
                if submit_rule:
                    with conn.session as s:
                         # Upsert rule
                        s.execute(text('''
                            INSERT INTO rules (disease_id, symptom_id, weight) 
                            VALUES (:did, :sid, :w)
                            ON CONFLICT (disease_id, symptom_id) 
                            DO UPDATE SET weight = :w
                        '''), {'did': selected_disease_id, 'sid': symptom_to_add, 'w': weight})
                        s.commit()
                    
                    st.success("Rule berhasil disimpan!")
                    st.rerun()

if __name__ == "__main__":
    admin_page()
