import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO
import tempfile

def parse_xml_file(xml_content):
    # Parse XML
    root = ET.fromstring(xml_content)
    
    # Define namespace
    ns = {'cbi': 'urn:CBI:xsd:CBIPaymentRequest.00.04.01'}
    
    # Extract transactions
    transactions = []
    for transaction in root.findall('.//cbi:CdtTrfTxInf', ns):
        destinatario = transaction.find('.//cbi:Cdtr/cbi:Nm', ns).text
        iban = transaction.find('.//cbi:CdtrAcct/cbi:Id/cbi:IBAN', ns).text
        importo = transaction.find('.//cbi:InstdAmt', ns).text
        causale = transaction.find('.//cbi:RmtInf/cbi:Ustrd', ns).text
        
        transactions.append({
            'Destinatario': destinatario,
            'IBAN': iban,
            'Importo': float(importo),
            'Causale': causale
        })
    
    return pd.DataFrame(transactions)

def export_to_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Convert DataFrame to list of lists for the table
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

def main():
    st.title("Parser Bonifici XML")
    
    # File upload
    uploaded_file = st.file_uploader("Carica il file XML dei bonifici", type=['xml'])
    
    if uploaded_file is not None:
        # Read and parse XML
        xml_content = uploaded_file.read().decode('utf-8')
        df = parse_xml_file(xml_content)
        
        # Column visibility toggles
        st.sidebar.header("Visualizza Colonne")
        columns_to_show = []
        for column in df.columns:
            if st.sidebar.checkbox(column, value=True):
                columns_to_show.append(column)
        
        # Display filtered DataFrame
        if columns_to_show:
            st.dataframe(df[columns_to_show])
            
            # Export to PDF button
            if st.button("Esporta in PDF"):
                pdf = export_to_pdf(df[columns_to_show])
                st.download_button(
                    label="Scarica PDF",
                    data=pdf,
                    file_name="bonifici.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("Seleziona almeno una colonna da visualizzare")

if __name__ == "__main__":
    main()