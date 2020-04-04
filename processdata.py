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


#%%

# import data to df
recipe_ingredients = pd.read_csv('/home/toriyokoyama/Projects/AI Recipes/ingredients.csv')
recipe_ingredients.dropna(inplace=True,subset=['ingredient-full'])
# create unique hash ID
recipe_ingredients['ID'] = recipe_ingredients['url'].apply(lambda x: uuid.uuid5(uuid.NAMESPACE_URL,x))
# add marker to indicate end of sentence for ingredients and make lowercase
recipe_ingredients['ingredient-full-mod'] = recipe_ingredients['ingredient-full'].apply(lambda x: x.lower() + ' EOS')

#%%

tokens = recipe_ingredients.loc[:,'ingredient-full-mod'].apply(nltk.word_tokenize)

#%%

wc = wordcloud.WordCloud(relative_scaling=1.0,stopwords=nltk.corpus.stopwords.words('english'))
wc.generate(''.join(recipe_ingredients.loc[:,'ingredient-full-mod']))

#%%

def plot_wordcloud(wc):
    plt.imshow(wc)
    plt.axis('off')
    plt.show()

plot_wordcloud(wc)

