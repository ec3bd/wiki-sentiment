#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 16:02:42 2019

@author: mikesung
"""
import numpy as np
import pandas as pd
import polyglot
from polyglot.text import Text, Word
from polyglot.downloader import downloader
import json
from stanfordcorenlp import StanfordCoreNLP
import os
from google.cloud import translate
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/Users/mikesung/Downloads/My First Project-daebfec3c5a1.json"


firstDf = pd.read_csv("/Users/mikesung/Downloads/wiki-sentiment/multi-lang_articles_pandas_fixed.csv", header=None, names = ['de', 'en', 'es', 'ja', 'ru', 'Title', 'zh'])
secondDf = pd.read_csv("/Users/mikesung/Downloads/wiki-sentiment/multi-lang_articles_pandas_fixed_3.csv", header=None, names = ['de', 'en', 'es', 'ja', 'ru', 'Title', 'zh'])

df = pd.concat([firstDf, secondDf], ignore_index=True)

ja = df['ja']
ja = ja.drop(labels=[10, 11])
ja = ja.reset_index(drop=True)

ru = df['ru']
ru = ru.drop(labels = [10])
ru = ru.reset_index(drop=True)
# get EN series
en = df['en']

# get DE series
de = df['de']
de = de.drop(labels = [5, 11])
de = de.reset_index(drop=True)

# get es series
es = df['es']

# get zh series
zh = df['zh']
zh = zh.drop(labels = [11])
zh = zh.reset_index(drop=True)


a = json.load()

with open('/Users/mikesung/Downloads/wiki-sentiment/japanRussiaFreq.json', 'r') as f:
    nerDict = json.load(f)

engSet = []
for key, subDict in nerDict.items():
    engSet.extend(list(subDict.keys()))

engSet = list(set(engSet))
engSet.append("United Nations")
jaNerDict = {}


jaDictKeys = list(jaDict.keys())
jaDictValues = list(jaDict.values())
jaDictCount = np.array([len(elem) for elem in jaDictValues])
argSort = np.argsort(ruDictCount,axis=None)[::-1]
jaDictCount = jaDictCount.tolist()

topDict = {}
for i in range(len(argSort)):
    topDict[ruDictKeys[argSort[i]]] = ruDictCount[argSort[i]]

jsonDict = {}
jsonDict['ru'] = topDict

with open('/Users/mikesung/Downloads/mergeDict.json', 'w') as fp:
    json.dump(mergeDict, fp)



def getNERMappings(top150Key):
    translator = Translator()
    retDict = {}
    for elem in top150Key:
        try:
            trans = translator.translate(elem, dest='en').text
            retDict[trans] = elem
        except:
            pass
    return retDict







def getSentimentScores(laNerDict, laDict):
    nlp = StanfordCoreNLP('/Users/mikesung/Downloads/wiki-sentiment/corenlp/stanford-corenlp-full-2018-10-05', lang='en', memory='8g', port=9000)
    
    translate_client = translate.Client()

    numDict = {}
    scoreDict = {}
    for enNer, laNer in laNerDict.items():
        print("Working on " + enNer + " " + laNer)
        if laNer in laDict:
            numDict[enNer] = len(laDict[laNer])
            scoreList = []
            for sentence in laDict[laNer]:
#                print(sentence)
                try:
                    trans = translate_client.translate(sentence,target_language='en')['translatedText']
                    results = nlp.sentiment(trans)
                    sentiVec = np.array(results['sentences'][0]['sentimentDistribution'])
                    scoreList.append(sentiVec)
                except:
                    pass
            scoreDict[enNer] = scoreList
                
        else:
            numDict[enNer] = 0
            scoreDict[enNer] = []
    return numDict, scoreDict
    

def getNamedEntities(series, countryCode='en', threshold=5):
    retDict = {}
    for i in range(len(series)):
        text = Text(series[i], hint_language_code=countryCode)

        for sentence in text.sentences:
#            print(sentence)
            for ent in sentence.entities:
                word = ent[0].title()
                if word not in retDict:
                    retDict[word] = []
                    retDict[word].append(sentence.string)
                else:
                    retDict[word].append(sentence.string)
    
    toBeDel = []
    for key, valueList in retDict.items():
        if len(valueList) < threshold:
            toBeDel.append(key)
    
    for key in toBeDel:
        del retDict[key]
    
    return retDict

def getNamedEntitiesStanford(series, countryCode='en', threshold=5):
    nlp = StanfordCoreNLP('/Users/mikesung/Downloads/wiki-sentiment/corenlp/stanford-corenlp-full-2018-10-05', lang=countryCode, memory='8g', port=9000)
    desired_classes = ['PERSON', 'LOCATION', 'ORGANIZATION', 'CITY', 'STATE_OR_PROVINCE', 'COUNTRY', 'NATIONALITY', 'RELIGION', 'IDEOLOGY']
    retDict = {}
    for i in range(len(series)):
        print("Working on article " + str(i))
        text = Text(series[i], hint_language_code=countryCode)
        for sentence in text.sentences:
            try:
                NERList = nlp.ner(sentence.string)
                for tup in NERList:
                    word = tup[0]
                    if tup[1] in desired_classes:
                        if word not in retDict:
                            retDict[word] = []
                            retDict[word].append(sentence.string)
                        else:
                            retDict[word].append(sentence.string)
            except:
                print("Article " + str(i) + "failed to load.")
                pass
    
    toBeDel = []
    for key, valueList in retDict.items():
        if len(valueList) < threshold:
            toBeDel.append(key)
    
    for key in toBeDel:
        del retDict[key]
    
    return retDict

def mergeLaDict(enDict, listOfOther, codeList = ['de', 'es', 'ja', 'ru', 'zh']):
    translate_client = translate.Client()
    retDict = {}
    for enKey in enDict.keys():
        retDict[enKey] = {}
        retDict[enKey]['en'] = enKey
    for i in range(len(listOfOther)):
        dic = listOfOther[i]
        countryCode = codeList[i]
        print("Working on " + countryCode)
        
        for laKey in dic.keys():
            transKey = translate_client.translate(laKey, target_language='en')['translatedText']
            if transKey in retDict:
                retDict[transKey][countryCode] = laKey
            else:
                retDict[transKey] = {}
                retDict[transKey][countryCode] = laKey
    return retDict
    


