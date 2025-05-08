from openai import OpenAI
import datetime
import requests
import json
import urllib.request
import os
from dotenv import load_dotenv
import pytz
import praw
import pandas as pd

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


def generate_MC_question_with_answers_v4(title, extract, reddit_posts, reddit_texts):
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                    You are a trivia master who writes fun and engaging multiple-choice questions.

                    Your goals:
                    - Make each question a real question (end with a question mark).
                    - The questions should not be True False type.
                    - Don't ask questions where the answer is just a single date or year.
                    - The subject (e.g. 'Pope Francis', '2025 Canadian election') must appear in the question for clarity.
                    - Do NOT give away the answer in the question or lead directly to it.
                    - Focus on ironic, unusual, precedent-breaking, or fun outcomes—not summaries or job titles.
                    - Keep answers short (max 6 words).
                    - The correct answer should feel surprising but true.
                    - Incorrect answers must be:
                    - Plausible but clearly false

                    Only respond with the following array:
                    [
                    "<question>",
                    "<Correct answer>",
                    "<Incorrect option 1>",
                    "<Incorrect option 2>",
                    "<Incorrect option 3>",
                    "<question category>",
                    "<question difficulty (1-10)>",
                    "<question rating (1-10)>",
                    "<subject>"
                    ]

                    Do NOT include line breaks, markdown formatting, or any text outside this array.

                    Examples:

                    Bad: "Who was Pope in 2025?"  
                    Good: "In 2025, what centuries-old ritual did Pope Francis skip during Easter?"

                    Bad: "Who invented the microwave?"  
                    Good: "Which kitchen device was inspired when radar melted a scientist's candy bar?"

                    Bad: "What was the original purpose of bubble wrap?"  
                    Good: "Which product began as a failed attempt to make textured wallpaper?"
                """
            },
            {
                "role": "user",
                "content": f"""
                    Create a multiple-choice trivia question about '{title}' using this background: {extract}

                    Use these Reddit posts to understand why the topic is timely, controversial, or emotionally charged:
                    {[(post, text) for (post, text) in zip(reddit_posts, reddit_texts)]}

                    Instructions:
                    - Don't ask questions where the answer is just a single date or year.
                    - Don't summarize what happened—reveal something interesting *about* it.
                    - Keep the subject in the question for clarity.
                    - All answers must be under 6 words.
                    - Ensure the question ends with a question mark.
                    - Ensure wrong answers are plausible but false.
                    - Do not use fantasy, aliens, magic, or absurdity unless the subject directly involves it.

                    Only return the specified array format, with no additional commentary.
                """
            }
        ]
    )

    # Extract and store the generated question
    return completion.choices[0].message.content


def extract_topics_from_downloaded_file(n = 20):
    # Step 1: Find latest CSV file in ./downloads
    download_dir = os.path.join(os.getcwd(), "downloads")
    csv_files = [f for f in os.listdir(download_dir) if f.endswith(".csv")]

    if not csv_files:
        raise FileNotFoundError("No CSV files found in downloads folder.")

    # Sort by modification time, get the latest one
    latest_file = max(
        [os.path.join(download_dir, f) for f in csv_files],
        key=os.path.getmtime
    )

    print("📥 Loading file:", os.path.basename(latest_file))
    df = pd.read_csv(latest_file)
    topics = {df.Trends[i]: df['Search volume'][i] for i in range(n)}
    return topics

def choose_best_topics(topics, n=10):
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content":
                f"""You are deciding which content is good for a trivia website.
                The following are trending google searches paired with the search volume
                Your job is to return a rating from 0 and 10 for each topic. 
                a score of 0 means that it should not be used for a trivia question 
                for example violence or weapons, or boring political or business topics
                a score of 10 means it is a good candidate for a trivia question, 
                if it has a high search volume, it is probably a good trivia question
                theyre going to be plugged in to python so it should be a dictionary
                where they keys are the searches as strings and the values are your ratings as ints.
                Respond with only the dictionary, with no additional explanation or text or newlines.
                {topics}"""
            }
        ])
    search_ratings = eval(completion.choices[0].message.content)
    chosen_topics = [key for key, _ in sorted(search_ratings.items(), key=lambda item: item[1], reverse=True)[:n]]
    return chosen_topics


def google_pipeline_question_gen(topics):
    client = OpenAI()
    results=[]
    for topic in topics:
        print(topic)
        find_why_trending = client.chat.completions.create(
            model="gpt-4o-mini-search-preview-2025-03-11",
            messages=[
                {
                    "role": "user",
                    "content": f"why is {topic}trending on google search? "
                }
            ])

        why_trending = (find_why_trending.choices[0].message.content)
        print(why_trending)

        make_three_questions = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": f"""Come up with 3 trivia questions about the following text - include the answer, and the link to the article.
                Do not include any formatting or any text beyond the question answer pairs
                {why_trending}."""
            }
        ])
        three_questions = make_three_questions.choices[0].message.content
        print(three_questions)
        make_question_and_answers = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Pick one of the following questions and turn it into an engaging multiple-choice trivia question.
                Choose the question that is the most fun and interesting, and is a moderate level of difficulty.
                Think of incorrect options that could reasonably answer the question, but are verifyably incorrect.
                Respond with only the following array of strings, with no additional explanation or text.
                Do not include markdown formatting or any text outside of the list. Do not add line breaks between entries.
                [   "<question>", "<The correct answer>", "<Incorrect option 1>", "<Incorrect option 2>", "<Incorrect option 3>" "<link>"]
    . 
                All values must be enclosed in double quotes and formatted as strings."""
            },
                {
                "role": "user",
                "content": f"""
                {three_questions}."""
            }
        ])

        results.append(make_question_and_answers.choices[0].message.content)
    return results