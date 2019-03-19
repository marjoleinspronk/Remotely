#!/usr/bin/python

# Import
#import requests

from flask import Flask, render_template, flash, request, redirect, url_for
import flask, sklearn, os, string, re, gensim
import pandas as pd
import pickle
import numpy as np
from sklearn.externals import joblib
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
from string import digits
from uszipcode import SearchEngine   # to convert zipcode to longitude and latitude
from haversine import haversine   # to calculate euclidian distance from longitude and latitude
search = SearchEngine(simple_zipcode=True)

#Initialize app
app = Flask(__name__, static_url_path='/static')


### Load shop vectors
with open('data/shopvectors_matrix.data', 'rb') as f:
    shopvectors_matrix = pickle.load(f)


#### Process user input
from nltk.corpus import stopwords
#nltk.download('stopwords')
stop = stopwords.words('english')

punctuations = string.punctuation

# Function to process sentence
def process_string_to_normvector(sentence, quiet_importance, user_socket):
    model = gensim.models.KeyedVectors.load('data/shop2vec_NYC_v1.model')
    model.init_sims(replace=True)   # forget original vectors, only use normalized ones (saves memory)
    #remove trailing spaces + lowercase
    processed = sentence.strip().lower().split()
    #remove numbers, stopwords, and punctuations
    processed = [token.translate({ord(k): None for k in digits}) for token in processed if(token not in stop and token not in punctuations)]
    remove = ['th','rd','st','']
    processed = [re.sub(r'\W', '', token).strip() if hasattr(token,'strip') else re.sub(r'\W', '', token) for token in processed]
    processed = [token for token in processed if (token not in remove and token in model.wv.vocab)]
    processed.append('work')
    processed = processed*5

    if quiet_importance ==2:
        processed.append('quiet')
    if quiet_importance ==3:
        processed.append('quiet')
        processed.append('quiet')
    if user_socket ==2:
        processed.append('charge')
    if(len(processed)==0):
        return None
    else:
        processed = np.mean([model.wv.word_vec(token) for token in processed],axis=0)
        return processed/np.linalg.norm(processed)

# Function to process zipcodes and get euclidian distance
def eucl_dist_zipcode(user_zip, shop_zip):

    user_zipcode = search.by_zipcode(user_zip)
    zip_dict_user = user_zipcode.to_dict()
    user_lat = zip_dict_user.get('lat')
    user_lng = zip_dict_user.get('lng')

    # get zipcode coffeeshop from df and convert to lat, lng
    shop_zipcode = search.by_zipcode(shop_zip)
    zip_dict_shop = shop_zipcode.to_dict()
    shop_lat = zip_dict_shop.get('lat')
    shop_lng = zip_dict_shop.get('lng')

    user_location = (user_lat, user_lng) # (lat, lon)
    shop_location = (shop_lat, shop_lng)

    eucl_distance = haversine(user_location, shop_location, unit='mi')
    return eucl_distance


# Similarity function
def cos_all (x,y):
    cs = cosine_similarity(y.reshape(1,-1), x.reshape(1,-1))
    return cs


# Input processing function
def process_input(sentence, quiet_importance, user_socket, user_zipcode):
    vector_userinput = process_string_to_normvector(sentence, quiet_importance, user_socket)
    if vector_userinput is None:
        return None
    else:
        new_df = pd.read_pickle('data/coffeeshop_info_NYC_NJ_zipcode_clean2.pkl')
        user_zipcode = str(user_zipcode)
        user_zip = user_zipcode   #user_zip = search.by_zipcode("10024")
        shop_zips = new_df.zip_string

        # Add to dataframe
        new_df["sims"] = [cos_all(vector_userinput,shopvectors_matrix[x]) for x in range(len(new_df))]
        new_df["eucl_dist"] = [eucl_dist_zipcode(user_zip, str(shop_zips[x])) for x in range(len(new_df))]
        new_df_2miles = new_df[new_df.eucl_dist <= 1.0]

        # Determine best matches
        winners = new_df_2miles.sort_values('sims', ascending=False).head(3)
        winner_name = winners.biz_name_x.iloc[0]
        winner_name2 = winners.biz_name_x.iloc[1]
        winner_name3 = winners.biz_name_x.iloc[2]
        winner_url = 'https://www.yelp.com/'+winners.biz_url.iloc[0]
        winner_url2 = 'https://www.yelp.com/'+winners.biz_url.iloc[1]
        winner_url3 = 'https://www.yelp.com/'+winners.biz_url.iloc[2]
        return winner_name, winner_name2, winner_name3, winner_url, winner_url2, winner_url3

##########################################################################################

@app.template_filter('nl2br')
def nl2br(s):
	return s.replace("\n", "<br />")

@app.template_filter('nan')
def not_available(s):
	return str(s).replace("nan", "Not Available")


#Standard home page. 'index.html' has the CSS and HTML for the app
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


# Home page redirects to recommender.html where the user fills out survey
@app.route('/recommender', methods=['GET', 'POST'])
def recommender():
    return render_template('recommender.html')


@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    #city = request.form['user_city']
    quiet_importance = int(request.form['quiet_importance'])
    user_socket = int(request.form['socket_importance'])
    sentence = request.form['user_shop_wishes']
    user_zipcode = int(request.form['user_zipcode'])

    [match, match2, match3, match_url, match_url2, match_url3] = process_input(sentence, quiet_importance, user_socket, user_zipcode)

    return render_template('recommendations.html', sentence=sentence, match=match, match2=match2, match3=match3, match_url=match_url, match_url2=match_url2, match_url3=match_url3)  #matches=matches, sentence=sentence,location=location


if __name__ == '__main__':
    #this runs your app locally
    app.run(host='0.0.0.0', port=5000, debug=True)
