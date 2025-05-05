import pandas as pd
import json
from datetime import datetime, timedelta
from URLtextProcessor import URLTextProcessor
from gdeltdoc import GdeltDoc, Filters

checkpoint_file = "raw_text_data/checkpoint.json"

countries = ['US', 'UK', 'IT']
themes = [
    "ELECTION", "ELECTION_FRAUD", "HEALTH_VACCINATION", "WB_635_PUBLIC_HEALTH", "TAX_FNCACT_TRAVEL_AGENT",
    "WB_723_PUBLIC_ADMINISTRATION", "TRANSPARENCY", "HEALTH_PANDEMIC", "GENERAL_HEALTH", "WB_696_PUBLIC_SECTOR_MANAGEMENT",
    "WB_1458_HEALTH_PROMOTION_AND_DISEASE_PREVENTION", "TOURISM",
    "TAX_FNCACT_JOURNALIST", "TAX_FNCACT_POLITICIANS", "WB_1765_CULTURE_HERITAGE_AND_SUSTAINABLE_TOURISM",
    "PUBLIC_TRANSPORT", "WB_1024_PUBLIC_INTERNATIONAL_LAW", "EPU_POLICY_LAW", "MEDICAL", "EDUCATION",
    "WB_1893_TAX_LAW", "WB_938_MEDIATION", "GENERAL_GOVERNMENT", "WB_621_HEALTH_NUTRITION_AND_POPULATION", "TAX_DISEASE",
    "WB_831_GOVERNANCE", "GOV_REFORM", "WB_2085_PUBLIC_SECTOR_DOWNSIZING"
]

tone = [">0", ">5", ">10", ">15", ">20", ">25"]
limit = 100
mode = 'artlist'
order = 'toneabsasc'

#read the checkpoint file
with open(checkpoint_file, "r") as f:
    data = json.load(f)
    
#YYYYMMDDHHMMSS
start_timestamp = data.get("timeend") if data else (datetime.now() - timedelta(days=1)).strftime("%Y%m%d%H%M%S")
end_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

def generate_timestamps(start: str, end: str):
    timestamps = []
    dt_start = datetime.strptime(start, "%Y%m%d%H%M%S")
    dt_end = datetime.strptime(end, "%Y%m%d%H%M%S")
    
    while dt_start <= dt_end:
        timestamps.append(dt_start.strftime("%Y%m%d%H%M%S"))
        dt_start += timedelta(hours=8)
    
    return timestamps

sequence = generate_timestamps(start_timestamp, end_timestamp)
print(f"Expected API calls: {len(sequence) * len(countries) * len(themes) * len(tone)}")
print(f"Maximum documents if each result is unique and limit is {limit}: {len(sequence) * len(countries) * len(themes) * len(tone) * limit}")

gd = GdeltDoc()

#Loop
for i in range(len(sequence) - 1):
    timestart = sequence[i]
    timeend = sequence[i + 1]
    chunck=pd.DataFrame()
    for country in countries:
        for theme in themes:
            for tone_value in tone:
                
                filters = Filters(
                    start_date=timestart,
                    end_date=timeend,
                    country=country,
                    theme=theme,
                    num_records=limit,
                    tone_abs=tone_value,
                    mode=mode,
                    sort=order
                )
                
                articles = gd.article_search(filters)
                if not articles.empty:
                    link_extractor = URLTextProcessor()
                    extracted_content = pd.DataFrame(link_extractor.process_links_and_extract_text(articles))
                    
                    chunck=pd.concat([chunck, extracted_content], ignore_index=True)
                    chunck.drop_duplicates(subset=["url"]).drop_duplicates(subset=["title"])

    with open("raw_text_data/checkpoint.json", "w") as f:
        json.dump({"timestart": timestart,"timeend": timeend}, f, indent=4)
    print(f"Checkpoint reached: {timestart} - {timeend} completed.")
    chunck.to_json(f"raw_text_data/{timestart}_{timeend}.json", orient='records', lines=False, force_ascii=False, indent=4)


print("Processo completato e dati salvati con successo!")
