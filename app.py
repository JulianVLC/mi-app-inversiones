import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# Configuración de pantalla adaptable
st.set_page_config(page_title="Mi App de Inversiones Segura", page_icon="📈", layout="wide")

# =========================================================================
# CONFIGURACIÓN DE SEGURIDAD Y BASE DE DATOS
# =========================================================================
CONTRASENA_ACCESO = "2707"  # Tu contraseña fija configurada

URL_GOOGLE_SHEETS = "https://google.com"
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

st.title("📱 Mi Portafolio Seguro en Tiempo Real")
st.caption("Conexión permanente con tu Hoja de cálculo de Google y encriptación de acceso.")

TIPO_CAMBIO_EUR_USD = 1.14

# Formulario informativo superior
with st.expander("📥 Cómo Registrar Nuevas Compras"):
    st.info("Para añadir un activo de forma permanente, abre tu Hoja de cálculo de Google e introduce una fila con los datos. Tu aplicación se actualizará sola.")

iffs_datos = []
total_costo_usd = 0.0
total_actual_usd = 0.0

if lista_activos:
    with st.spinner("🔄 Sincronizando cotizaciones vivas..."):
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
                ticker_data = yf.Ticker(ticker_str)
                precio_actual = ticker_data.fast_info['last_price']
                if precio_actual is None or precio_actual == 0:
                    precio_actual = costo_compra
            except:
                precio_actual = costo_compra
            
            # Cálculos directos basados en la moneda de origen de la acción
            costo_total_origen = cant_acciones * costo_compra
            valor_actual_origen = cant_acciones * precio_actual
            
            moneda_str = str(item.get("moneda", "EUR")).strip().upper()
            
            # Acumuladores globales unificados para los KPIs superiores
            costo_usd = costo_total_origen * TIPO_CAMBIO_EUR_USD if moneda_str == "EUR" else costo_total_origen
            actual_usd = valor_actual_origen * TIPO_CAMBIO_EUR_USD if moneda_str == "EUR" else valor_actual_origen
            
            total_costo_usd += costo_usd
            total_actual_usd += actual_usd
            
            rendimiento_dinero = valor_actual_origen - costo_total_origen
            rendimiento_porc = (rendimiento_dinero / costo_total_origen) * 100 if costo_total_origen > 0 else 0
            simbolo_orig = "€" if moneda_str == "EUR" else "$"
            
            iffs_datos.append({
                "Ticker": ticker_str, 
                "Nombre": item.get("nombre", ticker_str), 
                "ISIN": item.get("isin", "N/A"), 
                "Acciones": round(cant_acciones, 4),
                "Precio Compra": f"{simbolo_orig}{costo_compra:,.4f}", 
                "Precio Actual": f"{simbolo_orig}{precio_actual:,.4f}",
                "Inversión Inicial": f"{simbolo_orig}{costo_total_origen:,.2f}", 
                "Valor de Mercado": f"{simbolo_orig}{valor_actual_origen:,.2f}", 
                "Rendimiento": f"{rendimiento_porc:+.2f}%",
                "Monto_Grafico_USD": actual_usd # Mantenemos oculto el valor unificado para el gráfico circular
            })

    if iffs_datos:
        df = pd.DataFrame(iffs_datos)
        
        moneda_visual = st.radio("💱 Ver totales superiores en:", ["Euros (€)", "Dólares ($)"], horizontal=True)
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
        fig_pie = px.pie(df, values='Monto_Grafico_USD', names='Nombre', hole=0.4, template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("📋 Lista Detallada de Activos")
        # Quitamos la columna de gráfico para no confundir la vista tabular limpia
        df_mostrar = df.drop(columns=['Monto_Grafico_USD'])
        st.dataframe(df_mostrar, use_container_width=True)
    else:
        st.warning("Escribe tus fondos o acciones en tu Hoja de cálculo de Google para ver las métricas.")
else:
    st.warning("Tu Hoja de cálculo de Google está vacía o el enlace en la línea 14 no es correcto.")
