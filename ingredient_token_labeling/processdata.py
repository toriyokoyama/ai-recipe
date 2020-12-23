#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 23 20:57:56 2020

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

# Import data

recipe_ingredients = pd.read_pickle('/home/toriyokoyama/Projects/ai_recipes/ingredient_embedding/recipe_ingredients_clean.pickle')

#%%

# Functions

def tokens_to_rows_alt(group,token_col):
    '''
    function to use in pandas apply method to turn list of tokens into long format with the rest of the dataframe

    Parameters
    ----------
    group : dataframe
        input df with a column that is a list of tokens
    token_col : string
        column that is a list of tokens; which should be the last column

    Returns
    -------
    df that has the list of tokens long instead of wide

    '''
    
    r = group.iloc[0:1]

    # list of tokens
    ls = r[token_col].values[0]
    
    # repeat other columns of the df to match the number of tokens
    # turn an array of tokens into rows and concatente with the above
    return pd.DataFrame(np.concatenate((np.repeat(r.drop(token_col,axis=1).values,len(ls),axis=0)
                                        ,np.array(r[token_col].values[0]).reshape(-1,1)),axis=1)
                        ,columns=r.columns)

#%%

# tokenize words
recipe_ingredients['ingredient-token'] = recipe_ingredients.loc[:,'ingredient-full-mod'].apply(nltk.word_tokenize)

# make tokenized lists into dataframe in long format
cols = list(recipe_ingredients.drop('ingredient-token',axis=1).columns)
recipe_ingredients_long = recipe_ingredients.groupby(cols,group_keys=False).apply(tokens_to_rows_alt,token_col=('ingredient-token'))

recipe_ingredients_long.to_pickle('/home/toriyokoyama/Projects/ai_recipes/ingredient_token_labeling/recipe_ingredients_clean_long.pickle')


