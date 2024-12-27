import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
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

def filter_transactions(df, min_amount=None, max_amount=None, date_range=None, recipient=None):
    filtered_df = df.copy()
    if min_amount:
        filtered_df = filtered_df[filtered_df['Importo'] >= min_amount]
    if max_amount:
        filtered_df = filtered_df[filtered_df['Importo'] <= max_amount]
    if date_range:
        filtered_df = filtered_df[(filtered_df['Data'] >= date_range[0]) & 
                                (filtered_df['Data'] <= date_range[1])]
    if recipient:
        filtered_df = filtered_df[filtered_df['Destinatario'].str.contains(recipient, case=False)]
    return filtered_df

def generate_statistics(df):
    stats = {
        'bonifici_per_destinatario': df['Destinatario'].value_counts(),
        'importi_medi_per_destinatario': df.groupby('Destinatario')['Importo'].mean(),
        'trend_mensile': df.groupby(pd.to_datetime(df['Data']).dt.to_period('M'))['Importo'].sum()
    }
    return stats

def validate_iban(iban):
    # Rimuovi spazi e converti in maiuscolo
    iban = iban.replace(' ', '').upper()
    # Controllo lunghezza base per IBAN italiano
    if len(iban) != 27 or not iban.startswith('IT'):
        return False
    return True

def validate_transactions(df):
    df['IBAN_Valido'] = df['IBAN'].apply(validate_iban)
    return df

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
                df['Società Ordinante'] = company_name
                
                all_dfs.append(df)
                companies.add(company_name)
            
            # Concatena tutti i DataFrame
            combined_df = pd.concat(all_dfs, ignore_index=True)
            
            # Calcola le statistiche per società
            st.subheader("Dettaglio per società ordinante:")
            company_stats = combined_df.groupby('Società Ordinante').agg({
                'Importo': ['count', 'sum']
            }).round(2)

            # Rinomina le colonne per maggiore chiarezza
            company_stats.columns = ['Numero bonifici', 'Importo totale']

            # Per ogni società mostra le statistiche
            for company in companies:
                stats = company_stats.loc[company]
                st.write(f"- {company}:")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"   • Numero bonifici: {int(stats['Numero bonifici'])}")
                with col2:
                    st.write(f"   • Importo totale: €{stats['Importo totale']:,.2f}")
                st.write("---")
            
            # Column visibility toggles
            st.sidebar.header("Visualizza Colonne")
            columns_to_show = []
            
            for column in combined_df.columns:
                if column == 'Società Ordinante':
                    if st.sidebar.checkbox(column, value=False):
                        columns_to_show.append(column)
                else:
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
                        st.write(f"Importo totale: €{combined_df['Importo'].sum():,.2f}")
                
                # Mostra DataFrame
                st.dataframe(display_df)
                
                # Export to CSV button
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