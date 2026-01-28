import streamlit as st
import fitz
import re
import pandas as pd

st.set_page_config(page_title="Extractor Pro", page_icon="📊", layout="wide")
st.title("📊 Extractor de Facturas de Control Interno")

uploaded_files = st.file_uploader("Carga tus facturas (PDF)", type="pdf", accept_multiple_files=True)

def extraer_datos(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    texto = ""
    lineas = []
    for pagina in doc:
        t = pagina.get_text()
        texto += t
        lineas.extend([line.strip() for line in t.split('\n') if line.strip()])
    
    texto_unido = " ".join(lineas)

    # 1. NÚMERO DE FACTURA (Busca prefijos comunes como CONS, NAM, LERB, FES)
    n_fact = re.search(r'(No\.|Nº|Factura No|Venta No)\s*([A-Z]*\s?\d+)', texto_unido, re.IGNORECASE)
    
    # 2. EMISOR (Suele estar al inicio o cerca del NIT del emisor)
    # En Siigo el emisor suele estar después de los logos o al final de la primera sección
    emisor = "No detectado"
    if "SAS" in texto_unido:
        match_emisor = re.search(r'([A-Z0-9\s]{5,50}SAS)', texto_unido)
        if match_emisor: emisor = match_emisor.group(1)
    elif "STARLINK" in texto_unido:
        emisor = "STARLINK"

    # 3. NIT EMISOR
    # Buscamos el primer NIT que aparezca (suele ser el del emisor)
    nit = re.search(r'NIT:?\s?(\d[\d\.\-]+\d)', texto_unido, re.IGNORECASE)

    # 4. CONCEPTO (Descripción)
    concepto = "Ver en PDF"
    match_desc = re.search(r'(Descripción|Concepto)\s+(.*?)\s+(1\.00|Cantidad|Cant)', texto_unido, re.IGNORECASE)
    if match_desc:
        concepto = match_desc.group(2)
    elif "Suscripción" in texto_unido: # Caso Starlink
        concepto = "Suscripción de servicios"

    # 5. FECHA EMISIÓN
    fecha = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', texto_unido)

    # 6. TOTAL A PAGAR
    # Buscamos el valor más alto o el que sigue a "Total a Pagar"
    total = re.search(r'(Total a Pagar|Total a pagar|Total)\s?\$?\s?([\d\.,]{5,20})', texto_unido, re.IGNORECASE)

    # 7. CLIENTE
    cliente = "No detectado"
    match_cliente = re.search(r'(Señores|Razón Social)\s*:?\s*([A-Z\s]{5,60})', texto_unido, re.IGNORECASE)
    if match_cliente:
        cliente = match_cliente.group(2).replace("NIT", "").strip()

    return {
        "Factura #": n_fact.group(2) if n_fact else "N/A",
        "Emisor": emisor,
        "NIT Emisor": nit.group(1) if nit else "N/A",
        "Concepto": concepto[:80] + "..." if len(concepto) > 80 else concepto,
        "Fecha": fecha.group(1) if fecha else "N/A",
        "Total": total.group(2) if total else "N/A",
        "Cliente": cliente
    }

if uploaded_files:
    resultados = [extraer_datos(f) for f in uploaded_files]
    df = pd.DataFrame(resultados)
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Descargar para Excel", data=csv, file_name="reporte.csv", mime="text/csv")
