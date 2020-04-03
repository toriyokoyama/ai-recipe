# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
import re
import numpy as np

#%%

MEASUREMENT_UNITS = ['cup','cups','c','teaspoon','teaspoons','tsp','tablespoon','tablespoons','tbsp',
                     'ml','grams','g','kilograms','kg','milligrams','mg','oz','ounce','ounces','lbs','lb','pound','pounds',
                     'small','sm','medium','med','large','lg','quart','qt','liter','litre','l',
                     'ml','milliliter','millilitre','gallon','gal']
SPELLED_NUMBERS = ['one','two','three','four','five','six','seven','eight','nine','ten']
FRACTIONS = ['1/8','1/4','1/3','1/2','2/3','3/4','3/8','5/8','7/8','1⁄2','3⁄4','1⁄3','1⁄4','2⁄3']

#%%

class SeriouseatsSpider(scrapy.Spider):
    name = 'seriouseats'
    allowed_domains = ['seriouseats.com']
    start_urls = ['https://www.seriouseats.com/recipes',
                  'https://www.seriouseats.com/recipes/topics/meal/quick-dinners']

    custom_settings={ 'FEED_FORMAT': 'csv',
                     'FEED_EXPORTERS': {'csv':'AiRecipePipeline'}}
                     #'DEPTH_LIMIT': 1} # if testing, overriding depth_limit helps
    urls_visited = []
    
    def parse(self, response):
        xp = "//article[@class='c-card c-card--small']/a/@href"
        return (Request(url, callback=self.parse_recipe_site) for url in response.xpath(xp).extract())
        #xp = "//div[@class='module__wrapper']/a/@href"
        #return (Request(url, callback=self.parse_recipe_site) for url in response.xpath(xp).extract())
        
    def parse_recipe_site(self,response):    
        print('Processing URL '+response.url)
        # check if this url has been visited already to avoid duplicates and to stop perpetual crawl
        url_visited = response.url in self.urls_visited
        # add it to the urls visited
        self.urls_visited.append(response.url)
        
        # only export data for recipes 
        if ('recipes/' in response.url) and ('.html' in response.url) and (not url_visited):
            # create dictionary to store data that will be passed to the exporter
            recipe_data = {'ingredients':{'url':[],'title':[],'site':[],'amount':[],'units':[],'ingredient':[],'ingredient-full':[]},
                           'steps':{'url':[],'title':[],'site':[],'number':[],'step':[]},
                           'tags':{'url':[],'title':[],'site':[],'tag':[]},
                           'recipe-level':{'url':[],'title':[],'site':[],'cook_time_val':None,'cook_time_unit':None,'prep_time_val':None,'prep_time_unit':None,'total_time_val':None,'total_time_unit':None,'rating':None}}
            
            # extract title of the recipe; two forward slashes gets all text (includes those in format tags)
            title = response.xpath("//h1[@class='title recipe-title c-post__h1']//text()").extract()
            
            # process ingredients
            ingredients = response.xpath("//li[@class='ingredient']//text()").extract()
            for ingredient in ingredients:
                recipe_data['ingredients']['ingredient-full'].append(ingredient)
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
                # strip out punctuation and make lowercase
                ingredient_words = [ingredient_word.strip('.;,').lower() for ingredient_word in ingredient_words]
                # average number-number combos and numberunit combos
                ingredient_words_copy = ingredient_words.copy()
                ingredient_words = []
                for ingredient_word in ingredient_words_copy:
                    # blank
                    if ingredient_word == '':
                        continue
                     # two numbers separated by a hyphen
                    elif len(ingredient_word.split('-'))>1:
                        if all(part.isnumeric() for part in ingredient_word.split('-')):
                            ingredient_words.append(str((int(ingredient_word.split('-')[0])+int(ingredient_word.split('-')[1]))/2))
                    elif len(ingredient_word.split('–'))>1:
                        if all(part.isnumeric() for part in ingredient_word.split('–')):
                            ingredient_words.append(str((int(ingredient_word.split('–')[0])+int(ingredient_word.split('–')[1]))/2))
                    # a unit attached to a value
                    elif (ingredient_word[0].isnumeric()) and any(unit in ingredient_word for unit in MEASUREMENT_UNITS):
                        num = ''.join([c for c in ingredient_word if c.isnumeric()])
                        non_num = ''.join([c for c in ingredient_word if c.isnumeric()==False])
                        ingredient_words.append(num)
                        ingredient_words.append(non_num.strip('-–'))
                    else:
                        ingredient_words.append(ingredient_word)
                del ingredient_words_copy
                # create function to convert word numbers to actual numbers
                conv_spelled_to_num = lambda x: str(SPELLED_NUMBERS.index(x)+1) if x in SPELLED_NUMBERS else x
                amount = [conv_spelled_to_num(w) for w in ingredient_words if w.isnumeric() or w in FRACTIONS or w in SPELLED_NUMBERS]
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
                recipe_data['recipe-level']['rating'] = [response.xpath("//span[@class='info rating-value']/text()").extract()[0]]
            except:
                recipe_data['recipe-level']['rating'] = [-1]
                
            # get times
            times = response.xpath("//span[@class='info']/text()").extract()
            recipe_data['recipe-level']['url'].append(response.url)
            recipe_data['recipe-level']['title'].append(title)
            recipe_data['recipe-level']['site'].append(self.name)
            
            # store prep time
            preptime = times[0].split(' ')
            pt_val_cnt = 0
            pt_unit_cnt = 0
            for w in preptime:
                # if the word is numeric
                if w.isnumeric():
                    # if it's the first value word
                    if pt_val_cnt == 0:
                        recipe_data['recipe-level']['prep_time_val'] = [float(w)]
                    else: #if pt_unit_cnt == 0:
                        recipe_data['recipe-level']['prep_time_val'][0] += float(w)
                    pt_val_cnt += 1
                else:
                    # if it's the first unit word
                    if pt_unit_cnt == 0:
                        # if it's an hour unit
                        if ('hr' in w) or ('hour' in w):
                            recipe_data['recipe-level']['prep_time_val'][0] *= 60
                            pt_unit_cnt += 1
                        elif ('min' in w):
                            pt_unit_cnt += 1
            recipe_data['recipe-level']['prep_time_unit'] = ['min']
            
             # store total time
            totaltime = times[1].split(' ')
            tt_val_cnt = 0
            tt_unit_cnt = 0
            for w in totaltime:
                # if the word is numeric
                if w.isnumeric():
                    # if it's the first value word
                    if tt_val_cnt == 0:
                        recipe_data['recipe-level']['total_time_val'] = [float(w)]
                    else: #if tt_unit_cnt == 0:
                        recipe_data['recipe-level']['total_time_val'][0] += float(w)
                    tt_val_cnt += 1
                else:
                    # if it's the first unit word
                    if tt_unit_cnt == 0:
                        # if it's an hour unit
                        if ('hr' in w) or ('hour' in w):
                            recipe_data['recipe-level']['total_time_val'][0] *= 60
                            tt_unit_cnt += 1
                        elif ('min' in w):
                            tt_unit_cnt += 1
            recipe_data['recipe-level']['total_time_unit'] = ['min']
                    
            # derive cook time
            if (recipe_data['recipe-level']['total_time_unit'][0].lower() == recipe_data['recipe-level']['prep_time_unit'][0].lower()) or (recipe_data['recipe-level']['total_time_unit'][0].lower() == ''.join(list(recipe_data['recipe-level']['prep_time_unit'][0].lower())+['s'])):
                recipe_data['recipe-level']['cook_time_val'] = [recipe_data['recipe-level']['total_time_val'][0] - recipe_data['recipe-level']['prep_time_val'][0]]
                recipe_data['recipe-level']['cook_time_unit'] = [recipe_data['recipe-level']['total_time_unit'][0]]
            elif ('min' in recipe_data['recipe-level']['prep_time_unit'][0].lower()):
                recipe_data['recipe-level']['cook_time_val'] = [recipe_data['recipe-level']['total_time_val'][0] * 60 - recipe_data['recipe-level']['prep_time_val'][0]]
                recipe_data['recipe-level']['cook_time_unit'] = [recipe_data['recipe-level']['prep_time_unit'][0]]    
            else:
                #raise ValueError('Values of time in different units')
                recipe_data['recipe-level']['cook_time_val'] = [-1]
                recipe_data['recipe-level']['cook_time_unit'] = ['unk']
                
            # get steps, excluding the numbers here (derived)
            steps_section = response.xpath("//div[@class='recipe-procedure-text']/p/text()").extract()
            for i, steps in enumerate(steps_section):
                recipe_data['steps']['url'].append(response.url)
                recipe_data['steps']['title'].append(title)
                recipe_data['steps']['site'].append(self.name)   
                recipe_data['steps']['number'].append(i+1)
                # remove next line escapes
                recipe_data['steps']['step'].append(re.sub('\n','',steps))
                
            # get tags
            tags_section = response.xpath("//div[@class='entry-tags']/ul/li/a/text()").extract()
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
            next_urls = response.xpath("//div[@class='block block-related block-thumbnails-medium']/a/@href").extract()
            next_urls = next_urls + response.xpath("//div[@class='recipe-more__inner expanded']/a/@href").extract()
            next_urls = next_urls + response.xpath("//div[@class='entry-tags']/ul/li/a/@href").extract()
            next_urls = next_urls + response.xpath("//div[@class='module__wrapper']/a/@href").extract()
            
            for url in next_urls:
                yield (Request(url, callback=self.parse_recipe_site))
        
