import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import io
import locale

# Imposta il locale per il formato numerico europeo
locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')

def format_amount(amount):
    """Formatta l'importo in stile europeo: senza separatore migliaia, virgola per decimali"""
    return f"{amount:.2f}".replace('.', ',')

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
        importo = float(transaction.find('.//cbi:InstdAmt', ns).text)
        causale = transaction.find('.//cbi:RmtInf/cbi:Ustrd', ns).text
        
        transactions.append({
            'Destinatario': destinatario,
            'IBAN': iban,
            'Importo': format_amount(importo),
            'Causale': causale
        })
    
    return pd.DataFrame(transactions)

def export_to_csv(df):
    return df.to_csv(index=False, sep=';').encode('utf-8-sig')

def reset_app():
    st.session_state.clear()
    st.experimental_rerun()

def reset_app():
    st.session_state.clear()
    st.experimental_rerun()

def main():
    st.title("Parser Bonifici XML")
    
    # Initialize session state for the DataFrame if it doesn't exist
    if 'df' not in st.session_state:
        st.session_state.df = None
        
    # File upload
    uploaded_file = st.file_uploader("Carica il file XML dei bonifici", type=['xml'])
    
    # Clear button in the sidebar
    if st.sidebar.button("Pulisci Tutto"):
        reset_app()
    
    if uploaded_file is not None:
        try:
            # Read and parse XML
            xml_content = uploaded_file.read().decode('utf-8')
            st.session_state.df = parse_xml_file(xml_content)
            
            # Column visibility toggles
            st.sidebar.header("Visualizza Colonne")
            columns_to_show = []
            for column in st.session_state.df.columns:
                if st.sidebar.checkbox(column, value=True, key=f"col_{column}"):
                    columns_to_show.append(column)
            
            # Display filtered DataFrame
            if columns_to_show:
                st.dataframe(st.session_state.df[columns_to_show])
                
                # Export to CSV button
                csv = export_to_csv(st.session_state.df[columns_to_show])
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