# -*- coding: utf-8 -*-
import scrapy
import re
import numpy as np

#%%

MEASUREMENT_UNITS = ['cup','cups','c','teaspoon','teaspoons','tsp','tablespoon','tablespoons','tbsp',
                     'ml','grams','g','kilograms','kg','oz','ounce','ounces','lbs','lb','pound','pounds']
FRACTIONS = ['1/8','1/4','1/3','1/2','2/3','3/4','3/8','5/8','7/8']

#%%

class SeriouseatsSpider(scrapy.Spider):
    name = 'seriouseats'
    allowed_domains = ['seriouseats.com']
    start_urls = ['https://www.seriouseats.com/recipes/2012/02/rich-and-creamy-tonkotsu-ramen-broth-from-scratch-recipe.html']

    custom_settings={ 'FEED_FORMAT': 'csv',
                     'FEED_EXPORTERS': {'csv':'AiRecipePipeline'}}
    
    def parse(self, response):
        print('Processing URL '+response.url)
        
        recipe_data = {'ingredients':{'url':[],'title':[],'site':[],'amount':[],'units':[],'ingredient':[]},
                       'steps':{'url':[],'title':[],'site':[],'number':[],'step':[]},
                       'recipe-level':{'url':[],'title':[],'site':[],'cook_time_val':None,'cook_time_unit':None,'prep_time_val':None,'prep_time_unit':None,'total_time_val':None,'total_time_unit':None,'rating':None}}
        
        title = response.xpath("//h1[@class='title recipe-title c-post__h1']/text()").extract()
        
        # process ingredients
        ingredients = response.xpath("//li[@class='ingredient']/text()").extract()
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
            
        # get times
        times = response.xpath("//span[@class='info']/text()").extract()
        recipe_data['recipe-level']['url'].append(response.url)
        recipe_data['recipe-level']['title'].append(title)
        recipe_data['recipe-level']['site'].append(self.name)
        
        # get average rating
        recipe_data['recipe-level']['rating'] = [response.xpath("//span[@class='info rating-value']/text()").extract()[0]]
        
        # store prep time
        preptime = times[0].split(' ')
        # separate into value and the units; need to modify this to allow for something like 1 hour 30 minutes
        for w in preptime:
            if w.isnumeric():
                recipe_data['recipe-level']['prep_time_val'] = [float(w)]
            else:
                recipe_data['recipe-level']['prep_time_unit'] = [w]
                
        # store total time
        totaltime = times[1].split(' ')
        # separate into value and the units; need to modify this to allow for something like 1 hour 30 minutes
        for w in totaltime:
            if w.isnumeric():
                recipe_data['recipe-level']['total_time_val'] = [float(w)]
            else:
                recipe_data['recipe-level']['total_time_unit'] = [w]
                
        # derive cook time
        if (recipe_data['recipe-level']['total_time_unit'][0].lower() == recipe_data['recipe-level']['prep_time_unit'][0].lower()) or (recipe_data['recipe-level']['total_time_unit'][0].lower() == ''.join(list(recipe_data['recipe-level']['prep_time_unit'][0].lower())+['s'])):
            recipe_data['recipe-level']['cook_time_val'] = [recipe_data['recipe-level']['total_time_val'][0] - recipe_data['recipe-level']['prep_time_val'][0]]
            recipe_data['recipe-level']['cook_time_unit'] = [recipe_data['recipe-level']['total_time_unit'][0]]
        else:
            #raise ValueError('Values of time in different units')
            recipe_data['recipe-level']['cook_time_val'] = [-1]
            recipe_data['recipe-level']['cook_time_unit'] = [-1]
            
        # get steps from soup, excluding the numbers here
        steps_section = response.xpath("//div[@class='recipe-procedure-text']/text()").extract()
        for i, steps in enumerate(steps_section):
            recipe_data['steps']['url'].append(response.url)
            recipe_data['steps']['title'].append(title)
            recipe_data['steps']['site'].append(self.name)   
            recipe_data['steps']['number'].append(i)
            # remove next line escapes
            recipe_data['steps']['step'].append(re.sub('\n','',steps))
          
        yield recipe_data
