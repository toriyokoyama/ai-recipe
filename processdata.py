#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 20:39:43 2020

@author: toriyokoyama
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import nltk
import textblob
#import tensorflow as tf
#import keras
import os


#%%

recipe_ingredients = pd.read_csv('/home/toriyokoyama/Projects/AI Recipes/ingredients.csv')

#%%

tokens = recipe_ingredients.iloc[0:10].loc[:,'ingredient-full'].apply(nltk.word_tokenize)
