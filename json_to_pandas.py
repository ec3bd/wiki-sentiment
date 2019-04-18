'''
This python script will create a pandas dataframe in the following format:
id | text (english) | title | url (en-wiki) | topic
parsing from the english wikipedia set, only the topics / id / revid / article name / url / english text
will parse.

JSON format: {"id": "", "url":"", "title": "", "text": "..."}
JSON format extracted using: https://github.com/attardi/wikiextractor

https://www.mediawiki.org/wiki/API:Categories for topic
'''

import json
import pandas as pd
import requests

# Currently goes through 1 json instance at a time to make 1 csv for the articles in that json file.
pandas_df = pd.read_json("wiki_00.json",lines="True")
print(pandas_df.head())

'''
INDEXING:
id=0,text=1, title=2, url=3, topic (will be)=4
---

Next, can get its topic by: https://www.mediawiki.org/wiki/API:Categories for topic


'''
# default value is NONE for topic
pandas_df['topic']='NONE'
sess = requests.Session()
URL = "https://en.wikipedia.org/w/api.php"
# Go through the URLs in the dataset:

for index, row in pandas_df.iterrows():
	title = row['title']
	params = {
	"action": "query",
	"format": "json",
	"titles": title,
	"prop": "categories",
	}


	R = sess.get(url=URL, params=params)
	cat_dat = R.json()
	if 'continue' in cat_dat.keys():
		number = cat_dat['continue']['clcontinue'].split("|")[0]
		list_cat = cat_dat['query']['pages'][number]['categories'][0]
		# All categories associated are within this list.
		# Just grab first one that appears.
		# potential TODO: add all categories in a list?
		# Format of categories: "categories": [{ns:xx, title:xx}, {..}, {...}]
		# Format: "title": "Category:1985 births" --> split = ["category", "1985 births"]
		# Could get all topics from just list_cat.
		topic_cat = list_cat['title'].split(":")[1]
		print(topic_cat)
		# Change 'topic' to be the topic_cat
		row['topic'] = topic_cat
		pandas_df.loc[index, 'topic']= topic_cat

#print(pandas_df.head())

# Finally, place into csv for use in other people's code! (If you are using this dataset in other analysis)

pandas_df.to_csv(path_or_buf='wikipandas.csv', index=False)


# To see how the output can be used again, un-comment these two lines:
#new_pandas = pd.read_csv('wikipandas.csv')
#print(new_pandas.head())
