import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuración de la base de datos (Persistente en tu futuro NAS)
conn = sqlite3.connect('taller_profesional.db', check_same_thread=False)
c = conn.cursor()

def crear_tablas():
    c.execute('''CREATE TABLE IF NOT EXISTS ordenes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, equipo TEXT, 
                  serie TEXT, checklist TEXT, falla TEXT, estado TEXT, 
                  notas_tecnicas TEXT, fecha_ingreso TEXT)''')
    conn.commit()

crear_tablas()

st.set_page_config(page_title="Gestión Taller Pro", layout="wide", initial_sidebar_state="expanded")

# --- ESTILOS TIPO SAMII ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGACIÓN ---
menu = ["📊 Dashboard", "🆕 Recepción (Ingreso)", "🔧 Taller / Trazabilidad", "🔍 Buscador Histórico"]
choice = st.sidebar.radio("MENÚ PRINCIPAL", menu)

# --- LÓGICA: DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("Estado del Centro de Servicio")
    df = pd.read_sql_query("SELECT * FROM ordenes", conn)
    
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("En Diagnóstico", len(df[df['estado'] == 'En Diagnóstico']))
        col2.metric("Esperando Repuesto", len(df[df['estado'] == 'Esperando Repuesto']))
        col3.metric("Listos", len(df[df['estado'] == 'Listo']))
        col4.metric("Total Mes", len(df))
        
        st.subheader("Órdenes Recientes")
        st.dataframe(df.tail(10), use_container_width=True)
    else:
        st.info("No hay datos registrados aún.")

# --- LÓGICA: RECEPCIÓN (Inspirado en Checklist de SAMII) ---
elif choice == "🆕 Recepción (Ingreso)":
    st.subheader("📝 Registro de Nueva Orden de Servicio")
    
    with st.form("form_registro"):
        col_a, col_b = st.columns(2)
        with col_a:
            cliente = st.text_input("Nombre del Cliente")
            equipo = st.text_input("Modelo del Equipo (Ej: iPhone 13)")
            serie = st.text_input("Número de Serie / IMEI")
        
        with col_b:
            st.write("**Checklist de Entrada:**")
            c1 = st.checkbox("Enciende")
            c2 = st.checkbox("Pantalla OK")
            c3 = st.checkbox("Carga Batería")
            c4 = st.checkbox("Audio/Micrófono")
            falla = st.text_area("Falla Reportada por el Cliente")
        
        btn_guardar = st.form_submit_button("Generar Orden de Servicio")
        
        if btn_guardar:
            checklist_res = f"Enc:{c1}|Pan:{c2}|Car:{c3}|Aud:{c4}"
            fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
            c.execute("INSERT INTO ordenes (cliente, equipo, serie, checklist, falla, estado, notas_tecnicas, fecha_ingreso) VALUES (?,?,?,?,?,?,?,?)",
                      (cliente, equipo, serie, checklist_res, falla, "En Diagnóstico", "", fecha))
            conn.commit()
            st.success(f"¡Orden Generada! ID de Seguimiento: {c.lastrowid}")

# --- LÓGICA: TALLER (Trazabilidad Paso a Paso) ---
elif choice == "🔧 Taller / Trazabilidad":
    st.subheader("Gestión de Equipos en Taller")
    # Solo mostramos lo que NO está entregado
    df_taller = pd.read_sql_query("SELECT * FROM ordenes WHERE estado != 'Entregado'", conn)
    
    for _, row in df_taller.iterrows():
        with st.expander(f"OT #{row['id']} - {row['equipo']} | Cliente: {row['cliente']}"):
            c_izq, c_der = st.columns([1, 2])
            with c_izq:
                st.info(f"**Checklist:** {row['checklist']}")
                st.warning(f"**Falla:** {row['falla']}")
            
            with c_der:
                # Actualizar Estado
                nuevo_estado = st.selectbox("Cambiar Estado", 
                                            ["En Diagnóstico", "Esperando Repuesto", "Listo", "Entregado"], 
                                            index=["En Diagnóstico", "Esperando Repuesto", "Listo", "Entregado"].index(row['estado']),
                                            key=f"status_{row['id']}")
                
                # Notas técnicas (Historial)
                st.write("**Notas del Técnico:**")
                st.text(row['notas_tecnicas'])
                nueva_nota = st.text_input("Añadir comentario técnico", key=f"note_{row['id']}")
                
                if st.button("Actualizar Orden", key=f"btn_{row['id']}"):
                    fecha_nota = datetime.now().strftime("%d/%m %H:%M")
                    notas_actualizadas = row['notas_tecnicas'] + f"\n[{fecha_nota}]: {nueva_nota}" if nueva_nota else row['notas_tecnicas']
                    c.execute("UPDATE ordenes SET estado = ?, notas_tecnicas = ? WHERE id = ?", 
                              (nuevo_estado, notas_actualizadas, row['id']))
                    conn.commit()
                    st.rerun()

# --- LÓGICA: BUSCADOR ---
elif choice == "🔍 Buscador Histórico":
    st.subheader("Búsqueda de Equipos y Clientes")
    busqueda = st.text_input("Escribe el nombre del cliente, modelo o serie...")
    if busqueda:
        query = f"SELECT * FROM ordenes WHERE cliente LIKE '%{busqueda}%' OR equipo LIKE '%{busqueda}%' OR serie LIKE '%{busqueda}%'"
        res_busqueda = pd.read_sql_query(query, conn)
        st.table(res_busqueda)
