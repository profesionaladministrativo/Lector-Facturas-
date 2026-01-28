import streamlit as st
import fitz
import re
import pandas as pd

st.set_page_config(page_title="Extractor Administrativo", page_icon="📊", layout="wide")

st.title("📊 Extractor de Facturas para Gestión")
st.markdown("Extrae datos críticos directamente a una tabla organizada.")

uploaded_files = st.file_uploader("Carga tus facturas (PDF)", type="pdf", accept_multiple_files=True)

def limpiar_texto(t):
    return " ".join(t.split())

if uploaded_files:
    datos_finales = []
    
    for file in uploaded_files:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        # Extraemos el texto de la primera página (donde suele estar el encabezado)
        texto_completo = ""
        lineas = []
        for pagina in doc:
            t_pag = pagina.get_text()
            texto_completo += t_pag
            lineas.extend(t_pag.split('\n'))
        
        texto_limpio = limpiar_texto(texto_completo)

        # 1. Número de Factura
        n_fact = re.search(r'(Factura de venta No|Factura No|Factura #|No\.|Venta No)\s?(\w?\d+)', texto_limpio, re.IGNORECASE)
        
        # 2. Emisor (Suele ser la primera línea o el nombre más grande)
        emisor = lineas[0] if len(lineas) > 0 else "No detectado"

        # 3. NIT (Emisor)
        nit = re.search(r'NIT:?\s?(\d[\d\.\-]+\d)', texto_limpio, re.IGNORECASE)

        # 4. Concepto / Descripción
        # Buscamos texto entre palabras comunes de tablas de facturación
        concepto = "Ver descripción en PDF"
        match_desc = re.search(r'(Descripción|Concepto|Articulo)\s+(.*?)\s+(Cantidad|Cant|Valor|Precio)', texto_limpio, re.IGNORECASE)
        if match_desc:
            concepto = match_desc.group(2)

        # 5. Fecha de Emisión
        fecha = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', texto_limpio)

        # 6. Razón Social Cliente (A quien le facturan)
        # Buscamos después de etiquetas como "Señores", "Cliente" o "Vendido a"
        cliente = "No detectado"
        match_cliente = re.search(r'(Señor\(es\):?|Cliente:?|Vendido a:?|Nombre:?)\s+([A-Z\s]{5,50})', texto_limpio, re.IGNORECASE)
        if match_cliente:
            cliente = match_cliente.group(2).strip()

        datos_finales.append({
            "Número de Factura": n_fact.group(2) if n_fact else "N/A",
            "Emisor": emisor,
            "NIT": nit.group(1) if nit else "N/A",
            "Concepto": concepto[:100] + "..." if len(concepto) > 100 else concepto,
            "Fecha Emisión": fecha.group(1) if fecha else "N/A",
            "Cliente": cliente
        })

    # Mostrar resultados
    df = pd.DataFrame(datos_finales)
    st.subheader("Información Procesada")
    st.dataframe(df, use_container_width=True)

    # Exportar a Excel (CSV para máxima compatibilidad)
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Descargar Reporte para Excel",
        data=csv,
        file_name="reporte_contable.csv",
        mime="text/csv",
    )
