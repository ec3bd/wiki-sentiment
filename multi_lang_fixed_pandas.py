# Script to compile all english URL-based articles into a pandas dataframe with all language texts included.

import requests
import json
import sys
import wikipedia
import subprocess
import json
import pandas as pd

languagelist = ['en', 'zh', 'es', 'de', 'ru', 'ja']
#From translate.py ec3bd
#given a link to a wikipedia article, 
#will return the text content of that article in a dictionary keyed by its page title
def fetch_article(link):
	ind = link.index("/wiki/")
	title = link[ind+6:]
	print(title)
	wikipedia.set_lang("en")
	page = wikipedia.page(title)
	content = page.content
	#print(len(content))
	#Divide at earliest point to cut down on unnecessary characters
	try:
		content = content[:content.index("== See also ==")]
	except ValueError:
		try:
			content = content[:content.index("== References ==")]
		except ValueError:
			print("no references might be other language")

	#print("Num characters in article: "+ str(len(content)))

	retdict = {'title': title, 'en': content}
	#print(content.split()[:30])
	languagelist = ['zh', 'es', 'de', 'ru', 'ja']
	for lang_title in languagelist:
		#get languages this article is in
		param_dict = {"action":"query",
						"prop":"langlinks",
						"format":"json",
						"lllang": lang_title,
						"redirects":1,
						"titles":title}
		req = requests.get("https://en.wikipedia.org/w/api.php", params=param_dict)
		results = req.json()
		#print(results)

		for pageid, info in results['query']['pages'].items():
			if 'langlinks' in info.keys():
				for lang in info['langlinks']:
					#print(lang)
					wikipedia.set_lang(lang['lang'])
					page = wikipedia.page(lang['*'])
					content = page.content
					retdict[lang['lang']] = content
			else:
				retdict[lang_title]="NONE"
	print(retdict.keys())
	return retdict

# Combine multiple translated articles into a dictionary in the following form:
# {title: [title1, title2, title3 ... titleN], en: [en-text1, en-text2...], ... }

def compile_article_dict(article_list):
	article_dict = {"title":[], "en":[], "zh":[], "es":[], "de":[], "ru":[], "ja":[]}
	new_article_dict = {}
	for article in article_list:
		new_article_dict = fetch_article(article)
		#print(new_article_dict.keys())
		for k in new_article_dict.keys() & article_dict.keys():
			# Assuming actually changes the list in article_dict
			article_dict[k].append(new_article_dict[k])
	return article_dict

# Given dictionary with multiple languages titles/articles, creates a pandas dataframe
# with following headers: Title | en text | zh text | es text | de text | ru text | ja text
def articles_to_dataframe_append(article_dict):
	article_df = pd.DataFrame.from_dict(article_dict)
	print(article_df.head())
	# Finally, place into csv for others to use.
	with open('multi-lang_articles_pandas_1.csv', 'a') as f:
		article_df.to_csv(path_or_buf=f, index=False, header=False)
	return article_df

def articles_to_dataframe(article_dict):
	article_df = pd.DataFrame.from_dict(article_dict)
	print(article_df.head())
	# Finally, place into csv for others to use.
	with open('multi-lang_articles_pandas_1.csv', 'w') as f:
		article_df.to_csv(path_or_buf=f, index=False, header=False)
	return article_df

def main():
	link_list = []
	# raw_article_links.txt is the list of title , link\n lines.
	with open('raw_article_links.txt', 'r') as raw_text:
		# Comes in format title, link\n title, link\n
		line = raw_text.readline()
		while line:
			link_list.append(line.split(",")[1].lstrip().strip('\n'))
			line = raw_text.readline()

		#print(link_list)
	raw_text.close()

	article_dict = compile_article_dict(link_list)

	# If creating new dataframe, uncomment this one and comment following one.
	#art_df = articles_to_dataframe(article_dict)
	art_df = articles_to_dataframe_append(article_dict)
	#print(art_df.head())

if __name__ == '__main__':
	main()