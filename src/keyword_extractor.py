import spacy
from yake import KeywordExtractor
import re

# Carica i modelli spaCy per italiano e inglese
# Assicurati di averli installati:
# python -m spacy download it_core_news_sm
# python -m spacy download en_core_web_sm

try:
    nlp_it = spacy.load("it_core_news_sm")
except OSError:
    print("Download it_core_news_sm model for spaCy: python -m spacy download it_core_news_sm")
    exit()

try:
    nlp_en = spacy.load("en_core_web_sm")
except OSError:
    print("Download en_core_web_sm model for spaCy: python -m spacy download en_core_web_sm")
    exit()

def get_nlp_pipeline(lang: str):
    if lang.lower() == 'it':
        return nlp_it
    elif lang.lower() == 'en':
        return nlp_en
    else:
        raise ValueError("Lingua non supportata. Scegli tra 'it' o 'en'.")

def clean_text(text: str) -> str:
    """Rimuove caratteri speciali e spazi extra."""
    text = re.sub(r'\s+', ' ', text) # Rimuove spazi multipli
    text = re.sub(r'[^\w\s]', '', text) # Rimuove caratteri non alfanumerici (mantiene spazi)
    return text.strip()

def extract_keywords_yake(text: str, language: str, num_keywords: int = 10, dedup_lim: float = 0.9) -> list:
    """
    Estrae keyword da un testo usando YAKE.
    :param text: Il testo da cui estrarre le keyword.
    :param language: La lingua del testo ('it' o 'en').
    :param num_keywords: Numero massimo di keyword da estrarre.
    :param dedup_lim: Limite di deduplicazione per evitare keyword troppo simili (0.0 a 1.0).
    :return: Una lista di stringhe rappresentanti le keyword.
    """
    if not text:
        return []

    # Pulizia del testo prima dell'estrazione
    cleaned_text = clean_text(text)

    # Inizializza YAKE! con le impostazioni della lingua
    # max_ngram_size: dimensione massima dei n-grammi (parole consecutive) per le keyword
    # stopwords: utilizza le stopwords di NLTK, o puoi passare una lista personalizzata
    # dedupLim: limite di deduplicazione per evitare keyword molto simili
    # dedupFunc: funzione per la deduplicazione (frequenza o similarità)
    # n_keywords: numero massimo di keyword da estrarre
    kw_extractor = KeywordExtractor(lan=language,
                                    n=1, # n-gram size
                                    dedupLim=dedup_lim,
                                    top=num_keywords,
                                    features=None) # Disabilita funzionalità aggiuntive per semplicità

    keywords_with_score = kw_extractor.extract_keywords(cleaned_text)
    
    # Restituisce solo le stringhe delle keyword, ordinate per punteggio (YAKE restituisce già le migliori)
    return [kw for kw, score in keywords_with_score]

def get_keywords_from_article(article_dict: dict, num_keywords: int = 10) -> list:
    """
    Estrae keyword da un dizionario articolo (url, title, lang, text).
    Utilizza il titolo e poi il testo per un'estrazione più completa.
    :param article_dict: Il dizionario contenente i dati dell'articolo.
    :param num_keywords: Numero massimo di keyword da estrarre.
    :return: Una lista di keyword.
    """
    title = article_dict.get('title', '')
    text = article_dict.get('text', '')
    lang = article_dict.get('lang', 'en').lower()

    all_keywords = set()

    # Estrai keyword dal titolo (spesso molto rilevante)
    if title:
        title_keywords = extract_keywords_yake(title, lang, num_keywords=min(num_keywords, 5)) # Meno keyword dal titolo
        all_keywords.update(title_keywords)

    # Estrai keyword dal testo (più complete)
    if text:
        text_keywords = extract_keywords_yake(text, lang, num_keywords=num_keywords)
        all_keywords.update(text_keywords)
    
    # Converti in lista e filtra keyword troppo corte o non significative
    final_keywords = [kw for kw in list(all_keywords) if len(kw) > 2 and not kw.isdigit()] # Evita numeri puri
    
    # Rimuovi eventuali duplicati (anche se set dovrebbe gestirli) e limiti il numero
    return list(sorted(list(set(final_keywords)), key=len, reverse=True))[:num_keywords]

