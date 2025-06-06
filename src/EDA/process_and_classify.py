# --- Import ---
import os
import re
import json
import spacy
from typing import List, Dict, Generator, Any

# --- Config: Preprocessing ---
ALLOWED_LANGUAGES = {'English', 'Italian'}
INPUT_DIRECTORY = '../raw_text_data'
OUTPUT_FILE = './articles.jsonl'
DEDUPLICATED_OUTPUT_FILE = './articles_deduplicated.jsonl'
FILENAME_REGEX = re.compile(r'^\d{14}_\d{14}\.json$')

# --- Config: Classification ---
THRESHOLD = 20
OUTPUT_FILES = {
    'elezioni': "topic/election_articles.jsonl",
    'vaccini': "topic/vax_articles.jsonl"
}
LANGUAGES = {'italian', 'english'}
BAD_DOMAINS = ["https://www.zazoom.it/"]

def should_exclude_document(doc):
    """Verifica se il dominio del link (o una parte dell'URL) è uno dei domini da scartare."""
    link = doc.get('url', '')
    for domain in BAD_DOMAINS:
        # Usa regex per il matching parziale del dominio nel link
        if domain in link:
            return True
    return False


# --- spaCy Models ---
nlp_it = spacy.load("it_core_news_sm", disable=["ner"])
nlp_en = spacy.load("en_core_web_sm", disable=["ner"])

# --- Funzioni Preprocessing  ---

def list_valid_files(directory: str) -> List[str]:
    """
    Restituisce tutti i percorsi di file validi nella directory che rispettano il pattern.
    """
    return [
        os.path.join(directory, filename)
        for filename in os.listdir(directory)
        if FILENAME_REGEX.match(filename)
    ]

def read_documents(filepath: str) -> Generator[Dict[str, Any], None, None]:
    """
    Generatore che itera sui documenti JSON all'interno di un file.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"Il file {filepath} non contiene una lista di documenti.")
        for document in data:
            yield document

def is_valid_language(document: Dict[str, Any]) -> bool:
    """
    Controlla se il documento ha un campo 'language' ammesso.
    """
    language = document.get('language')
    return language in ALLOWED_LANGUAGES

def preprocess_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Esegue preprocessing su un documento (attualmente identità).
    """
    # Qui si possono aggiungere trasformazioni future
    return document

def save_documents(documents: List[Dict[str, Any]], output_path: str) -> None:
    """
    Salva una lista di documenti nel file di output in formato JSONL.
    Assicurandosi che venga aperto in modalità append per non sovrascrivere i dati precedenti.
    """
    # Creiamo il file se non esiste, ma non lo sovrascriviamo mai
    file_exists = os.path.exists(output_path)
    with open(output_path, 'a', encoding='utf-8') as f:
        # Se il file non esiste ancora, scriviamo l'intestazione o solo i dati senza intestazione
        if not file_exists:
            pass  # non è necessario scrivere nulla, i dati vengono solo appesi.
        for doc in documents:
            json_line = json.dumps(doc, ensure_ascii=False)
            f.write(json_line + '\n')

def process_directory(input_dir: str, output_file: str) -> None:
    """
    Processo principale: legge, filtra, preprocessa e scrive.
    """
    files = list_valid_files(input_dir)
    for filepath in files:
        valid_documents = []
        for document in read_documents(filepath):
            if is_valid_language(document):
                processed_document = preprocess_document(document)
                valid_documents.append(processed_document)
        save_documents(valid_documents, output_file)
        os.remove(filepath)

def deduplicate_jsonl(input_path: str, output_path: str):
    seen_urls = set()
    seen_titles = set()
    unique_entries = []

    with open(input_path, 'r', encoding='utf-8') as infile:
        for line in infile:
            try:
                entry = json.loads(line)
                url = entry.get("url")
                title = entry.get("title")

                # Se già visto l'url o il title, salta
                if url in seen_urls or title in seen_titles or should_exclude_document(entry):
                    continue

                seen_urls.add(url)
                seen_titles.add(title)
                unique_entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"Errore di parsing JSON: {e}")

    with open(output_path, 'a', encoding='utf-8') as outfile:
        for entry in unique_entries:
            json.dump(entry, outfile, ensure_ascii=False)
            outfile.write('\n')

    print(f"Rimossi duplicati. Totale articoli unici: {len(unique_entries)}")


# --- Funzioni Classificazione (seconda parte) ---

def create_keyword_sets():
    """
    Crea insiemi di parole chiave per ciascuna categoria (italiano e inglese).
    
    Returns:
        dizionario con categorie e relative parole chiave suddivise in primarie e secondarie
    """
    return {
    'vaccini': {
        'primarie': set([
            'vaccin', 'immuniz', 'pandem', 'covid', 'dos', 'richiam', 'campagn vaccin',
            'vaccine', 'immuniz', 'pandem', 'inocul', 'medical', 'health', 'hospital', 'vax',
            'vaccine campaign', 'immunization', 'vaccine distribution', 'covid vaccine',
            'vaccine rollout', 'vaccine dose', 'covid-19 vaccine', 'vaccination center',
            'flu vaccine', 'inoculation', 'vaccine trial', 'booster dose', 'vaccination program',
            'coronavirus vaccine', 'immunization program', 'vaccination clinic', 'epidemic control'
        ]),
        'secondarie': set([
            'virus', 'epidem', 'contag', 'protezion', 'asl', 'ospedal', 'medic',
            'virus', 'epidem', 'contag', 'protect', 'hospit', 'medic',
            'disease', 'infection', 'pandemic', 'healthcare', 'public health', 'epidemiology',
            'quarantine', 'vaccination effort', 'health policy', 'virus transmission', 'health system'
        ])
    },
    'elezioni': {
        'primarie': set([
            'elezion', 'vot', 'votazion', 'candidat', 'segg', 'elettor', 'elect', 'ballot',
            'poll station', 'voter', 'president', 'govern', 'partit', 'coalizion', 'campagn',
            'votant', 'elettoral', 'deputat', 'senator', 'parlament', 'candidato', 'sindac',
            'programma', 'politic', 'riform', 'campagna elettoral', 'processo elettoral',
            'legge elettorale', 'coalizione', 'opposizion', 'concorrenz', 'contest', 'resultat',
            'programma elettoral', 'riunion', 'discuss', 'result', 'opposit', 'riforma',
            'governo', 'ballottaggio', 'elettori', 'votazione', 'elettorato', 'mandat', 'seggeria',
            'voto elettronico', 'regolament', 'parlamento', 'elezioni politiche',
            'voto anticipato', 'scrutinio', 'voto per corrispondenza', 'sezione elettorale',
            'voto all\'estero', 'voto di preferenza', 'voto disgiunto', 'voto segreto',
            'voto elettronico', 'voto assistito', 'voto per delega', 'voto per corrispondenza',
            'election day', 'polls', 'ballot box', 'political campaign', 'election reform', 
            'candidate', 'voting rights', 'ballot papers', 'referendum', 'voter registration', 
            'electoral system', 'election commission', 'political debate', 'election turnout', 'vote count'
        ]),
        'secondarie': set([
            'politic', 'partit', 'elettoral', 'mandat', 'votant', 'assemble', 'regolament', 
            'diritt', 'system elettoral', 'coalizion', 'lobby', 'popolazion', 'responsabil',
            'popul', 'candidacy', 'allianc', 'poter', 'scelt', 'choic', 'competit', 'context',
            'represent', 'elector', 'elector program', 'party', 'voter turnout', 'results',
            'candidate', 'parlamento', 'referendum', 'political party', 'campaign',
            'political reform', 'election campaign', 'vote', 'political system', 'candidate profile',
            'political analysis', 'political strategy', 'political debate', 'political agenda',
            'political discourse', 'political communication', 'political engagement', 'political activism',
            'political participation', 'political representation', 'political influence', 'political power',
            'political landscape', 'political climate', 'political opinion', 'political ideology',
            'political spectrum', 'political polarization', 'political discourse analysis', 'political rhetoric',
            'political campaign strategy', 'political marketing', 'political advertising', 'political messaging',
            'political branding', 'political communication strategy', 'political public relations',
            'political polling', 'political survey', 'political research', 'political analysis tools',
            'politician', 'election results', 'campaign trail', 'political party leader', 'electoral college',
            'senate election', 'house of representatives', 'voting machines', 'political endorsement', 'voter suppression',
            'polling station', 'ballot initiative', 'polling data', 'electoral district'
        ])
    }
}
'''
    'pubblica_amministrazione': {
        'primarie': set([
            'pubbl amministr', 'comun', 'region', 'provinci', 'minister', 'ent pubblic',
            'public administr', 'municip', 'region', 'provinc', 'ministr', 'public ent',
            'government', 'local government', 'state administration', 'public sector', 'public office',
            'public service', 'administration', 'city hall', 'ministry', 'public affairs',
            'municipal services', 'state government', 'regional government', 'public policy',
            'public institutions', 'policy maker', 'governmental body', 'bureaucracy'
        ]),
        'secondarie': set([
            'cittadin', 'serviz', 'proced', 'digitalizzazion', 'burocr',
            'citizen', 'servic', 'procedur', 'digitiz', 'bureaucraci', 'govern',
            'government services', 'public services', 'civil service', 'public relations',
            'e-government', 'bureaucratic process', 'administrative procedure', 'public institutions',
            'citizenship', 'social services', 'government reform', 'public management', 'civil rights',
            'digital governance', 'e-government services', 'public administration reform'
        ])
    },
'''

def get_doc_language(doc):
    """Restituisce la lingua del documento (italiano o inglese)."""
    return doc.get("language", "").lower()

def lemmatize(text, lang):
    """Lemmatizza il testo in base alla lingua."""
    nlp = nlp_it if lang == "italian" else nlp_en
    if len(text) > 1000000:
        return []
    
    doc = nlp(text)
    return [token.lemma_.lower() for token in doc if not token.is_stop and token.is_alpha]

def score_document(lemmas, keyword_sets):
    """Calcola il punteggio del documento in base alle parole chiave."""
    scores = {}
    for category, keywords in keyword_sets.items():
        primary = sum(1 for kw in keywords['primarie'] if kw in lemmas)
        secondary = sum(1 for kw in keywords['secondarie'] if kw in lemmas)
        score = 10 * primary + 3 * secondary
        scores[category] = score
    return scores


def classify_documents():
    keyword_sets = create_keyword_sets()
    output_writers = {cat: open(fname, 'a', encoding='utf-8') for cat, fname in OUTPUT_FILES.items()}
    total, relevant = 0, 0

    with open(DEDUPLICATED_OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            total += 1
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue

            lang = get_doc_language(doc)
            if lang not in LANGUAGES:
                continue
            if should_exclude_document(doc):
                continue

            full_text = (doc.get("title", "") + " " + doc.get("text", "")).strip()
            lemmas = lemmatize(full_text, lang)
            scores = score_document(lemmas, keyword_sets)
            best_topic = max(scores, key=scores.get)
            if scores[best_topic] >= THRESHOLD:
                json.dump(doc, output_writers[best_topic], ensure_ascii=False)
                output_writers[best_topic].write("\n")
                relevant += 1

    for writer in output_writers.values():
        writer.close()

    print(f"Totale documenti processati: {total}")
    print(f"Documenti rilevanti salvati: {relevant}")
    for cat, file in OUTPUT_FILES.items():
        print(f"{cat}: file -> {file}")

# --- Entry Point ---
if __name__ == '__main__':
    process_directory(INPUT_DIRECTORY, OUTPUT_FILE)
    deduplicate_jsonl(OUTPUT_FILE, DEDUPLICATED_OUTPUT_FILE)
    classify_documents()
