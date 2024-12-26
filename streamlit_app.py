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
        importo = float(transaction.find('.//cbi:InstdAmt', ns).text)
        causale = transaction.find('.//cbi:RmtInf/cbi:Ustrd', ns).text
        
        transactions.append({
            'Destinatario': destinatario,
            'IBAN': iban,
            'Importo': importo,
            'Causale': causale
        })
    
    return pd.DataFrame(transactions)

def export_to_csv(df):
    return df.to_csv(index=False, sep=';').encode('utf-8-sig')

def export_to_pdf(df):
    buffer = io.BytesIO()
    
    # PDF Header
    buffer.write(b'%PDF-1.4\n')
    
    # Create a simple text stream
    text = "Elenco Bonifici\n\n"
    
    # Add header
    text += " | ".join(df.columns) + "\n"
    text += "-" * 80 + "\n"
    
    # Add data
    for _, row in df.iterrows():
        text += " | ".join(str(item) for item in row) + "\n"
    
    # Write content
    content = f"""
1 0 obj
<< /Type /Catalog
   /Pages 2 0 R
>>
endobj

2 0 obj
<< /Type /Pages
   /Kids [3 0 R]
   /Count 1
>>
endobj

3 0 obj
<< /Type /Page
   /Parent 2 0 R
   /Resources << /Font << /F1 4 0 R >> >>
   /MediaBox [0 0 595 842]
   /Contents 5 0 R
>>
endobj

4 0 obj
<< /Type /Font
   /Subtype /Type1
   /BaseFont /Courier
>>
endobj

5 0 obj
<< /Length {len(text)} >>
stream
BT
/F1 10 Tf
50 750 Td
({text}) Tj
ET
endstream
endobj

xref
0 6
0000000000 65535 f
0000000010 00000 n
0000000060 00000 n
0000000120 00000 n
0000000250 00000 n
0000000330 00000 n

trailer
<< /Size 6
   /Root 1 0 R
>>
startxref
480
%%EOF
"""
    
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)
    return buffer

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
                
                # Container for export buttons
                col1, col2, col3 = st.columns(3)
                
                # Export to CSV button
                with col1:
                    csv = export_to_csv(st.session_state.df[columns_to_show])
                    st.download_button(
                        label="Scarica CSV",
                        data=csv,
                        file_name="bonifici.csv",
                        mime="text/csv"
                    )
                
                # Export to PDF button
                with col2:
                    pdf = export_to_pdf(st.session_state.df[columns_to_show])
                    st.download_button(
                        label="Scarica PDF",
                        data=pdf,
                        file_name="bonifici.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("Seleziona almeno una colonna da visualizzare")
                
        except Exception as e:
            st.error(f"Errore durante l'elaborazione del file: {str(e)}")

if __name__ == "__main__":
    main()