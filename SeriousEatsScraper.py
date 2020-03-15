#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 10:21:10 2020

@author: toriyokoyama
"""

import os
os.chdir('/home/toriyokoyama/Projects/AI Recipes/')
from RecipeScraper import RecipeScraper
import re
import numpy as np

#%%

MEASUREMENT_UNITS = ['cup','cups','c','teaspoon','teaspoons','tsp','tablespoon','tablespoons','tbsp',
                     'ml','grams','g','kilograms','kg','oz','ounce','ounces']
FRACTIONS = ['1/8','1/4','1/3','1/2','2/3','3/4','3/8','5/8','7/8']

#%%

class SeriousEatsScraper(RecipeScraper):
    def get_ingredients(self):
        '''
        get ingredients as a list of dictionaries with amounts, units, and actual ingredient
        
        would be great if I could eventually apply a temporal NN to split these out appropriately
        '''
        ingredients = self.soup.findAll('li',{'class':'ingredient'})
        ingredients_processed = []
        for ingredient in ingredients:
            # turn ingredient item into a list
            ingredient_words = ingredient.get_text()
            # get start and end of parentheses
            paren_st = [c.start() for c in re.finditer('\(',ingredient_words)]
            paren_end = [c.start() for c in re.finditer('\)',ingredient_words)]
            ingredient_char = []
            ingredient_char_incl = np.ones((len(ingredient_words)))
            if paren_st != [] and paren_end != []:
                for start, end in zip(paren_st,paren_end):
                    ingredient_char_incl[start:end+1] = 0
            for i in range(len(ingredient_words)):
                if ingredient_char_incl[i]==1:
                    ingredient_char.append(ingredient_words[i])
            ingredient_words = ''.join(ingredient_char).split(' ')
            # remove ones that are in parentheses, strip out punctuation, and make lowercase
            ingredient_words = [ingredient_word.strip('.;,').lower() for ingredient_word in ingredient_words]
            amount = [w for w in ingredient_words if w.isnumeric() or w in FRACTIONS]
            units = [w for w in ingredient_words if w in MEASUREMENT_UNITS]
            food = [w for w in ingredient_words if w not in amount and w not in units]
            ingredients_processed.append({'Amount':' '.join(amount),'Units':' '.join(units),'Ingredient':' '.join(food)})
        return ingredients_processed
            
            
