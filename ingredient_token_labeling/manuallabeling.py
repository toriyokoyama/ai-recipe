#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 25 12:09:16 2020

@author: toriyokoyama
"""

import pandas as pd

#recipe_ingredients_long_label = pd.read_pickle('/home/toriyokoyama/Projects/ai_recipes/ingredient_token_labeling/recipe_ingredients_clean_long.pickle')
#recipe_ingredients_long_label['label'] = ''

recipe_ingredients_long_label = pd.read_pickle('/home/toriyokoyama/Projects/ai_recipes/ingredient_token_labeling/recipe_ingredients_clean_long_label.pickle')

#%%

r = 0
ignore_filled = True
while r < len(recipe_ingredients_long_label):
    if (recipe_ingredients_long_label['label'].iloc[r] != '') & (ignore_filled == True):
        r += 1
        continue
    elif recipe_ingredients_long_label['ingredient-token'].iloc[r] == 'EOS':
        recipe_ingredients_long_label['label'].iloc[r] = 'EOS'
    else:
        print('Full item: {}'.format(recipe_ingredients_long_label['ingredient-full-mod'].iloc[r]))
        print('Token: {}'.format(recipe_ingredients_long_label['ingredient-token'].iloc[r]))
        print('Enter the table for the token from the following options: \n(c)ount, \n(a)mount, \n(m)easure, \n(s)ize, \n(p)reparation, \n(f)ood, \n(o)ther')
        print('XXX to stop, (b<n>) to go back')
        label = input('>>')
        if label=='XXX':
            break
        elif label[0]=='b':
            r -= int(label[1])
            ignore_filled = False
            continue
        else:
            recipe_ingredients_long_label['label'].iloc[r] = label
    ignore_filled = True
    r += 1
    
#%%

recipe_ingredients_long_label[recipe_ingredients_long_label['label'] != ''].shape
    
#%%

# write out updated data
recipe_ingredients_long_label.to_pickle('/home/toriyokoyama/Projects/ai_recipes/ingredient_token_labeling/recipe_ingredients_clean_long_label.pickle')
