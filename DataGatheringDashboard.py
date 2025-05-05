import streamlit as st
from gdeltdoc import GdeltDoc, Filters, near, repeat
import pandas as pd
import datetime 
import json
import os, re
from urllib.parse import urlparse
from datetime import datetime, timedelta
from URLtextProcessor import URLTextProcessor

def load_json_list(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def load_tsv_first_column(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return [line.split('\t')[0].strip() for line in file if line.strip()]
    except FileNotFoundError:
        return []

def save_search_to_log(search_details):
    log_dir = "search_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "search_history.json")
    
    # Add timestamp to search details
    search_details["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Load existing logs
    try:
        with open(log_file, 'r', encoding='utf-8') as file:
            logs = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    # Add new search details
    logs.append(search_details)
    
    # Save updated logs
    with open(log_file, 'w', encoding='utf-8') as file:
        json.dump(logs, file, indent=4)
    
    return True

def save_searched_domain_set(df):
    log_dir = "1_Filters_list"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "domains.json")
    # Estrarre solo le colonne di interesse
    df = df[["domain", "language", "sourcecountry"]]
    
    # Convertire il DataFrame in un insieme di dizionari per garantire unicità
    new_records = {tuple(row) for row in df.itertuples(index=False, name=None)}
    
    # Se il file esiste, caricare i dati esistenti
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            try:
                existing_records = {tuple(d.values()) for d in json.load(f)}
            except json.JSONDecodeError:
                existing_records = set()
    else:
        existing_records = set()
    
    # Unire i nuovi record con quelli esistenti
    updated_records = existing_records | new_records
    
    # Convertire l'insieme in una lista di dizionari
    updated_records_list = [dict(zip(["domain", "language", "sourcecountry"], record)) for record in updated_records]
    
    # Salvare i dati aggiornati nel file JSON
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(updated_records_list, f, ensure_ascii=False, indent=4)
    
    print(f"Salvati {len(updated_records_list)} record unici in {log_file}")

def extract_domain(url: str) -> str:
    # Rimuove il prefisso 'http://', 'https://', e 'www.'
    parsed_url = urlparse(url)
    
    # Otteniamo il dominio senza prefisso
    domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path
    
    # Rimuoviamo eventuali 'www.' dal dominio
    domain = domain.replace('www.', '')
    
    # Rimuoviamo eventuali slash finali
    domain = domain.rstrip('/')
    
    return domain

def save_results_csv():
    # Create directory if it doesn't exist
    results_dir = "search_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(results_dir, f"gdelt_results_{timestamp}.csv")
    
    # Save to CSV
    st.session_state.search_results.to_csv(filename, index=False)
    st.session_state.csv_filename = filename
    st.session_state.csv_saved = True


def main():
    st.markdown("""
    <style>
        .main-title {
            text-align: center;
            font-size: 40px;
            font-weight: bold;
            margin-top: 20px;
        }
        .subtitle {
            text-align: left;
            font-size: 18px;
            margin-top: 5px;
            color: #555;
        }
    </style>
    """, unsafe_allow_html=True)

    # Visualizza il titolo principale centrato
    st.markdown('<div class="main-title">API Filter Dashboard for Global Database of Events, Language, and Tone (GDELT)</div>', unsafe_allow_html=True)

    # Visualizza il sottotitolo a sinistra
    st.markdown('<div class="subtitle">Realtime open data global graph, updated every 15 min</div>', unsafe_allow_html=True)
    # Initialize session state variables
    
    if 'country_list' not in st.session_state:
        st.session_state.country_list = ['UK','US','IT','DE','FR','JP','CA','AU','GB']
    if 'themes_list' not in st.session_state:
        st.session_state.themes_list = []
    if 'keyword_list' not in st.session_state:
        st.session_state.keyword_list = []
    if 'domain_list' not in st.session_state:
        st.session_state.domain_list = []
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'query_string' not in st.session_state:
        st.session_state.query_string = None
    if 'log_saved' not in st.session_state:
        st.session_state.log_saved = False
    if 'csv_saved' not in st.session_state:
        st.session_state.csv_saved = False
    if 'csv_filename' not in st.session_state:
        st.session_state.csv_filename = None
    if 'search_completed' not in st.session_state:
        st.session_state.search_completed = False
    if 'search_details' not in st.session_state:
        st.session_state.search_details = None
    if 'domain_list' not in st.session_state:
        st.session_state.domain_list = []
    if 'domain_input_list' not in st.session_state:
        st.session_state.domain_input_list = []
    if 'tone_direction' not in st.session_state:
        st.session_state.tone_direction = None
    if 'tone_intensity' not in st.session_state:
        st.session_state.tone_intensity = None
    if 'tone' not in st.session_state:
        st.session_state.tone = ''
    if 'toneabs_direction' not in st.session_state:
        st.session_state.toneabs_direction = None
    if 'toneabs_intensity' not in st.session_state:
        st.session_state.toneabs_intensity = None
    if 'toneabs' not in st.session_state:
        st.session_state.toneabs = ''
    if 'mode' not in st.session_state:
        st.session_state.mode = ''
    if 'sort' not in st.session_state:
        st.session_state.sort_column =''
    
    default_folder = "1_Filters_list"
    country_file = os.path.join(default_folder, "country_list.json")
    theme_file = os.path.join(default_folder, "LOOKUP-GKGTHEMES.TXT")
    domain_file = os.path.join(default_folder, "domains.json")
    domain_file = os.path.join(default_folder, "domains.json")

    if st.sidebar.button("Carica dati dai file"):
        st.session_state.country_list = load_json_list(country_file)
        st.session_state.themes_list = load_tsv_first_column(theme_file)
        st.session_state.domain_list = load_json_list(domain_file)
        st.sidebar.success("Filtri caricati correttamente")
    
    st.sidebar.header("Filtri di Ricerca")
    
    filter_method = st.sidebar.radio("Metodo di filtraggio delle date", ("Intervallo di Date", "Timespan"))
    
    if filter_method == "Intervallo di Date":
        st.session_state.start_date = st.sidebar.date_input("Data di inizio", st.session_state.get('start_date', datetime.now() - timedelta(days=7) ))
        st.session_state.end_date = st.sidebar.date_input("Data di fine", st.session_state.get('end_date', datetime.now()))
        st.session_state.timespan = None
    else:
        st.session_state.timespan = st.sidebar.selectbox("Timespan", ["15min","30min","1h","2h","3h","4h","6h","12h", "1d","2d","3d","5d", "1w","2w","3w", "1m","2m","3m","4m","6m","9m","12m","18m", "24m"], index=2)
        st.session_state.start_date = None
        st.session_state.end_date = None
    
    # Input per aggiungere una keyword
    keyword_input = st.sidebar.text_input("Insert Keyword")
    if st.sidebar.button("Add Keyword") and keyword_input.strip():
        keyword_input = keyword_input.strip()
        if keyword_input not in st.session_state.keyword_list:
            st.session_state.keyword_list.append(keyword_input)
            st.sidebar.success(f"Aggiunto: {keyword_input}")

    # Visualizza la lista delle keyword con la possibilità di rimuoverle
    if len(st.session_state.keyword_list)>0:
        st.sidebar.subheader("Keywords salvate:")
    for keyword in st.session_state.keyword_list:
        col1, col2 = st.sidebar.columns([0.8, 0.2])
        col1.text(keyword)
        if col2.button("❌", key=f"remove_{keyword}",help="Rimuovi questa keyword dai filtri di ricerca"):
            st.session_state.keyword_list.remove(keyword)
            st.rerun()
    

    # Input per aggiungere un dominio manualmente
    domain_input = st.sidebar.text_input("Inserisci o seleziona un dominio: (esempio: gazzetta.it)")
    if st.sidebar.button("Aggiungi Dominio") and domain_input.strip():
        domain_input = domain_input.strip()
        if domain_input not in st.session_state.domain_list:
            domain_input = extract_domain(domain_input.strip())
            st.session_state.domain_list.append(domain_input)  # Aggiunge solo se nuovo
        st.session_state.domain_input_list.append(domain_input)
        st.sidebar.success(f"Aggiunto: {domain_input} ai filtri di ricerca")
    
    if len(st.session_state.domain_input_list)>0:
        st.sidebar.subheader("Domini salvati:")
    for domain in st.session_state.domain_input_list:
        col1, col2, col3 = st.sidebar.columns([0.7, 0.15, 0.15])
        col1.text(domain)
        if col2.button("❌", key=f"delete_{domain}", help="Rimuovi questo dominio dai filtri di ricerca"):
            st.session_state.domain_input_list.remove(domain)
            st.sidebar.success(f"{domain} rimosso dai filtri di ricerca")
            st.rerun()
            
        if domain not in st.session_state.domain_list:    
            if col3.button("➕", key=f"trust_{domain}",help="Aggiungi questo dominio alle fonti affidabili"):
                st.session_state.domain_list.append(domain)
                st.rerun()
        else:
            if col3.button("➖", key=f"untrust_{domain}",help="Rimuovi questo dominio dalle fonti affidabili"):
                st.session_state.domain_list.remove(domain)
                st.rerun()


    st.sidebar.subheader("Paesi")
    st.session_state.countries = st.sidebar.multiselect("Seleziona i paesi", st.session_state.country_list, default=st.session_state.get('countries', ['UK','US','IT']),)
    
    st.sidebar.subheader("Temi")
    st.session_state.selected_themes = st.sidebar.multiselect("Seleziona i temi", st.session_state.themes_list, default=st.session_state.get('selected_themes', []))
    

    # HOME PAGE
    st.subheader("Filtri avanzati")

    # INSTRUCTIONS Ordinamento e Modalità
    tooltip_info = {
    "datedesc": "Ordina per data di pubblicazione, mostrando prima gli articoli più recenti.",
    "dateasc": "Ordina per data di pubblicazione, mostrando prima gli articoli più vecchi.",
    "tonedesc": "Ordina per tono, mostrando prima gli articoli con il tono più positivo.",
    "toneasc": "Ordina per tono, mostrando prima gli articoli con il tono più negativo.",
    "hybridrel": "SUGGESTED: Ordina combinando rilevanza testuale e popolarità della fonte.",
    "artlist": "DATA DEFAULT: Visualizza gli articoli in un elenco semplice con dettagli essenziali.",
    "timelinevol": "INFO: Mostra una timeline con il volume degli articoli trovati.",
    "timelinevolraw": "INFO: Mostra il numero esatto di articoli trovati senza normalizzazione.",
    "timelinetone": "INFO: Visualizza una timeline con l’andamento del tono degli articoli.",
    "timelinelang": "INFO: Mostra il volume degli articoli trovati diviso per lingua.",
    "timelinesourcecountry": "INFO: Visualizza una timeline basata sul paese di origine della fonte.",
    }

    # Sezione Ordinamento e Modalità
    with st.expander("Opzioni di Ordinamento e Modalità"):
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.session_state.sort = st.selectbox("Scegli la modalità di ordinamento", ["datedesc", "dateasc", "tonedesc","toneasc" "hybridrel"], key="sort_select")
            with col2:
                st.text( st.session_state.sort, help=tooltip_info[st.session_state.sort])
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.session_state.mode = st.selectbox("Scegli la modalità di ricerca", ["artlist", "timelinevol", "timelinevolraw", "timelinetone", "timelinelang", "timelinesourcecountry"], key="mode_select")
            with col2:
                st.text( st.session_state.mode, help=tooltip_info[st.session_state.mode])

    # Sezione Near e Repeat
    with st.expander("Opzioni Near e Repeat"):
        with st.container():
            with st.container():
                st.subheader("Near")
                st.session_state.near_distance = st.number_input("Distanza Near", min_value=1, max_value=10, value=st.session_state.get('near_distance', 5))
                st.session_state.near_word1 = st.text_input("Parola 1", value=st.session_state.get('near_word1', ""))
                st.session_state.near_word2 = st.text_input("Parola 2", value=st.session_state.get('near_word2', ""))
            
            with st.container():
                st.subheader("Repeat")
                st.session_state.repeat_count = st.number_input("Conteggio Repeat", min_value=1, max_value=10, value=st.session_state.get('repeat_count', 3))
                st.session_state.repeat_word = st.text_input("Parola da contare", value=st.session_state.get('repeat_word', ""))

    # Sezione Tono e Tono Assoluto
    with st.expander("Opzioni di Tono e Tono Assoluto"):
        tono_scelto = st.radio("Seleziona il tipo di Tono da utilizzare:", ["Tono", "Tono Assoluto"])
        
        if tono_scelto == "Tono":
            with st.container():
                st.subheader("Threshold Tono Positivo o Negativo")
                tone_options = ["greater than", "less than"]
                tone_dict = {"greater than": ">", "less than": "<"}
                st.session_state.tone_direction = st.radio("Scegli una direzione positiva o negativa:", tone_options)
                
                st.session_state.tone_intensity = st.slider("Scegli un valore tra -25 e 25:", min_value=-25, max_value=25, value=st.session_state.get('tone_intensity', 0), step=1)
                
                if st.session_state.tone_direction:
                    st.session_state.tone = f"{tone_dict[st.session_state.tone_direction]} {st.session_state.tone_intensity}"
                    st.write(f'Tono selezionato: {st.session_state.tone}')
        
        elif tono_scelto == "Tono Assoluto":
            with st.container():
                st.subheader("Threshold Tono Assoluto da Neutro a Positivo o Negativo")
                tone_options = ["greater than", "less than"]
                st.session_state.toneabs_direction = st.radio("Scegli una direzione da neutra a polarizzante:", tone_options)
                tone_dict = {"greater than": ">", "less than": "<"}
                
                st.session_state.toneabs_intensity = st.slider("Scegli un valore tra 0 e 25:", min_value=0, max_value=25, value=st.session_state.get('toneabs_intensity', 0), step=1)
                
                if st.session_state.toneabs_direction:
                    st.session_state.toneabs = f"{tone_dict[st.session_state.toneabs_direction]} {st.session_state.toneabs_intensity}"
                    st.write(f'Tono Assoluto Selezionato: {st.session_state.toneabs}')

    # Sezione Numero di Record
    with st.expander("Numero di Record (Min. 25 Max. 250)"):
        st.session_state.num_records = st.number_input("Numero di record", min_value=25, max_value=250, value=st.session_state.get('num_records', 250))


    # Search button logic
    if st.button("Search"):
        # Reset save states
        st.session_state.log_saved = False
        st.session_state.csv_saved = False
        st.session_state.csv_filename = None
        
        near_obj = near(st.session_state.near_distance, st.session_state.near_word1, st.session_state.near_word2) if st.session_state.near_word1 and st.session_state.near_word2 else None
        repeat_obj = repeat(st.session_state.repeat_count, st.session_state.repeat_word) if st.session_state.repeat_word else None
        
        filters = Filters(
            timespan=st.session_state.timespan if st.session_state.timespan else None,
            start_date=st.session_state.start_date.strftime("%Y%m%d%H%M%S") if st.session_state.start_date else None,
            end_date=st.session_state.end_date.strftime("%Y%m%d%H%M%S") if st.session_state.end_date else None,
            domain=st.session_state.domain_input_list[0] if len(st.session_state.domain_input_list) == 1 else st.session_state.domain_input_list,
            keyword=st.session_state.keyword_list[0] if len(st.session_state.keyword_list) == 1 else st.session_state.keyword_list,
            country=st.session_state.countries[0] if len(st.session_state.countries) == 1 else st.session_state.countries,
            theme=st.session_state.selected_themes[0] if len(st.session_state.selected_themes) == 1 else st.session_state.selected_themes,
            near=near_obj,
            repeat=repeat_obj,
            num_records=st.session_state.num_records,
            tone=st.session_state.tone,
            tone_abs=st.session_state.toneabs,
            mode=st.session_state.mode,
            sort=st.session_state.sort
        )

        st.session_state.query_string = str(filters.query_string)
        
        # Perform the search
        gd = GdeltDoc()
        if st.session_state.mode == "artlist":
            articles = gd.article_search(filters)
        else:
            articles = gd.timeline_search(st.session_state.mode,filters)
        
        articles = articles.drop_duplicates(subset=["title"], keep="first")
        
        if not articles.empty:
            save_searched_domain_set(articles)
            st.session_state.search_results = articles
            st.session_state.search_completed = True
            
            # Store search details
            st.session_state.search_details = {
                "query_string": st.session_state.query_string,
                "filter_method": filter_method,
                "timespan": st.session_state.timespan if st.session_state.timespan else None,
                "start_date": st.session_state.start_date.strftime("%Y%m%d%H%M%S") if st.session_state.start_date else None,
                "end_date": st.session_state.end_date.strftime("%Y%m%d%H%M%S") if st.session_state.end_date else None,
                "domain": st.session_state.domain_input_list[0] if len(st.session_state.domain_input_list) == 1 else st.session_state.domain_input_list,
                "keywords": st.session_state.keyword_list,
                "countries": st.session_state.countries,
                "themes": st.session_state.selected_themes,
                "near_settings": {
                    "distance": st.session_state.near_distance,
                    "word1": st.session_state.near_word1,
                    "word2": st.session_state.near_word2
                },
                "repeat_settings": {
                    "count": st.session_state.repeat_count,
                    "word": st.session_state.repeat_word
                },
                "num_records": st.session_state.num_records,
                "results_count": len(articles),
                "tone": st.session_state.tone,
                "toneabs": st.session_state.toneabs,
                "mode": st.session_state.mode,
                "sort": st.session_state.sort
            }
        else:
            st.session_state.search_results = None
            st.session_state.search_completed = False
            st.warning("Nessun risultato trovato.")
    
    # Always display results if they exist in session state
    if st.session_state.search_completed and st.session_state.search_results is not None:
        st.subheader("Filtri Generati:")
        st.code(st.session_state.query_string)
        
        st.subheader("Risultati Ricerca:")
        st.dataframe(st.session_state.search_results)
        
        # Display action buttons and messages
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Salva ricerca nel log"):
                save_search_to_log(st.session_state.search_details)
            
            if st.session_state.log_saved:
                st.success("Ricerca salvata nel log con successo!")
        
        with col2:
            if st.button("Salva risultati in CSV"):
                save_results_csv()
            
            if st.session_state.csv_saved:
                st.success(f"Risultati salvati in: {st.session_state.csv_filename}")
                
                with open(st.session_state.csv_filename, "rb") as file:
                    st.download_button(
                        label="Download CSV",
                        data=file,
                        file_name=os.path.basename(st.session_state.csv_filename),
                        mime="text/csv"
                    )
                    
        with col3:
            if st.button("Scrape link contents"):
                if not st.session_state.timespan:
                    link_extractor = URLTextProcessor(
                        memory_file=f"raw_text_data/user_search_{st.session_state.start_date.strftime('%Y%m%d%H%M%S')}_{st.session_state.end_date.strftime('%Y%m%d%H%M%S')}.json"
                    )
                else:
                    link_extractor = URLTextProcessor(
                        memory_file=f"raw_text_data/user_search_{st.session_state.timespan}.json"
                    )

                link_extractor.process_links_save_text_save_link(st.session_state.search_results)
                st.session_state.extracted_file = link_extractor.memory_file
                st.success("Contenuti estratti e salvati con successo!")

        
        # Caricamento e visualizzazione degli articoli
        if 'extracted_file' in st.session_state and os.path.exists(st.session_state.extracted_file):
            with open(st.session_state.extracted_file, 'r', encoding='utf-8') as f:
                articles = json.load(f)

                if isinstance(articles, list) and all(isinstance(a, dict) for a in articles):
                    title_to_doc = {article["title"].strip(): article for article in articles}
                    titles = list(title_to_doc.keys())

                    st.subheader("📚 Seleziona gli articoli da esplorare:")
                    selected_titles = st.multiselect("Titoli disponibili:", titles)

                    st.subheader("🧠 Seleziona la modalità di annotazione")
                    annotation_mode = st.radio(
                        "Come vuoi procedere con l'annotazione?",
                        ("Manuale", "Automatica con LLM"),
                        key="annotation_mode"
                    )

                    for title in selected_titles:
                        cols = st.columns([0.85, 0.15])
                        with cols[0]:
                            st.markdown(f"### 📰 {title}")
                        with cols[1]:
                            is_clickbait = st.checkbox("Clickbait?", key=f"clickbait_{title}")

                        if "annotations" not in st.session_state:
                            st.session_state.annotations = {}
                        if title not in st.session_state.annotations:
                            st.session_state.annotations[title] = {}
                        st.session_state.annotations[title]["clickbait"] = int(is_clickbait)

                        doc = title_to_doc[title]
                        with st.expander(f"Visualizza contenuto estratto per: {title}", expanded=False):
                            st.markdown(f"**🔗 URL:** [{doc['url']}]({doc['url']})")
                            st.markdown(f"**🌍 Lingua:** {doc.get('language', 'Non specificata')}")
                            st.markdown("---")

                            st.markdown("**✍️ Modifica il contenuto estratto (se necessario):**")
                            modified_text = st.text_area("Testo estratto:", doc['text'], height=300, key=f"modified_text_{title}")

                            if modified_text != doc['text']:
                                st.session_state.annotations[title]["modified_text"] = modified_text
                                st.success("Testo aggiornato con successo!")

                        # == Generazione automatica ==
                        if annotation_mode == "Automatica con LLM" and "llm_generated" not in st.session_state.annotations[title]:
                            # TODO:
                            # Prepara il prompt semplificato per clickbait e disinfo signals
                            # Chiamata al tuo LLM locale (es. llama.cpp)
                            # llm_clickbait_output = llama_cpp(prompt_clickbait + titolo_articolo)
                            # llm_clickbait_output = llama_cpp(prompt_disinfo + text)
                            
                            # Esempio simulato:
                            llm_clickbait_output = {"clickbait": True}
                            # Salva il risultato come flag binario
                            st.session_state.annotations[title]["clickbait"] = int(llm_clickbait_output["clickbait"])
                            # Eventualmente anche altre annotazioni testuali
                            st.session_state.annotations[title]["spans"] = [
                                {"text": "Esempio LLM: frase 1", "tag": "manipolazione emotiva"}
                            ]

                            st.session_state.annotations[title]["llm_generated"] = True
                            st.success("✅ Annotazioni generate e valutazione clickbait completata.")

                        # == Interfaccia di annotazione sempre visibile ==
                        st.markdown("## 🖋️ Aggiungi annotazione testuale")

                        annotation_text = st.text_area("🔍 Segmento di testo da annotare:", height=150, key=f"annotation_text_{title}")
                        tag_label = st.selectbox("🏷️ Tipo di disinformazione", [
                            "trolling", "pseudoscience", "discredit", "polarization", "hate_speech","racist", "sexist", "toxic_speech","conspiracy"
                        ], key=f"tag_{title}")

                        if st.button("➕ Aggiungi annotazione", key=f"add_ann_{title}"):
                            if annotation_text.strip():
                                if "spans" not in st.session_state.annotations[title]:
                                    st.session_state.annotations[title]["spans"] = []
                                st.session_state.annotations[title]["spans"].append({
                                    "text": annotation_text.strip(),
                                    "tag": tag_label
                                })
                                st.success(f"Annotazione aggiunta: [{tag_label}] “{annotation_text.strip()}”")
                            else:
                                st.error("❌ Devi inserire un segmento di testo per l'annotazione.")

                        # == Visualizzazione annotazioni correnti ==
                        if title in st.session_state.annotations:
                            st.markdown("### 🧾 Annotazioni correnti:")

                            clickbait_flag = st.session_state.annotations[title].get("clickbait", "N/A")
                            st.markdown(f"- 🏷️ **Clickbait**: {'✅ Sì' if clickbait_flag == 1 else '❌ No'}")

                            for i, ann in enumerate(st.session_state.annotations[title].get("spans", [])):
                                col1, col2 = st.columns([0.9, 0.1])
                                with col1:
                                    st.markdown(f"{i+1}. **{ann['tag']}** – \"{ann['text']}\"")
                                with col2:
                                    if st.button(f"❌", key=f"remove_{title}_{i}"):
                                        del st.session_state.annotations[title]["spans"][i]
                                        st.success("Annotazione rimossa con successo!")

                    # ---- Salvataggio annotazioni ----
                    st.markdown("---")
                    st.subheader("📦 Salvataggio annotazioni")

                    if st.button("💾 Esporta tutto in JSON annotato"):
                        if "annotations" in st.session_state:
                            annotated_data = []

                            for title, ann in st.session_state.annotations.items():
                                article = title_to_doc.get(title, {})
                                annotated_data.append({
                                    "title": title,
                                    "url": article.get("url", ""),
                                    "language": article.get("language", "N/A"),
                                    "text": ann.get("modified_text", article.get("text", "")),
                                    "clickbait": ann.get("clickbait", 0),
                                    "annotations": ann.get("spans", [])
                                })

                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_file = f"annotated_data/user_annotated_articles_{timestamp}.json"
                            with open(output_file, "w", encoding="utf-8") as f:
                                json.dump(annotated_data, f, indent=2, ensure_ascii=False)

                            st.success(f"✅ Dati esportati con successo in `{output_file}`")
                            st.download_button(
                                label="📥 Scarica il file JSON",
                                data=json.dumps(annotated_data, indent=2, ensure_ascii=False),
                                file_name=output_file,
                                mime="application/json"
                            )
                        else:
                            st.warning("⚠️ Nessuna annotazione trovata da esportare.")
                else:
                    st.info("⚠️ Nessun file caricato per la visualizzazione. Assicurati di aver completato la fase di scraping.")
if __name__ == "__main__":
    main()