from openai import OpenAI
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import requests
import json
import time
import urllib.parse
import urllib.request
from openai import OpenAI
import os
from dotenv import load_dotenv

def wiki_trending_today(n):
    """Grab n trending wikipedia articles from today
    Returns a tuple, (titles, extracts)"""
    today = datetime.datetime.now()
    date = today.strftime('%Y/%m/%d')
    language_code = 'en'
    load_dotenv()
    wiki_key = os.getenv("wiki_key")
    user_agent = '94gent@gmail.com'
    headers = {
        'Authorization': wiki_key,
        'User-Agent': user_agent
    }
    base_url = 'https://api.wikimedia.org/feed/v1/wikipedia/'
    url = base_url + language_code + '/featured/' + date
    response = requests.get(url, headers=headers)
    response = json.loads(response.text)
    titles= []
    extracts=[]
    for i in response['mostread']['articles'][:n]:
        if 'description' in i.keys():
            titles.append(i['titles']['normalized'])
            extracts.append(i['extract'])
    return titles, extracts

def generate_MC_question_with_answers(title, extract):
    client = OpenAI()

    t, e = title, extract

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a trivia master. Create an engaging multiple-choice trivia question."
            },
            {
                "role": "system",
                "content": "Your response format must be: ['<question>', '<The correct answer>', '<Incorrect option 1>', '<Incorrect option 2>', '<Incorrect option 3>', '<question category>', '<question difficulty (from 1-10)>', '<question rating based on how much you think people will like this question (from 1-10)>', 'Who or what is the subject of this question']. All values must be enclosed in double quotes and formatted as strings."
            },
            {
                "role": "user",
                "content": f"Ask a multiple-choice trivia question about the topic '{t}'. Ensure that the question references this context: {e}."
            }
        ])

    # Extract and store the generated question
    return completion.choices[0].message.content


def find_corresponding_news(titles, n, m):
    """given a list of titles, collect news articles corresponding to the first n titles
    Returns a list of strings, where each string can be used as a context for LLM
    """
    gnews_key=st.secrets["gnews_key"]
    all_contexts=[]
    for title in titles[:n]:
        context=[]
        url = f'https://gnews.io/api/v4/search?q="{urllib.parse.quote(title)}"&lang=en&country=us&max={m}&apikey={gnews_key}'
        with urllib.request.urlopen(url) as res:
            data = json.loads(res.read().decode("utf-8"))
            for i in range(len(data['articles'])):
                context.append(data["articles"][i]['content'])
        time.sleep(1)
        all_contexts.append(context)
    all_str_context=[]
    for context in all_contexts:
        strcontext=""
        for i in context:
            strcontext += i +'\n'
        all_str_context.append(strcontext)
    return all_str_context