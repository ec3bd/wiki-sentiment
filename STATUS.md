Current status is:

You run testwrap.py with a space delimited list of wikipedia links and it should grab them and whatever other language counterparts they have and goes right up to making a google request but no api key. We need to talk about scalability because it'll be expensive to translate a bunch of full articles.

Google actually gives $300 api credit first time you sign up but at $20/million characters that goes quick. The articles I've been seeing vary but topics that might be controversial are often around 100,000 characters, and it's harder to trim even simple things like references before translating, specifically because it's before translating. This would be 100,000 per article per language. ie $10 per article for even just 5 languages. So not sustainable.


Solutions I propose (that aren't necessarily mutually exclusive):
* Use the the 6 stanford corenlp models (including english) to parse for certain parts of speech on all and named entities on the 4 that implement it and cut down drastically on the size by grabbing things like adjectives and adverbs preferentially. One issue is the translation quality is likely affected by the input being a string of loosely connected words when it's expecting a sentence.
* the wikipedia api actually allows for a summary request, I don't know the availability in terms of language/length or how well they would really capture the sentiment.
* Definitely in addition to any other strategy we need to set up a storage mechanism for the translated articles and safeguards to prevent redundancy of live api requests. ie translate at cost once and then append it to storage and use it how we want later





I print various things about the data gathered so far to help understand the structure, feel free to add or subtract any explanatory prints
