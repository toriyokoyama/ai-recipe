#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 24 16:37:37 2020

@author: toriyokoyama
"""

import os
os.chdir('/home/toriyokoyama/Projects/ai_recipes/')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import nltk
#import wordcloud
#import textblob
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
from ingredient_embedding.helpers import *
import fasttext
#import tensorflow as tf
#import keras
import keras.backend as K
import keras.layers as L
import keras.models as M
import keras.optimizers as O


#%%

recipe_ingredients_long = pd.read_pickle('/home/toriyokoyama/Projects/ai_recipes/ingredient_token_labeling/recipe_ingredients_clean_long.pickle')
recipe_ingredients_long_label = pd.read_pickle('/home/toriyokoyama/Projects/ai_recipes/ingredient_token_labeling/recipe_ingredients_clean_long_label.pickle')

# TODO
# reorganize data to feed into an LSTM: see below

#%%
X_train = np.zeros((X_array.shape[0],WINDOW_LEN,X_array.shape[1]))
y_train = np.zeros((y_array.shape[0],WINDOW_LEN,y_array.shape[1])) #y_array

for i in range(WINDOW_LEN,len(X_train)):
    #svcNumStart = X_array[i][1]
    X_train[i] = X_array[i-WINDOW_LEN:i,:]
    #change date rank into a lag based on placement in window
    X_train[i][i-WINDOW_LEN:i,:][:,1] = X_train[i][i-WINDOW_LEN:i,:][:,1] - max(X_train[i][i-WINDOW_LEN:i,:][:,1],default=0)

#limit to ones with data
X_train = X_train[WINDOW_LEN:]

for i in range(WINDOW_LEN,len(y_train)):
    #svcNumStart = X_array[i][1]
    y_train[i] = np.tile(y_array[i],(WINDOW_LEN,1))

#limit to ones with data
y_train = y_train[WINDOW_LEN:]

print(X_train.shape,y_train.shape)

#%%
#build LSTM model
HIDDEN_UNITS = 1
model = Sequential()
model.add(LSTM(HIDDEN_UNITS,input_shape=(X_train.shape[1],X_train.shape[2]),return_sequences=True,stateful=False,activation='tanh'))
#model.add(Dropout(0.25))
#model.add(LSTM(HIDDEN_UNITS,return_sequences=True,stateful=False,activation='tanh'))
#model.add(Dropout(0.25))
#model.add(LSTM(HIDDEN_UNITS,return_sequences=True,stateful=False,activation='tanh'))
#model.add(Dropout(0.25))
#model.add(Dense(1,activation='softmax'))
model.add(Dense(units=y_train.shape[2],activation='softmax')) #,input_shape=(1,X_train.shape[1],1)
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

#%%
#fit to model

#for epoch in range(5):
#    for i in range(len(X_train)):
#        if i % 21 == 0:
#            model.reset_states()
#        model.train_on_batch(np.expand_dims(np.expand_dims(X_train[i],axis=0),axis=0),
#                             np.expand_dims(np.expand_dims(np.array(y_train[i]),axis=0),axis=0))

model.fit(X_train,y_train,batch_size=1,epochs=5,verbose=1,shuffle=False)

#to do it in batches:
#for epoch in range(2):
#    for i in range(len(X_train)):
#        model.train_on_batch(np.expand_dims(X_train[i],axis=0),
#                             np.expand_dims(np.tile(np.array(y_train[i]),(WINDOW_LEN,1)),axis=0))

#print(model.test_on_batch(X_train[50:75],
#                          np.tile(np.array(y_train[50:75]),(WINDOW_LEN,1))))

for i in range(100,200):
    print(np.argmax(model.predict_on_batch(np.expand_dims(X_train[i],axis=0))[0][WINDOW_LEN-1]))