import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
#import pulp as pu
import io

def parse_xml_file(xml_content):
    """
    Legge il contenuto di un file XML in formato pain.001.001.03
    ed estrae le informazioni dei bonifici (CdtTrfTxInf).
    
    Restituisce:
    - DataFrame con colonne [Data, Destinatario, IBAN, Importo, Causale]
    - Nome della società ordinante (company_name)
    """
    
    root = ET.fromstring(xml_content)
    
    # Namespace "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"
    ns = {'iso': 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03'}
    
    # 1) Società ordinante
    company_name_node = root.find('.//iso:CstmrCdtTrfInitn/iso:GrpHdr/iso:InitgPty/iso:Nm', ns)
    company_name = company_name_node.text if company_name_node is not None else 'SOCIETÀ NON TROVATA'
    
    # 2) Data di esecuzione (valida per tutti i bonifici in questo XML)
    exec_date_node = root.find('.//iso:CstmrCdtTrfInitn/iso:PmtInf/iso:ReqdExctnDt', ns)
    data_bonifico = exec_date_node.text if exec_date_node is not None else ''
    
    # 3) Trova tutte le transazioni (CdtTrfTxInf)
    transactions = []
    for transaction in root.findall('.//iso:CstmrCdtTrfInitn/iso:PmtInf/iso:CdtTrfTxInf', ns):
        
        # Destinatario
        destinatario_node = transaction.find('.//iso:Cdtr/iso:Nm', ns)
        destinatario = destinatario_node.text if destinatario_node is not None else ''
        
        # IBAN
        iban_node = transaction.find('.//iso:CdtrAcct/iso:Id/iso:IBAN', ns)
        iban = iban_node.text if iban_node is not None else ''
        
        # Importo (sotto <Amt><InstdAmt>)
        importo_node = transaction.find('.//iso:Amt/iso:InstdAmt', ns)
        importo_text = importo_node.text if importo_node is not None else '0'
        # Assicuriamoci di convertire stringa in float
        importo = float(importo_text.replace(',', '.'))
        
        # Causale (RmtInf -> Ustrd)
        causale_node = transaction.find('.//iso:RmtInf/iso:Ustrd', ns)
        causale = causale_node.text if causale_node is not None else ''
        
        transactions.append({
            'Data': data_bonifico,
            'Destinatario': destinatario,
            'IBAN': iban,
            'Importo': importo,
            'Causale': causale
        })
    
    return pd.DataFrame(transactions), company_name

def export_to_csv(df):
    """
    Converte un DataFrame Pandas in CSV (UTF-8),
    restituendo i dati binari pronti per il download.
    """
    return df.to_csv(index=False).encode('utf-8')

def main():
    st.title("Parser Bonifici XML (pain.001.001.03)")
    
    # File upload - accetta più file .xml
    uploaded_files = st.file_uploader(
        "Carica uno o più file XML dei bonifici (pain.001.001.03)", 
        type=['xml'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        try:
            # Lista per contenere tutti i DataFrame
            all_dfs = []
            # Set per elencare le diverse società ordinanti
            companies = set()
            
            # Processa ogni file caricato
            for uploaded_file in uploaded_files:
                xml_content = uploaded_file.read().decode('utf-8')
                df, company_name = parse_xml_file(xml_content)
                
                # Aggiungiamo la colonna "Società Ordinante" a ogni riga di questo DataFrame
                df['Società Ordinante'] = company_name
                
                # Uniamo il DF alla lista
                all_dfs.append(df)
                # Aggiungiamo il nome dell'azienda al set
                companies.add(company_name)
            
            # Unisce tutti i DataFrame in uno solo
            combined_df = pd.concat(all_dfs, ignore_index=True)
            
            # Visualizzazione delle società ordinanti
            st.subheader("Società ordinanti:")
            for company in companies:
                st.write(f"- {company}")
            
            # Sidebar per selezionare quali colonne visualizzare
            st.sidebar.header("Visualizza Colonne")
            columns_to_show = []
            for column in combined_df.columns:
                # Di default, tutte le colonne tranne "Società Ordinante" sono selezionate
                if column == 'Società Ordinante':
                    # default = False
                    if st.sidebar.checkbox(column, value=False):
                        columns_to_show.append(column)
                else:
                    # default = True per le altre
                    if st.sidebar.checkbox(column, value=True):
                        columns_to_show.append(column)
            
            # Se l'utente ha selezionato almeno una colonna, procedi
            if columns_to_show:
                display_df = combined_df[columns_to_show].copy()
                
                # Ordina per data se la colonna "Data" è selezionata
                if 'Data' in columns_to_show:
                    display_df = display_df.sort_values('Data')
                
                # Aggiungi riga di totale se la colonna "Importo" è selezionata
                if 'Importo' in columns_to_show:
                    total_row = pd.DataFrame([{
                        col: 'TOTALE' if col == 'Destinatario' else 
                             combined_df['Importo'].sum() if col == 'Importo' else ''
                        for col in columns_to_show
                    }])
                    display_df = pd.concat([display_df, total_row], ignore_index=True)
                
                # Mostra statistiche rapide
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Numero totale bonifici: {len(combined_df)}")
                with col2:
                    if 'Importo' in columns_to_show:
                        st.write(f"Importo totale: {combined_df['Importo'].sum():.2f}")
                
                # Visualizza la tabella
                st.dataframe(display_df)
                
                # Pulsante per scaricare il CSV
                # Esporta il DataFrame senza la riga di 'TOTALE'
                csv = export_to_csv(combined_df[columns_to_show])
                st.download_button(
                    label="Scarica CSV",
                    data=csv,
                    file_name="bonifici_combinati.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Seleziona almeno una colonna da visualizzare.")
                
        except Exception as e:
            st.error(f"Errore durante l'elaborazione del file: {str(e)}")

if __name__ == "__main__":
    main()
