import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
#import pulp as pu
import io

def parse_xml_file(xml_content):
    # Parse XML
    root = ET.fromstring(xml_content)
    
    # Define namespace
    ns = {'cbi': 'urn:CBI:xsd:CBIPaymentRequest.00.04.01'}
    
    # Extract company info
    company_name = root.find('.//cbi:InitgPty/cbi:Nm', ns).text
    
    # Extract transactions
    transactions = []
    for transaction in root.findall('.//cbi:CdtTrfTxInf', ns):
        destinatario = transaction.find('.//cbi:Cdtr/cbi:Nm', ns).text
        iban = transaction.find('.//cbi:CdtrAcct/cbi:Id/cbi:IBAN', ns).text
        importo = transaction.find('.//cbi:InstdAmt', ns).text
        causale = transaction.find('.//cbi:RmtInf/cbi:Ustrd', ns).text
        # Data di esecuzione
        data_bonifico = root.find('.//cbi:ReqdExctnDt/cbi:Dt', ns).text
        
        transactions.append({
            'Data': data_bonifico,
            'Destinatario': destinatario,
            'IBAN': iban,
            'Importo': float(importo),
            'Causale': causale
        })
    
    # Crea il DataFrame a partire dalla lista di dizionari
    df = pd.DataFrame(transactions)
    
    # Ritorna anche il nome dell'azienda (società ordinante)
    return df, company_name

def export_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def main():
    st.title("Parser Bonifici XML")
    
    # File upload - ora accetta più file
    uploaded_files = st.file_uploader("Carica uno o più file XML dei bonifici", type=['xml'], accept_multiple_files=True)
    
    if uploaded_files:
        try:
            # Lista per contenere tutti i DataFrame
            all_dfs = []
            companies = set()
            
            # Processa ogni file
            for uploaded_file in uploaded_files:
                xml_content = uploaded_file.read().decode('utf-8')
                df, company_name = parse_xml_file(xml_content)
                
                # Aggiunge la colonna "Società Ordinante"
                # in modo che appaia in ogni riga relativa al file corrente
                df['Società Ordinante'] = company_name
                
                all_dfs.append(df)
                companies.add(company_name)
            
            # Concatena tutti i DataFrame
            combined_df = pd.concat(all_dfs, ignore_index=True)
            
            # Mostra le società coinvolte
            st.subheader("Società ordinanti:")
            for company in companies:
                st.write(f"- {company}")
            
            # Column visibility toggles
            st.sidebar.header("Visualizza Colonne")
            columns_to_show = []
            
            # Quando settiamo i checkbox, vogliamo che "Società Ordinante" sia di default non selezionata.
            for column in combined_df.columns:
                if column == 'Società Ordinante':
                    # Default = False per questa colonna
                    if st.sidebar.checkbox(column, value=False):
                        columns_to_show.append(column)
                else:
                    # Default = True per le altre colonne
                    if st.sidebar.checkbox(column, value=True):
                        columns_to_show.append(column)
            
            # Display filtered DataFrame
            if columns_to_show:
                # Ordina per data se presente
                display_df = combined_df[columns_to_show].copy()
                if 'Data' in columns_to_show:
                    display_df = display_df.sort_values('Data')
                
                # Aggiungi riga totale se 'Importo' è presente
                if 'Importo' in columns_to_show:
                    total_row = pd.DataFrame([{
                        col: 'TOTALE' if col == 'Destinatario' else 
                             combined_df['Importo'].sum() if col == 'Importo' else ''
                        for col in columns_to_show
                    }])
                    display_df = pd.concat([display_df, total_row], ignore_index=True)
                
                # Mostra statistiche
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Numero totale bonifici: {len(combined_df)}")
                with col2:
                    if 'Importo' in columns_to_show:
                        st.write(f"Importo totale: {combined_df['Importo'].sum():.2f}")
                
                # Mostra DataFrame
                st.dataframe(display_df)
                
                # Export to CSV button
                # Esportiamo i dati senza la riga "TOTALE"
                csv = export_to_csv(combined_df[columns_to_show])  
                st.download_button(
                    label="Scarica CSV",
                    data=csv,
                    file_name="bonifici_combinati.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Seleziona almeno una colonna da visualizzare")
                
        except Exception as e:
            st.error(f"Errore durante l'elaborazione del file: {str(e)}")

if __name__ == "__main__":
    main()
