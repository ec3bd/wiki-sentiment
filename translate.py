#Setting up a pipeline for the task: #english article -> machine translated -> stanford nlp -> multiple sentiment scores

import requests
import json
import sys
import wikipedia
from stanfordcorenlp import StanfordCoreNLP
from googletrans import Translator
import subprocess
import json

languagelist = ['en', 'zh', 'es', 'de' ] #'ru', 'ja'  hold off on these til we have integrated support for other models


def main():
	#Goes through space ddelimited list of full article links and puts them through the pipeline.
	#if using a dataset of articles,
	if len(sys.argv) > 1:
		for arg in sys.argv[1:]:

			article = fetch_article(arg)

			# stanford_corenlp(article)

			perform_ne(article)
			# for lang in article:
			# 	print(lang)
			print(article['zh']['ner'])
			# translated = translate(article)
			# sentiments = stanford_corenlp(translated)
			# print(arg)
			# print(sentiments)

	else:
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
			sentences = article[lang]['content'].split(". ")
			for sentence in sentences:
				try:
					entities = nlp.ner(sentence)
					for entity in entities:
						if entity[1] in desired_classes:
							try:
								ne_freqs[entity] += 1
							except KeyError:
								ne_freqs[entity] = 1
				except json.decoder.JSONDecoderError:
					print("error on \"" + sentence + "\"")

		article[lang]['ner'] = sorted(ne_freqs.items(), reverse=True, key=lambda w: w[1])


def sentiment(article):
	with open('dictionary.json', 'r') as file:
		dictionary = json.loads(file.read())
	english_text = article['en']['content'].split(". ")
	for lang in article:
		if lang != 'en':
			sentences = article[lang]['content'].split(". ")
			selected = []
			for sentence in sentences:
				words = [] #build list of all dict words that appear in any sentence
				for k, v in dictionary[lang].items():
					if v in sentence:
						words.append(k)
				if len(words) > 0:
					selected.append((words, sentence))
			

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
			with StanfordCoreNLP('./corenlp/stanford-corenlp-full-2018-10-05', lang=lang, memory='8g') as nlp:
				for sentence in eng_selected:
					results = nlp.sentiment(sentence[1])
					print(sentence)
					print(results['sentences'][0]['sentimentDistribution'])


#given a link to a wikipedia article,
#will return the text content of that article in a dictionary keyed by its page title
def fetch_article(link):
	ind = link.index("/wiki/")
	title = link[ind+6:]
	print(title)
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
					'lllimit': 200,
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

#input: dictionary with {'en:english article text as string, 'zh': chinese article text} etc etc
#output: dictionary with keys being various two-letter language codes and items being the translated article text
def translate(sentence):
		data = {"q":sentence,
				"target":"en",
				"source":'de',
				"format":"text",
				"key":"AIzaSyADeq50tLy0JgwXsMgxeOe7ai-FCfy6A_A"}
		req = requests.post("https://translation.googleapis.com", data=data)
		return req


def stanford_corenlp(article):
		if lang == 'en':
			with StanfordCoreNLP('./corenlp/stanford-corenlp-full-2018-10-05', lang=lang, memory='8g') as nlp:
				#print(article[lang]['content'])
				article[lang]['ner'] = nlp.ner(article[lang]['content'])
				article[lang]['sa'] = nlp.sentiment

if __name__ == '__main__':
	main()
