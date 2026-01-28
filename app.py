import streamlit as st
import fitz
import re
import pandas as pd

st.set_page_config(page_title="Lector Facturas Control Interno", page_icon="📝", layout="wide")
st.title("📝 Extractor de Facturas (Siigo, Starlink y otros)")

uploaded_files = st.file_uploader("Carga tus facturas PDF", type="pdf", accept_multiple_files=True)

def extraer_datos_robusto(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    texto_paginas = [pag.get_text() for pag in doc]
    texto_completo = " ".join(texto_paginas).replace('\n', ' ')
    primera_pagina = texto_paginas[0] if texto_paginas else ""

    # 1. NÚMERO DE FACTURA (Mejorado para CONS, NAM, LERB y FES de Starlink)
    n_fact = re.search(r'(No\.|Nº|Factura No|Venta No)\s*([A-Z]*\s?-?\d+)', texto_completo, re.IGNORECASE)
    
    # 2. EMISOR
    emisor = "No detectado"
    if "STARLINK" in texto_completo.upper():
        emisor = "STARLINK / SPACEX"
    else:
        # Busca nombres que terminen en SAS o nombres al principio
        match_emisor = re.search(r'([A-Z0-9\s]{3,50}(SAS|S\.A\.S|S\.A))', texto_completo)
        if match_emisor: emisor = match_emisor.group(1).strip()

    # 3. NIT EMISOR (El primer NIT que aparece suele ser el del emisor)
    nit = re.search(r'NIT:?\s?(\d[\d\.\-]+\d)', texto_completo, re.IGNORECASE)

    # 4. CONCEPTO (Descripción)
    concepto = "Ver detalle en PDF"
    if "STARLINK" in texto_completo.upper():
        match_star = re.search(r'(Suscripción.*?)(\d)', texto_completo, re.IGNORECASE)
        if match_star: concepto = match_star.group(1).strip()
    else:
        match_desc = re.search(r'(Descripción|Concepto)\s+(.*?)\s+(1\.00|Cantidad|Cant)', texto_completo, re.IGNORECASE)
        if match_desc: concepto = match_desc.group(2).strip()

    # 5. FECHA DE GENERACIÓN
    fecha = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', texto_completo)

    # 6. TOTAL A PAGAR (Busca el valor monetario después de 'Total a Pagar')
    total = "No detectado"
    match_total = re.search(r'(Total a Pagar|Total a pagar|Total)\s*:?\s?\$?\s?([\d\.,]{5,20})', texto_completo, re.IGNORECASE)
    if match_total:
        total = match_total.group(2).strip()

    # 7. NOMBRE CLIENTE (A quien le facturan)
    cliente = "No detectado"
    match_cliente = re.search(r'(Señores|Razón Social)\s*:?\s*([A-Z\s]{5,60})', texto_completo, re.IGNORECASE)
    if match_cliente:
        cliente = match_cliente.group(2).replace("NIT", "").replace(":", "").strip()

    return {
        "Número de Factura": n_fact.group(2) if n_fact else "N/A",
        "Emisor": emisor,
        "NIT": nit.group(1) if nit else "N/A",
        "Concepto": concepto[:100],
        "Fecha de Generación": fecha.group(1) if fecha else "N/A",
        "Total a Pagar": total,
        "Nombre Cliente": cliente
    }

if uploaded_files:
    resultados = [extraer_datos_robusto(f) for f in uploaded_files]
    df = pd.DataFrame(resultados)
    
    st.subheader("Resultados de la Extracción")
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Descargar Reporte Excel (CSV)", data=csv, file_name="control_interno_facturas.csv", mime="text/csv")
