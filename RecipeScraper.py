#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 15 09:40:00 2020

@author: toriyokoyama
"""

#%%
# import libraries
from bs4 import BeautifulSoup
import mechanicalsoup
from gazpacho import Soup
import requests

#%%
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
}

#%%

MEASUREMENT_UNITS = ['cup','cups','c','teaspoon','teaspoons','tsp','tablespoon','tablespoons','tbsp',
                     'ml','grams','g','kilograms','kg','oz','ounce','ounces','lbs','lb','pound','pounds']
FRACTIONS = ['1/8','1/4','1/3','1/2','2/3','3/4','3/8','5/8','7/8']

#%%
# define abstract class for general scraper
class RecipeScraper(object):
    def __init__(self,url):
        self.url = url
        self.req = requests.get(self.url,headers=HEADERS)
        self.soup = BeautifulSoup(self.req.content,'html.parser')
        
    def get_soup(self):
        '''
        return beautifulsoup object. will mostly be used for testing and writing code.
        '''
        return self.soup
    
    def get_url(self):
        '''
        return url
        '''
        return self.url
    
    def get_host(self):
        '''
        return host
        '''
        raise NotImplementedError('This method needs to be implemented')
    
    def get_ingredients(self):
        '''
        parse html for ingredient list
        '''
        raise NotImplementedError('This method needs to be implemented')
        
    def get_cook_time(self):
        '''
        parse html for cooktime
        '''
        raise NotImplementedError('This method needs to be implemented')
        
    def get_prep_time(self):
        '''
        parse html for preptime
        '''
        raise NotImplementedError('This method needs to be implemented')
        
    def get_total_time(self):
        '''
        parse html for preptime
        '''
        raise NotImplementedError('This method needs to be implemented')
        
    def get_steps(self):
        '''
        parse html for recipe steps
        '''
        raise NotImplementedError('This method needs to be implemented')
        
    def get_rating(self):
        '''
        parse html for rating
        '''
        raise NotImplementedError('This method needs to be implemented')
