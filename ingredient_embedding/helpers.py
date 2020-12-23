#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 20:50:56 2020

@author: toriyokoyama
"""

import numpy as np

def cleanup(ingredient):
    '''
    Clean up ingredients for tokenization and analysis

    Parameters
    ----------
    ingredient : string
        ingredient item from a recipe

    Returns
    -------
    ingredient : string
        cleaned up string

    '''
    ingredient = ingredient.replace('\(','')
    ingredient = ingredient.replace('\)','')
    ingredient = ingredient.replace('(','')
    ingredient = ingredient.replace(')','')
    ingredient = ingredient.replace(';','')
    ingredient = ingredient.replace('.','')
    ingredient = ingredient.replace(',','')
    ingredient = ingredient.replace(':','')
    ingredient = ingredient.replace('*','')
    ingredient = ingredient.strip(' ')
    ingredient = ingredient.replace(u'\xa0',' ')
    ingredient = ingredient.lower()
    return ingredient

def vectorize(tokens,model,vector_size=100):
    '''
    Vectorize/embed the tokens for an ingredient item

    Parameters
    ----------
    tokens : list
        words making up an ingredient
    model : fasttext model object
        fasttext model object for embedding words, trained with recipe data 
    vector_size : int, optional
        size of embedding. The default is VECTOR_SIZE.

    Returns
    -------
    array
        average word embedding for all tokens/words in an ingredient item

    '''
    total_vector = np.zeros((vector_size,))
    for t in tokens:
        total_vector += model[t]
    return total_vector / len(tokens)

def mean_ingredient_vec(frame,vector_size=100):
    '''
    get mean of ingredient vectors by recipe to compare recipes

    Parameters
    ----------
    frame : dataframe
        dataframe of recipes that has column with ingredient vectors as arrays

    Returns
    -------
    avg : array
        average ingredient vector

    '''
    arr = np.concatenate(frame['ingredient-vec'].array).reshape(-1,vector_size)
    avg = np.mean(arr,axis=0)
    return avg

if __name__ == '__main__':
    pass