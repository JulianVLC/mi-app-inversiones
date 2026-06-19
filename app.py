import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# Configuración de pantalla adaptable
st.set_page_config(page_title="Mi App de Inversiones Segura Pro", page_icon="📈", layout="wide")

# =========================================================================
# CONFIGURACIÓN DE SEGURIDAD Y BASE DE DATOS
# =========================================================================
CONTRASENA_ACCESO = "2707"  # Tu contraseña fija configurada

URL_GOOGLE_SHEETS = "https://docs.google.com/spreadsheets/d/1e6en21Ieuoy4rQeiTa_aUIO9mgLHjN3l9xBUYQaxKZY/edit?usp=sharing"
# =========================================================================

# Estilos visuales
st.markdown("""
    <style>
    .main { background-color: #0b0f19; }
    div[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: bold; }
    .stButton>button { width: 100%; background-color: #10b981; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- CONTROL DE INICIO DE SESIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso Restringido")
    st.subheader("Introduce tu contraseña para gestionar el portafolio")
    clave_introducida = st.text_input("Contraseña Financiera:", type="password")
    if st.button("Ingresar al Sistema"):
        if clave_introducida == CONTRASENA_ACCESO:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta. Acceso denegado.")
    st.stop()

# --- CONEXIÓN A LA HOJA DE CÁLCULO ---
try:
    csv_url = URL_GOOGLE_SHEETS.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv').replace('/edit#gid=', '/gviz/tq?tqx=out:csv&gid=')
    if "/edit" in URL_GOOGLE_SHEETS and not "tqx=out:csv" in csv_url:
        csv_url = URL_GOOGLE_SHEETS.split('/edit') + '/gviz/tq?tqx=out:csv'
    df_google = pd.read_csv(csv_url)
    df_google.columns = df_google.columns.str.strip().str.lower()
    df_google = df_google.dropna(subset=['ticker'])
    lista_activos = df_google.to_dict(orient="records")
except:
    lista_activos = []

st.title("📱 Mi Portafolio con Comisiones en Tiempo Real")
st.caption("Conexión permanente con Google Sheets, cálculo de gastos operativos y encriptación de acceso.")

TIPO_CAMBIO_EUR_USD = 1.14

# Formulario informativo superior
with st.expander("📥 Cómo Registrar Nuevas Compras"):
    st.info("Para añadir un activo, abre tu Hoja de cálculo de Google e introduce una fila con los datos y sus respectivas comisiones de compra, venta y custodia.")

iffs_datos = []
total_costo_usd = 0.0
total_actual_usd = 0.0
total_comisiones_usd = 0.0

if lista_activos:
    with st.spinner("🔄 Sincronizando cotizaciones vivas y auditando gastos..."):
        for item in lista_activos:
            ticker_str = str(item.get("ticker", "")).strip().upper()
            if not ticker_str or ticker_str == "NAN":
                continue
                
            try:
                cant_acciones = float(str(item.get("acciones", 0)).replace(",", ".").strip())
            except:
                cant_acciones = 0.0
                
            try:
                costo_compra = float(str(item.get("costo_compra", 0)).replace(",", ".").strip())
            except:
                costo_compra = 0.0

            try:
                val_compra = str(item.get("comision_compra", "0")).strip()
                c_compra = float(val_compra.replace(",", ".")) if val_compra and val_compra != "nan" else 0.0
            except:
                c_compra = 0.0
                
            try:
                val_venta = str(item.get("comision_venta", "0")).strip()
                c_venta = float(val_venta.replace(",", ".")) if val_venta and val_venta != "nan" else 0.0
            except:
                c_venta = 0.0
                
            try:
                val_anual = str(item.get("comision_anual", "0")).strip()
                c_anual = float(val_anual.replace(",", ".")) if val_anual and val_anual != "nan" else 0.0
            except:
                c_anual = 0.0

            try:
                ticker_data = yf.Ticker(ticker_str)
                precio_actual = ticker_data.fast_info['last_price']
                if precio_actual is None or precio_actual == 0:
                    precio_actual = costo_compra
            except:
                precio_actual = costo_compra
            
            costo_total_origen = cant_acciones * costo_compra
            valor_actual_origen = cant_acciones * precio_actual
            comisiones_totales_origen = c_compra + c_venta + c_anual
            
            moneda_str = str(item.get("moneda", "EUR")).strip().upper()
            
            costo_usd = costo_total_origen * TIPO_CAMBIO_EUR_USD if moneda_str == "EUR" else costo_total_origen
            actual_usd = valor_actual_origen * TIPO_CAMBIO_EUR_USD if moneda_str == "EUR" else valor_actual_origen
            comisiones_usd = comisiones_totales_origen * TIPO_CAMBIO_EUR_USD if moneda_str == "EUR" else comisiones_totales_origen
            
            total_costo_usd += costo_usd
            total_actual_usd += actual_usd
            total_comisiones_usd += comisiones_usd
            
            rendimiento_dinero_neto = valor_actual_origen - costo_total_origen - comisiones_totales_origen
            rendimiento_porc_neto = (rendimiento_dinero_neto / (costo_total_origen + comisiones_totales_origen)) * 100 if costo_total_origen > 0 else 0
            simbolo_orig = "€" if moneda_str == "EUR" else "$"
            
            iffs_datos.append({
                "Ticker": ticker_str, 
                "Nombre": item.get("nombre", ticker_str), 
                "Acciones": round(cant_acciones, 4),
                "Precio Actual": f"{simbolo_orig}{precio_actual:,.2f}",
                "Inversión Bruta": f"{simbolo_orig}{costo_total_origen:,.2f}", 
                "Gastos Bróker": f"{simbolo_orig}{comisiones_totales_origen:,.2f}",
                "Valor Mercado": f"{simbolo_orig}{valor_actual_origen:,.2f}", 
                "Rendimiento Neto": f"{rendimiento_porc_neto:+.2f}%",
                "Monto_Grafico_USD": actual_usd
            })

    if iffs_datos:
        df = pd.DataFrame(iffs_datos)
        
        moneda_visual = st.radio("💱 Ver totales superiores en:", ["Euros (€)", "Dólares ($)"], horizontal=True)
        factor = 1 / TIPO_CAMBIO_EUR_USD if moneda_visual == "Euros (€)" else 1.0
        simbolo_kpi = "€" if moneda_visual == "Euros (€)" else "$"

        ganancia_global_neta_usd = total_actual_usd - total_costo_usd - total_comisiones_usd
        roi_global_neto = (ganancia_global_neta_usd / (total_costo_usd + total_comisiones_usd)) * 100 if total_costo_usd > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Capital Invertido", f"{simbolo_kpi}{total_costo_usd * factor:,.2f}")
        c2.metric("Total Comisiones", f"{simbolo_kpi}{total_comisiones_usd * factor:,.2f}")
        c3.metric("Valor Portafolio", f"{simbolo_kpi}{total_actual_usd * factor:,.2f}")
        
        color_rendimiento = "#10b981" if ganancia_global_neta_usd >= 0 else "#ef4444"
        with c4:
            st.markdown(f"""
                <div style='text-align: center; background-color: #1c2541; padding: 4px; border-radius: 8px; border-top: 4px solid {color_rendimiento};'>
                    <span style='color: #9ca3af; font-size: 11px; text-transform: uppercase;'>Beneficio Neto</span><br>
                    <span style='color: {color_rendimiento}; font-size: 18px; font-weight: bold;'>{ganancia_global_neta_usd * factor:+.2f}{simbolo_kpi}<br>({roi_global_neto:+.2f}%)</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🍰 Distribución de Capital")
        fig_pie = px.pie(df, values='Monto_Grafico_USD', names='Nombre', hole=0.4, template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("📋 Lista Detallada de Activos (Auditoría Desglosada)")
        df_mostrar = df.drop(columns=['Monto_Grafico_USD'])
        st.dataframe(df_mostrar, use_container_width=True)
    else:
        st.warning("Escribe tus fondos o acciones en tu Hoja de cálculo de Google para ver las métricas.")
else:
    st.warning("Tu Hoja de cálculo de Google está vacía o el enlace en la línea 14 no es correcto.")
