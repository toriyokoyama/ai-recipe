#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 24 22:15:33 2020

@author: toriyokoyama
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import numpy as np
from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

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
df = pd.read_csv('/home/toriyokoyama/Projects/ai_recipes/tags.csv')
# clean tags
df['tag'] = df['tag'].str.lower()
# assign higher level cuisine for consistency
df_cuisine = df.merge(CUISINE_DF,left_on='tag',right_on='cuisine_child',how='inner')
# load ingredients
df_ingredients = pd.read_csv('/home/toriyokoyama/Projects/ai_recipes/ingredients.csv')
# combine data
df_combine = df_cuisine.merge(df_ingredients,on='url',how='inner')

# TODO: need to finish up manual labeling so that this makes more sense
unique_ingredients = sorted(list(df_combine['ingredient'].astype('str').unique()))

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(
        children='Ingredient by Cuisine',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),
    
    dcc.Dropdown(
        id='ingredient-chosen',
        options=[{'label': i, 'value': i} for i in unique_ingredients],
        value='Ingredient Choice'
    ),

    dcc.Graph(
        id='example-graph'
    )
])

@app.callback(Output('example-graph','figure'),
              [Input('ingredient-chosen','value')])
def update_graph(ingredient):
    
    df_filter = df_combine[df_combine['ingredient']==ingredient][['cuisine_parent','ingredient']]
    df_grp = df_filter.groupby('cuisine_parent').count().reset_index()
    
    fig = px.bar(df_grp, x='cuisine_parent', y="ingredient", barmode="group")
    
    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)