#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  2 19:54:45 2019

@author: zsoltvarga
"""
#refactored for preliminary publication

#first session, loading and structuring the data
import pandas as pd

#this is the source file, I converted it as plain text from pdf
source_txt = "D:\\Working\\working_docs\\26_baranyai_phd\\homiliak.txt"

#this function gets the speeches out of the text. it searches for text between the 
#beginning and end strings and appends them to a list as strings
def get_sections(f, speeches_list, last_line, begin, end):
        current_speech = []
        for line in f:
            # found start of section so start iterating from next line
            if last_line.startswith(begin):
                current_speech.append(last_line.rstrip())
            if line.startswith(begin) or last_line.startswith(begin):
                current_speech.append(line.rstrip())
                for line in f: 
                    if not line.startswith(end):
                        current_speech.append(line.rstrip())
                    # found end so end function
                    else:
                        speeches_list.append(current_speech)
                        #WOW: i somehow ended up with a first recursion
                        #it's ugly this way, but at least it works
                        #this last line thing is reqiured, because there's no way to
                        #turn back the counter for the lines in the file
                        get_sections(f, speeches_list, line, begin, end)
        return speeches_list


#TODO: implement corpus reader, with "†" as the boundary character between texts

#in this case the speeches are well structured and a distinct pattern can be recognised
#so it's relatively easy to identify and extract them
#I extract them line by line, so the resulting data structure is a list of strings for each speech
#and the resulting corpus is a list of speeches, e.g. a list of lists of strings

# Open the file and grab the speeches as list of lines
f = open(source_txt, encoding="utf8", errors='ignore')
all_speeches = []
last_line = ''
#get all speeches into a list of lists of strings
d = get_sections(f, all_speeches, last_line, '†','†')
f.close()
                      
#create an empty dataframe for storing the data
df = pd.DataFrame()

#in most speeches the first line is a prefix, the second line is the title and the rest is the text
#so i just break them up this way
df['PREFIX'] = [x[0] for x in all_speeches]
df['TITLE'] = [x[2] for x in all_speeches]
df['textlines'] = [x for x in all_speeches]

#saving the dataframe into a pickle to be re-used later
df.to_pickle( "D:\\Working\\working_docs\\26_baranyai_phd\\df.pickle")
#end of first session
#-------------------------------------------------------------------------

#second session, pre-processing and cleaning
import pandas as pd
import re
#loading the previously saved dataframe back into memory
df = pd.read_pickle( "D:\\Working\\working_docs\\26_baranyai_phd\\df.pickle")

#removing headers and footers and page numbers that were saved from the pdf into the text file
text = [[line for line in speech if not "Dr. Kövér Fidél" in line and line != "" and not line.isdigit()] for speech in df.textlines]
#prefix = [x[0] for x in text]
#title = [x[1] for x in text]
#extracting the third line from the speeches into the LOCATIONDATE column
df['LOCATIONDATE'] = [x[2] for x in text]

#removing extra spaces and hyphens (while trying to glue back hyphenated words)
preprocessed_speeches = [' '.join(x[3:]).replace('- ', '').strip() for x in text]
preprocessed_speeches_nospace = [re.sub(' +', ' ', str(x)) for x in preprocessed_speeches ]

#a simple helper function to extract the year (4 consecutive digits)
def get_year(text):
    try:
        return re.search('\d{4}', text).group(0)
    except:
        return None

#extracting the year for each speech into the YEAR column, and the pre-processed text into the TEXT column
#removing the old text column (list of lines) and saving the "clean dataframe"
df['YEAR'] = [get_year(x) for x in df.LOCATIONDATE]
df['TEXT'] = preprocessed_speeches_nospace
df = df.copy().drop(['textlines'], axis = 1)
df.to_pickle( "D:\\Working\\working_docs\\26_baranyai_phd\\df_clean.pickle")
#end of second session
#-------------------------------------------------------------------------


#third session, cleaning up the date format to enable time series analysis
import pandas as pd
import re
#loading the previously saved dataframe back into memory
df_clean = pd.read_pickle( "D:\\Working\\working_docs\\26_baranyai_phd\\df_clean.pickle")

#a helper function to convert the date from the text into a proper datetime format
def get_date(text):
    from datetime import datetime
    import re
    monthdic = {'január':1,
                'február':2,
                'március':3,
                'április':4,
                'május':5,
                'június':6,
                'július':7,
                'augusztus':8,
                'szeptember':9,
                'október':10,
                'november':11,
                'december':12}
    try:
        a = re.search('(\d{4})(\.\s)(.*?)(\d{1,2})(\.)', text)
        print (a)
        year = a.group(1)
        print ("year: ", year)
        month = monthdic[a.group(3).strip()]
        #month = 1
        print ("month: ", a.group(3), month)
        day = a.group(4)
        print ("day: ", day)
        print('-'.join([str(year), str(month), str(day)]))
        return datetime.strptime('-'.join([str(year), str(month), str(day)]),'%Y-%m-%d')
    except:
        return None


#trying to get the date from the LOCATIONDATE column and save it datetime format in the DATE column
df_clean['DATE'] = df_clean['LOCATIONDATE'].apply(lambda x: get_date(x))

#df_clean.to_pickle( "D:\\Working\\working_docs\\26_baranyai_phd\\df_clean.pickle")
#df_clean = pd.read_pickle( "D:\\Working\\working_docs\\26_baranyai_phd\\df_clean.pickle")

#if we can't get the date from the locationdate field, let's check the text itself
df_clean['DATE2'] = df_clean['TEXT'].apply(lambda x: get_date(x))
df_clean['DATE3'] = df_clean.DATE.fillna(df_clean['TEXT'].apply(lambda x: get_date(x)), inplace=False).copy()
df_clean.isnull().sum(axis = 0)

#if we can't get the date from text itself, then let's check the title
df_clean['DATE4'] = df_clean['TITLE'].apply(lambda x: get_date(x))
df_clean['DATE5'] = df_clean.DATE3.fillna(df_clean['TITLE'].apply(lambda x: get_date(x)), inplace=False).copy()
df_clean.isnull().sum(axis = 0)

df_clean.to_pickle( "D:\\Working\\working_docs\\26_baranyai_phd\\df_clean.pickle")
#end of third session
#-------------------------------------------------------------------------

#Session 4, creating an Excel file for manual checking and pre-processing
#loading the previously saved dataframe back into memory
import pandas as pd

#loading the previously saved dataframe back into memory
df_clean = pd.read_pickle( "D:\\Working\\working_docs\\26_baranyai_phd\\df_clean.pickle")

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter("D:\\Working\\working_docs\\26_baranyai_phd\\text_and_metadata_extraction.xlsx", engine='xlsxwriter')
# Convert the dataframe to an XlsxWriter Excel object.
df_clean.to_excel(writer, sheet_name='Sheet1')
# Close the Pandas Excel writer and output the Excel file.
writer.save()
#End of Session 4
#-------------------------------------------------------------------------

#Session 5, linguistic pre-processing using Spacy and a Hungarian language model

#open on Mac
#the path to the files may be different for each session, pls check your system and adjust as necessary
import pandas as pd
df_clean = pd.read_pickle( "./Downloads/sermon_mining/df_clean.pickle")


#Some clean-up, making copies of the dataframes, to preserve compatibility with previous workflow
df_clean['DATE'] = df_clean['DATE5']
df_viz = df_clean.copy().drop(['DATE2', 'DATE3', 'DATE4', 'DATE5'], axis = 1)
df_lda = df_viz.copy()

#fire up spacy and the new hungarian models
import spacy
#pip install https://github.com/oroszgy/spacy-hungarian-models/releases/download/hu_core_ud_lg-0.1.0/hu_core_ud_lg-0.1.0-py3-none-any.whl  
#also need to install the latest regex package from conda, otherwise it won't work
import hu_core_ud_lg
nlp = hu_core_ud_lg.load()
preprocessed_speeches = []

#a function for removing Hungarian stopwords, non-alphanumeric stuff, and creating a lemmatized bag of words
for index, row in df_lda.iterrows():
    print(index)
    preprocessed = []
    doc = nlp(df_lda.iloc[index].TEXT)
    for token in doc:
        if not token.is_stop and token.is_alpha and str(token.lemma_).lower() not in ['a', 'az', 'és']:
            preprocessed.append(str(token.lemma_).lower())
    preprocessed_speeches.append(preprocessed)    
        
#    print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_,
#          token.shape_, token.is_alpha, token.is_stop)

#remove all lemmas (word roots) that are shorter than 4 characters, and remove "download" and "felvétel"
#and save the lemmatized bag of word representation in the LEMMA column
preprocessed_speeches_clean = [x[2:] for x in preprocessed_speeches if len(x)>4]
preprocessed_speeches_clean2 = [[lemma for lemma in wordlist if lemma !="download" and 'felvétel' not in lemma] for wordlist in preprocessed_speeches_clean]
df_lda['LEMMA'] = preprocessed_speeches
#df_lda['DATE'] = df_lda['URL'].astype(str).str[12:19]
#df_lda['YEAR'] = df_lda['DATE'].astype(str).str[0:4]
#df_lda['MONTH'] = df_lda['DATE'].astype(str).str[5:]

#get the year from the preprocessed date column
#df_lda['YEAR'] = df_lda.YEAR.fillna(df_lda['DATE'].dt.year)
#df_lda['YEAR'] = df_lda['YEAR'].apply(str)

df_lda['YEAR'] = df_lda.YEAR.fillna(df_lda['DATE'].dt.strftime('%Y'))
df_lda.isnull().sum(axis = 0)

df_lda.to_pickle("./Downloads/sermon_mining/df_preprocessed.pickle")
#End of Session 5
#-------------------------------------------------------------------------

#Session 6, create LDA topic models with Gensim
import pandas as pd
df_lda = pd.read_pickle("./Downloads/sermon_mining/df_preprocessed.pickle")
preprocessed_speeches_clean2 = [[lemma for lemma in wordlist if lemma !="download" and 'felvétel' not in lemma] for wordlist in df_lda['LEMMA']]

#create topic models
import gensim

dictionary = gensim.corpora.Dictionary(preprocessed_speeches_clean2)
count = 0
for k, v in dictionary.iteritems():
    print(k, v)
    count += 1
    if count > 10:
        break

dictionary.filter_extremes(no_below=10, no_above=0.5, keep_n=25000)

bow_corpus = [dictionary.doc2bow(doc) for doc in preprocessed_speeches_clean2]

from gensim import corpora, models
tfidf = models.TfidfModel(bow_corpus)
corpus_tfidf = tfidf[bow_corpus]
from pprint import pprint
for doc in corpus_tfidf:
    pprint(doc)
    break

#we will create two-two models of 10 and 5 topics using the pre-processed full text speeches. a full bag-of-words topic model
#and another one that is based on the tf-idf representation (see wikipedia for tf-idf)
lda_model = gensim.models.LdaMulticore(bow_corpus, num_topics=10, id2word=dictionary, passes=2, workers=2)
for idx, topic in lda_model.print_topics(-1):
    print('Topic: {} \nWords: {}'.format(idx, topic))

lda_model_tfidf = gensim.models.LdaMulticore(corpus_tfidf, num_topics=10, id2word=dictionary, passes=2, workers=4)
for idx, topic in lda_model_tfidf.print_topics(-1):
    print('Topic: {} Word: {}'.format(idx, topic))

#create interactive topid model visualisation
import pyLDAvis
import pyLDAvis.gensim   

vis = pyLDAvis.gensim.prepare(lda_model, bow_corpus, dictionary)
vis
pyLDAvis.display(vis)
pyLDAvis.save_html(vis, './Downloads/sermon_mining/lda.html')

lda_model_5 = gensim.models.LdaMulticore(bow_corpus, num_topics=5, id2word=dictionary, passes=2, workers=2)
vis_5 = pyLDAvis.gensim.prepare(lda_model_5, bow_corpus, dictionary)
pyLDAvis.save_html(vis_5, './Downloads/sermon_mining/lda_5.html')

vis_tf_idf = pyLDAvis.gensim.prepare(lda_model_tfidf, bow_corpus, dictionary)
vis_tf_idf
pyLDAvis.display(vis)
pyLDAvis.save_html(vis_tf_idf, './Downloads/sermon_mining/lda_tf_idf.html')

lda_model_tfidf_5 = gensim.models.LdaMulticore(corpus_tfidf, num_topics=5, id2word=dictionary, passes=2, workers=4)
vis_tf_idf_5 = pyLDAvis.gensim.prepare(lda_model_tfidf_5, bow_corpus, dictionary)
pyLDAvis.save_html(vis_tf_idf_5, './Downloads/sermon_mining/lda_tf_idf_5.html')
#it seems the tf-idf does not have any added value over the full bag of words model, as LDA is classifying into topics by word-topic probability distribution
#End of Session 6
#-------------------------------------------------------------------------

#Session 7, generating word clouds out of speeches
#we group the speeches by year and generate a word cloud for each year
from wordcloud import WordCloud
import matplotlib.pyplot as plt

for year in df_lda['YEAR'].unique():
    speeches_of_the_year = []
    for i, row in df_lda[df_lda['YEAR']==str(year)].iterrows():
        #creating one long string out of the list of lemmas for the wordcloud
        speeches_of_the_year.append(' '.join(row['LEMMA']))
    wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               stopwords = nlp.Defaults.stop_words).generate(str(speeches_of_the_year))
    wordcloud.to_file('./Downloads/sermon_mining/wordcloud/wordcloud_'+str(year)+'.png')
    #fig = plt.figure(
    #           figsize = (40, 30),
    #           facecolor = 'k',
    #           edgecolor = 'k')
    #plt.imshow(wordcloud, interpolation = 'bilinear')
    #plt.axis('off')
    #plt.tight_layout(pad=0)
    #plt.show()
    #filename = './Documents/speech_mining/wordcloud_'+str(year)
    #fig.savefig(filename, bbox_inches='tight')
    #print(filename)


from collections import Counter
#generating word clouds with extended stop words so that very frequent words will not "crowd out" the real keywords
extended_stopwords = nlp.Defaults.stop_words | {'jézus', 'isten', 'ember', 'krisztus', 'úr', 'élet'}
for year in df_lda['YEAR'].unique():
    speeches_of_the_year = []
    for i, row in df_lda[df_lda['YEAR']==str(year)].iterrows():
        speeches_of_the_year.append(' '.join(row['LEMMA']))
    #remove the top 10 most frequent words
    wordcount = Counter(' '.join(speeches_of_the_year).split())
    most_occur = wordcount.most_common(10)
    pruned_speeches_of_the_year = [x for x in speeches_of_the_year if x not in most_occur]
    wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               stopwords = extended_stopwords).generate(str(pruned_speeches_of_the_year))
    wordcloud.to_file('./Downloads/sermon_mining/wordcloud/wordcloud_wo_deity_pruned_'+str(year)+'.png')
    
#getting the adjectives, nouns and verbs from the text (using the Hungarian language model previously loaded up in Spacy)
adjectives_all_speeches = []
for index, row in df_lda.iterrows():
    print(index)
    adjectives = []
    doc = nlp(df_lda.iloc[index].TEXT)
    for token in doc:
        if token.pos_ == 'ADJ' and token.is_alpha:
            adjectives.append(str(token.lemma_).lower())
            print(token.lemma_)
    adjectives_all_speeches.append(adjectives)
    
nouns_all_speeches = []
for index, row in df_lda.iterrows():
    print(index)
    nouns = []
    doc = nlp(df_lda.iloc[index].TEXT)
    for token in doc:
        if token.pos_ == 'NOUN' and token.is_alpha: # and str(token) not in ['január', 'február',
                                #'március', 'április', 'május', 'június', 'július',
                                #'augusztus', 'szeptember', 'október', 'november',
                                #'december'] and "felvétel" not in str(token) and "Lekció" not in str(token) and "Sorozat" not in str(token):
            nouns.append(str(token.lemma_).lower())
            print(token.lemma_)
    nouns_all_speeches.append(nouns)

verbs_all_speeches = []
for index, row in df_lda.iterrows():
    print(index)
    verbs = []
    doc = nlp(df_lda.iloc[index].TEXT)
    for token in doc:
        if token.pos_ == 'VERB' and token.is_alpha:
            verbs.append(str(token.lemma_).lower())
            print(token.lemma_)
    verbs_all_speeches.append(verbs)

df_lda['ADJECTIVES'] = adjectives_all_speeches
df_lda['NOUNS'] = nouns_all_speeches
df_lda['VERBS'] = verbs_all_speeches
df_lda.to_pickle("./Downloads/sermon_mining/df_preprocessed.pickle")

#creating word clouds for adjectives, nouns and verbs

#creating an extended stopword list for adjectives
extended_stopwords_adjectives = nlp.Defaults.stop_words #| {'oly', 'ily'}
for year in df_lda['YEAR'].unique():
    speeches_of_the_year = []
    for i, row in df_lda[df_lda['YEAR']==str(year)].iterrows():
        #creating one long string out of the list of lemmas for the wordcloud
        speeches_of_the_year.append(' '.join(row['ADJECTIVES']))
    wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               stopwords = extended_stopwords_adjectives).generate(str(speeches_of_the_year))
    wordcloud.to_file('./Downloads/sermon_mining/wordcloud/wordcloud_adjectives_'+str(year)+'.png')

extended_stopwords_verbs = nlp.Defaults.stop_words #| {'tud', 'mond'}
for year in df_lda['YEAR'].unique():
    speeches_of_the_year = []
    for i, row in df_lda[df_lda['YEAR']==str(year)].iterrows():
        #creating one long string out of the list of lemmas for the wordcloud
        speeches_of_the_year.append(' '.join(row['VERBS']))
    wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               stopwords = extended_stopwords_verbs).generate(str(speeches_of_the_year))
    wordcloud.to_file('./Downloads/sermon_mining/wordcloud/wordcloud_verbs_'+str(year)+'.png')

for year in df_lda['YEAR'].unique():
    speeches_of_the_year = []
    for i, row in df_lda[df_lda['YEAR']==str(year)].iterrows():
        #creating one long string out of the list of lemmas for the wordcloud
        speeches_of_the_year.append(' '.join(row['NOUNS']))
    wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               stopwords = nlp.Defaults.stop_words).generate(str(speeches_of_the_year))
    wordcloud.to_file('./Downloads/sermon_mining/wordcloud/wordcloud_nouns_'+str(year)+'.png')

#End of Session 7
#-------------------------------------------------------------------------

#Session 8, dictionary based sentiment analysis experiments
#this is a long session. first we will load up a Hungarian sentiment lexicon and try to quantify the sentiments
#using a dictionary-based approach
#we save the sentiment values in the dataframe and then try to plot the change of the tonality of speeches
#on a time scale, using various smoothing methods, because the original data shows a high fluctuation
#we try rolling average, normalisation, standardisation
#we also plot just the positive, just the negative, and also the difference between the two (absolut sentiment)


#load up the Hungarian sentiment dictionaries
#http://opendata.hu/dataset/hungarian-sentiment-lexicon
with open('./Downloads/PrecoSenti/PrecoNeg.txt') as f:
    negative_sents = f.read().splitlines()
f.close()

with open('./Downloads/PrecoSenti/PrecoPos.txt') as f:
    positive_sents = f.read().splitlines()
f.close()

def calculate_sent_score(string, wordlist):
    """
    Helper function to calculate sentiment score. 
    """
    counter = 0
    for sentiment in wordlist:
        counter += string.count(sentiment)
    print(counter)
    return(counter)

calculate_sent_score(df_lda['TEXT'][3], positive_sents)
calculate_sent_score(df_lda['TEXT'][3], negative_sents)

df_lda_temp = df_lda.copy()

df_lda_temp['POS'] = df_lda_temp['TEXT'].apply(lambda text: calculate_sent_score(text, positive_sents))
df_lda_temp['NEG'] = df_lda_temp['TEXT'].apply(lambda text: calculate_sent_score(text, negative_sents))
df_lda_temp['SENTIMENT'] =  df_lda_temp['POS'] - df_lda_temp['NEG']

df_lda_temp['SENTIMENT_WEIGHTED'] =  (df_lda_temp['POS'] - df_lda_temp['NEG']) / len(df_lda_temp['TEXT'])

df_lda_temp.to_pickle("./Downloads/sermon_mining/df_preprocessed_sentiments.pickle")


#let's try to get the day of the month with a regex
#from datetime import datetime
#import re
#dayofmonth_all_speeches = []
#for i, row in df_lda_temp.iterrows():
#    try:
#        dayofmonth = re.search(r'(?:Dátum:\s\d\d\d\d\.\s\b[^\W\d_]+\b\s)(\d+)(\.)', row['TEXT']).group(1)
#    except:
#        dayofmonth = None
#    print(dayofmonth)
#    dayofmonth_all_speeches.append(dayofmonth)
#
#df_lda_temp['DAYOFMONTH'] =  dayofmonth_all_speeches
#df_lda_temp = df_lda_temp[df_lda_temp['DAYOFMONTH'].astype(str) != 'None']
#df_lda_temp['FULLDATE'] = df_lda_temp['DATE'].astype(str) + '-' + df_lda_temp['DAYOFMONTH'].astype(str)
#df_lda_temp['FULLDATE'] = df_lda_temp['FULLDATE'].apply(lambda x: datetime.strptime(x,'%Y-%m-%d'))

#we need to get the dates in proper full format to generate time series graphs
df_lda_temp['FULLDATE'] = df_lda_temp['DATE']
df_lda_temp.dropna(subset=['DATE'], inplace = True)

# create the plot space upon which to plot the data
fig, ax = plt.subplots(figsize = (10,10))

# add the x-axis and the y-axis to the plot
ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
        df_lda_temp.sort_values('FULLDATE')['SENTIMENT'], 
        color = 'red')

# rotate tick labels
plt.setp(ax.get_xticklabels(), rotation=45)

# set title and labels for axes
ax.set(xlabel="Date",
       ylabel="Sentiment score (positive-negative",
       title="Sentiment in the Rev. Kövér's speeches")
fig.savefig("./Downloads/sermon_mining/wordcloud/fidel_sentiments_.png")       

#rolling average plot
series = df_lda_temp.sort_values('FULLDATE')['SENTIMENT']
# Tail-rolling average transform
rolling = series.rolling(window=3)
rolling_mean = rolling.mean()

# create the plot space upon which to plot the data
fig, ax = plt.subplots(figsize = (10,10))

# add the x-axis and the y-axis to the plot
#ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
#        df_lda_temp.sort_values('FULLDATE')['SENTIMENT'], 
#        color = 'red')

ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
        rolling_mean, 
        color = 'blue')

# rotate tick labels
plt.setp(ax.get_xticklabels(), rotation=45)

# set title and labels for axes
ax.set(xlabel="Date",
       ylabel="Sentiment score (positive-negative",
       title="Sentiment in the Rev. Kövér's speeches (rolling average)")


from matplotlib import pyplot
series = df_lda_temp.sort_values('FULLDATE')['SENTIMENT']
series.hist()
pyplot.show()

# Standardize time series data
from sklearn.preprocessing import StandardScaler
from math import sqrt
# load the dataset and print the first 5 rows
series = df_lda_temp.sort_values('FULLDATE')['SENTIMENT']
print(series.head())
# prepare data for standardization
values = series.values
values = values.reshape((len(values), 1))
# train the standardization
scaler = StandardScaler()
scaler = scaler.fit(values)
print('Mean: %f, StandardDeviation: %f' % (scaler.mean_, sqrt(scaler.var_)))
# standardization the dataset and print the first 5 rows
standardised = scaler.transform(values)
for i in range(5):
	print(standardised[i])
# inverse transform and print the first 5 rows
inversed = scaler.inverse_transform(standardised)
for i in range(5):
	print(inversed[i])

# create the plot space upon which to plot the data
fig, ax = plt.subplots(figsize = (10,10))

# add the x-axis and the y-axis to the plot
ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
        standardised, 
        color = 'red')

# rotate tick labels
plt.setp(ax.get_xticklabels(), rotation=45)

# set title and labels for axes
ax.set(xlabel="Date",
       ylabel="Sentiment score (positive-negative",
       title="Sentiment in the Rev. Kövér's speeches (standardised)")
       

# Normalize time series data
from sklearn.preprocessing import MinMaxScaler
# load the dataset and print the first 5 rows
series = df_lda_temp.sort_values('FULLDATE')['SENTIMENT']
print(series.head())
# prepare data for normalization
values = series.values
values = values.reshape((len(values), 1))
# train the normalization
scaler = MinMaxScaler(feature_range=(0, 1))
scaler = scaler.fit(values)
print('Min: %f, Max: %f' % (scaler.data_min_, scaler.data_max_))
# normalize the dataset and print the first 5 rows
normalized = scaler.transform(values)
for i in range(5):
	print(normalized[i])
# inverse transform and print the first 5 rows
inversed = scaler.inverse_transform(normalized)
for i in range(5):
	print(inversed[i])

#trendline stuff, but makes no sense as we have data for all timestamps
#import numpy as np
#z = np.polyfit(range(0, 621),
#    df_lda_temp.sort_values('FULLDATE')['SENTIMENT'].as_matrix().flatten(), 1)
#p = np.poly1d(z)

# create the plot space upon which to plot the data
fig, ax = plt.subplots(figsize = (10,10))

# add the x-axis and the y-axis to the plot
ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
        normalized, 
        color = 'red')

#ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
#        p(df_lda_temp.sort_values('FULLDATE')['SENTIMENT'].as_matrix()), 
#        color = 'blue')


# rotate tick labels
plt.setp(ax.get_xticklabels(), rotation=45)

# set title and labels for axes
ax.set(xlabel="Date",
       ylabel="Sentiment score (positive-negative)",
       title="Sentiment in the Rev. Kövér's speeches (normalised)")

#let's try to plot both the positive and the negative scores on one plot
      # create the plot space upon which to plot the data
fig, ax = plt.subplots(figsize = (10,10))

# add the x-axis and the y-axis to the plot
ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
        df_lda_temp.sort_values('FULLDATE')['NEG']*-1, 
        color = 'red')

ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
        df_lda_temp.sort_values('FULLDATE')['POS'], 
       color = 'green')

#ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
#        df_lda_temp.sort_values('FULLDATE')['SENTIMENT'], 
#        color = 'blue')

# rotate tick labels
plt.setp(ax.get_xticklabels(), rotation=45)

# set title and labels for axes
ax.set(xlabel="Date",
       ylabel="Sentiment score (positive-negative)",
       title="Sentiment in the Rev. Kövér's speeches (pos, neg)")
fig.savefig("./Downloads/sermon_mining/wordcloud/fidel_sentiments_pos_neg.png") 

#plotting the final sentiment score weighted by text length
fig, ax = plt.subplots(figsize = (10,10))

# add the x-axis and the y-axis to the plot
ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
        df_lda_temp.sort_values('FULLDATE')['SENTIMENT_WEIGHTED'], 
        color = 'blue')

# rotate tick labels
plt.setp(ax.get_xticklabels(), rotation=45)

# set title and labels for axes
ax.set(xlabel="Date",
       ylabel="Sentiment score (positive-negative)",
       title="Sentiment in the Rev. Kövér's speeches (weighted by text length)")

 
#rolling mean of the length-weighted sentiment score
series = df_lda_temp.sort_values('FULLDATE')['SENTIMENT_WEIGHTED']
# Tail-rolling average transform
rolling = series.rolling(window=2)
rolling_mean = rolling.mean()

fig, ax = plt.subplots(figsize = (10,10))

# add the x-axis and the y-axis to the plot
ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
        rolling_mean,
        #df_lda_temp.sort_values('FULLDATE')['SENTIMENT_WEIGHTED'],
        color = 'blue', linestyle='-')

# rotate tick labels
plt.setp(ax.get_xticklabels(), rotation=45)

# set title and labels for axes
ax.set(xlabel="Date",
       ylabel="Sentiment score (positive-negative)",
       title="Sentiment in the Rev. Kövér's speeches (weighted by length, rolling mean window=2)")

fig.savefig("./Downloads/sermon_mining/wordcloud/fidel_sentiments_rolling_mean2.png")
#import seaborn as sns
#sns.regplot(x=df_lda_temp.sort_values('FULLDATE')['FULLDATE'], y=rolling_mean, fit_reg=False)
#sns.plt.show()
#End of Session 8
#-------------------------------------------------------------------------


#updating the dataframe with the manual corrections (some manual work was needed to deductively and intuitively infer some missing dates)
#we load up the manually edited Excel table and consolidate the dates in the YEAR and DATE column, then save the pandas dataframe
df =  pd.read_pickle("C:\\Users\\admin\\Dropbox\\sermon_mining\\kover_fidel\\df_preprocessed_sentiments.pickle")
df2 = pd.read_excel("C:\\Users\\admin\\Dropbox\\sermon_mining\\kover_fidel\\text_and_metadata_extraction_manual_corrections.xlsx")

df_full = df.copy()
df_full['YEAR'] = df2['YEAR']
df_full['DATE'] = df2['DATE5']

df_full.to_pickle("C:\\Users\\admin\\Dropbox\\sermon_mining\\kover_fidel\\df_preprocessed_full.pickle")
#End of update
#-------------------------------------------------------------------------


#Session 9, we try to use a Hungarian sentiment analysis docker package by Huszti D. 
#and the Named Entity Recognition package by Orosz Gy.
#it is much more complicated to set up properly than I would have thought
#you need a docker image and a different configuarion than specified in its documentation
#nevertheless, these are the only available resources through Python and REST at the moment


#setting up the environment, loading up the pre-processed dataframe, setting up the REST API connection to the Docker image
#and also loading up the Hungarian language model in Spacy. we need to communicate with the docker image in json format.

import pandas as pd
df_full = pd.read_pickle("C:\\Users\\admin\\Dropbox\\sermon_mining\\kover_fidel\\df_preprocessed_full.pickle")

import requests
sentence = df_full.iloc[1]['TEXT'].split('.')[0]
host="http://localhost:5000"
endpoint="sentiment"
url = "{}/{}".format(host, endpoint)
result = requests.post(url, json={"sentence": sentence})
print(result.text)

import spacy
#pip install https://github.com/oroszgy/spacy-hungarian-models/releases/download/hu_core_ud_lg-0.1.0/hu_core_ud_lg-0.1.0-py3-none-any.whl  
#also need to install the latest regex package from conda, otherwise it won't work
import hu_core_ud_lg
nlp = hu_core_ud_lg.load()


"""
This is the sentiment analysis part, it requires the dhuszti/sentanalysis docker image:

docker pull dhuszti/sentanalysis

Windózon ezzel kell indítani, mert különben nem tud csatlakozni (port forwarding, -p 5000:5000, és akkor a localhost:5000 a REST API belépési pontja)

docker run -it -p 5000:5000 --privileged=true --name=sentanalysishun dhuszti/sentanalysis

de itt még be kell lépni a konténerbe és elindítani a szervert:
cd root
cd SentimentAnalysisHUN-master 
cd src
python ./Application.py

vagy:
docker exec -it sentanalysishun python root/SentimentAnalysisHUN-master/src/Application.py
    
"""

negative_sent_list = []
positive_sent_list = []
no_of_sentences = []
sentiment_list = []
for i, row in df_full.iterrows():
    print (i)
    doc = nlp(df_full.iloc[i]['TEXT'])
    neg_tonality = 0
    pos_tonality = 0
    number_of_sentences = 0
    sentiment_list_in_row = []
    for sent in doc.sents:
        print(sent.text)
        result = requests.post(url, json={"sentence": sent.text})
        print(result.text)
        print('-------------------------------------------------')
        try:
            neg_tonality += result.json()['results'][0]["negative probability"]
            pos_tonality += result.json()['results'][0]["positive probalitiy"]
            sentiment_list_in_row.append(result.json()['results'][0]["sentiment"])
            number_of_sentences += 1
        except:
            print('exception')
    negative_sent_list.append(neg_tonality)
    positive_sent_list.append(pos_tonality)
    no_of_sentences.append(number_of_sentences)
    sentiment_list.append(sentiment_list_in_row)

#for item in set(sentiment_list[500]):
#    print(item, sentiment_list[500].count(item))

neutral = []
negative = []
positive = []
for item in sentiment_list:
    neutral.append(item.count('neutral'))
    negative.append(item.count('negative'))
    positive.append(item.count('positive'))


"""
This is the NER part, provided by the oroszgy/hunlp image (the image needs to be fixed, the magyarlanc binary is corrupted in the image, must be replaced)

docker pull oroszgy/hunlp

docker run -it -p 9090:9090 oroszgy/hunlp

Ha nem indul el:

docker run -it --name="hunlp" oroszgy/hunlp:latest /bin/bash

rm magyarlanc-3.0.jar
wget http://rgai.inf.u-szeged.hu/project/nlp/research/magyarlanc/magyarlanc-3.0.jar

Teszt:
curl -X POST -H "Content-Type: application/json" -d '{"text": "Szia világ!"}' "http://localhost:9090/v1/annotate"


Another option is to use my own forked image:
    
docker pull hutranslation/nlp

docker run -it -p 9090:9090 hutranslation/nlp

Ha nem indul el:

docker run -it --name="hunlp" hutranslation/nlp:latest /bin/bash

./hunlp.sh


Make sure you installed the wrapper: pip install https://github.com/oroszgy/hunlp/releases/download/0.2/hunlp-0.2.0.tar.gz

"""

from hunlp import HuNlp

nlp_ner = HuNlp()
doc = nlp("Egyszerű szöveges tartalom Szegedről. Luxembourg messze van, mint Makó Jeruzsálemtől, mondta Zsolt.")

#tests to check if everything works properly
for sent in doc:
    for tok in sent:
        print(tok.text, tok.lemma, tok.tag)
        
for sent in doc:
    for tok in sent:
        if tok.entity_type != "O":
            print(tok.text, tok.entity_type, tok.lemma)

for ent in doc.entities:
    print (ent)

list(doc.entities)
#end of tests

location_list = []
person_list = []
org_list = []
for i, row in df_full.iterrows():
    print (i)
    doc = nlp(df_full.iloc[i]['TEXT'])
    location_list_in_row = []
    person_list_in_row = []
    org_list_in_row = []
    for sent in doc.sents:
        print(sent)
        print('-------------------------------------------------')
        sentence_for_NER = nlp_ner(sent.text)
        for sent_ in sentence_for_NER:
            for tok in sent_:
                if tok.entity_type != "O":
                    print(tok.text, tok.entity_type, tok.lemma)
                    if tok.entity_type == "I-LOC":
                        location_list_in_row.append(tok.lemma)
                    if tok.entity_type == "I-PER":
                        person_list_in_row.append(tok.lemma)   
                    if tok.entity_type == "I-ORG":
                        org_list_in_row.append(tok.lemma)
                    
    location_list.append(location_list_in_row)
    person_list.append(person_list_in_row)
    org_list.append(org_list_in_row)

#after calculating the sentiment values, we save them in separate columns, along with the positive, negative and neutral sentences.
df_full['negative_values'] = negative_sent_list
df_full['negative_sentences'] = negative
df_full['positive_values'] = positive_sent_list
df_full['positive_sentences'] = positive
df_full['neutral_sentences'] = neutral
df_full['number_of_sentences'] = no_of_sentences

#after extracing the named entities, we save them in separate columns.
df_full['persons'] = person_list
df_full['locations'] = location_list
df_full['organisations'] = org_list

#finally we save the extended dataframe that now contains a full set of extracted metadata and enrichments
df_full.to_pickle("C:\\Users\\admin\\Dropbox\\sermon_mining\\kover_fidel\\df_preprocessed_full_w_NER_and_SENT.pickle")

#End of Session 9 (it was a bit overwhelming, wasn't it?)
#-------------------------------------------------------------------------


#Session 10. We will focus on speeches dealing with King Stephen (István) to explore textual features in this subset of the corpus (word clouds)
import pandas as pd
df_full = pd.read_pickle("C:\\Users\\admin\\Dropbox\\sermon_mining\\kover_fidel\\df_preprocessed_full_w_NER_and_SENT.pickle")

#list all uniqe items (the different identified organisations, locations and persons)
list(set().union(*[set(x) for x in org_list]))
list(set().union(*[set(x) for x in location_list]))
list(set().union(*[set(x) for x in person_list]))
#it seems to be far from perfect, but we have to make do with what we have

#play around with István (and save a subset to Excel to have a human readable baseline)
df_full[df_full['TEXT'].str.contains("István")].to_excel("C:\\Users\\admin\\Dropbox\\sermon_mining\\kover_fidel\\istvan.xlsx")

df_istvan = df_full[df_full['TEXT'].str.contains("István")].copy()

#first we generate word clouds for each year based on the speeches referring to István
from collections import Counter
from wordcloud import WordCloud
#generating word clouds with extended stop words
extended_stopwords = nlp.Defaults.stop_words | {'jézus', 'isten', 'ember', 'krisztus', 'úr', 'élet'}
for year in df_istvan['YEAR'].unique():
    speeches_of_the_year = []
    for i, row in df_istvan[df_istvan['YEAR']==str(year)].iterrows():
        speeches_of_the_year.append(' '.join(row['LEMMA']))
    #remove the top 10 words
    wordcount = Counter(' '.join(speeches_of_the_year).split())
    most_occur = wordcount.most_common(10)
    pruned_speeches_of_the_year = [x for x in speeches_of_the_year if x not in most_occur]
    wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               stopwords = extended_stopwords).generate(str(pruned_speeches_of_the_year))
    wordcloud.to_file('./Downloads/sermon_mining/wordcloud/wordcloud_istvan_'+str(year)+'.png')
    
#let's generate a word cloud based on ALL speeches referring to István, but excluding the 10 most common words
speeches = []
for i, row in df_istvan.iterrows():
    speeches.append(' '.join(row['LEMMA']))
wordcount = Counter(' '.join(speeches).split())
#get first tuple elements from a list a tuples (we dont't need the counts)
most_occur = [i[0] for i in wordcount.most_common(10)]
pruned_speeches = [x for x in speeches if x not in most_occur]
wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               stopwords = extended_stopwords).generate(str(pruned_speeches))
wordcloud.to_image()
    
#let's generate a word cloud based on ALL speeches referring to István, using only the adjectives
speeches = []
for i, row in df_istvan.iterrows():
    speeches.append(' '.join(row['ADJECTIVES']))
wordcount = Counter(' '.join(speeches).split())
#get first tuple elements from a list a tuples (we dont't need the counts)
#most_occur = [i[0] for i in wordcount.most_common(5)]
most_occur = []
pruned_speeches = [x for x in speeches if x not in most_occur]
wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               stopwords = extended_stopwords).generate(str(pruned_speeches))
wordcloud.to_image()

#let's generate a word cloud based on ALL speeches referring to István, using only the verbs
speeches = []
for i, row in df_istvan.iterrows():
    speeches.append(' '.join(row['VERBS']))
wordcount = Counter(' '.join(speeches).split())
#get first tuple elements from a list a tuples (we dont't need the counts)
most_occur = [i[0] for i in wordcount.most_common(4)]
stopset = set(extended_stopwords|set(most_occur))
#most_occur = []
#pruned_speeches = [x for x in speeches if x not in most_occur]
wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               stopwords = stopset).generate(str(pruned_speeches))
wordcloud.to_image()

#let's generate a word cloud based on ALL speeches referring to István, using only the nouns
speeches = []
for i, row in df_istvan.iterrows():
    speeches.append(' '.join(row['NOUNS']))
wordcount = Counter(' '.join(speeches).split())
#get first tuple elements from a list a tuples (we dont't need the counts)
#most_occur = [i[0] for i in wordcount.most_common(10)]
most_occour = []
pruned_speeches = [x for x in speeches if x not in most_occur]
wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               stopwords = extended_stopwords).generate(str(pruned_speeches))
wordcloud.to_image()

#End of Session 10
#-------------------------------------------------------------------------


#Session 11, we will explore n-grams in the speeches referring to István, to see the colocations associated with King Stephen
import re
from nltk.util import ngrams

#we first create a long text containing the lemmatized forms of the István speeches and feed it into the NLP parser (the Hungarian language model in Spacy)
speeches = []
s = ""
for i, row in df_istvan.iterrows():
    speeches.append(' '.join(row['LEMMA']))
s = s.join(speeches)
doc = nlp(s)

#tokenizing, and removing leftover punctuation and spaces
tokens = [token.orth_ for token in doc if not token.is_punct | token.is_space] 

#creating a list of ngrams from the tokenized text
output = list(ngrams(tokens, 5))

#filtering for ngrams (5-grams) containing the word "istván", so we only get the colocations of Istvn
istvan_ngrams5 = [item for item in output if "istván" in item]

#creating a word cloud of István 5-grams
istvan_colocations = []
for ngram5 in istvan_ngrams5:
    print(ngram5)
    ngram5_nlp = nlp(' '.join(ngram5))
    print(ngram5_nlp)
    for token in ngram5_nlp:
        if token.pos_ == 'ADJ' and token.is_alpha:
            istvan_colocations.append(str(token.lemma_).lower())
text = ' '.join(istvan_colocations)
wordcloud = WordCloud(
               width = 3000,
               height = 2000,
               background_color = 'white',
               collocations = False,
               stopwords = extended_stopwords).generate(text)
wordcloud.to_image()

#plotting sentiments calculated by the HUNLP package

#first we calculate a weighted average of negative and positive sentiment values based on the number of sentences in the respective speeches
df_full['HUNLP_sentiment'] = (df_full['negative_values'] / df_full['negative_sentences'] - df_full['positive_values']/ df_full['positive_sentences'])/df_full['number_of_sentences']

#we drop all lines where the date cannot be identified, as we are plotting how sentiments change with time
df_temp = df_full.dropna(subset=['DATE'])
#one series for the values weighted by total sentences
sent_series = df_temp['negative_values'] / df_temp['number_of_sentences'] - df_temp['positive_values']/ df_temp['number_of_sentences']
#one series for the values weighted by positive or negative sentences
sent_series2 = df_temp['negative_sentences'] / df_temp['number_of_sentences'] - df_temp['positive_sentences']/ df_temp['number_of_sentences']

#too much variation
fig, ax = plt.subplots(figsize = (10,10))

# add the x-axis and the y-axis to the plot
ax.plot(df_temp.sort_values('DATE')['DATE'], 
        #df_full['HUNLP_sentiment'], 
        sent_series,
        color = 'blue')

#ax.plot(df_temp.sort_values('DATE')['DATE'], 
#        #df_full['HUNLP_sentiment'], 
#        sent_series2,
#        color = 'red')

#ax.plot(df_lda_temp.sort_values('FULLDATE')['FULLDATE'], 
#        p(df_lda_temp.sort_values('FULLDATE')['SENTIMENT'].as_matrix()), 
#        color = 'blue')


# rotate tick labels
plt.setp(ax.get_xticklabels(), rotation=45)

# set title and labels for axes
ax.set(xlabel="Date",
       ylabel="Sentiment score (positive-negative)",
       title="Sentiment in the Rev. Kövér's speeches (dhuszti/sentanalysis)")


#now let's see how bigrams containing István change per year
speeches = []
s = ""
for i, row in df_full.iterrows():
    speeches.append(' '.join(row['TEXT']))
s = s.join(speeches)
doc = nlp(s)

tokens = [token.orth_ for token in doc if not token.is_punct | token.is_space] 

output_test = list(ngrams(tokens, 2))

#helper function for ngrams, so that we can get rid of n-grams containing digits
def contains_digit(s):
    return any(i.isdigit() for i in s)

df_istvan.dropna(subset=['DATE'], inplace=True)
from collections import defaultdict
bigram_dict = defaultdict()
for year in df_istvan['YEAR'].unique():
    print(year)
    speeches_of_the_year = []
    for i, row in df_istvan[df_istvan['YEAR']==year].iterrows():
        print (i)
        #creating one long string out of the list of lemmas for the wordcloud
        speeches_of_the_year.append(row['TEXT'])
    print(speeches_of_the_year)
    txt = ' '.join(speeches_of_the_year)
    doc = nlp(txt)
    tokens = [token.orth_ for token in doc if not token.is_punct | token.is_space] 
    tokens_clean = [token for token in tokens if not (token.lower() in extended_stopwords) | (token == "-e") | contains_digit(token)]
    output = list(ngrams(tokens_clean, 2))
    bigram_dict[year] = output
        
#TODO clean up bigram list from stopwords and duplicates
top_bigram_dict = defaultdict()
for year, bigrams in bigram_dict.items():
    print(year)
    bigram_count = Counter(bigram_dict[year])
    popular_bigrams = bigram_count.most_common(10)
    top_bigram_dict[year] = popular_bigrams

#plotting frequency distributions
import nltk
import matplotlib.pyplot as plt
from nltk.util import ngrams

s = ""
speeches = []
for i, row in df_istvan.iterrows():
    speeches.append(row['TEXT'])
s = s.join(speeches)
doc = nlp(s)
tokens = [token.orth_ for token in doc if not token.is_punct | token.is_space] 
tokens_clean = [token for token in tokens if not (token.lower() in extended_stopwords) | (token == "-e") | contains_digit(token)]
freqdist = nltk.FreqDist(tokens_clean)
plt.figure(figsize=(16,5))
freqdist.plot(50)

freqdist = nltk.FreqDist(list(ngrams(tokens_clean, 2)))
plt.figure(figsize=(16,5))
freqdist.plot(50)

freqdist = nltk.FreqDist(list(ngrams(tokens_clean, 3)))
plt.figure(figsize=(16,5))
freqdist.plot(50)

#full freqdist for the whole corpus
s = ""
speeches = []
for i, row in df_full.iterrows():
    speeches.append(row['TEXT'])
s = s.join(speeches)
doc = nlp(s)
tokens = [token.orth_ for token in doc if not token.is_punct | token.is_space] 
tokens_clean = [token for token in tokens if not (token.lower() in extended_stopwords) | (token == "-e") | contains_digit(token)]
freqdist = nltk.FreqDist(tokens_clean)
plt.figure(figsize=(16,5))
freqdist.plot(50)

freqdist = nltk.FreqDist(list(ngrams(tokens_clean, 2)))
plt.figure(figsize=(16,5))
freqdist.plot(50)

#not enough memory to handle the full text by the language model (16GB is insufficient), need to divide to 3 parts and then merge
s1 = s[:950002]
s2 = s[950002:1900000]
s3 = s[1900001:]

full_tokens = []
doc = nlp(s1)
tokens = [token.orth_ for token in doc if not token.is_punct | token.is_space] 
tokens_clean = [token for token in tokens if not (token.lower() in extended_stopwords) | (token == "-e") | contains_digit(token)]
doc2 = nlp(s2)
tokens_2 = [token.orth_ for token in doc2 if not token.is_punct | token.is_space] 
tokens_clean_2 = [token for token in tokens_2 if not (token.lower() in extended_stopwords) | (token == "-e") | contains_digit(token)]
doc3 = nlp(s3)
tokens_3 = [token.orth_ for token in doc3 if not token.is_punct | token.is_space] 
tokens_clean_3 = [token for token in tokens_3 if not (token.lower() in extended_stopwords) | (token == "-e") | contains_digit(token)]

full_tokens = tokens_clean + tokens_clean_2 + tokens_clean_3
freqdist = nltk.FreqDist(full_tokens)
plt.figure(figsize=(16,5))
freqdist.plot(50)

freqdist = nltk.FreqDist(list(ngrams(full_tokens, 2)))
plt.figure(figsize=(16,5))
freqdist.plot(50)

freqdist = nltk.FreqDist(list(ngrams(full_tokens, 3)))
plt.figure(figsize=(16,5))
freqdist.plot(50)

freqdist = nltk.FreqDist(list(ngrams(full_tokens, 4)))
plt.figure(figsize=(16,5))
freqdist.plot(50)

freqdist = nltk.FreqDist(list(ngrams(full_tokens, 5)))
plt.figure(figsize=(16,5))
freqdist.plot(50)