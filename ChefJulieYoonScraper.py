#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 10:21:10 2020

@author: toriyokoyama
"""

#import os
#os.chdir('/home/toriyokoyama/Projects/AI Recipes/')
import sys
sys.path.insert(1,'/home/toriyokoyama/Projects/AI Recipes/')
sys.path.insert(1,'/home/torisbaker/Git/ai-recipe/')
from RecipeScraper import RecipeScraper
import re
import numpy as np

#%%

class ChefJulieYoonScraper(RecipeScraper):
    
    def get_host(self):
        '''
        return host site
        '''
        return 'chefjulieyoon.com'
    
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
            # exclude characters between parentheses
            if paren_st != [] and paren_end != []:
                for start, end in zip(paren_st,paren_end):
                    ingredient_char_incl[start:end+1] = 0
            # create list of characters to keep
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
    
    def get_cook_time(self):
        '''
        get cook time
        '''
        # get time from soup
        cooktime = self.soup.find('time',{'itemprop':'cookTime'}).get_text().split(' ')
        cooktime_dict = {}
        # separate into value and the units; need to modify this to allow for something like 1 hour 30 minutes
        for w in cooktime:
            if w.isnumeric():
                cooktime_dict['value'] = float(w)
            else:
                cooktime_dict['unit'] = w
        
        return cooktime_dict
    
    def get_prep_time(self):
        '''
        get prep time
        '''
        # get time from soup
        preptime = self.soup.find('time',{'itemprop':'prepTime'}).get_text().split(' ')
        preptime_dict = {}
        # separate into value and the units; need to modify this to allow for something like 1 hour 30 minutes
        for w in preptime:
            if w.isnumeric():
                preptime_dict['value'] = float(w)
            else:
                preptime_dict['unit'] = w
        
        return preptime_dict
    
    def get_total_time(self):
        '''
        get total time
        '''
        # get time from soup
        totaltime = self.soup.find('time',{'itemprop':'totalTime'}).get_text().split(' ')
        totaltime_dict = {}
        # separate into value and the units; need to modify this to allow for something like 1 hour 30 minutes
        for w in totaltime:
            if w.isnumeric():
                totaltime_dict['value'] = float(w)
            else:
                totaltime_dict['unit'] = w
        
        return totaltime_dict
    
    def get_steps(self):
        '''
        get recipe steps
        '''
        # get steps from soup, excluding the numbers here
        steps_section = self.soup.findAll('li',{'class':'instruction'})
        steps_dict = {}
        for i, steps in enumerate(steps_section):
            # remove next line escapes
            steps_dict['step'+str(i+1)] = re.sub('\n','',steps.get_text())
        
        return steps_dict

    
    def get_rating(self):
        '''
        get rating
        '''
        
        # no rating on this website        
        return -1
    
#%%
cjy = ChefJulieYoonScraper('https://chefjulieyoon.com/2015/07/korean-spicy-kimchi-noodles/')            
