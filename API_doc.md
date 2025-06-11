# Servizio API GDELT

## Scopo del Modulo

Il modulo presentato fornisce un'interfaccia Python per interagire con il servizio GDELT (Global Database of Events, Language, and Tone) 2.0 API, in particolare con l'endpoint [https://api.gdeltproject.org/api/v2/doc/doc](https://api.gdeltproject.org/api/v2/doc/doc). Esso è progettato per supportare:

* **Ricerca di articoli** mediante filtri semantici e metadati.
* **Analisi temporale** della copertura mediatica tramite differenti modalità di aggregazione (timeline).

Il modulo si compone di due entità principali:

1. `Filters`: costruisce in modo robusto e componibile i parametri di query.
2. `GdeltDoc`: client API che invia richieste e restituisce i risultati in formato `pandas.DataFrame`.

---

## Funzionalità Principali

### 1. Costruzione della Query (Classe `Filters`)

La classe `Filters` incapsula la logica di costruzione dei parametri di query, assicurando compatibilità con le specifiche dell'API. I parametri accettati permettono una filtrazione avanzata sui contenuti testuali e metadati associati agli articoli di notizie.

#### Input

* `start_date`, `end_date`: date di inizio/fine in formato `YYYY-MM-DD`.
* `timespan`: alternativa al range di date; es. `15min`, `24h`, `30d`.
* `keyword`: lista o stringa, utilizzata per la ricerca nei testi degli articoli.
* `domain`, `domain_exact`: dominio (parziale o esatto) della fonte.
* `near`, `repeat`: vincoli sintattici su prossimità o ripetizione delle parole nel testo.
* `country`: codice FIPS del paese della fonte.
* `theme`: temi GKG.
* `tone`, `tone_abs`: tonalità media dei contenuti.
* `num_records`: numero massimo di articoli da restituire (max 250).

#### Output

* `query_string`: stringa finale di query, da passare al client `GdeltDoc`.

---

### 2. Client API (Classe `GdeltDoc`)

Il client `GdeltDoc` fornisce metodi di accesso ai dati:

#### a. `article_search(filters: Filters) -> pd.DataFrame`

Esegue una richiesta all'API con modalità `artlist` per recuperare una lista di articoli.

**Output**: `DataFrame` con colonne: `url`, `url_mobile`, `title`, `seendate`, `socialimage`, `domain`, `language`, `sourcecountry`.

#### b. `timeline_search(mode: str, filters: Filters) -> pd.DataFrame`

Esegue una richiesta all'API per aggregazioni temporali.

**Modalità supportate**:

* `timelinevol`: percentuale della copertura mediatica.
* `timelinevolraw`: volume assoluto.
* `timelinetone`: media della tonalità.
* `timelinelang`: aggregazione per lingua.
* `timelinesourcecountry`: aggregazione per paese.

**Output**: `DataFrame` con colonna `datetime` e una o più colonne per serie temporali.

---

## Output e Integrazione Applicativa

I risultati sono restituiti come oggetti `pandas.DataFrame`, facilitando la successiva analisi, visualizzazione o salvataggio.

### Integrazione tipica

```python
from gdeltdoc import GdeltDoc, Filters

filters = Filters(
    keyword=["climate change", "carbon emissions"],
    start_date="2023-01-01",
    end_date="2023-02-01",
    country="US",
    theme="ENV_CLIMATE"
)

gd = GdeltDoc()
articles_df = gd.article_search(filters)
timeline_df = gd.timeline_search("timelinevol", filters)
```

---

## Riutilizzo del Modulo

Il modulo è pensato per essere riutilizzabile in contesti come:

* Dashboard di monitoraggio media.
* Sistemi di alerting su specifici temi/paesi.
* Studi longitudinali su temi e sentiment.

La separazione tra definizione dei filtri e invio delle richieste consente di costruire pipelines dati modulari e scalabili.

Degli esempi di integrazione sono presenti nella cartella `src/` con funzioni di scraping automatico, dashboard per custom research (manuale e per similarity).

`src/URLtextProcessor.py` è la funzionalità cardine del processo di estrazione, GDELT estrae solo i campi titolo, url, data, e country, per il contenuto testuale degli articoli presenti nei link, è necessario l'applicazione della funzione `process_links_save_text_save_link(self, df)` e `fetch_and_process_single_url(self, url: str)`
