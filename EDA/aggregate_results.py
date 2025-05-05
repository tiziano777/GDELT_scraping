import os
import re
import json
from typing import List, Dict, Generator, Any

# --- Configurazioni ---
ALLOWED_LANGUAGES = {'English', 'Italian'}
INPUT_DIRECTORY = '../raw_text_data'
OUTPUT_FILE = './articles.jsonl'
FILENAME_REGEX = re.compile(r'^\d{14}_\d{14}\.json$')

# --- Funzioni Modulari ---

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

# --- Entry Point ---

if __name__ == '__main__':
    process_directory(INPUT_DIRECTORY, OUTPUT_FILE)
    
