#Setting up a pipeline for the task: #english article -> machine translated -> stanford nlp -> multiple sentiment scores

import requests
import json
import sys
import wikipedia
from stanfordcorenlp import StanfordCoreNLP
from polyglot.text import Text, Word
from googletrans import Translator
import subprocess

languagelist = ['en', 'zh', 'es', 'de' ] #'ru', 'ja'  hold off on these til we have integrated support for other models
# nlp = StanfordCoreNLP('http://localhost', port=7000)


def main():
	#Goes through space ddelimited list of full article links and puts them through the pipeline.
	#if using a dataset of articles,
	if len(sys.argv) > 1:
		for arg in sys.argv[1:]:

			article = fetch_article(arg)

			# stanford_corenlp(article)

			perform_ne(article)
			for lang in article:
				print(lang)
				print(article[lang]['ner'])
			#sentiment(article)
			# translated = translate(article)
			# sentiments = stanford_corenlp(translated)
			# print(arg)
			# print(sentiments)

	else:
		build_dictionary()
		print("Please enter at least one Wikipedia link to analyse.")

def show_named_entities():
	overall_entities = {}
	with open('prospectiveTopics.txt', 'r') as topics:
		for line in topics:
			fetch_article(line)

def perform_ne(article):
	desired_classes = ['PERSON', 'LOCATION', 'ORGANIZATION', 'CITY', 'STATE_OR_PROVINCE', 'COUNTRY', 'NATIONALITY', 'RELIGION', 'IDEOLOGY']

	for lang in article:
		ne_freqs = {}
		with StanfordCoreNLP('./corenlp/stanford-corenlp-full-2018-10-05', lang=lang, memory='8g') as nlp:
			if lang == 'zh':
				text = Text(article[lang]['content'], hint_language_code='zh')
				sentences = [sentence.string for sentence in text.sentences]
			else:
				sentences = article[lang]['content'].split(". ")	
			for sentence in sentences:
				try:
					# print(sentence)
					entities = nlp.ner(sentence)
					for entity in entities:
						if entity[1] in desired_classes:
							try:
								ne_freqs[entity] += 1
							except KeyError:
								ne_freqs[entity] = 1
				except Exception as e:
					print("error on \"" + sentence + "\"")
			# except json.decode.JSONDecodeError as e:
			# 	print("error on \"" + sentence + "\"")
			# 	print(e)
			article[lang]['ner'] = sorted(ne_freqs.items(), reverse=True, key=lambda w: w[1])


def sentiment(article):
	with open('dictionary.json', 'r') as file:
		dictionary = json.loads(file.read())
	english_text = article['en']['content'].split(". ")
	for lang in article:
		print(lang)
		if lang != 'en':
			if lang == 'zh':
				text = Text(article[lang]['content'], hint_language_code='zh')
				sentences = [sentence.string for sentence in text.sentences]
				#sentences = article[lang]['content'].split("。")
			else:
				continue
				sentences = article[lang]['content'].split(". ")
			selected = []
			for sentence in sentences:
				words = [] #build list of all dict words that appear in any sentence
				for k, v in dictionary[lang].items():
					if v in sentence:
						words.append(k)
				if len(words) > 0:
					selected.append((words, sentence))

			#translate by batch
			translator = Translator()
			strings = [w[1] for w in selected]
			if lang == 'zh':
				langcode = 'zh-CN'
			else:
				langcode = lang
			translations = translator.translate(strings, dest='en', src=langcode)
			translated = []
			for i in range(len(strings)):
				translated.append((selected[i][0], translations[i].text))

			#analyze sentiment
			with StanfordCoreNLP('/Users/xiangezhang/corenlp/stanford-corenlp-full-2018-10-05', lang='en', memory='8g') as nlp:
				for sentence in translated:
					results = nlp.sentiment(sentence[1])
					print(sentence)
					print(results['sentences'][0]['sentimentDistribution'])



		elif lang == 'en':
			#repeat on each article for the english keys
			eng_selected = []
			for sentence in english_text:
				words = []
				for k, v in dictionary['de'].items():
					if k in sentence:
						words.append(k)
				if len(words) > 0:
					eng_selected.append((words, sentence))
			sentiment_agg = {}
			print(len(english_text))
			print(len(eng_selected))
			with StanfordCoreNLP('/Users/xiangezhang/corenlp/stanford-corenlp-full-2018-10-05', lang=lang, memory='8g') as nlp:
				for sentence in eng_selected:
					results = nlp.sentiment(sentence[1])
					print(sentence)
					print(results['sentences'][0]['sentimentDistribution'])


def sentiment2():
	dictfiles = {'de':'deDict.json', 'ru':'ruDict.json','ja':'jaDict.json','es':'esDict.json','zh':'zhDict.json','en':'enDict.json'}
	sentence_dict = {}
	for lang in dictfiles:
		with open(dictfiles[lang], 'r') as file:
			sentence_dict[lang] = json.loads(file.read())

	with open('mergeDict.json', 'r') as file:
		mergeDict = json.loads(file.read())

	subset = {k:v for k,v in mergeDict.items() if len(v) == 6}
	print(len(subset))
	subset = {k:v for k,v in mergeDict.items() if len(v) >= 5}
	
	print(len(subset))

#given a link to a wikipedia article,
#will return the text content of that article in a dictionary keyed by its page title
def fetch_article(link):
	ind = link.index("/wiki/")
	title = link[ind+6:]
	print(title)
	wikipedia.set_lang('en')
	page = wikipedia.page(title)
	content = page.content
	#Divide at earliest point to cut down on unnecessary characters
	try:
		content = content[:content.index("== See also ==")]
	except ValueError:
		try:
			content = content[:content.index("== References ==")]
		except ValueError:
			print("no references might be other language")

	print("Num characters in article: "+ str(len(content)))

	retdict = {'en': {'title' : title, 'content' : content}}

	#get languages this article is in
	param_dict = {"action":"query",
					"prop":"langlinks",
					"format":"json",
					"redirects":1,
					'lllimit': 300,
					"titles":title}
	req = requests.get("https://en.wikipedia.org/w/api.php", params=param_dict)
	results = req.json()
	# print(results)
	# print(req.url)


	#retrieve foriegn language versions and put them in the dictionary
	for pageid, info in results['query']['pages'].items():
		print(info)
		for lang in info['langlinks']:
			print(lang)
			if lang['lang'] in languagelist: #only get chinese, german, spanish
				wikipedia.set_lang(lang['lang'])
				page = wikipedia.page(lang['*'])
				content = page.content
				retdict[lang['lang']] = {'title': lang['*'], 'content': content}

	#clean the article text, take out headers and newlines
	for lang in retdict:
		content = retdict[lang]['content']
		ind = 0


		while(True):
			first = content.find("===")
			if first == -1:
				break
			pair = content.find("===", first+1)
			content = content[:first] + content[pair+3:]
		while(True):
			first = content.find("==")
			if first == -1:
				break
			pair = content.find("==", first+1)
			content = content[:first] + content[pair+2:]


		content = content.replace("\n", "")

		retdict[lang]['content'] == content


	return retdict


def build_dictionary():
	ne_dict = {}
	for lang in languagelist:
		ne_dict[lang] = {}
	# with open('wiki_articles.txt', 'r') as file:
	# 	for line in file:
	# 		if line.strip() == "" or line[0]=='#':
	# 			continue
	# 		line = line.split(", ")
	# 		article = fetch_article(line[1].strip())
	# 		perform_ne(article)

	# 		for lang in article:
	# 			for ne in article[lang]['ner']:
	# 				if ne[0][0] in ne_dict[lang]:
	# 					ne_dict[lang][ne[0][0]] += ne[1]
	# 				else:
	# 					ne_dict[lang][ne[0][0]] = ne[1]
	# 		with open('all_entities.json', 'w') as file:
	# 			file.write(json.dumps(ne_dict))

	# then load and use same file to try and find intersection of terms
	with open('all_entities.json', 'r') as file:
		ne_dict = json.loads(file.read())

	translator = Translator()
	translated = {}
	for lang in languagelist:
		translated[lang] = {}
	for lang in ne_dict:
		if lang == 'en':
			for k, v in ne_dict[lang].items():
				if k in translated[lang]:
					pass
				else:
					translated[lang][k] = k
		else:
			if lang == 'zh':
				langcode = 'zh-CN'
			else:
				langcode = lang
			
			for k, v in ne_dict[lang].items():
				if v > 5:
					try:
						translation = translator.translate(k, dest='en', src=langcode).text
					except Exception:

					if translation in translated[lang]:
						pass
					else:
						translated[lang][translation] = k
	common_entities = {}
	for lang in translated:
		for k, v in translated[lang].items():
			if k in common_entities:
				common_entities[k][lang] = v
			else:
				common_entities[k] = {}
				common_entities[k][lang] = v
	sorted_common_entities = sorted(common_entities.items(), key = lambda w: len(w[1]), reverse=True)
	print(sorted_common_entities)
	with open('common_entities.json', 'w') as file:
		file.write(json.dumps(sorted_common_entities))




#input: dictionary with {'en:english article text as string, 'zh': chinese article text} etc etc
#output: dictionary with keys being various two-letter language codes and items being the translated article text
def translate(sentence):
		data = {"q":sentence,
				"target":"en",
				"source":'de',
				"format":"text",
				"key":""}
		req = requests.post("https://translation.googleapis.com", data=data)
		return req



def stanford_corenlp(article):
	for lang in article:
		with StanfordCoreNLP('corenlp/stanford-corenlp-full-2018-10-05', lang=lang, memory='8g') as nlp:
			print(article[lang]['content'])
			article[lang]['ner'] = nlp.ner(article[lang]['content'])

#takes in a classification vector of dim 5 and returns a double that attempts to collate those 5 confidences into a score denoting overall positive or negative sentiment
def collate_sentiment_score(scores):
	return -2*scores[0] - scores[1] + scores[3] + 2*scores[4]

def calculate_controversy(dictionary ):
	pass

if __name__ == '__main__':
	main()
