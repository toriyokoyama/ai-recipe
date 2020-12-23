#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 20:57:56 2020

@author: toriyokoyama
"""

import os
os.chdir('/home/toriyokoyama/Projects/ai_recipes/')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import nltk
import wordcloud
#import textblob
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
from ingredient_embedding.helpers import *
import fasttext

#%%

# Import data and model

recipe_ingredients = pd.read_pickle('/home/toriyokoyama/Projects/ai_recipes/ingredient_embedding/recipe_ingredients_clean.pickle')
model = fasttext.load_model('/home/toriyokoyama/Projects/ai_recipes/ingredient_embedding/recipe_ingredients_embedding_model.bin')

#%%

# Global variables

VECTOR_SIZE = model['word'].shape[0]

#%%

####################################
# analysis functions for closeness #
####################################

def plot_wordcloud():
    '''
    create wordcloud for analysis
    '''
    wc = wordcloud.WordCloud(relative_scaling=1.0,stopwords=nltk.corpus.stopwords.words('english'))
    wc.generate(''.join(recipe_ingredients.loc[:,'ingredient-full-mod']))
    plt.imshow(wc)
    plt.axis('off')
    plt.show()

def get_closest(item,labels,vecs,topn=5):
    '''
    find topn items using cosine similarity
    '''
    # get cosine similarity of vectors
    cs_matrix = cosine_similarity(vecs)

    word_idx = labels.index(item)
    cs_vec = cs_matrix[word_idx,:]
    most_similar_idx = np.argsort(cs_vec)[::-1][:topn]
    
    return np.array(labels)[most_similar_idx], vecs[most_similar_idx]

def display_closest_tsnescatterplot(item, labels, wv, topn=20):

    # get close items
    close_items, close_vecs = get_closest(item, labels, wv, topn=topn)
    
    tsne = TSNE(n_components=2)
    Y = tsne.fit_transform(close_vecs)

    x_coords = Y[:, 0]
    y_coords = Y[:, 1]
    # display scatter plot
    plt.scatter(x_coords, y_coords)

    for label, x, y in zip(close_items, x_coords, y_coords):
        plt.annotate(label, xy=(x, y), xytext=(0, 0), textcoords='offset points')
    plt.xlim(x_coords.min()+0.00005, x_coords.max()+0.00005)
    plt.ylim(y_coords.min()+0.00005, y_coords.max()+0.00005)
    plt.show()


#############################
# visual analysis and tests #
#############################

# create wordcloud plot
plot_wordcloud()

# pull word vectors from trained model
words = []
word_vectors = np.empty((len(model.words),VECTOR_SIZE))

for w, word in enumerate(model.words):
    words.append(word)
    word_vectors[w,:] = model[word]
    
# get closest ingredient compared to other ingredient vectors
get_closest('onion',words,word_vectors,topn=20)[0]

display_closest_tsnescatterplot('sugar', words, word_vectors)


# tokenize words and get vectors for each ingredient list item
recipe_ingredients['ingredient-token'] = recipe_ingredients.loc[:,'ingredient-full-mod'].apply(nltk.word_tokenize)
recipe_ingredients['ingredient-vec'] = recipe_ingredients['ingredient-token'].apply(lambda x: vectorize(x,model,VECTOR_SIZE))

# aggregate recipe information to get an average vector
agg_recipe_df = recipe_ingredients[['ID','title','url','ingredient-vec']].groupby(['ID','title','url']).apply(mean_ingredient_vec,vector_size=VECTOR_SIZE).reset_index()
agg_recipe_df.columns = ['ID','title','url','ingredient-vec']

recipe_labels = list(agg_recipe_df['title'])
recipe_vecs = np.concatenate(agg_recipe_df['ingredient-vec'].array).reshape(-1,VECTOR_SIZE)

# get closest recipe compared to other recipe vectors
get_closest(recipe_labels[1000],recipe_labels,recipe_vecs)[0]

display_closest_tsnescatterplot(recipe_labels[1],recipe_labels,recipe_vecs)

# export recipe vector by ID
pd.concat((agg_recipe_df[['ID','url']],pd.DataFrame(recipe_vecs,columns=['emb'+str(i) for i in range(0,VECTOR_SIZE)])),axis=1).to_csv('/home/toriyokoyama/Projects/ai_recipes/recipe_ingredients_embedding.csv',index=False)
