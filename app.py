import streamlit as st
import os
from azure.storage.blob import BlobServiceClient
import requests

import pymssql

# Configura variabili
AZURE_BLOB_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=ictarchiviazione;AccountKey=Dns7fsa7Hv9OHhUnfTEXJSE0wIUEyvmbA9zWK4C0fJArG9nLw8V+D1r8AJA40TsGzeOcKGSUsm2f+AStMtQuPw==;EndpointSuffix=core.windows.net"
BLOB_CONTAINER_NAME = "ict-final"

AZURE_SEARCH_ENDPOINT = "https://ict-aisearch.search.windows.net"
AZURE_SEARCH_API_KEY = "IWU3BTSzC9Vv3JrbPSss1JNwjP5jroYbThxe1cwB3BAzSeDMhVWE"
INDEXER_NAME = "ict-indexer-meta-2"


def get_distinct_tipi(query:str):

    conn = pymssql.connect(server = 'sqlserverict.database.windows.net', 
    database = 'ict_database',                
    user = 'phaesmatos@sqlserverict',                
    password = 'E123678!' )

    cursor = conn.cursor()
    cursor.execute(query)
    tipi = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tipi

def inserisci_documento_nel_db(area, topic, ente, tipo, nome_file):
    conn = pymssql.connect(server = 'sqlserverict.database.windows.net', 
    database = 'ict_database',                
    user = 'phaesmatos@sqlserverict',                
    password = 'E123678!' )
    cursor = conn.cursor()
    
    insert_query = """
        INSERT INTO [Document Library] (
            [Area], [Topic_prevalente], [Ente_emittente], [Tipo_Documento], [Nome_file]
        ) VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (area, topic, ente, tipo, nome_file))
    conn.commit()
    conn.close()

# Inizializza il client Blob
blob_service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

st.title("📄 Caricatore Documenti su Azure")

area_disponibili = get_distinct_tipi("SELECT DISTINCT Area FROM [Document Library] WHERE Area IS NOT NULL")
if area_disponibili:
    area = st.selectbox("Seleziona L'Area di documento", area_disponibili)
else:
    st.warning("⚠️ Nessun tipo trovato nel database.")


topic_disponibili = get_distinct_tipi("SELECT DISTINCT [Topic_prevalente] FROM [Document Library] WHERE [Topic_prevalente] IS NOT NULL")
if topic_disponibili:
    topic = st.selectbox("Seleziona il topic del documento", topic_disponibili)
else:
    st.warning("⚠️ Nessun topic trovato nel database.")


enti_disponibili = get_distinct_tipi("SELECT DISTINCT [Ente_emittente] FROM [Document Library] WHERE [Ente_emittente] IS NOT NULL")
if enti_disponibili:
    ente = st.selectbox("Seleziona l' ente emittente del documento", enti_disponibili)
else:
    st.warning("⚠️ Nessun topic trovato nel database.")


tipo_disponibili = get_distinct_tipi("SELECT DISTINCT [Tipo_Documento] FROM [Document Library] WHERE [Tipo_Documento] IS NOT NULL")
if tipo_disponibili:
    tipo = st.selectbox("Seleziona il tipo del documento", tipo_disponibili)
else:
    st.warning("⚠️ Nessun topic trovato nel database.")



#tipo = st.selectbox("Seleziona il tipo di documento", ["Normativa Istituzionale EU","Normativa Istituzionale Italiana","Non Istituzionali","Interno Banche","Report Generati"])
uploaded_file = st.file_uploader("Carica un documento (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

if uploaded_file:
    blob_name = uploaded_file.name

    # Upload su Blob
    with st.spinner("Caricamento su Azure Blob..."):
        container_client.upload_blob(
        name=blob_name,
        data=uploaded_file,
        overwrite=True,
        metadata={"tipo": area} )
        st.success(f"✅ File '{blob_name}' caricato con successo.")


    try:
            inserisci_documento_nel_db(area, topic, ente, tipo, blob_name)
            st.success("✅ Riga inserita nel database.")
    except Exception as e:
            st.error(f"❌ Errore nell'inserimento nel database: {e}")

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
