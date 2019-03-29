#Setting up a pipeline for the task:
#english article -> machine translated -> stanford nlp -> multiple sentiment scores 

import requests
import json
import sys
import wikipedia
from stanfordcorenlp import StanfordCoreNLP
import subprocess




def main():
	#Goes through space ddelimited list of full article links and puts them through the pipeline.
	#if using a dataset of articles, 
	if len(sys.argv) > 1:
		for arg in sys.argv[1:]:
			article = fetch_article(arg)
			stanford_corenlp(article)
			translated = translate(article)
			# sentiments = stanford_corenlp(translated)
			# print(arg)
			# print(sentiments)

	else:
		print("Please enter at least one Wikipedia link to analyse.")


#given a link to a wikipedia article, 
#will return the text content of that article in a dictionary keyed by its page title
def fetch_article(link):
	ind = link.index("/wiki/")
	title = link[ind+6:]
	print(title)
	page = wikipedia.page(title)
	content = page.content
	print(len(content))
	#Divide at earliest point to cut down on unnecessary characters
	try:
		content = content[:content.index("== See also ==")]
	except ValueError:
		try:
			content = content[:content.index("== References ==")]
		except ValueError:
			print("no references might be other language")

	print("Num characters in article: "+ str(len(content)))

	return {title : content}

#input: dictionary with {title:english article text as string}
#output: dictionary with keys being various two-letter language codes and items being the translated article text
def translate(article):

	for title in article:
		#get languages this article is in
		param_dict = {"action":"query",
						"prop":"langlinks",
						"format":"json",
						"redirects":1,
						"titles":title}
		req = requests.get("https://en.wikipedia.org/w/api.php", params=param_dict)
		results = req.json()
		print(results)
		print(req.url)

		languages = {}
		for pageid, info in results['query']['pages'].items():
			for lang in info['langlinks']:
				languages[lang['lang']] = {"title": lang['*']}

		print(languages)


		#get translated articles
		for lang in languages:
			wikipedia.set_lang(lang)
			page = wikipedia.page(languages[lang]['title'])
			content = page.content
			#print(content)
			data = {"q":content,
					"target":"en",
					"source":lang,
					"format":"text",
					"key":"NO KEY HERE UNTIL WE GET A STORAGE MECHANISM GOING, or compress foriegn language to "}
			#req = requests.post("https://translation.googleapis.com", data=data)


def stanford_corenlp(article):
	nlp = StanfordCoreNLP('corenlp/', lang='en')

	for title in article:
		with open("input.txt",'w') as infile:
			infile.write(article[title])

		#command = ["java", "-cp", "\"*\"", "edu.stanford.nlp.pipeline.Stanfo"]
		article['pos'] = nlp.pos_tag(article[title])

	print (article)
if __name__ == '__main__':
	main()