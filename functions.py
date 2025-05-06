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


def verify_accuracy(question, correct_answer, context, subject):
    """
    Checks the factual accuracy of the question andcorrect answer.

    The quality of incorrect answers are checked in a evaluate_incorrect_answers. 
    The balance of both correct and incorrect answers is checked in evaluate_question_balance.
    
    Overall process: The correct answer is factual, the incorrect answers are not too obviously wrong, and 
    all the questions are balanced in length and complexity.
    Functions used:
    - verify_accuracy
    - evaluate_incorrect_answers
    - evaluate_question_balance
    """
    load_dotenv()
    client = OpenAI()
    
    completion = client.chat.completions.create(
        model = "gpt-4",
        messages = [
            {
                "role":"system",
                "content": 
                """
                You are a fact-checking expert. Your task is to verify if a trivia question and it's answer are factually accurate.
                Respond with a JSON object containing:
                { 
                    "is_factual": boolean,
                    "confidence_score": number (0-1),
                    "explanation": string,
                    "suggested_corrections": array of strings
                }

                IMPORTANT RULES:
                1. Use double quotes for all property names and string values in the JSON response.
                2. Always include the "suggested_corrections" array, even if empty.
                3. For known incorrect answers, set confidence_score to 0.3 or lower.
                4. For factual questions, set confidence_score to 0.8 or higher.
                """
            },
            {
                "role":"user",
                "content": 
                f"""
                Verify the following trivia question:
                Subject: {subject}
                Question: {question}
                Correct Answer: {correct_answer}
                Context: 
                {context}

                Is this question and answer factually accurate? Provide your assessment using the JSON format specified above.
                """
            }
        ]
    )
    
    return completion.choices[0].message.content


def evaluate_incorrect_answers(question, correct_answer, incorrect_answers, subject):
    """
    Checks the quality of incorrect answers so that they are not too easy or obvious. The correct_answer is only used as context for the prompt. 
    
    The accuracy of the question and correct answer is checked in verify_accuracy. 
    The balance of both correct and incorrect answers is checked in evaluate_question_balance.
    
    Overall process: The correct answer is factual, the incorrect answers are not too obviously wrong, and 
    all the questions are balanced in length and complexity.
    Functions used:
    - verify_accuracy
    - evaluate_incorrect_answers
    - evaluate_question_balance
    """
    load_dotenv()
    client = OpenAI()

    completion = client.chat.completions.create(
        model = 'gpt-4',
        messages = [
            {
                'role':'system',
                'content':
                """
                You are a trivia question quality expert. Your task is to evaluate the quality of incorrect answers in a multiple-choice question.
                Respond with a JSON object containing:
                {
                    'overall_quality': number (0-1),
                    'answer_analysis': 
                    [
                        {
                            'answer': string,
                            'is_plausible': boolean,
                            'difficulty_level': number (1-10),
                            'explanation': string
                        }
                    ],
                    'suggested_improvements': array of strings (optional)
                }
                """
            },
            {
                 'role':'user',
                 'content': 
                 f"""
                Evaluate the following trivia question and its answers:
                 Question: {question}
                 Correct Answer: {correct_answer}
                 Incorrect Answers: {incorrect_answers}
                 Subject: {subject}

                 Are the incorrect answers plausible and challenging? Would they make the question too easy or too hard?
                 
                 IMPORTANT RULES:
                1. Use double quotes for all property names and string values in the JSON response.
                2. An answer is plausible if:
                   - It's close to the correct answer (e.g., a different city, a different person)
                   - It's a reasonable mistake someone might make
                   - For dates, answers within a few days to 5 years are plausible.
                3. An answer is not plausible if:
                    - It's obviously wrong (e.g. a different planet, a different century, etc.)
                    - The sentiment of the answer doesn't match the sentiment of the question (e.g. a question about a tragedy is answered with a joke)
                4. For obviously not plausible answers, set difficulty_level to 2 or lower.
                5. For very plausible answers, set difficulty_level to 6 or higher, and make sure there is only one suggested_improvements.
                6. Always include the suggested_improvements key, even if it is just an empty array [] for no suggestions.
                 """
            }
        ]
    )

    return completion.choices[0].message.content


def evaluate_question_balance(question, correct_answer, incorrect_answers, subject):
    """
    Checks the balance of both correct and incorrect answers in terms of structure. 
    
    The accuracy of the question and correct answer is checked in verify_accuracy. 
    The quality of incorrect answers is checked in evaluate_incorrect_answers.
    
    Overall process: The correct answer is factual, the incorrect answers are not too obviously wrong, and 
    all the questions are balanced in length and complexity.
    Functions used:
    - verify_accuracy
    - evaluate_incorrect_answers
    - evaluate_question_balance
    """
    client = OpenAI()

    completion = client.chat.completions.create(
        model = 'gpt-4',
        messages = 
        [
            {
                'role': 'system',
                'content':
                """
                You are a trivia question balance expert. Your task is to ensure that both the correct and incorrect answers are well balanced in terms of length, complexity, and format.
                Respond with a JSON object containing:
                {
                    'is_well_balanced': boolean,
                    'balance_score': number (0-1),
                    'analysis': 
                    {
                        'length_balance': boolean, // Are all answers similar in length?
                        'complexity_balance': boolean, // Are all answers similar in complexity?
                        'format_balance': boolean // Are all answers similar in format (e.g. standardized dates, capitalization of names and locations, etc.)
                    },
                    'reccomendations': array of strings (optional)
                }
                """
            },
            {
                'role': 'user',
                'content':
                f"""
                Evaluate the structural balance of this trivia question:
                Question: {question}
                Correct Answer: {correct_answer}
                Incorrect Answers: {incorrect_answers}
                Subject: {subject}

                Focus only on the structural aspects:
                1. Are all answers similar in length?
                2. Are all answers similar in complexity?
                3. Are all answers in the same format (e.g. standardized dates, capitalization of names and locations, etc.)?
                The goal is for questions to be similar in structure, but not identical.
                
                IMPORTANT RULES:
                1. Use double quotes for all property names and string values in the JSON response.
                ...

                """
            }
        ]
    )

    return completion.choices[0].message.content
