import pandas as pd
import requests
import os
import trafilatura
import concurrent.futures
import json
import traceback # Importa il modulo traceback

class URLTextProcessor:
    """Classe per la gestione di URL, estrazione di testo, pulizia e salvataggio di link unici."""

    def __init__(self, memory_file="raw_text_data/raw.json"):
        """
        Inizializza la classe con il file di memoria.
        
        :param memory_file: Il nome del file JSON per memorizzare i link salvati.
        """
        self.memory_file = memory_file
        # Assicurati che la directory esista per il file di memoria
        os.makedirs(os.path.dirname(self.memory_file) or '.', exist_ok=True)


    def _load_saved_links(self):
        """Carica gli URL già salvati nel file JSON utilizzando pandas, se esiste."""
        if os.path.exists(self.memory_file):
            try:
                df = pd.read_json(self.memory_file, encoding="utf-8")
                return df if not df.empty else pd.DataFrame(columns=['url', 'title', 'language', 'text'])
            except (ValueError, json.JSONDecodeError) as e:
                print(f"ERRORE: Impossibile caricare {self.memory_file}: {e}")
                traceback.print_exc() # Stampa lo stack trace completo
                return pd.DataFrame(columns=['url', 'title', 'language', 'text'])
        return pd.DataFrame(columns=['url', 'title', 'language', 'text'])

    def _save_links(self, new_links):
        """Salva nuovi URL e titoli nel file JSON utilizzando pandas."""
        if not new_links:
            return

        saved_links_df = self._load_saved_links()
        new_links_df = pd.DataFrame(new_links)
        
        combined_df = pd.concat([saved_links_df, new_links_df], ignore_index=True)
        final_df = combined_df.drop_duplicates(subset=["url"], keep="first")
        
        os.makedirs(os.path.dirname(self.memory_file) or '.', exist_ok=True)
        try:
            final_df.to_json(self.memory_file, orient='records', lines=False, force_ascii=False, indent=4)
        except Exception as e:
            print(f"ERRORE: Impossibile salvare i link in {self.memory_file}: {e}")
            traceback.print_exc() # Stampa lo stack trace completo


    def _fetch_text_from_url(self, url):
        """Effettua una richiesta HTTP."""
        try:
            response = requests.get(url, timeout=15) # Aumentato il timeout a 15 secondi
            response.raise_for_status() # Lancia un'eccezione per codici di stato HTTP errati
            print(f"DEBUG: HTML scaricato con successo da: {url}")
            return response.text
        except requests.exceptions.Timeout as e:
            print(f'ERRORE HTTP: Timeout raggiunto per URL: {url} - {e}')
            traceback.print_exc() # Stampa lo stack trace completo
            return None
        except requests.exceptions.RequestException as e:
            print(f'ERRORE HTTP: Richiesta fallita per URL: {url} - {e}')
            traceback.print_exc() # Stampa lo stack trace completo
            return None
        except Exception as e:
            print(f'ERRORE GENERICO in _fetch_text_from_url per URL: {url} - {e}')
            traceback.print_exc() # Stampa lo stack trace completo
            return None


    def _clean_text_and_extract_metadata(self, raw_html, url):
        """
        Utilizza trafilatura per pulire il testo estratto e recuperare metadati come titolo e lingua.
        """
        if not raw_html:
            print(f"DEBUG: Nessun HTML grezzo fornito per l'URL: {url}")
            return None, None, None # testo, titolo, lingua

        try:
            extracted = trafilatura.extract(
                raw_html,
                url=url,
                include_links=False,
                include_comments=False,
                favor_precision=True,
                output_format="json"
            )
            
            if extracted:
                try:
                    data = json.loads(extracted)
                    text = data.get('text')
                    title = data.get('title')
                    language = data.get('language')
                    print(f"DEBUG: Trafilatura ha estratto testo, titolo e lingua per {url}")
                    return text, title, language
                except json.JSONDecodeError as e:
                    print(f"ERRORE JSON: Trafilatura ha restituito un JSON non valido per {url}. Errore: {e}")
                    print(f"DEBUG: Output RAW di trafilatura (truncated): {extracted[:500]}...") # Stampa parte dell'output JSON
                    traceback.print_exc()
                    # Fallback a estrazione testo semplice se JSON decoding fallisce
                    text_fallback = trafilatura.extract(raw_html, include_links=False, include_comments=False, favor_precision=True)
                    return text_fallback, None, None 
            else:
                print(f"AVVISO: Trafilatura non ha estratto alcun contenuto per l'URL: {url}")
                return None, None, None
        except Exception as e:
            print(f"ERRORE TRAFILATURA: Eccezione durante l'estrazione con Trafilatura per URL: {url} - {e}")
            traceback.print_exc()
            return None, None, None


    def _process_texts(self, df):
        """
        Estrae e pulisce il testo da una lista di URL parallelizzando le richieste HTTP.
        """
        df = df.drop_duplicates(subset=["url"]).drop_duplicates(subset=["title"])

        new_entries = []

        def process_row(row):
            url = row["url"]
            original_title = row.get("title")
            original_language = row.get("language")

            print(f"DEBUG: Processo URL: {url}") # Logga l'URL che sta per essere processato
            raw_text = self._fetch_text_from_url(url)
            text, extracted_title, extracted_language = self._clean_text_and_extract_metadata(raw_text, url)
            
            final_title = extracted_title if extracted_title else original_title
            final_language = (extracted_language if extracted_language else original_language or 'en').lower()

            if text: # Modifica: Rimuovi la condizione 'and final_title'
                print(f"DEBUG: Estrazione testo riuscita per URL: {url}")
                return {"url": url, "title": final_title, "language": final_language, "text": text}
            else:
                print(f"AVVISO: Fallita estrazione testo per URL: {url}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(process_row, row): row for _, row in df.iterrows()}
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        new_entries.append(result)
                except Exception as e:
                    error_row = futures[future]
                    error_url = error_row.get("url", "<URL non disponibile>")
                    print(f"ERRORE THREAD: Eccezione nel thread per URL: {error_url}")
                    traceback.print_exc() # Stampa lo stack trace completo
                    
        return new_entries

    def process_links_save_text_save_link(self, df):
        """Esegue l'intero stack: estrazione, pulizia e salvataggio dei dati."""
        print("Inizio elaborazione e pulizia...")
        new_entries = self._process_texts(df)
        
        if new_entries:
            self._save_links(new_entries)
            print(f"Salvato {len(new_entries)} nuovi articoli in {self.memory_file}.")
        else:
            print("Nessun nuovo articolo trovato.")

        return new_entries

    def fetch_and_process_single_url(self, url: str):
        """
        Scarica, pulisce ed estrae testo, titolo e lingua da un singolo URL.
        Restituisce un dizionario con 'url', 'title', 'lang', 'text'.
        """
        print(f"DEBUG: Avvio fetch_and_process_single_url per: {url}") # Logga l'inizio
        try:
            raw_html = self._fetch_text_from_url(url)
            if not raw_html:
                print(f"AVVISO: Nessun HTML scaricato per l'URL: {url}. Impossibile procedere con l'estrazione.")
                return None

            # `_clean_text_and_extract_metadata` tenterà di estrarre titolo e lingua, ma non è obbligatorio per il successo.
            text, title, language = self._clean_text_and_extract_metadata(raw_html, url)
            
            # Qui il successo dipende SOLO dalla presenza del testo.
            # Il titolo può essere None, e la lingua sarà quella scelta dall'utente.
            if text:
                print(f"DEBUG: Testo estratto con successo da URL: {url}. Titolo: {title if title else 'Non estratto'}")
                return {
                    "url": url,
                    # Il titolo sarà None se non estratto da trafilatura, ma è accettabile.
                    "title": title.strip() if title else None, 
                    "lang": language.lower() if language else 'en', # Usa lingua rilevata o fallback. Sarà sovrascritta dalla UI.
                    "text": text.strip()
                }
            else:
                print(f"AVVISO: Impossibile estrarre TESTO dall'URL: {url} dopo lo scraping HTML. Il titolo non è un requisito.")
                return None
        except Exception as e:
            print(f"ERRORE GENERALE in fetch_and_process_single_url per URL: {url} - {e}")
            traceback.print_exc() # Stampa lo stack trace completo
            return None

