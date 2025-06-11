import streamlit as st
from gdeltdoc import GdeltDoc, Filters, near, repeat
import pandas as pd
import datetime
import json
import os
from urllib.parse import urlparse
from datetime import datetime, timedelta
from URLtextProcessor import URLTextProcessor # Assicurati che questa classe esista
from keyword_extractor import get_keywords_from_article # Importa il nuovo modulo

# --- Funzioni di utilità ---
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
    
    search_details["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as file:
            logs = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    logs.append(search_details)
    
    with open(log_file, 'w', encoding='utf-8') as file:
        json.dump(logs, file, indent=4)
    
    return True

def save_searched_domain_set(df):
    log_dir = "1_Filters_list"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "domains.json")
    df = df[["domain", "language", "sourcecountry"]]
    
    new_records = {tuple(row) for row in df.itertuples(index=False, name=None)}
    
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            try:
                existing_records = {tuple(d.values()) for d in json.load(f)}
            except json.JSONDecodeError:
                existing_records = set()
    else:
        existing_records = set()
    
    updated_records = existing_records | new_records
    
    updated_records_list = [dict(zip(["domain", "language", "sourcecountry"], record)) for record in updated_records]
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(updated_records_list, f, ensure_ascii=False, indent=4)
    
    print(f"Salvati {len(updated_records_list)} record unici in {log_file}")

def extract_domain(url: str) -> str:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path
    domain = domain.replace('www.', '')
    domain = domain.rstrip('/')
    return domain

def save_results_csv():
    results_dir = "search_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(results_dir, f"gdelt_results_{timestamp}.csv")
    
    st.session_state.search_results.to_csv(filename, index=False)
    st.session_state.csv_filename = filename
    st.session_state.csv_saved = True

# --- Nuova Pagina per la Ricerca di Similarità ---
def similarity_search_page():
    st.markdown("---")
    st.markdown('<div class="main-title">Ricerca di Similarità Articoli</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Trova articoli correlati basandosi su un URL di partenza.</div>', unsafe_allow_html=True)
    
    # Input URL dell'articolo
    input_url = st.text_input("Inserisci l'URL dell'articolo di partenza:", key="similarity_url_input")

    # Selezione della lingua (lato utente, come richiesto)
    selected_lang = st.selectbox("Seleziona la lingua dell'articolo:", ["en", "it"], key="similarity_lang_select")

    # Delta temporale per la ricerca GDELT
    time_delta_days = st.slider("Delta temporale (giorni indietro da oggi) per la ricerca GDELT:", 1, 30, 10, key="similarity_time_delta")
    
    if st.button("Estrai Testo e Keyword", key="extract_button"):
        if input_url:
            with st.spinner("Estrazione del testo e delle keyword in corso..."):
                try:
                    processor = URLTextProcessor() 
                    article_data = processor.fetch_and_process_single_url(input_url)
                    
                    if article_data and article_data.get('text'): # Verifica che il testo sia stato estratto
                        # Imposta la lingua del dizionario con quella selezionata dall'utente
                        article_data['lang'] = selected_lang 
                        
                        # Estrai keyword dal testo (il titolo sarà ignorato se None in get_keywords_from_article)
                        extracted_keywords = get_keywords_from_article(article_data, num_keywords=15) 
                        
                        st.session_state.similarity_article_data = article_data
                        st.session_state.extracted_keywords_for_similarity = extracted_keywords
                        # Non salviamo initial_article_title in session_state, non ci serve nella UI

                        st.success("Testo e keyword estratte con successo!")
                        
                        # Mostra i dati dell'articolo estratto per debug
                        with st.expander("Dati Articolo Estratti (per debug)"):
                            st.json(article_data) 

                    else:
                        # Messaggio di errore più specifico se il testo non è stato estratto
                        st.error(f"Impossibile estrarre il testo dall'URL fornito: {input_url}. Controlla che l'URL sia valido e accessibile.")
                        st.session_state.similarity_article_data = None
                        st.session_state.extracted_keywords_for_similarity = []

                except Exception as e:
                    st.error(f"Errore durante l'estrazione: {e}")
                    st.session_state.similarity_article_data = None
                    st.session_state.extracted_keywords_for_similarity = []
        else:
            st.warning("Per favore, inserisci un URL valido per iniziare.")

    # Se le keyword sono state estratte, mostrale e permetti la modifica
    if 'extracted_keywords_for_similarity' in st.session_state and st.session_state.extracted_keywords_for_similarity:
        st.markdown("---")
        st.subheader("🔍 Keyword suggerite dal testo dell'articolo:")
        st.write("Queste keyword sono state estratte automaticamente. Puoi aggiungerne o rimuoverne.")

        # Campo per aggiungere nuove keyword
        new_keyword_input = st.text_input("Aggiungi una nuova keyword:", key="add_similarity_keyword")
        if st.button("Aggiungi Keyword", key="add_similarity_keyword_button") and new_keyword_input.strip():
            kw = new_keyword_input.strip()
            if kw not in st.session_state.extracted_keywords_for_similarity:
                st.session_state.extracted_keywords_for_similarity.append(kw)
                st.rerun() 

        # Mostra le keyword attuali e permette la rimozione
        st.markdown("---")
        st.subheader("Keyword correnti per la ricerca:")
        
        current_keywords = list(st.session_state.extracted_keywords_for_similarity)
        num_cols = 4 
        cols = st.columns(num_cols)
        
        for i, keyword in enumerate(current_keywords):
            with cols[i % num_cols]:
                st.markdown(f"**{keyword}**")
                if st.button("Rimuovi", key=f"remove_sim_kw_{keyword}"):
                    st.session_state.extracted_keywords_for_similarity.remove(keyword)
                    st.rerun() 
        
        st.markdown("---")
        if st.button("Cerca Articoli Simili con GDELT", key="gdelt_similarity_search_button"):
            # Aggiunto controllo per assicurarsi che 'similarity_article_data' e 'lang' siano presenti
            if st.session_state.extracted_keywords_for_similarity and st.session_state.similarity_article_data and 'lang' in st.session_state.similarity_article_data:
                with st.spinner("Esecuzione della ricerca GDELT per articoli simili..."):
                    end_date_gdelt = datetime.now()
                    start_date_gdelt = end_date_gdelt - timedelta(days=time_delta_days)

                    filters = Filters(
                        start_date=start_date_gdelt.strftime("%Y%m%d%H%M%S"),
                        end_date=end_date_gdelt.strftime("%Y%m%d%H%M%S"),
                        keyword=st.session_state.extracted_keywords_for_similarity,
                        num_records=250, 
                        sort="hybridrel", 
                        mode="artlist",
                        country=st.session_state.similarity_article_data['lang'] 
                    )

                    gd = GdeltDoc()
                    similar_articles = gd.article_search(filters)

                    if not similar_articles.empty:
                        # Rimuovi l'articolo di input dai risultati se presente
                        input_url = st.session_state.similarity_article_data['url'] if st.session_state.similarity_article_data else None
                        if input_url:
                            input_domain = extract_domain(input_url)
                            similar_articles_filtered = similar_articles[
                                (similar_articles['url'] != input_url) &
                                (similar_articles['domain'] != input_domain)
                            ]
                        else:
                            similar_articles_filtered = similar_articles
                        
                        if not similar_articles_filtered.empty:
                            st.session_state.similarity_search_results = similar_articles_filtered
                            st.success(f"Trovati {len(similar_articles_filtered)} articoli simili!")
                            st.dataframe(similar_articles_filtered)

                            # Opzione per scaricare i risultati
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            csv_dir = "similarity_results"
                            if not os.path.exists(csv_dir):
                                os.makedirs(csv_dir)
                            csv_filename = os.path.join(csv_dir, f"gdelt_similar_articles_{timestamp}.csv")
                            
                            similar_articles_filtered.to_csv(csv_filename, index=False)
                            with open(csv_filename, "rb") as file:
                                st.download_button(
                                    label="Download Articoli Simili (CSV)",
                                    data=file,
                                    file_name=os.path.basename(csv_filename),
                                    mime="text/csv"
                                )
                        else:
                            st.warning("Nessun articolo simile trovato dopo la filtrazione dell'articolo di input.")
                    else:
                        st.warning("Nessun articolo simile trovato con le keyword e il delta temporale specificati.")
            else:
                st.warning("Per favore, estrai il testo e le keyword dall'URL di partenza prima di cercare articoli simili.")
                st.session_state.similarity_search_results = None # Resetta i risultati se non validi
                
    # --- Nuovo Blocco: Scrape Link Contents e Analisi nella Pagina di Similarità ---
    # MODIFICA QUI: Aggiunto controllo per None prima di accedere a .empty
    if st.session_state.get('similarity_search_results') is not None and not st.session_state.similarity_search_results.empty:
        st.markdown("---")
        st.subheader("🔗 Scrape contenuti dai risultati di ricerca simili")
        
        if st.button("Scrape link contents (risultati simili)", key="scrape_sim_results_button"):
            with st.spinner("Scraping dei contenuti dagli articoli simili..."):
                # Assicurati che la directory esista per il file di memoria dello scrape
                raw_text_data_dir = "raw_text_data"
                os.makedirs(raw_text_data_dir, exist_ok=True)
                
                # Genera un nome file specifico per i risultati di similarità
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                memory_file_path_sim = os.path.join(raw_text_data_dir, f"sim_search_articles_{timestamp}.json")
                
                link_extractor = URLTextProcessor(memory_file=memory_file_path_sim)
                scraped_articles = link_extractor.process_links_save_text_save_link(st.session_state.similarity_search_results)
                
                # Filtra gli articoli che hanno effettivamente estratto del testo
                st.session_state.similarity_extracted_articles = [
                    art for art in scraped_articles if art and art.get('text')
                ]
                
                if st.session_state.similarity_extracted_articles:
                    st.success(f"Contenuti estratti con successo da {len(st.session_state.similarity_extracted_articles)} articoli simili!")
                else:
                    st.warning("Nessun contenuto estratto dagli articoli simili.")
                st.rerun() # Ricarica per visualizzare la sezione di selezione

    if 'similarity_extracted_articles' in st.session_state and st.session_state.similarity_extracted_articles:
        st.markdown("---")
        st.subheader("📚 Seleziona gli articoli simili da esplorare:")
        
        # Prepara la lista di articoli per la selezione, gestendo il caso di titolo mancante
        sim_article_titles = {
            article.get("title", f"Articolo {i}").strip(): article 
            for i, article in enumerate(st.session_state.similarity_extracted_articles)
        }
        titles_for_multiselect = list(sim_article_titles.keys())

        selected_sim_titles = st.multiselect("Titoli disponibili:", titles_for_multiselect, key="selected_sim_titles")

        st.subheader("🧠 Modalità di Analisi Segnali di Disinformazione")
        sim_analysis_mode = st.radio(
            "Come vuoi procedere con l'analisi?",
            ("Manuale", "Automatica con LLM"),
            key="sim_analysis_mode"
        )

        # Inizializza un dictionary per le analisi specifiche di questi articoli
        if "sim_annotations" not in st.session_state:
            st.session_state.sim_annotations = {}

        for current_title_or_fallback in selected_sim_titles:
            sim_doc = sim_article_titles[current_title_or_fallback] # Recupera l'articolo completo
            
            # Inizializza lo stato per l'articolo corrente se non esiste
            if current_title_or_fallback not in st.session_state.sim_annotations:
                st.session_state.sim_annotations[current_title_or_fallback] = {"disinfo_analysis": None, "llm_generated_sim": False}

            st.markdown(f"### 📰 Analisi per: {current_title_or_fallback}")
            st.markdown(f"**🔗 URL:** [{sim_doc['url']}]({sim_doc['url']})")
            st.markdown(f"**🌍 Lingua:** {sim_doc.get('language', 'Non specificata')}")
            
            with st.expander(f"Visualizza Testo Estratto (per {current_title_or_fallback})", expanded=False):
                st.write(sim_doc['text'])
            
            # Bottone per generare l'analisi
            if st.button(f"Genera Analisi Segnali Disinformazione (LLM)", key=f"gen_disinfo_sim_{current_title_or_fallback}"):
                if sim_analysis_mode == "Automatica con LLM":
                    with st.spinner(f"Generazione analisi per '{current_title_or_fallback}'..."):
                        # TODO: Qui si integrerebbe la chiamata reale all'LLM
                        # Esempio simulato di output LLM
                        simulated_llm_analysis = {
                            "summary": "Analisi automatica: Il testo presenta toni polarizzanti e potrebbe contenere elementi di pseudoscienza riguardo al tema X.",
                            "confidence": "media",
                            "flags": ["polarization", "pseudoscience"]
                        }
                        st.session_state.sim_annotations[current_title_or_fallback]["disinfo_analysis"] = simulated_llm_analysis
                        st.session_state.sim_annotations[current_title_or_fallback]["llm_generated_sim"] = True
                        st.success(f"✅ Analisi generata per '{current_title_or_fallback}' (simulato).")
                        st.rerun()
                else:
                    st.info("Modalità manuale selezionata. Genera l'analisi manualmente o cambia modalità.")

            # Visualizzazione dell'analisi (se presente)
            if st.session_state.sim_annotations[current_title_or_fallback]["disinfo_analysis"]:
                st.markdown("---")
                st.subheader("📊 Risultato Analisi Segnali Disinformazione:")
                analysis_data = st.session_state.sim_annotations[current_title_or_fallback]["disinfo_analysis"]
                
                st.write(f"**Riepilogo:** {analysis_data.get('summary', 'N/A')}")
                st.write(f"**Confidenza:** {analysis_data.get('confidence', 'N/A')}")
                st.write(f"**Flags:** {', '.join(analysis_data.get('flags', [])) if analysis_data.get('flags') else 'N/A'}")
                
                if st.button("Elimina Analisi", key=f"del_analysis_sim_{current_title_or_fallback}"):
                    st.session_state.sim_annotations[current_title_or_fallback]["disinfo_analysis"] = None
                    st.session_state.sim_annotations[current_title_or_fallback]["llm_generated_sim"] = False
                    st.success("Analisi eliminata.")
                    st.rerun()
            st.markdown("---") # Separatore per ogni articolo selezionato


        # Pulsante per salvare tutte le analisi generate in un JSON
        if st.session_state.sim_annotations:
            if st.button("💾 Esporta tutte le analisi in JSON", key="export_all_sim_analysis"):
                output_analysis_data = []
                for title, analysis in st.session_state.sim_annotations.items():
                    original_article = sim_article_titles.get(title, {})
                    if analysis["disinfo_analysis"]: # Salva solo le analisi che sono state generate
                        output_analysis_data.append({
                            "title": original_article.get("title", title),
                            "url": original_article.get("url", ""),
                            "language": original_article.get("language", "N/A"),
                            "text_truncated": original_article.get("text", "")[:500] + "..." if original_article.get("text") else "", # Truncate text for export
                            "disinformation_analysis": analysis["disinfo_analysis"]
                        })
                
                if output_analysis_data:
                    output_file_dir = "disinformation_analysis_results"
                    os.makedirs(output_file_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = os.path.join(output_file_dir, f"disinfo_analysis_sim_{timestamp}.json")
                    
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(output_analysis_data, f, indent=2, ensure_ascii=False)
                    
                    st.success(f"✅ Analisi esportate con successo in {output_file}")
                    st.download_button(
                        label="📥 Scarica il file JSON di analisi",
                        data=json.dumps(output_analysis_data, indent=2, ensure_ascii=False),
                        file_name=os.path.basename(output_file),
                        mime="application/json"
                    )
                else:
                    st.warning("Nessuna analisi da esportare. Genera alcune analisi prima.")


# --- Funzione che contiene la logica della HomePage esistente ---
def display_home_page():
    default_folder = "1_Filters_list"
    country_file = os.path.join(default_folder, "country_list.json")
    theme_file = os.path.join(default_folder, "LOOKUP-GKGTHEMES.TXT")
    domain_file = os.path.join(default_folder, "domains.json")

    if st.sidebar.button("Carica dati dai file"):
        st.session_state.country_list = load_json_list(country_file)
        st.session_state.themes_list = load_tsv_first_column(theme_file)
        st.session_state.domain_list = load_json_list(domain_file)
        st.sidebar.success("Filtri caricati correttamente")
    
    st.sidebar.header("Filtri di Ricerca")
    
    filter_method = st.sidebar.radio("Metodo di filtraggio delle date", ("Intervallo di Date", "Timespan"))
    
    if filter_method == "Intervallo di Date":
        st.session_state.start_date = st.sidebar.date_input("Data di inizio", st.session_state.start_date)
        st.session_state.end_date = st.sidebar.date_input("Data di fine", st.session_state.end_date)
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
    st.session_state.countries = st.sidebar.multiselect("Seleziona i paesi", st.session_state.country_list, default=st.session_state.countries)
    
    st.sidebar.subheader("Temi")
    st.session_state.selected_themes = st.sidebar.multiselect("Seleziona i temi", st.session_state.themes_list, default=st.session_state.selected_themes)
    

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
                st.session_state.sort = st.selectbox("Scegli la modalità di ordinamento", ["datedesc", "dateasc", "tonedesc","toneasc", "hybridrel"], key="sort_select")
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
                st.session_state.near_distance = st.number_input("Distanza Near", min_value=1, max_value=10, value=st.session_state.near_distance)
                st.session_state.near_word1 = st.text_input("Parola 1", value=st.session_state.near_word1)
                st.session_state.near_word2 = st.text_input("Parola 2", value=st.session_state.near_word2)
            
            with st.container():
                st.subheader("Repeat")
                st.session_state.repeat_count = st.number_input("Conteggio Repeat", min_value=1, max_value=10, value=st.session_state.repeat_count)
                st.session_state.repeat_word = st.text_input("Parola da contare", value=st.session_state.repeat_word)

    # Sezione Tono e Tono Assoluto
    with st.expander("Opzioni di Tono e Tono Assoluto"):
        tono_scelto = st.radio("Seleziona il tipo di Tono da utilizzare:", ["Tono", "Tono Assoluto"], key="tono_choice")
        
        if tono_scelto == "Tono":
            with st.container():
                st.subheader("Threshold Tono Positivo o Negativo")
                tone_options = ["greater than", "less than"]
                tone_dict = {"greater than": ">", "less than": "<"}
                st.session_state.tone_direction = st.radio("Scegli una direzione positiva o negativa:", tone_options, key="tone_dir_home")
                
                st.session_state.tone_intensity = st.slider("Scegli un valore tra -25 e 25:", min_value=-25, max_value=25, value=st.session_state.tone_intensity, step=1, key="tone_int_home")
                
                if st.session_state.tone_direction:
                    st.session_state.tone = f"{tone_dict[st.session_state.tone_direction]} {st.session_state.tone_intensity}"
                    st.write(f'Tono selezionato: {st.session_state.tone}')
        
        elif tono_scelto == "Tono Assoluto":
            with st.container():
                st.subheader("Threshold Tono Assoluto da Neutro a Positivo o Negativo")
                tone_options = ["greater than", "less than"]
                st.session_state.toneabs_direction = st.radio("Scegli una direzione da neutra a polarizzante:", tone_options, key="toneabs_dir_home")
                tone_dict = {"greater than": ">", "less than": "<"}
                
                st.session_state.toneabs_intensity = st.slider("Scegli un valore tra 0 e 25:", min_value=0, max_value=25, value=st.session_state.toneabs_intensity, step=1, key="toneabs_int_home")
                
                if st.session_state.toneabs_direction:
                    st.session_state.toneabs = f"{tone_dict[st.session_state.toneabs_direction]} {st.session_state.toneabs_intensity}"
                    st.write(f'Tono Assoluto Selezionato: {st.session_state.toneabs}')

    # Sezione Numero di Record
    with st.expander("Numero di Record (Min. 25 Max. 250)"):
        st.session_state.num_records = st.number_input("Numero di record", min_value=25, max_value=250, value=st.session_state.num_records, key="num_records_home")


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
                        file_name=os.path.basename(csv_filename),
                        mime="text/csv"
                    )
                    
        with col3:
            if st.button("Scrape link contents"):
                # Assicurati che la directory esista
                raw_text_data_dir = "raw_text_data"
                os.makedirs(raw_text_data_dir, exist_ok=True)

                if not st.session_state.timespan:
                    memory_file_path = os.path.join(raw_text_data_dir, f"user_search_{st.session_state.start_date.strftime('%Y%m%d%H%M%S')}_{st.session_state.end_date.strftime('%Y%m%d%H%M%S')}.json")
                else:
                    memory_file_path = os.path.join(raw_text_data_dir, f"user_search_{st.session_state.timespan}.json")

                link_extractor = URLTextProcessor(memory_file=memory_file_path)
                link_extractor.process_links_save_text_save_link(st.session_state.search_results)
                st.session_state.extracted_file = memory_file_path
                st.success("Contenuti estratti e salvati con successo!")

        
        # Caricamento e visualizzazione degli articoli
        if 'extracted_file' in st.session_state and os.path.exists(st.session_state.extracted_file):
            with open(st.session_state.extracted_file, 'r', encoding='utf-8') as f:
                articles = json.load(f)

                if isinstance(articles, list) and all(isinstance(a, dict) for a in articles):
                    # Il titolo può essere None, quindi filtra per la presenza del titolo prima di creare la mappa
                    # O usa un fallback se il titolo è cruciale per la visualizzazione qui
                    title_to_doc = {article.get("title", f"Articolo {i}").strip(): article for i, article in enumerate(articles)}
                    titles = list(title_to_doc.keys())

                    st.subheader("📚 Seleziona gli articoli da esplorare:")
                    selected_titles = st.multiselect("Titoli disponibili:", titles)

                    st.subheader("🧠 Seleziona la modalità di annotazione")
                    annotation_mode = st.radio(
                        "Come vuoi procedere con l'annotazione?",
                        ("Manuale", "Automatica con LLM"),
                        key="annotation_mode"
                    )

                    # Inizializza st.session_state.annotations se non esiste
                    if "annotations" not in st.session_state:
                        st.session_state.annotations = {}

                    for title_or_fallback in selected_titles: # Usa il titolo o il fallback
                        cols = st.columns([0.85, 0.15])
                        with cols[0]:
                            st.markdown(f"### 📰 {title_or_fallback}")
                        with cols[1]:
                            if title_or_fallback not in st.session_state.annotations:
                                st.session_state.annotations[title_or_fallback] = {"clickbait": 0, "spans": []}
                            
                            is_clickbait = st.checkbox(
                                "Clickbait?", 
                                value=bool(st.session_state.annotations[title_or_fallback].get("clickbait", 0)), 
                                key=f"clickbait_{title_or_fallback}"
                            )
                            st.session_state.annotations[title_or_fallback]["clickbait"] = int(is_clickbait)

                        doc = title_to_doc[title_or_fallback]
                        with st.expander(f"Visualizza contenuto estratto per: {title_or_fallback}", expanded=False):
                            st.markdown(f"**🔗 URL:** [{doc['url']}]({doc['url']})")
                            st.markdown(f"**🌍 Lingua:** {doc.get('language', 'Non specificata')}")
                            st.markdown("---")

                            st.markdown("**✍️ Modifica il contenuto estratto (se necessario):**")
                            current_text = st.session_state.annotations[title_or_fallback].get("modified_text", doc['text'])
                            modified_text = st.text_area("Testo estratto:", current_text, height=300, key=f"modified_text_{title_or_fallback}")

                            if modified_text != current_text:
                                st.session_state.annotations[title_or_fallback]["modified_text"] = modified_text
                                st.success("Testo aggiornato con successo!")

                        # == Generazione automatica ==
                        if annotation_mode == "Automatica con LLM" and not st.session_state.annotations[title_or_fallback].get("llm_generated", False):
                            st.info("Simulando l'annotazione automatica con LLM (TODO: implementare la chiamata API reale).")
                            simulated_clickbait_result = {"clickbait": True}
                            simulated_spans = [
                                {"text": "Questo è un esempio di frase annotata da LLM.", "tag": "manipolazione emotiva"},
                                {"text": "Un altro esempio di disinformazione generato.", "tag": "conspiracy"}
                            ]
                            
                            st.session_state.annotations[title_or_fallback]["clickbait"] = int(simulated_clickbait_result["clickbait"])
                            st.session_state.annotations[title_or_fallback]["spans"] = simulated_spans 
                            st.session_state.annotations[title_or_fallback]["llm_generated"] = True 
                            st.success("✅ Annotazioni generate e valutazione clickbait completata (simulato).")
                            st.rerun() 


                        # == Interfaccia di annotazione sempre visibile ==
                        st.markdown("## 🖋️ Aggiungi annotazione testuale")

                        annotation_text = st.text_area("🔍 Segmento di testo da annotare:", height=150, key=f"annotation_text_{title_or_fallback}")
                        tag_label = st.selectbox("🏷️ Tipo di disinformazione", [
                            "trolling", "pseudoscience", "discredit", "polarization", "hate_speech","racist", "sexist", "toxic_speech","conspiracy"
                        ], key=f"tag_{title_or_fallback}")

                        if st.button("➕ Aggiungi annotazione", key=f"add_ann_{title_or_fallback}"):
                            if annotation_text.strip():
                                if "spans" not in st.session_state.annotations[title_or_fallback]:
                                    st.session_state.annotations[title_or_fallback]["spans"] = []
                                st.session_state.annotations[title_or_fallback]["spans"].append({
                                    "text": annotation_text.strip(),
                                    "tag": tag_label
                                })
                                st.success(f"Annotazione aggiunta: [{tag_label}] “{annotation_text.strip()}”")
                                st.rerun() 
                            else:
                                st.error("❌ Devi inserire un segmento di testo per l'annotazione.")

                        # == Visualizzazione annotazioni correnti ==
                        if title_or_fallback in st.session_state.annotations:
                            st.markdown("### 🧾 Annotazioni correnti:")

                            clickbait_flag = st.session_state.annotations[title_or_fallback].get("clickbait", "N/A")
                            st.markdown(f"- 🏷️ **Clickbait**: {'✅ Sì' if clickbait_flag == 1 else '❌ No'}")

                            if "spans" in st.session_state.annotations[title_or_fallback] and st.session_state.annotations[title_or_fallback]["spans"]:
                                for i, ann in enumerate(st.session_state.annotations[title_or_fallback]["spans"]):
                                    col1, col2 = st.columns([0.9, 0.1])
                                    with col1:
                                        st.markdown(f"{i+1}. **{ann['tag']}** – \"{ann['text']}\"")
                                    with col2:
                                        if st.button(f"❌", key=f"remove_{title_or_fallback}_{i}"):
                                            del st.session_state.annotations[title_or_fallback]["spans"][i]
                                            st.success("Annotazione rimossa con successo!")
                                            st.rerun() 

                    # ---- Salvataggio annotazioni ----
                    st.markdown("---")
                    st.subheader("📦 Salvataggio annotazioni")

                    if st.button("💾 Esporta tutto in JSON annotato"):
                        if "annotations" in st.session_state:
                            annotated_data = []

                            for title_or_fallback, ann in st.session_state.annotations.items():
                                article = title_to_doc.get(title_or_fallback, {}) 
                                annotated_data.append({
                                    "title": article.get("title", title_or_fallback), 
                                    "url": article.get("url", ""),
                                    "language": ann.get("language", article.get("language", "N/A")), 
                                    "text": ann.get("modified_text", article.get("text", "")),
                                    "clickbait": ann.get("clickbait", 0),
                                    "annotations": ann.get("spans", [])
                                })

                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_file_dir = "annotated_data"
                            os.makedirs(output_file_dir, exist_ok=True) 
                            output_file = os.path.join(output_file_dir, f"user_annotated_articles_{timestamp}.json")
                            
                            with open(output_file, "w", encoding="utf-8") as f:
                                json.dump(annotated_data, f, indent=2, ensure_ascii=False)

                            st.success(f"✅ Dati esportati con successo in {output_file}")
                            st.download_button(
                                label="📥 Scarica il file JSON",
                                data=json.dumps(annotated_data, indent=2, ensure_ascii=False),
                                file_name=os.path.basename(output_file),
                                mime="application/json"
                            )

# --- Funzione Main del tuo Streamlit ---
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

    if 'page' not in st.session_state:
        st.session_state.page = 'home' 

    st.sidebar.markdown("---")
    st.sidebar.header("Navigazione")
    if st.sidebar.button("Home (Ricerca GDELT)", key="nav_home"):
        st.session_state.page = 'home'
    if st.sidebar.button("Ricerca di Similarità", key="nav_similarity"):
        st.session_state.page = 'similarity_search'
    st.sidebar.markdown("---")


    # Inizializza session state variables
    if 'country_list' not in st.session_state: st.session_state.country_list = ['UK','US','IT','DE','FR','JP','CA','AU','GB']
    if 'themes_list' not in st.session_state: st.session_state.themes_list = []
    if 'keyword_list' not in st.session_state: st.session_state.keyword_list = []
    if 'domain_list' not in st.session_state: st.session_state.domain_list = []
    if 'search_results' not in st.session_state: st.session_state.search_results = None
    if 'query_string' not in st.session_state: st.session_state.query_string = None
    if 'log_saved' not in st.session_state: st.session_state.log_saved = False
    if 'csv_saved' not in st.session_state: st.session_state.csv_saved = False
    if 'csv_filename' not in st.session_state: st.session_state.csv_filename = None
    if 'search_completed' not in st.session_state: st.session_state.search_completed = False
    if 'search_details' not in st.session_state: st.session_state.search_details = None
    if 'domain_input_list' not in st.session_state: st.session_state.domain_input_list = []
    if 'tone_direction' not in st.session_state: st.session_state.tone_direction = None
    if 'tone_intensity' not in st.session_state: st.session_state.tone_intensity = None
    if 'tone' not in st.session_state: st.session_state.tone = ''
    if 'toneabs_direction' not in st.session_state: st.session_state.toneabs_direction = None
    if 'toneabs_intensity' not in st.session_state: st.session_state.toneabs_intensity = None
    if 'toneabs' not in st.session_state: st.session_state.toneabs = ''
    if 'mode' not in st.session_state: st.session_state.mode = ''
    if 'sort' not in st.session_state: st.session_state.sort =''
    if 'start_date' not in st.session_state: st.session_state.start_date = datetime.now() - timedelta(days=7)
    if 'end_date' not in st.session_state: st.session_state.end_date = datetime.now()
    if 'timespan' not in st.session_state: st.session_state.timespan = None
    if 'num_records' not in st.session_state: st.session_state.num_records = 250
    if 'selected_themes' not in st.session_state: st.session_state.selected_themes = []
    if 'countries' not in st.session_state: st.session_state.countries = ['UK','US','IT']
    if 'near_distance' not in st.session_state: st.session_state.near_distance = 5
    if 'near_word1' not in st.session_state: st.session_state.near_word1 = ""
    if 'near_word2' not in st.session_state: st.session_state.near_word2 = ""
    if 'repeat_count' not in st.session_state: st.session_state.repeat_count = 3
    if 'repeat_word' not in st.session_state: st.session_state.repeat_word = ""
    if 'annotations' not in st.session_state: st.session_state.annotations = {}


    # Per la pagina di similarità
    if 'similarity_article_data' not in st.session_state: st.session_state.similarity_article_data = None
    if 'extracted_keywords_for_similarity' not in st.session_state: st.session_state.extracted_keywords_for_similarity = []
    if 'similarity_search_results' not in st.session_state: st.session_state.similarity_search_results = None
    if 'similarity_extracted_articles' not in st.session_state: st.session_state.similarity_extracted_articles = None
    if 'sim_annotations' not in st.session_state: st.session_state.sim_annotations = {}


    if st.session_state.page == 'home':
        display_home_page()
    elif st.session_state.page == 'similarity_search':
        similarity_search_page()

if __name__ == "__main__":
    main()
