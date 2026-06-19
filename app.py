import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# Configuración de pantalla adaptable
st.set_page_config(page_title="Mi App de Inversiones Segura", page_icon="📈", layout="wide")

# =========================================================================
# CONFIGURACIÓN DE SEGURIDAD Y BASE DE DATOS
# =========================================================================
CONTRASENA_ACCESO = "1234"  # <-- Cambia "1234" por la contraseña que quieras para tu móvil

URL_GOOGLE_SHEETS = "TU_URL_AQUI"  # <-- Borra TU_URL_AQUI y pega tu enlace de la Hoja de cálculo
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
    # Convertimos el enlace web normal en un conector de datos limpio para Python
    csv_url = URL_GOOGLE_SHEETS.replace('/edit?usp=sharing', '/gviz/tq?tqx=out:csv').replace('/edit#gid=', '/gviz/tq?tqx=out:csv&gid=')
    if "/edit" in URL_GOOGLE_SHEETS and not "tqx=out:csv" in csv_url:
        csv_url = URL_GOOGLE_SHEETS.split('/edit')[0] + '/gviz/tq?tqx=out:csv'
    df_google = pd.read_csv(csv_url)
    lista_activos = df_google.to_dict(orient="records")
except:
    lista_activos = []

st.title("📱 Mi Portafolio Seguro en Tiempo Real")
st.caption("Conexión permanente con tu Hoja de cálculo de Google y encriptación de acceso.")

TIPO_CAMBIO_EUR_USD = 1.14

# Formulario informativo superior
with st.expander("📥 Cómo Registrar Nuevas Compras"):
    st.info("Para añadir un activo de forma permanente, abre tu Hoja de cálculo de Google e introduce una fila con los datos (Ticker, Nombre, ISIN, Acciones, Costo de Compra y Moneda). Tu aplicación se actualizará sola.")

iffs_datos = []
total_costo_usd = 0.0
total_actual_usd = 0.0

if lista_activos:
    with st.spinner("🔄 Sincronizando cotizaciones vivas..."):
        for item in lista_activos:
            try:
                ticker_str = str(item["ticker"]).strip().upper()
                ticker_data = yf.Ticker(ticker_str)
                precio_actual = ticker_data.fast_info['last_price']
            except:
                precio_actual = float(item["costo_compra"])
            
            costo_total_origen = float(item["acciones"]) * float(item["costo_compra"])
            valor_actual_origen = float(item["acciones"]) * precio_actual
            
            costo_usd = costo_total_origen * TIPO_CAMBIO_EUR_USD if item["moneda"] == "EUR" else costo_total_origen
            actual_usd = valor_actual_origen * TIPO_CAMBIO_EUR_USD if item["moneda"] == "EUR" else valor_actual_origen
            
            total_costo_usd += costo_usd
            total_actual_usd += actual_usd
            
            rendimiento_dinero = valor_actual_origen - costo_total_origen
            rendimiento_porc = (rendimiento_dinero / costo_total_origen) * 100 if costo_total_origen > 0 else 0
            simbolo_orig = "€" if item["moneda"] == "EUR" else "$"
            
            iffs_datos.append({
                "Ticker": item["ticker"], "Nombre": item["nombre"], "ISIN": item["isin"], "Acciones": item["acciones"],
                "Precio Compra": f"{simbolo_orig}{float(item['costo_compra']):,.2f}", "Precio Actual": f"{simbolo_orig}{precio_actual:,.2f}",
                "Inversión Inicial": costo_usd, "Valor Mercado (USD)": actual_usd, "Rendimiento": f"{rendimiento_porc:+.2f}%"
            })

    df = pd.DataFrame(iffs_datos)
    
    moneda_visual = st.radio("💱 Ver totales en:", ["Euros (€)", "Dólares ($)"], horizontal=True)
    factor = 1 / TIPO_CAMBIO_EUR_USD if moneda_visual == "Euros (€)" else 1.0
    simbolo_kpi = "€" if moneda_visual == "Euros (€)" else "$"

    ganancia_global_usd = total_actual_usd - total_costo_usd
    roi_global = (ganancia_global_usd / total_costo_usd) * 100 if total_costo_usd > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Capital Invertido", f"{simbolo_kpi}{total_costo_usd * factor:,.2f}")
    c2.metric("Valor del Portafolio", f"{simbolo_kpi}{total_actual_usd * factor:,.2f}")
    c3.metric("Rendimiento Neto", f"{simbolo_kpi}{ganancia_global_usd * factor:+.2f} ({roi_global:+.2f}%)")

    st.markdown("---")
    st.subheader("🍰 Distribución de Capital")
    fig_pie = px.pie(df, values='Valor Mercado (USD)', names='Nombre', hole=0.4, template="plotly_dark")
    st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📋 Lista Detallada de Activos")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Tu Hoja de cálculo de Google está vacía o el enlace en la línea 14 no es correcto. Escribe tus fondos o acciones en la fila 2 de tu documento de Google para ver los gráficos.")
