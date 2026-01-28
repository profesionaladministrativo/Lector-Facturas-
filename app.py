import streamlit as st
import fitz
import re
import pandas as pd

st.set_page_config(page_title="Extractor Control Interno", page_icon="📝", layout="wide")
st.title("📝 Extractor de Facturas Multi-Formato")

uploaded_files = st.file_uploader("Carga tus facturas PDF", type="pdf", accept_multiple_files=True)

def extraer_datos_final(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    texto_completo = ""
    for pagina in doc:
        texto_completo += pagina.get_text()
    
    # Limpieza básica para facilitar la búsqueda
    texto_limpio = " ".join(texto_completo.split())

    # 1. NÚMERO DE FACTURA
    # Busca CONS, NAM, LERB o el FES de Starlink
    n_fact = re.search(r'(No\.|Nº|Factura No|Venta No)\s*([A-Z]*\s?-?\d+)', texto_limpio, re.IGNORECASE)
    
    # 2. EMISOR
    emisor = "No detectado"
    if "STARLINK" in texto_limpio.upper():
        emisor = "STARLINK / SPACEX"
    elif "CONSTRUCSION SAS" in texto_limpio.upper():
        emisor = "CONSTRUCSION SAS"
    elif "NAM CONSTRUCCIONES" in texto_limpio.upper():
        emisor = "NAM CONSTRUCCIONES SAS"
    else:
        match_emisor = re.search(r'([A-Z0-9\s]{3,50}(SAS|S\.A\.S|S\.A))', texto_limpio)
        if match_emisor: emisor = match_emisor.group(1).strip()

    # 3. NIT EMISOR
    nit = re.search(r'NIT:?\s?(\d[\d\.\-]+\d)', texto_limpio, re.IGNORECASE)

    # 4. CONCEPTO
    concepto = "Ver detalle en PDF"
    if "STARLINK" in texto_limpio.upper():
        # Busca específicamente la suscripción en Starlink
        match_star = re.search(r'DESCRIPCIÓN\s*(.*?)\s*125\.000', texto_limpio, re.IGNORECASE)
        if match_star: concepto = match_star.group(1).strip()
    else:
        match_desc = re.search(r'(Descripción|Concepto)\s+(.*?)\s+(1\.00|Cantidad|Cant)', texto_limpio, re.IGNORECASE)
        if match_desc: concepto = match_desc.group(2).strip()

    # 5. FECHA DE GENERACIÓN
    # En Starlink se llama "Fecha Validación"
    fecha = re.search(r'(Fecha Validación:|Fecha:?|Generación)\s*([\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', texto_limpio, re.IGNORECASE)
    if not fecha: # Búsqueda genérica de fecha si la anterior falla
        fecha = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', texto_limpio)

    # 6. TOTAL A PAGAR
    # En tus facturas el total aparece con puntos y comas
    total = "N/A"
    # Buscar patrón de moneda al final de "Total a Pagar" o similar
    match_total = re.search(r'(Total a Pagar|Total a pagar|Total)\s*:?\s?\$?\s*([\d\.,]{5,20})', texto_limpio, re.IGNORECASE)
    if match_total:
        total = match_total.group(2).strip()

    # 7. NOMBRE CLIENTE
    cliente = "No detectado"
    # Específico para tus consorcios
    match_cliente = re.search(r'(Señores|Razón Social)\s*:?\s*([A-Z\s]{5,70})', texto_limpio, re.IGNORECASE)
    if match_cliente:
        cliente = match_cliente.group(2).replace("NIT", "").replace(":", "").strip()

    return {
        "Número de Factura": n_fact.group(2) if n_fact else "N/A",
        "Emisor": emisor,
        "NIT Emisor": nit.group(1) if nit else "N/A",
        "Concepto": concepto[:100],
        "Fecha Emisión": fecha.group(2) if fecha and len(fecha.groups()) > 1 else (fecha.group(1) if fecha else "N/A"),
        "Total a Pagar": total,
        "Nombre Cliente": cliente
    }

if uploaded_files:
    resultados = [extraer_datos_final(f) for f in uploaded_files]
    df = pd.DataFrame(resultados)
    st.subheader("Datos Extraídos con Éxito")
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Descargar Excel", data=csv, file_name="reporte_control_interno.csv", mime="text/csv")
