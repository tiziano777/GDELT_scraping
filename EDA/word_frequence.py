import pandas as pd
import re
import random
import heapq
from collections import Counter
import json
import seaborn as sns
import matplotlib.pyplot as plt

class ItalianEnglishWordFrequency:
    """
    Classe per analizzare e visualizzare le frequenze delle parole nei documenti,
    utilizzando la lingua esplicitamente dichiarata (italiano o inglese).
    """
    
    def __init__(self):
        """
        Inizializza le risorse per le stopwords per le lingue supportate.
        """
        # Stopwords per le lingue italiane e inglesi
        self.italian_stopwords = {'e', 'è', 'di', 'il', 'la', 'i', 'le', 'un', 'una', 'che',
                                  'per', 'in', 'a', 'con', 'su', 'da', 'del', 'al', 'non',
                                  'si', 'lo', 'come', 'ma', 'se', 'ed'}
        self.english_stopwords = {'the', 'and', 'of', 'to', 'a', 'in', 'for', 'on', 'is', 'that', 'by'}
        
        self.word_counts = Counter()  # Contatore per le parole
        self.top_keywords = []  # Lista per le parole più frequenti
        self.df = None  # Dataframe per i risultati
        self.non_word_char = re.compile(r'[^\w\s]')  # Regex per rimuovere caratteri non alfanumerici
        self.digits = re.compile(r'\d+')  # Regex per rimuovere numeri

    def _extract_keywords(self, documents, top_n=20, min_word_length=3, max_documents=None):
        """
        Estrae parole chiave in base alla lingua specificata in ciascun documento.
        
        Args:
            documents (iterable): Iterabile di oggetti JSONL con chiavi 'text' e 'language'.
            top_n (int): Numero di parole chiave da restituire.
            min_word_length (int): Lunghezza minima delle parole da considerare.
            max_documents (int, opzionale): Numero massimo di documenti da elaborare.
        
        Returns:
            list: Lista di tuple (parola, conteggio, lingua).
        """
        self.word_counts.clear()  # Pulisce il contatore delle parole
        document_count = 0  # Contatore per i documenti processati

        for doc in documents:
            if max_documents and document_count >= max_documents:
                break

            # Controllo se il documento contiene i campi necessari
            if not isinstance(doc, dict) or 'text' not in doc or 'language' not in doc:
                continue
            
            lang = doc['language'].strip().lower()
            if lang == 'italian':
                stopwords_set = self.italian_stopwords
                lang_code = 'IT'
            elif lang == 'english':
                stopwords_set = self.english_stopwords
                lang_code = 'EN'
            else:
                continue  # Lingua non supportata
            
            # Pulizia del testo
            text = str(doc['text']).lower()  # Rendi tutto il testo in minuscolo
            text = self.non_word_char.sub(' ', text)  # Rimuovi caratteri non alfanumerici
            text = self.digits.sub(' ', text)  # Rimuovi numeri
            words = text.split()  # Dividi il testo in parole
            
            for word in words:
                if len(word) >= min_word_length and word not in stopwords_set:
                    self.word_counts[(word, lang_code)] += 1

            document_count += 1

        # Selezione delle top_n parole più frequenti
        self.top_keywords = heapq.nlargest(top_n, self.word_counts.items(), key=lambda x: x[1])

        # Creazione del DataFrame
        data = [(word, count, lang) for (word, lang), count in self.top_keywords]
        self.df = pd.DataFrame(data, columns=['Parola', 'Frequenza', 'Lingua'])

        return self.top_keywords

    def _generate_colorful_palette(self, n):
        """
        Genera n colori RGB brillanti in formato hex.
        
        Args:
            n (int): Numero di colori da generare.
        
        Returns:
            list: Lista di stringhe colore in formato esadecimale.
        """
        return [
            f'#{random.randint(100, 255):02x}{random.randint(100, 255):02x}{random.randint(100, 255):02x}'
            for _ in range(n)
        ]


    def _plot_and_save_histogram(self, title='Frequenza delle Parole Chiave nei Documenti', plot_filename='word_frequency.png', csv_filename='word_frequencies.csv'):
        """
        Visualizza un istogramma colorato delle parole chiave estratte, salva l'immagine e il file CSV.

        Args:
            title (str): Titolo del grafico.
            plot_filename (str): Percorso del file immagine in uscita (es. 'output.png').
            csv_filename (str): Percorso del file CSV in uscita (es. 'word_frequencies.csv').

        Returns:
            tuple: Nomi dei file immagine e CSV salvati.
        """
        if self.df is None or self.df.empty:
            raise ValueError("Nessun dato disponibile. Eseguire prima _extract_keywords().")

        # Ridurre il numero di colori alla lunghezza effettiva dei dati
        n_colors = len(self.df)
        colors = self._generate_colorful_palette(n_colors)

        # Uso di seaborn per creare un grafico
        
        plt.figure(figsize=(10, 6))
        ax = sns.barplot(x='Parola', y='Frequenza', data=self.df, palette=colors[:n_colors])

        # Imposta l'orientamento delle etichette x
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
        
        # Imposta titolo e etichette assi
        ax.set_title(title)
        ax.set_xlabel('Parola Chiave')
        ax.set_ylabel('Numero di Occorrenze')

        # Salvataggio immagine
        plt.tight_layout()
        plt.savefig(plot_filename)
        
        # Salva il DataFrame come file CSV
        self.df.to_csv(csv_filename, index=False)

        return plot_filename, csv_filename


    def _print_keywords(self):
        """
        Stampa la lista delle parole chiave estratte.
        """
        if not self.top_keywords:
            print("Nessuna parola chiave estratta. Eseguire prima _extract_keywords().")
            return

        print("\nParole chiave più frequenti:")
        for word, count, lang in self.top_keywords:
            print(f"{word} ({lang}): {count}")

    def analyze_and_save(self, filepath, top_n=20, min_word_length=3, title='Frequenza delle Parole Chiave nei Documenti', max_documents=None):
        """
        Esegue estrazione e visualizzazione in un unico metodo, salvando l'immagine.

        Args:
            filepath (str): Percorso del file JSONL.
            top_n (int): Numero di parole da estrarre.
            min_word_length (int): Lunghezza minima delle parole.
            title (str): Titolo del grafico.
            filename (str): Nome del file di output dell'immagine.
            max_documents (int, opzionale): Numero massimo di documenti da elaborare.

        Returns:
            str: Percorso del file PNG salvato.
        """
        # Apre il file JSONL e lo processa riga per riga
        with open(filepath, 'r') as f:
            documents = (json.loads(line) for line in f)

            # Estrazione parole chiave
            self._extract_keywords(documents, top_n=top_n, min_word_length=min_word_length, max_documents=max_documents)

            # Salvataggio grafico
            return self._plot_and_save_histogram(title=title)
