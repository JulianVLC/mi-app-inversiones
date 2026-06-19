import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# 1. Configuración de pantalla adaptable
st.set_page_config(
    page_title="Mi App de Inversiones Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados para alertas y diseño oscuro
st.markdown("""
    <style>
    .main { background-color: #0b0f19; }
    div[data-testid="stMetricValue"] { font-size: 26px !important; font-weight: bold; }
    .stButton>button { width: 100%; background-color: #10b981; color: white; border-radius: 6px; font-weight: bold; }
    .alerta-diversificacion { background-color: #7c2d12; color: #fdba74; padding: 15px; border-radius: 6px; margin-bottom: 20px; border-left: 5px solid #f97316; }
    </style>
""", unsafe_allow_html=True)

st.title("📱 Mi Portafolio Inteligente (EUR / USD)")
st.caption("Software financiero con actualización automática de precios de mercado, cálculo de pesos y alertas de riesgo.")

# 2. Base de Datos en Memoria (Inicializada con activos de ejemplo)
if 'portafolio' not in st.session_state:
    st.session_state.portafolio = [
        {"ticker": "AAPL", "nombre": "Apple Inc.", "isin": "US0378331005", "acciones": 15.0, "costo_compra": 170.0, "moneda": "USD"},
        {"ticker": "VOO", "nombre": "Vanguard S&P 500 ETF", "isin": "US9229083632", "acciones": 8.0, "costo_compra": 415.0, "moneda": "USD"},
        {"ticker": "SAN.MC", "nombre": "Banco Santander", "isin": "ES0113900J37", "acciones": 500.0, "costo_compra": 3.90, "moneda": "EUR"}
    ]

# Paridad del tipo de cambio fija para unificación (1 EUR = 1.14 USD)
TIPO_CAMBIO_EUR_USD = 1.14

# 3. Formulario Avanzado de Entrada de Datos
with st.expander("📥 Registrar Nueva Compra (Acciones, Fondos o ETFs)"):
    col1, col2 = st.columns(2)
    with col1:
        nuevo_ticker = st.text_input("Ticker oficial de Yahoo Finance (Ej: TSLA, MSFT, TEF.MC)", "").upper().strip()
        nuevo_isin = st.text_input("Código ISIN del activo (Ej: US88160R1014)", "").upper().strip()
        moneda_origen = st.selectbox("Moneda de cotización original del activo", ["USD", "EUR"])
    with col2:
        nuevas_acciones = st.number_input("Cantidad de Acciones / Títulos comprados", min_value=0.0001, step=1.0, value=1.0, format="%.4f")
        nuevo_costo = st.number_input("Precio pagado por cada Acción (Tu Costo)", min_value=0.01, step=1.0, value=100.0)
    
    if st.button("💾 Guardar y Sincronizar Activo"):
        if nuevo_ticker:
            with st.spinner("Conectando con los servidores bursátiles..."):
                try:
                    asset = yf.Ticker(nuevo_ticker)
                    nombre_real = asset.info.get('longName', nuevo_ticker)
                    
                    st.session_state.portafolio.append({
                        "ticker": nuevo_ticker,
                        "nombre": nombre_real,
                        "isin": nuevo_isin if nuevo_isin else "N/A",
                        "acciones": nuevas_acciones,
                        "costo_compra": nuevo_costo,
                        "moneda": moneda_origen
                    })
                    st.success(f"¡{nombre_real} guardado con éxito!")
                    st.rerun()
                except:
                    st.error("Error: No se encuentra ese Ticker. Revisa si lleva extensión (ej: '.MC' para España).")
        else:
            st.warning("Escribe un Ticker antes de guardar.")

# 4. Procesamiento de Mercado en Tiempo Real
iffs_datos = []
total_costo_usd = 0.0
total_actual_usd = 0.0

if st.session_state.portafolio:
    with st.spinner("🔄 Actualizando cotizaciones en vivo desde la bolsa..."):
        for item in st.session_state.portafolio:
            try:
                ticker_data = yf.Ticker(item["ticker"])
                precio_actual = ticker_data.fast_info['last_price']
            except:
                precio_actual = item["costo_compra"] # Si falla internet, usa el costo
            
            costo_total_origen = item["acciones"] * item["costo_compra"]
            valor_actual_origen = item["acciones"] * precio_actual
            
            # Unificar todo a Dólares (USD) internamente para poder sumar peras con manzanas
            costo_usd = costo_total_origen * TIPO_CAMBIO_EUR_USD if item["moneda"] == "EUR" else costo_total_origen
            actual_usd = valor_actual_origen * TIPO_CAMBIO_EUR_USD if item["moneda"] == "EUR" else valor_actual_origen
            
            total_costo_usd += costo_usd
            total_actual_usd += actual_usd
            
            rendimiento_dinero = valor_actual_origen - costo_total_origen
            rendimiento_porc = (rendimiento_dinero / costo_total_origen) * 100 if costo_total_origen > 0 else 0
            
            # Detector de Volatilidad Crítica (Alerta -5%)
            alerta_volatilidad = "⚠️ Caída >5%" if rendimiento_porc <= -5.0 else "✅ Estable / Alza"
            
            simbolo_orig = "€" if item["moneda"] == "EUR" else "$"
            
            iffs_datos.append({
                "Ticker": item["ticker"],
                "Nombre": item["nombre"],
                "ISIN": item["isin"],
                "Acciones": item["acciones"],
                "Precio Compra": f"{simbolo_orig}{item['costo_compra']:,.2f}",
                "Precio Actual": f"{simbolo_orig}{precio_actual:,.2f}",
                "Inversión Inicial": costo_usd,
                "Valor Mercado (USD)": actual_usd,
                "Rendimiento": f"{rendimiento_porc:+.2f}%",
                "Estado Alerta": alerta_volatilidad
            })

    df = pd.DataFrame(iffs_datos)
    
    # Calcular pesos de diversificación basados en el capital total
    df["Peso (%)"] = (df["Valor Mercado (USD)"] / total_actual_usd) * 100

    # 5. Ejecución del Módulo de Alertas de Diversificación
    activos_concentrados = df[df["Peso (%)"] > 30.0]
    for _, row in activos_concentrados.iterrows():
        st.markdown(f"""
            <div class="alerta-diversificacion">
                <strong>🚨 ALERTA DE RIESGO:</strong> Tu posición en <b>{row['Nombre']}</b> representa el <b>{row['Peso (%)']:.2f}%</b> de tu portafolio. 
                Supera el límite del 30%. Considera diversificar para proteger tu capital.
            </div>
        """, unsafe_allow_html=True)

    # 6. Moneda Visual de Preferencia del Usuario
    moneda_visual = st.radio("💱 Ver totales del cuadro de mandos en:", ["Euros (€)", "Dólares ($)"], horizontal=True)
    factor = 1 / TIPO_CAMBIO_EUR_USD if moneda_visual == "Euros (€)" else 1.0
    simbolo_kpi = "€" if moneda_visual == "Euros (€)" else "$"

    # Renderizar KPIs de dinero total
    ganancia_global_usd = total_actual_usd - total_costo_usd
    roi_global = (ganancia_total_usd / total_costo_usd) * 100 if total_costo_usd > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Capital Total Invertido", f"{simbolo_kpi}{total_costo_usd * factor:,.2f}")
    c2.metric("Valor del Portafolio en Vivo", f"{simbolo_kpi}{total_actual_usd * factor:,.2f}")
    
    color_rendimiento = "#10b981" if ganancia_global_usd >= 0 else "#ef4444"
    st.markdown(f"""
        <div style='text-align: center; background-color: #1c2541; padding: 10px; border-radius: 8px; border-top: 4px solid {color_rendimiento};'>
            <span style='color: #9ca3af; font-size: 12px; text-transform: uppercase;'>Rendimiento Neto Total</span><br>
            <span style='color: {color_rendimiento}; font-size: 24px; font-weight: bold;'>{ganancia_global_usd * factor:+\,.2f}{simbolo_kpi} ({roi_global:+.2f}%)</span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 7. Gráficos Visuales
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("🍰 Distribución de pesos y Diversificación")
        fig_pie = px.pie(df, values='Peso (%)', names='Nombre', hole=0.4, template="plotly_dark", title="Porcentaje del total patrimonial")
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_g2:
        st.subheader("📉 Estado de Alertas por Volatilidad")
        fig_bar = px.bar(df, x="Ticker", y="Valor Mercado (USD)", color="Estado Alerta", color_discrete_map={"✅ Estable / Alza": "#10b981", "⚠️ Caída >5%": "#ef4444"}, template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)

    # 8. Tabla de inventario
    st.subheader("📋 Lista Detallada de Activos")
    df_visual = df.copy()
    df_visual["Peso (%)"] = df_visual["Peso (%)"].map(lambda x: f"{x:.2f}%")
    df_visual["Inversión Inicial"] = df_visual["Inversión Inicial"].map(lambda x: f"{simbolo_kpi}{x * factor:,.2f}")
    df_visual["Valor Mercado (USD)"] = df_visual["Valor Mercado (USD)"].map(lambda x: f"{simbolo_kpi}{x * factor:,.2f}")
    df_visual.rename(columns={"Valor Mercado (USD)": f"Valor de Mercado ({simbolo_kpi})"}, inplace=True)
    st.dataframe(df_visual, use_container_width=True)

else:
    st.info("El portafolio no tiene activos registrados. Utiliza el desplegable de arriba para añadir tus primeras acciones o fondos.")
