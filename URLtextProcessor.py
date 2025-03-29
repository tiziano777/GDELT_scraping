import pandas as pd
import requests
import json
import os
import trafilatura

class URLTextProcessor:
    """Classe per la gestione di URL, estrazione di testo, pulizia e salvataggio di link unici."""

    def __init__(self, memory_file="raw_text_data/raw.json"):
        """
        Inizializza la classe con il file di memoria.
        
        :param memory_file: Il nome del file JSON per memorizzare i link salvati.
        """
        self.memory_file = memory_file

    def _load_saved_links(self):
        """Carica gli URL già salvati nel file JSON utilizzando pandas, se esiste."""
        if os.path.exists(self.memory_file):
            try:
                return pd.read_json(self.memory_file, encoding="utf-8")
            except ValueError:
                return pd.DataFrame()  # Restituisce un DataFrame vuoto in caso di errore
        return pd.DataFrame()

    def _save_links(self, new_links):
        """Salva nuovi URL e titoli nel file JSON utilizzando pandas."""
        saved_links = self._load_saved_links()
        new_links_df = pd.DataFrame(new_links)
        saved_links = pd.concat([saved_links, new_links_df], ignore_index=True)
        saved_links.to_json(self.memory_file, orient='records', lines=False, force_ascii=False, indent=4)

    def _fetch_text_from_url(self, url):
        """Effettua una richiesta HTTP """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            return None

    def _clean_text(self, raw_text):
        """Utilizza trafilatura per pulire il testo estratto e mantenere solo il corpo dell'articolo."""
        if raw_text:
            cleaned_text = trafilatura.extract(raw_text)
            return cleaned_text if cleaned_text else None
        return None

    def _process_texts(self, df):
        """Estrae e pulisce il testo da una lista di URL."""
        saved_links = self._load_saved_links()
        #saved_urls = set(saved_links["url"]) if not saved_links.empty else set()

        df = df.drop_duplicates(subset=["url"]).drop_duplicates(subset=["title"])

        new_entries = []
        for _, row in df.iterrows():
            url, title, language = row["url"], row["title"], row["language"]
            
            '''
            if url in saved_urls:
                continue  # Saltiamo gli URL già salvati
            '''
            raw_text = self._fetch_text_from_url(url)
            #print(raw_text)
            cleaned_text = self._clean_text(raw_text)

            if cleaned_text:
                new_entries.append({"url": url, "title": title, "language": language, "text": cleaned_text})
            
        return new_entries

    def process_links_and_save_extracted_text(self, df):
        """Esegue l'intero stack: estrazione, pulizia e salvataggio dei dati."""
        print("Inizio elaborazione e pulizia...")
        new_entries = self._process_texts(df)
        
        if new_entries:
            self._save_links(new_entries)
        else:
            print("Nessun nuovo articolo trovato.")

        return new_entries

    def process_links_and_extract_text(self, df):
        """Esegue l'intero stack: estrazione, pulizia e salvataggio dei dati."""
        new_entries = self._process_texts(df)
        
        if new_entries:
            print(f"{len(new_entries)} nuovi articoli salvati.")
        else:
            print("Nessun nuovo articolo trovato.")

        return new_entries

