import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import io

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

def export_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def main():
    st.title("Parser Bonifici XML")
    
    # File upload
    uploaded_file = st.file_uploader("Carica il file XML dei bonifici", type=['xml'])
    
    if uploaded_file is not None:
        try:
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
                
                # Export to CSV button
                csv = export_to_csv(df[columns_to_show])
                st.download_button(
                    label="Scarica CSV",
                    data=csv,
                    file_name="bonifici.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Seleziona almeno una colonna da visualizzare")
                
        except Exception as e:
            st.error(f"Errore durante l'elaborazione del file: {str(e)}")

if __name__ == "__main__":
    main()