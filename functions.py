from openai import OpenAI
import datetime
import requests
import json
import urllib.request
import os
from dotenv import load_dotenv
import pytz
import praw


def wiki_trending_today(n):
    """Grab n trending wikipedia articles from today
    Returns a tuple, (titles, extracts)"""
    pacific = pytz.timezone('US/Pacific')
    today = datetime.datetime.now(pacific)
    date = today.strftime('%Y/%m/%d')
    print(f"Date being used: {date}")
    language_code = 'en'
    load_dotenv()
    wiki_key = os.getenv("wiki_key")
    user_agent = '94gent@gmail.com'
    headers = {
        # 'Authorization': wiki_key,
        'User-Agent': user_agent
    }
    url = 'https://en.wikipedia.org/api/rest_v1/feed/featured/' + date

    response = requests.get(url, headers=headers)
    response = json.loads(response.text)
    titles= []
    extracts=[]
    for i in response['mostread']['articles'][:n]:
        if 'description' in i.keys():
            title = i['titles']['normalized']
            titles.append(title)
            extract = i['extract']
            extracts.append(extract)
            print(title)
    return titles, extracts




def get_reddit(title, n=3):
    """Finds relevant reddit posts about a given title.
    Input: title -> str
            n -> number of headlines & texts to return
    Output: headlines (list of strings), text (list of strings)
    """
    load_dotenv()

    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    headlines = []
    text = []
    dates=[]
    subreddit = reddit.subreddit("all")

    for submission in subreddit.search(
        query=title,
        sort="relevance",         # or "new", "relevance", etc.
        time_filter="week", # or "all", "month", "week", "day", "hour"
        limit=n
    ):
        timestamp = submission.created_utc
        post_date = datetime.datetime.fromtimestamp(timestamp)
        r_title = submission.title
        headlines.append(r_title)
        text.append(submission.selftext)
        dates.append(post_date.strftime("%Y-%m-%d %H:%M"))
    return (headlines, text, dates)



def generate_MC_question_with_answers(title, extract, reddit_posts, reddit_texts):
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a trivia master. Create an engaging multiple-choice trivia question. 
                Respond with only the following array of strings, with no additional explanation or text.
                Do not include markdown formatting or any text outside of the list. Do not add line breaks between entries.
                [   "<question>",
                    "<The correct answer>",
                    "<Incorrect option 1>",
                    "<Incorrect option 2>",
                    "<Incorrect option 3>",
                    "<question category>",
                    "<question difficulty (1-10)>",
                    "<question rating (1-10)>",
                    "<subject of question>" ]
    . 
                All values must be enclosed in double quotes and formatted as strings."""
            },
            {
                "role": "user",
                "content": f"""Ask a multiple-choice trivia question about '{title}'.
                Use this context as background information: {extract}.
                Use these reddit posts to understand why this topic is relevant right now.
                {[(post, text) for (post, text) in zip(reddit_posts, reddit_texts)]}
                Allude to why this topic is relevant in the question."""
            }
        ])

    # Extract and store the generated question
    return completion.choices[0].message.content

