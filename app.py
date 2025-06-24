import streamlit as st
import os
from azure.storage.blob import BlobServiceClient
import requests
import pyodbc

# Configura variabili
AZURE_BLOB_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=ictarchiviazione;AccountKey=Dns7fsa7Hv9OHhUnfTEXJSE0wIUEyvmbA9zWK4C0fJArG9nLw8V+D1r8AJA40TsGzeOcKGSUsm2f+AStMtQuPw==;EndpointSuffix=core.windows.net"
BLOB_CONTAINER_NAME = "ict-final"

AZURE_SEARCH_ENDPOINT = "https://ict-aisearch.search.windows.net"
AZURE_SEARCH_API_KEY = "IWU3BTSzC9Vv3JrbPSss1JNwjP5jroYbThxe1cwB3BAzSeDMhVWE"
INDEXER_NAME = "ict-indexer-meta-2"

def get_distinct_tipi():
    server = 'sqlserverict.database.windows.net'  
    database = 'ict_database'                  
    username = 'phaesmatos'                 
    password = 'E123678!'                  
    driver = '{ODBC Driver 18 for SQL Server}'  

    conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Area FROM [Document Library] WHERE Area IS NOT NULL")
        rows = cursor.fetchall()
        return [row[0] for row in rows if row[0]]

# Inizializza il client Blob
blob_service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

st.title("📄 Caricatore Documenti su Azure")

#tipi_disponibili = get_distinct_tipi()
#if tipi_disponibili:
#    tipo = st.selectbox("Seleziona il tipo di documento", tipi_disponibili)
#else:
#    st.warning("⚠️ Nessun tipo trovato nel database.")

tipo = st.selectbox("Seleziona il tipo di documento", ["Normativa Istituzionale EU","Normativa Istituzionale Italiana","Non Istituzionali","Interno Banche","Report Generati"])
uploaded_file = st.file_uploader("Carica un documento (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

if uploaded_file:
    blob_name = uploaded_file.name

    # Upload su Blob
    with st.spinner("Caricamento su Azure Blob..."):
        container_client.upload_blob(
        name=blob_name,
        data=uploaded_file,
        overwrite=True,
        metadata={"tipo": tipo.lower()} )
        st.success(f"✅ File '{blob_name}' caricato con successo.")

    # Avvio dell'indexer
    if st.button("Avvia indicizzazione"):
        st.info("Invio richiesta per avviare l’indexer...")

        response = requests.post(
            f"{AZURE_SEARCH_ENDPOINT}/indexers/{INDEXER_NAME}/run?api-version=2023-10-01-Preview",
            headers={"Content-Type": "application/json", "api-key": AZURE_SEARCH_API_KEY},
        )

        if response.status_code == 202:
            st.success("🚀 Indexer avviato con successo.")
        else:
            st.error(f"Errore nell'avvio dell'indexer: {response.status_code}\n{response.text}")
