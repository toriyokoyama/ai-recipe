#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 20:39:43 2020

@author: toriyokoyama
"""

import uuid
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import nltk
import wordcloud
import textblob
#import sklearn
#import tensorflow as tf
#import keras
import os
import fasttext
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE

#%%

# Global variables

VECTOR_SIZE = 100

#%%

####################
# helper functions #
####################

def cleanup(ingredient):
    '''
    Clean up ingredients for tokenization and analysis

    Parameters
    ----------
    ingredient : string
        ingredient item from a recipe

    Returns
    -------
    ingredient : string
        cleaned up string

    '''
    ingredient = ingredient.replace('\(','')
    ingredient = ingredient.replace('\)','')
    ingredient = ingredient.replace('(','')
    ingredient = ingredient.replace(')','')
    ingredient = ingredient.replace(';','')
    ingredient = ingredient.replace('.','')
    ingredient = ingredient.replace(',','')
    ingredient = ingredient.replace(':','')
    ingredient = ingredient.replace('*','')
    ingredient = ingredient.strip(' ')
    ingredient = ingredient.replace(u'\xa0',' ')
    ingredient = ingredient.lower()
    return ingredient

def vectorize(tokens,model,vector_size=VECTOR_SIZE):
    '''
    Vectorize/embed the tokens for an ingredient item

    Parameters
    ----------
    tokens : list
        words making up an ingredient
    model : fasttext model object
        fasttext model object for embedding words, trained with recipe data 
    vector_size : int, optional
        size of embedding. The default is VECTOR_SIZE.

    Returns
    -------
    array
        average word embedding for all tokens/words in an ingredient item

    '''
    total_vector = np.zeros((vector_size,))
    for t in tokens:
        total_vector += model[t]
    return total_vector / len(tokens)

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

def get_closest_words(word,labels,word_vecs,topn=5):
    '''
    find topn words using cosine similarity
    '''
    # get cosine similarity of vectors
    cs_matrix = cosine_similarity(word_vecs)

    word_idx = labels.index(word)
    cs_vec = cs_matrix[word_idx,:]
    most_similar_idx = np.argsort(cs_vec)[::-1][:topn]
    
    return np.array(labels)[most_similar_idx], word_vecs[most_similar_idx]

def display_closestwords_tsnescatterplot(word, words, wv, topn=20):

    # get close words
    close_words, close_vecs = get_closest_words(word, words, wv, topn=topn)
    
    tsne = TSNE(n_components=2)
    Y = tsne.fit_transform(close_vecs)

    x_coords = Y[:, 0]
    y_coords = Y[:, 1]
    # display scatter plot
    plt.scatter(x_coords, y_coords)

    for label, x, y in zip(close_words, x_coords, y_coords):
        plt.annotate(label, xy=(x, y), xytext=(0, 0), textcoords='offset points')
    plt.xlim(x_coords.min()+0.00005, x_coords.max()+0.00005)
    plt.ylim(y_coords.min()+0.00005, y_coords.max()+0.00005)
    plt.show()

#%%

##########################
# clean and process data #
##########################

# import data to df
recipe_ingredients = pd.read_csv('/home/toriyokoyama/Projects/AI Recipes/ingredients.csv')
recipe_ingredients.dropna(inplace=True,subset=['ingredient-full'])
# create unique hash ID
recipe_ingredients['ID'] = recipe_ingredients['url'].apply(lambda x: uuid.uuid5(uuid.NAMESPACE_URL,x))

# add marker to indicate end of sentence for ingredients and make lowercase
recipe_ingredients['ingredient-full-mod'] = recipe_ingredients['ingredient-full'].apply(lambda x: cleanup(x) + ' EOS')

# see if file already exists (and delete if it does)
try:
    os.remove('/home/toriyokoyama/Projects/AI Recipes/ingredients.txt')
except:
    pass

# create text file that fasttext can use to process
ID = ''
with open('/home/toriyokoyama/Projects/AI Recipes/ingredients.txt','w') as f:
    for ingredient, rid in zip(recipe_ingredients['ingredient-full'],recipe_ingredients['ID']):
        if ID == '':
            pass
        elif ID != rid:
            f.write('EOS \n')
        ingredient = cleanup(ingredient)
        f.write(ingredient + ' ')
        ID = rid

#%%

# train word vector using recipe data
model = fasttext.train_unsupervised('/home/toriyokoyama/Projects/AI Recipes/ingredients.txt',
                                    model='cbow',
                                    maxn=100)

#%%

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
    
get_closest_words('sugar',words,word_vectors)

display_closestwords_tsnescatterplot('sugar', words, word_vectors)

#%% 

# tokenize words and get vectors

recipe_ingredients['ingredient-token'] = recipe_ingredients.loc[:,'ingredient-full-mod'].apply(nltk.word_tokenize)
recipe_ingredients['ingredient-vec'] = recipe_ingredients['ingredient-token'].apply(lambda x: vectorize(x,model))

# TODO
# get mean of ingredient vectors by recipe to compare recipes

recipe_ingredients[['ID','title','ingredient-vec']].groupby(['ID','title']).sum()
