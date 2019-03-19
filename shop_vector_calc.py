# Script to calculate shop vectors and save the matrix

### Import packages
import nltk
import pandas as pd
import numpy as np
import re
import gensim
import pickle
#import keras   # used in Jupyter notebook's extra exploratory analysis



### Load scraped data and preprocess
scrape_path = '~/Insight/project/scraped_data/'
reviews = pd.read_csv(scrape_path+'New%20York%2C%20NY&attrs20190122-013855.csv')



### Clean review text
# Get sentences from pandas dataframe. This will be a list of lists.
sentences = cleanreviews['lemmas'].tolist()
len(sentences)

# Function to clean up review text
def standardize_text(df, text_field):
    df[text_field] = df[text_field].str.replace(r"http\S+", "")
    df[text_field] = df[text_field].str.replace(r"http", "")
    df[text_field] = df[text_field].str.replace(r"@\S+", "")
    df[text_field] = df[text_field].str.replace(r"[^A-Za-z0-9(),!?@\'\`\"\_\n]", " ")
    df[text_field] = df[text_field].str.replace(r"@", "at")
    df[text_field] = df[text_field].str.lower()
    return df

cleanreviews = standardize_text(reviews, "review-text")

# Tokenize
from nltk.tokenize import RegexpTokenizer

tokenizer = RegexpTokenizer(r'\w+')   # separate sentences into different words

cleanreviews["tokens"] = cleanreviews["review-text"].apply(tokenizer.tokenize)

# Remove stop words
from nltk.corpus import stopwords
nltk.download('stopwords')
stop = stopwords.words('english')

cleanreviews['nostop'] = cleanreviews['tokens'].apply(lambda x: [item for item in x if item not in stop])

# Lemmatize
from nltk.stem.wordnet import WordNetLemmatizer
nltk.download('wordnet')
lemmatizer = WordNetLemmatizer()

def lemmatize_text(text):
    return [lemmatizer.lemmatize(x) for x in text]

cleanreviews['lemmas'] = cleanreviews['nostop'].apply(lemmatize_text)



### Prepare dataframe for modeling
coffeeshops = cleanreviews.groupby(['biz_url']).agg({'review-rating': 'mean', 'lemmas': lambda x: list(x)})

# Function to flatten the list of lists to one list with all review words
def flatten(inputdata):
    flat_list = [item for sublist in inputdata for item in sublist]
    return flat_list

coffeeshops['shopdoc'] = coffeeshops['lemmas'].apply(flatten)


# Get documents from pandas dataframe to make the vectors. This will be a list of lists (one list per shop)
sentences_shop = coffeeshops['shopdoc'].tolist()



### Create and train word2vec model
from gensim.models import Word2Vec

# Build model
#model = Word2Vec(sentences, size=100, window=5, min_count=3, workers=4)   # size and window for CBOW
model = Word2Vec(sentences, size=150, window=10, min_count=2, workers=10)  # size and window for skipgram
# Train model
model.train(sentences_shop, total_examples=len(sentences_shop), epochs=10)

# Save model
model.save("shop2vec_NYC_v1.model")



### Create vectors for shops
def rmv_nonDict (x, rmv, vocab):
    w = [token for token in x if (token not in rmv and token in vocab)]
    return w

remove = ['th','rd','st','']   # add anything you want to remove

# remove words not in vocabulary
coffeeshops['shopdoc_clean'] = coffeeshops['shopdoc'].apply(lambda x: rmv_nonDict(x, remove, model.wv.vocab))

# Create the vectors matrix: list of length number of shops
shopvectors_matrix = []

for i in range(len(coffeeshops)):
    review = coffeeshops.shopdoc_clean[i]
    shopvector = np.mean([model.wv.word_vec(token) for token in review],axis=0)
    shopvectors_matrix.append(shopvector)


### Save shop vectors
with open('shopvectors_matrix.data', 'wb') as f:
    # store the data as binary data stream
    pickle.dump(shopvectors_matrix, f)
