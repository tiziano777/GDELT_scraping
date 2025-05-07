import json
import spacy
import re

# === CONFIGURAZIONE ===
INPUT_FILE = "articles_deduplicated.jsonl"
THRESHOLD = 20

OUTPUT_FILES = {
    'elezioni': "topic/election_articles.jsonl",
    'vaccini': "topic/vax_articles.jsonl",
    #'pubblica_amministrazione': "topic/PA_articles.jsonl"
}

LANGUAGES = {'italian', 'english'}
BAD_DOMAINS = ["https://www.zazoom.it/"]



# === CARICAMENTO MODELLI spaCy ===
nlp_it = spacy.load("it_core_news_sm", disable=["ner"])
nlp_en = spacy.load("en_core_web_sm", disable=["ner"])

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

# === FUNZIONI ===

def get_doc_language(doc):
    """Restituisce la lingua del documento (italiano o inglese)."""
    return doc.get("language", "").lower()

def lemmatize(text, lang):
    """Lemmatizza il testo in base alla lingua."""
    nlp = nlp_it if lang == "italian" else nlp_en
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

def should_exclude_document(doc):
    """Verifica se il dominio del link (o una parte dell'URL) è uno dei domini da scartare."""
    link = doc.get('link', '')
    for domain in BAD_DOMAINS:
        # Usa regex per il matching parziale del dominio nel link
        if re.search(re.escape(domain), link):
            return True
    return False

# === MAIN ===

def main():
    keyword_sets = create_keyword_sets()

    # Creazione dei file di output in modalità scrittura
    output_writers = {cat: open(fname, 'w', encoding='utf-8') for cat, fname in OUTPUT_FILES.items()}
    total, relevant = 0, 0

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            total += 1
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Controllo della lingua
            lang = get_doc_language(doc)
            if lang not in LANGUAGES:
                continue

            # Filtro in base al link
            if should_exclude_document(doc):
                continue

            # Lemmatizzazione del testo
            full_text = (doc.get("title", "") + " " + doc.get("text", "")).strip()
            lemmas = lemmatize(full_text, lang)
            scores = score_document(lemmas, keyword_sets)

            # Categoria con il punteggio massimo
            best_topic = max(scores, key=scores.get)
            if scores[best_topic] >= THRESHOLD:
                json.dump(doc, output_writers[best_topic], ensure_ascii=False)
                output_writers[best_topic].write("\n")
                relevant += 1

    # Chiudere i file di output
    for writer in output_writers.values():
        writer.close()

    print(f"Totale documenti processati: {total}")
    print(f"Documenti rilevanti salvati: {relevant}")
    for cat, file in OUTPUT_FILES.items():
        print(f"{cat}: file -> {file}")

if __name__ == "__main__":
    main()