import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuración de la Base de Datos en el NAS
conn = sqlite3.connect('gestion_tecnica.db', check_same_thread=False)
c = conn.cursor()

# Crear tablas si no existen
c.execute('''CREATE TABLE IF NOT EXISTS servicios 
             (id INTEGER PRIMARY KEY, cliente TEXT, equipo TEXT, falla TEXT, estado TEXT, fecha TEXT)''')
conn.commit()

st.set_page_config(page_title="ServiceTech Pro", layout="wide")

# --- INTERFAZ ---
st.title("🛠️ Sistema de Trazabilidad - Centro Técnico")

menu = ["Dashboard", "Nueva Entrada", "Taller / Trazabilidad"]
choice = st.sidebar.selectbox("Menú Principal", menu)

if choice == "Dashboard":
    st.subheader("Estado del Taller")
    df = pd.read_sql_query("SELECT * FROM servicios", conn)
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("En Revisión", len(df[df['estado'] == 'En Diagnóstico']))
        col2.metric("Esperando Repuesto", len(df[df['estado'] == 'Esperando Repuesto']))
        col3.metric("Listos para Entrega", len(df[df['estado'] == 'Listo']))
        st.dataframe(df)
    else:
        st.info("No hay equipos en el sistema.")

elif choice == "Nueva Entrada":
    st.subheader("Registro de Equipo")
    with st.form("form_entrada"):
        cliente = st.text_input("Nombre del Cliente")
        equipo = st.text_input("Equipo (Ej: Samsung S23, Laptop Dell)")
        falla = st.text_area("Falla Reportada")
        submitted = st.form_submit_button("Registrar Ingreso")
        
        if submitted:
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("INSERT INTO servicios (cliente, equipo, falla, estado, fecha) VALUES (?,?,?,?,?)",
                      (cliente, equipo, falla, "En Diagnóstico", fecha_actual))
            conn.commit()
            st.success(f"Equipo de {cliente} registrado correctamente.")

elif choice == "Taller / Trazabilidad":
    st.subheader("Actualización de Estados")
    df = pd.read_sql_query("SELECT * FROM servicios WHERE estado != 'Entregado'", conn)
    
    for index, row in df.iterrows():
        with st.expander(f"OT #{row['id']} - {row['equipo']} ({row['cliente']})"):
            st.write(f"**Falla:** {row['falla']}")
            nuevo_estado = st.selectbox("Cambiar Estado", 
                                        ["En Diagnóstico", "Esperando Repuesto", "Listo", "Entregado"], 
                                        key=row['id'])
            if st.button("Actualizar", key=f"btn_{row['id']}"):
                c.execute("UPDATE servicios SET estado = ? WHERE id = ?", (nuevo_estado, row['id']))
                conn.commit()
                st.rerun()
