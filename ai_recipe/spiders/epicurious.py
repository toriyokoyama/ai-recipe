# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
import re
import numpy as np

#%%

MEASUREMENT_UNITS = ['cup','cups','c','teaspoon','teaspoons','tsp','tablespoon','tablespoons','tbsp',
                     'ml','grams','g','kilograms','kg','oz','ounce','ounces','lbs','lb','pound','pounds']
FRACTIONS = ['1/8','1/4','1/3','1/2','2/3','3/4','3/8','5/8','7/8']

#%%

class EpicuriousSpider(scrapy.Spider):
    name = 'epicurious'
    allowed_domains = ['epicurious.com']
    start_urls = ['https://www.epicurious.com/search?content=recipe'] + ['https://www.epicurious.com/search?content=recipe&page=' + str(pg) for pg in range(2,2020)] #looks like there are 2019 total pages of recipes

    custom_settings={ 'FEED_FORMAT': 'csv',
                     'FEED_EXPORTERS': {'csv':'AiRecipePipeline'}}
                     #'DEPTH_LIMIT': 1} # if testing, overriding depth_limit helps
    urls_visited = []
    
    def parse(self, response):
        xp = "//article[@class='recipe-content-card']/a/@href"
        return (Request('https://www.' + self.allowed_domains[0] + url, callback=self.parse_recipe_site) for url in response.xpath(xp).extract())
       
    def parse_recipe_site(self,response):    
        print('Processing URL '+response.url)
        # check if this url has been visited already to avoid duplicates and to stop perpetual crawl
        url_visited = response.url in self.urls_visited
        # add it to the urls visited
        self.urls_visited.append(response.url)
        
        # only export data for recipes 
        if ('recipes/' in response.url) and ('views/' in response.url) and (not url_visited):
            # create dictionary to store data that will be passed to the exporter
            recipe_data = {'ingredients':{'url':[],'title':[],'site':[],'amount':[],'units':[],'ingredient':[]},
                           'steps':{'url':[],'title':[],'site':[],'number':[],'step':[]},
                           'tags':{'url':[],'title':[],'site':[],'tag':[]},
                           'recipe-level':{'url':[],'title':[],'site':[],'cook_time_val':None,'cook_time_unit':None,'prep_time_val':None,'prep_time_unit':None,'total_time_val':None,'total_time_unit':None,'rating':None}}
            
            # extract title of the recipe; two forward slashes gets all text (includes those in format tags)
            title = [response.xpath("//div[@class='title-source']/h1/text()").extract()[0].replace('\n','').strip(' ')]
            
            # process ingredients
            ingredients = response.xpath("//div[@class='ingredients-info']//ol/li/ul/li/text()").extract()
            for ingredient in ingredients:
                # turn ingredient item into a list
                ingredient_words = ingredient
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
                recipe_data['ingredients']['url'].append(response.url)
                recipe_data['ingredients']['title'].append(title)
                recipe_data['ingredients']['site'].append(self.name)
                recipe_data['ingredients']['amount'].append(' '.join(amount))
                recipe_data['ingredients']['units'].append(' '.join(units))
                recipe_data['ingredients']['ingredient'].append(' '.join(food))
            
            # get average rating
            try:
                recipe_data['recipe-level']['rating'] = [response.xpath("//span[@class='rating']/text()").extract()[0].split('/')[0]]
            except:
                recipe_data['recipe-level']['rating'] = [-1]
                
            # get times
            recipe_data['recipe-level']['url'].append(response.url)
            recipe_data['recipe-level']['title'].append(title)
            recipe_data['recipe-level']['site'].append(self.name)
            
            # store prep time; in the recipes i've looked at, i didn't see any estimated times
            recipe_data['recipe-level']['prep_time_val'] = [-1]
            recipe_data['recipe-level']['prep_time_unit'] = ['unk']
            
            # store total time; in the recipes i've looked at, i didn't see any estimated times
            recipe_data['recipe-level']['total_time_val'] = [-1]
            recipe_data['recipe-level']['total_time_unit'] = ['unk']
                    
            # derive cook time; in the recipes i've looked at, i didn't see any estimated times
            recipe_data['recipe-level']['cook_time_val'] = [-1]
            recipe_data['recipe-level']['cook_time_unit'] = ['unk']
                
            # get steps, excluding the numbers here (derived)
            steps_section = response.xpath("//div[@class='instructions']//ol/li/ol/li/text()").extract()
            for i, steps in enumerate(steps_section):
                recipe_data['steps']['url'].append(response.url)
                recipe_data['steps']['title'].append(title)
                recipe_data['steps']['site'].append(self.name)   
                recipe_data['steps']['number'].append(i+1)
                # remove next line escapes
                recipe_data['steps']['step'].append(steps.replace('\n','').strip(' '))
                
            # get tags
            tags_section = response.xpath("//dl[@class='tags']//dt/text()").extract()
            for tag in tags_section:
                recipe_data['tags']['url'].append(response.url)
                recipe_data['tags']['title'].append(title)
                recipe_data['tags']['site'].append(self.name)   
                recipe_data['tags']['tag'].append(tag)
              
            yield recipe_data
        
        # stop crawling further urls if that has already been done for this url
        if url_visited:
            return None
        else:
            # otherwise, look go deeper into other links on the page
            next_urls = response.xpath("//div[@class='riser-item']/a/@href").extract()
            next_urls = next_urls + ['https://www.' + self.allowed_domains[0] + ending for ending in response.xpath("//dl[@class='tags']//a/@href").extract()]
            
            for url in next_urls:
                yield (Request(url, callback=self.parse_recipe_site))
        
