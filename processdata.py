#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 20:39:43 2020

@author: toriyokoyama
"""

import uuid
import pandas as pd
import os
import fasttext
from helpers import *
import pickle

#%%

# Global variables

VECTOR_SIZE = 100

#%%

###############################################
# clean and process data and create embedding #
###############################################

if __name__ == '__main__':
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
    
    # train word vector using recipe data
    model = fasttext.train_unsupervised('/home/toriyokoyama/Projects/AI Recipes/ingredients.txt',
                                        model='cbow',
                                        maxn=100,
                                        dim=VECTOR_SIZE)
    
    recipe_ingredients.to_pickle('/home/toriyokoyama/Projects/AI Recipes/recipe_ingredients_clean.pickle')
    model.save_model('/home/toriyokoyama/Projects/AI Recipes/recipe_ingredients_embedding_model.bin')
    
