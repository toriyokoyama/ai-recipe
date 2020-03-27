# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
#from scrapy_splash import SplashRequest
import re
import numpy as np

#%%

MEASUREMENT_UNITS = ['cup','cups','c','teaspoon','teaspoons','tsp','tablespoon','tablespoons','tbsp',
                     'ml','grams','g','kilograms','kg','oz','ounce','ounces','lbs','lb','pound','pounds']
FRACTIONS = ['1/8','1/4','1/3','1/2','2/3','3/4','3/8','5/8','7/8']

#%%

class Food52Spider(scrapy.Spider):
    name = 'food52'
    allowed_domains = ['food52.com']
    start_urls = ['https://food52.com/recipes',
                  'https://food52.com/recipes/search?tag=test-kitchen-approved&o=relevance'] + ['https://food52.com/recipes/search?o=relevance&page=' + str(pg) +'&tag=test-kitchen-approved' for pg in range(2,210)]

    custom_settings={ 'FEED_FORMAT': 'csv',
                     'FEED_EXPORTERS': {'csv':'AiRecipePipeline'}}
                     #'DEPTH_LIMIT': 1} # if testing, overriding depth_limit helps
    urls_visited = []
    
    def parse(self, response):
        urls = []
        xp = "//a[@class='photo photo-block__link']/@href"
        urls.extend(['https://www.' + self.allowed_domains[0] + url for url in response.xpath(xp).extract()])
        xp = "//div[@id='ingredient']//a/@href"
        urls.extend(['https://www.' + self.allowed_domains[0] + url for url in response.xpath(xp).extract()])
        xp = "//div[@id='meal']//a/@href"
        urls.extend(['https://www.' + self.allowed_domains[0] + url for url in response.xpath(xp).extract()])
        xp = "//div[@id='cuisine']//a/@href"
        urls.extend(['https://www.' + self.allowed_domains[0] + url for url in response.xpath(xp).extract()])
        xp = "//div[@id='dish-type']//a/@href"
        urls.extend(['https://www.' + self.allowed_domains[0] + url for url in response.xpath(xp).extract()])
        xp = "//div[@id='special-consideration']//a/@href"
        urls.extend(['https://www.' + self.allowed_domains[0] + url for url in response.xpath(xp).extract()])
        xp = "//div[@id='occasion']//a/@href"
        urls.extend(['https://www.' + self.allowed_domains[0] + url for url in response.xpath(xp).extract()])
        xp = "//div[@id='preparation']//a/@href"
        urls.extend(['https://www.' + self.allowed_domains[0] + url for url in response.xpath(xp).extract()])
        
        return (Request(url, callback=self.parse_recipe_site) for url in urls)
    
    '''(Request(url, callback=self.parse_recipe_site, meta={
                            'splash': {
                                'args': {
                                    # set rendering arguments here
                                    'html': 1,
                                    'png': 1,
                        
                                    # 'url' is prefilled from request url
                                    # 'http_method' is set to 'POST' for POST requests
                                    # 'body' is set to request body for POST requests
                                },
                        
                                # optional parameters
                                #'endpoint': 'render.json',  # optional; default is render.json
                                #'splash_url': '<url>',      # optional; overrides SPLASH_URL
                                #'slot_policy': scrapy_splash.SlotPolicy.PER_DOMAIN,
                                #'splash_headers': {},       # optional; a dict with headers sent to Splash
                                #'dont_process_response': True, # optional, default is False
                                #'dont_send_headers': True,  # optional, default is False
                                #'magic_response': False,    # optional, default is True
                            }
                        }) for url in urls)'''
       
    def parse_recipe_site(self,response):    
        print('Processing URL '+response.url)
        # check if this url has been visited already to avoid duplicates and to stop perpetual crawl
        url_visited = response.url in self.urls_visited
        # add it to the urls visited
        self.urls_visited.append(response.url)
        
        # this appears for recipes, and hopefully not on other types of pages
        breadcrumbs = response.xpath("//div[@class='breadcrumbs']//text()").extract()
        # only export data for recipes 
        if ('recipes/' in response.url) and (len(breadcrumbs) > 0) and (not url_visited):
            # create dictionary to store data that will be passed to the exporter
            recipe_data = {'ingredients':{'url':[],'title':[],'site':[],'amount':[],'units':[],'ingredient':[]},
                           'steps':{'url':[],'title':[],'site':[],'number':[],'step':[]},
                           'tags':{'url':[],'title':[],'site':[],'tag':[]},
                           'recipe-level':{'url':[],'title':[],'site':[],'cook_time_val':None,'cook_time_unit':None,'prep_time_val':None,'prep_time_unit':None,'total_time_val':None,'total_time_unit':None,'rating':None}}
            
            # extract title of the recipe; two forward slashes gets all text (includes those in format tags)
            title = [response.xpath("//h1[@class='recipe__title']/text()").extract()[0].replace('\n','').strip(' ')]
            
            # process ingredients
            ingredients = response.xpath("//div[@class='recipe__list recipe__list--ingredients']//ul/li//text()").extract()
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
            #try:
            #    recipe_data['recipe-level']['rating'] = [response.xpath("//span[@class='rating']/text()").extract()[0].split('/')[0]]
            #except:
            #ignoring for now, since I can't figure out the CSS
            recipe_data['recipe-level']['rating'] = [-1]
                
            # get times
            times = response.xpath("//ul[@class='recipe__details']/li/text()").extract()
            recipe_data['recipe-level']['url'].append(response.url)
            recipe_data['recipe-level']['title'].append(title)
            recipe_data['recipe-level']['site'].append(self.name)
            
            # store prep time
            # sometimes there are no times available
            if len(times) == 0:
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
            else:
                recipe_data['recipe-level']['prep_time_val'] = [-1]
                recipe_data['recipe-level']['prep_time_unit'] = ['unk']     
                
             # store cook time
             # sometimes there are no times available
            if len(times) == 0:
                cooktime = times[1].split(' ')
                ct_val_cnt = 0
                ct_unit_cnt = 0
                for w in cooktime:
                    # if the word is numeric
                    if w.isnumeric():
                        # if it's the first value word
                        if ct_val_cnt == 0:
                            recipe_data['recipe-level']['cook_time_val'] = [float(w)]
                        else: #if ct_unit_cnt == 0:
                            recipe_data['recipe-level']['cook_time_val'][0] += float(w)
                        ct_val_cnt += 1
                    else:
                        # if it's the first unit word
                        if ct_unit_cnt == 0:
                            # if it's an hour unit
                            if ('hr' in w) or ('hour' in w):
                                recipe_data['recipe-level']['cook_time_val'][0] *= 60
                                ct_unit_cnt += 1
                            elif ('min' in w):
                                ct_unit_cnt += 1
                recipe_data['recipe-level']['cook_time_unit'] = ['min']
            else:
                recipe_data['recipe-level']['cook_time_val'] = [-1]
                recipe_data['recipe-level']['cook_time_unit'] = ['unk']  
                    
            # derive total time
            if (recipe_data['recipe-level']['prep_time_unit']== ['unk']) or (recipe_data['recipe-level']['cook_time_unit'] == ['unk']):
                recipe_data['recipe-level']['total_time_val'] = [-1]
                recipe_data['recipe-level']['total_time_unit'] = ['unk']
            else:
                recipe_data['recipe-level']['total_time_val'] = [recipe_data['recipe-level']['prep_time_val'][0] + recipe_data['recipe-level']['cook_time_val'][0]]
                recipe_data['recipe-level']['total_time_unit'] = ['min']
                
            # get steps, excluding the numbers here (derived)
            steps_section = response.xpath("//div[@id='recipeDirectionsRoot']//span//text()").extract()
            for i, steps in enumerate(steps_section):
                recipe_data['steps']['url'].append(response.url)
                recipe_data['steps']['title'].append(title)
                recipe_data['steps']['site'].append(self.name)   
                recipe_data['steps']['number'].append(i+1)
                # remove next line escapes
                recipe_data['steps']['step'].append(steps.replace('\n','').strip(' '))
                
            # get tags
            tags_section = response.xpath("//div[@class='recipe__tags']//ul/li/a/text()").extract()
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
            next_urls = ['https://www.' + self.allowed_domains[0] + ending for ending in response.xpath("//a[@class='photo photo-block__link']/@href").extract()]
            next_urls = next_urls + ['https://www.' + self.allowed_domains[0] + ending for ending in response.xpath("//div[@class='recipe__tags']//ul/li/a/@href").extract()]
            
            for url in next_urls:
                yield (Request(url, callback=self.parse_recipe_site))

                '''(Request(url, callback=self.parse_recipe_site, meta={
                            'splash': {
                                'args': {
                                    # set rendering arguments here
                                    'html': 1,
                                    'png': 1,
                        
                                    # 'url' is prefilled from request url
                                    # 'http_method' is set to 'POST' for POST requests
                                    # 'body' is set to request body for POST requests
                                },
                        
                                # optional parameters
                                #'endpoint': 'render.json',  # optional; default is render.json
                                #'splash_url': '<url>',      # optional; overrides SPLASH_URL
                                #'slot_policy': scrapy_splash.SlotPolicy.PER_DOMAIN,
                                #'splash_headers': {},       # optional; a dict with headers sent to Splash
                                #'dont_process_response': True, # optional, default is False
                                #'dont_send_headers': True,  # optional, default is False
                                #'magic_response': False,    # optional, default is True
                            }
                        }))
        '''
