from EDA.wordFrequence.word_frequence import ItalianEnglishWordFrequency

input_file_path = '/home/tiziano/GDELT_scraping/EDA/articles.jsonl'
analyzer = ItalianEnglishWordFrequency()

analyzer.analyze_and_save(filepath=input_file_path,top_n=1000)
