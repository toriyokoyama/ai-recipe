#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 20:07:02 2020

@author: toriyokoyama
"""

import os
os.chdir('/home/toriyokoyama/Projects/ai_recipes/')

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import multilabel_confusion_matrix, confusion_matrix
import lightgbm as lgbm
from hyperopt import pyll, fmin, Trials, hp, tpe, STATUS_OK
import csv
import ast
from timeit import default_timer as timer
import uuid
from imblearn.over_sampling import  SMOTE

CUISINES_alt = ['thai','thailand',
            'mexican','mexico',
            'chinese','china',
            'japanese','japan',
            'korean','korea',
            'indian','india','pakistani','pakistan',
            'american','america',
            'german','germany',
            'french','france',
            'italian','italy',
            'mediterranean',
            'greek','greece',
            'bbq','barbeque','b.b.q.','barbecue',
            'soul food','soul','southern']

CUISINES = ['thai','thai',
            'mexican','mexican',
            'chinese','chinese',
            'japanese','japanese',
            'korean','korean',
            'indian','indian','indian','indian',
            'american','american',
            'german','german',
            'french','french',
            'italian','italian',
            'mediterranean',
            'greek','greek',
            'bbq','bbq','bbq','bbq',
            'soul food','soul food','soul food']

CUISINE_DF = pd.DataFrame({'cuisine_parent':CUISINES,'cuisine_child':CUISINES_alt})

# import tag data
df = pd.read_csv('tags.csv')
# assign ID data
df['ID'] = df['url'].apply(lambda x: uuid.uuid5(uuid.NAMESPACE_URL,x))
# clean tags
df['tag'] = df['tag'].str.lower()
# assign higher level cuisine for consistency
df_cuisine = df.merge(CUISINE_DF,left_on='tag',right_on='cuisine_child',how='inner')
# import recipe ingredient embedding
recipe_ingredient_embedding = pd.read_csv('recipe_ingredients_embedding.csv')
emb_cols = recipe_ingredient_embedding.columns[2:]
df_cuisine = df_cuisine.merge(recipe_ingredient_embedding,how='left',on='url')
# remove null
df_cuisine = df_cuisine[~df_cuisine.isnull().any(axis=1)]

#%%

# check distribution of cuisines
cnt_by_cuisine = df_cuisine.groupby('cuisine_parent').count()['url']
cnt_by_cuisine_pct = cnt_by_cuisine / np.sum(cnt_by_cuisine)

#%%

# encode and split data
le = LabelEncoder()
y = le.fit_transform(df_cuisine['cuisine_parent'])
X_train, X_test, y_train, y_test = train_test_split(df_cuisine.loc[:,emb_cols],y,test_size=0.3,random_state=1234)

smote = SMOTE()
X_train_resamp, y_train_resamp = smote.fit_resample(X_train, y_train)

#%%

###########################################################
#### Perform classification prediction on cuisine tags ####
###########################################################

# much of the below adapted from https://github.com/WillKoehrsen/hyperparameter-optimization/blob/master/Bayesian%20Hyperparameter%20Optimization%20of%20Gradient%20Boosting%20Machine.ipynb

params = {
    'class_weight': hp.choice('class_weight', [None, 'balanced']),
    'boosting_type': hp.choice('boosting_type', [{'boosting_type': 'gbdt', 'subsample': hp.uniform('gdbt_subsample', 0.5, 1)}, 
                                                 {'boosting_type': 'dart', 'subsample': hp.uniform('dart_subsample', 0.5, 1)},
                                                 {'boosting_type': 'goss', 'subsample': 1.0}]),
    'num_leaves': hp.quniform('num_leaves', 16, 200, 1),
    'learning_rate': hp.loguniform('learning_rate', np.log(0.001), np.log(0.1)),
    #'subsample_for_bin': hp.quniform('subsample_for_bin', 20000, 300000, 20000),
    'min_child_samples': hp.quniform('min_child_samples', 20, 500, 5),
    'reg_alpha': hp.uniform('reg_alpha', 0.0, 1.0),
    'reg_lambda': hp.uniform('reg_lambda', 0.0, 1.0),
    'colsample_bytree': hp.uniform('colsample_by_tree', 0.6, 1.0),
    'objective':'multiclass',
    'num_class':len(df_cuisine['cuisine_parent'].unique()),
    #'device_type':'gpu',
    #'max_bin': 63,
    'num_threads':0
}

# get first level of parameters
param_keys = list(params.keys())

# search through hyperopt distributions for choices
dict_nodes = []
for k,v in params.items():
    try:
        dict_nodes.extend([node for node in pyll.dfs(v) if node.name == 'dict'])
    except:
        pass
# in nodes that are dictionaries (i.e. the list of dictionary choices)
for d in dict_nodes:
    for param in d.named_args:
        param_keys.append(param[0])
# use set to remove duplicates
param_keys = sorted(list(set(param_keys)))        

N_FOLDS = 3

def objective(params, n_folds = N_FOLDS):
    """Objective function for Gradient Boosting Machine Hyperparameter Optimization"""
    
    # Keep track of evals
    global ITERATION
    
    ITERATION += 1
    
    # Retrieve the subsample if present otherwise set to 1.0
    subsample = params['boosting_type'].get('subsample', 1.0)
    
    # Extract the boosting type
    params['boosting_type'] = params['boosting_type']['boosting_type']
    params['subsample'] = subsample
    
    # Make sure parameters that need to be integers are integers
    for parameter_name in ['num_leaves', 'min_child_samples']:
        params[parameter_name] = int(params[parameter_name])
    
    start = timer()
    
    # Perform n_folds cross validation
    cv_results = lgbm.cv(params, train_set, num_boost_round = 20000, nfold = n_folds, 
                        early_stopping_rounds = 10, metrics = 'multi_logloss', seed = 50)
    
    run_time = timer() - start
    
    # Extract the best score
    best_score = np.min(cv_results['multi_logloss-mean'])
    
    # Loss must be minimized
    loss = best_score
    
    # Boosting rounds that returned the highest cv score
    n_estimators = int(np.argmin(cv_results['multi_logloss-mean']) + 1)
    
    param_data = []
    for k,v in sorted(params.items()):
        param_data.append(v)

    # Write to the csv file ('a' means append)
    of_connection = open(out_file, 'a')
    writer = csv.writer(of_connection)
    iter_data = [ITERATION, loss, n_estimators, run_time, params]
    iter_data.extend(param_data)
    writer.writerow(iter_data)
    
    # Dictionary with information for evaluation
    return {'loss': loss, 'params': params, 'iteration': ITERATION,
            'estimators': n_estimators, 
            'train_time': run_time, 'status': STATUS_OK}

# Create a lgb dataset
train_set = lgbm.Dataset(X_train, label = y_train)
#train_set = lgbm.Dataset(X_train_resamp, label = y_train_resamp)

# Keep track of results
bayes_trials = Trials()

# File to save first results
out_file = 'cuisine_labeling/gbm_trials.csv'
#out_file = 'cuisine_labeling/gbm_trials_smote.csv'
of_connection = open(out_file, 'w')
writer = csv.writer(of_connection)

# Write the headers to the file
headers = ['loss', 'params', 'iteration', 'estimators', 'train_time']
headers.extend(param_keys)
writer.writerow(headers)
of_connection.close()

# Global variable
global  ITERATION

ITERATION = 0
MAX_EVALS = 100

# Run optimization
best = fmin(fn = objective, space = params, algo = tpe.suggest, 
            max_evals = MAX_EVALS, trials = bayes_trials, rstate = np.random.RandomState(50))

#%%

#param_df = pd.DataFrame(columns=list(ast.literal_eval(results.loc[0,'params']).copy().keys())+['iteration'])
#for row in range(len(results)):
#    param_df = pd.concat((param_df,pd.DataFrame(np.array(list(ast.literal_eval(results.loc[row,'params']).values())+[results.loc[row,'iteration']]).reshape(1,-1),columns=param_df.columns)),axis=0)
    
#results_split = results.merge(param_df,on='iteration')
#results_split.to_csv('cuisine_labeling/gbm_trials_split_smote.csv')

results = pd.read_csv('cuisine_labeling/gbm_trials.csv')
#results = pd.read_csv('cuisine_labeling/gbm_trials_split_smote.csv')

# Sort with best scores on top and reset index for slicing
results.sort_values('loss', ascending = True, inplace = True)
results.reset_index(inplace = True, drop = True)
results.head()

# Extract the ideal number of estimators and hyperparameters
best_n_estimators = int(results.loc[0, 'estimators'])
best_params = ast.literal_eval(results.loc[0, 'params']).copy()

# Re-create the best model and train on the training data
#model = lgbm.LGBMClassifier(n_estimators=best_bayes_estimators, n_jobs = -1, 
#                                       objective = 'binary', random_state = 50, **best_bayes_params)

model = lgbm.train(best_params,train_set,num_boost_round=best_n_estimators)
model.save_model('cuisine_labeling/gbm_model.txt')
#model.save_model('cuisine_labeling/gbm_model_smote.txt')

preds = model.predict(df_cuisine.loc[:,emb_cols])

preds[0:10]

#%%

model = lgbm.Booster(model_file='cuisine_labeling/gbm_model.txt')
model_smote = lgbm.Booster(model_file='cuisine_labeling/gbm_model_smote.txt')
preds = model.predict(X_test)
preds_smote = model_smote.predict(X_test)

pred_class = le.classes_[np.argmax(preds,axis=1)]
pred_smote_class = le.classes_[np.argmax(preds_smote,axis=1)]
y_test_class = le.classes_[y_test]

multilabel_confusion_matrix(y_test_class,pred_class,labels=le.classes_)

import matplotlib.pyplot as plt
import seaborn as sns
cm = confusion_matrix(y_test_class,pred_class,labels=le.classes_)
cm_pct_act = cm / np.sum(cm,axis=1).reshape(-1,1)
cm_pct_prd = cm / np.sum(cm,axis=0).reshape(1,-1)
cm_pct_all = cm / np.sum(cm) #,axis=0)

plt.figure(figsize=(15,10))
plt.title('Confusion Matrix % Actual')
plt.xlabel('Predicted')
plt.ylabel('Actual')
sns.heatmap(cm_pct_act,
            xticklabels=le.classes_,
            yticklabels=le.classes_,
            annot=True,
            fmt='0.1%')

plt.figure(figsize=(15,10))
plt.title('Confusion Matrix % Predicted')
plt.xlabel('Predicted')
plt.ylabel('Actual')
sns.heatmap(cm_pct_prd,
            xticklabels=le.classes_,
            yticklabels=le.classes_,
            annot=True,
            fmt='0.1%')

plt.figure(figsize=(15,10))
plt.title('Confusion Matrix % All')
plt.xlabel('Predicted')
plt.ylabel('Actual')
sns.heatmap(cm_pct_all,
            xticklabels=le.classes_,
            yticklabels=le.classes_,
            annot=True,
            fmt='0.1%')

plt.figure(figsize=(15,10))
plt.title('Confusion Matrix All')
plt.xlabel('Predicted')
plt.ylabel('Actual')
sns.heatmap(cm,
            xticklabels=le.classes_,
            yticklabels=le.classes_,
            annot=True,
            fmt='d')

cm_smote = confusion_matrix(y_test_class,pred_smote_class,labels=le.classes_)
cm_smote_pct_act = cm_smote / np.sum(cm_smote,axis=1).reshape(-1,1)
cm_smote_pct_prd = cm_smote / np.sum(cm_smote,axis=0).reshape(1,-1)
cm_smote_pct_all = cm_smote / np.sum(cm_smote) #,axis=0)

plt.figure(figsize=(15,10))
plt.title('Confusion Matrix % Actual SMOTE')
plt.xlabel('Predicted')
plt.ylabel('Actual')
sns.heatmap(cm_smote_pct_act,
            xticklabels=le.classes_,
            yticklabels=le.classes_,
            annot=True,
            fmt='0.1%')

plt.figure(figsize=(15,10))
plt.title('Confusion Matrix % Predicted SMOTE')
plt.xlabel('Predicted')
plt.ylabel('Actual')
sns.heatmap(cm_smote_pct_prd,
            xticklabels=le.classes_,
            yticklabels=le.classes_,
            annot=True,
            fmt='0.1%')

plt.figure(figsize=(15,10))
plt.title('Confusion Matrix % All SMOTE')
plt.xlabel('Predicted')
plt.ylabel('Actual')
sns.heatmap(cm_smote_pct_all,
            xticklabels=le.classes_,
            yticklabels=le.classes_,
            annot=True,
            fmt='0.1%')

plt.figure(figsize=(15,10))
plt.title('Confusion Matrix All SMOTE')
plt.xlabel('Predicted')
plt.ylabel('Actual')
sns.heatmap(cm_smote,
            xticklabels=le.classes_,
            yticklabels=le.classes_,
            annot=True,
            fmt='d')


# TODO
# handle class imbalance, rerun with larger max estimators, rerun with original data to compare
