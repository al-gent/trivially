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


def generate_MC_question_with_answers_v2(title, extract, reddit_posts, reddit_texts):
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are a trivia master that values accuracy. Create a fun and engaging multiple-choice trivia question. 
                Respond with only the following array of strings, with no additional explanation or text.
                Do not include markdown formatting or any text outside of the list. Do not add line breaks between entries. Do not use any emojis.
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
                "content": f"""Create a multiple-choice trivia question about '{title}'.
                Use this context as background information: {extract}.
                Use these reddit posts to understand why this topic is relevant right now.
                {[(post, text) for (post, text) in zip(reddit_posts, reddit_texts)]}
                Allude to why this topic is relevant in the question.
                Try to have the main topic or subject in the question and not the asnwer.
                When possible try to avoid using the words or phrases in the answer in teh question as well."""
            }
        ])

    # Extract and store the generated question
    return completion.choices[0].message.content


def generate_MC_question_with_answers_v3(title, extract, reddit_posts, reddit_texts):
    client = OpenAI()

    completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a highly precise trivia master that creates unique, insightful multiple-choice questions rooted in timely context. 
        Return only a JSON-style list of strings in this format:
        [
            "<question>",
            "<correct answer>",
            "<incorrect option 1>",
            "<incorrect option 2>",
            "<incorrect option 3>",
            "<category>",
            "<difficulty (1-10)>",
            "<rating (1-10)>",
            "<subject>"
        ]
        - The question must be specific, interesting, and not just biographical or headline-based.
        - The question should reference a unique or lesser-known fact or angle about the topic, especially one that connects to current relevance.
        - Do not use the correct answer's exact wording in the question unless unavoidable.
        - Use reasoning, consequence, or impact when possible (e.g., "What policy introduced by X had this effect?" or "Which controversial stance did X take in 2025?")
        - Never repeat the subject or answer in the question if it spoils it.
        - Do not include any text, explanation, or formatting outside the list of strings.
        """
                },
                {
                    "role": "user",
                    "content": f"""Topic: '{title}'.
                    Use this background context: {extract}.
                    Incorporate insight from these Reddit discussions to understand current public interest and framing:
                    {[(post, text) for (post, text) in zip(reddit_posts, reddit_texts)]}
                    Allude to why this topic is relevant in the question.
                    Try to have the main topic or subject in the question and not the asnwer.
                    When possible try to avoid using the words or phrases in the answer in teh question as well."""
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
                    You are a trivia master who writes fun, clever, and surprising multiple-choice questions.

                    Your goals:
                    - Make each question a real question (end with a question mark).
                    - The subject (e.g. 'Pope Francis', '2025 Canadian election') must appear in the question for clarity.
                    - Do NOT give away the answer in the question or lead directly to it.
                    - Focus on ironic, unusual, precedent-breaking, or fun outcomes—not summaries or job titles.
                    - Keep answers short (max 6 words).
                    - The correct answer should feel surprising but true.
                    - Incorrect answers must be:
                    - Plausible but clearly false
                    - Related to the topic (avoid nonsense or fantasy)
                    - Interesting or funny in a grounded way (no aliens, magic, etc.)

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
                    - Highlight something ironic, surprising, controversial, or precedent-breaking.
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



def verify_accuracy(question, correct_answer, context, subject):
    """
    Checks the factual accuracy of the question and the correct answer.

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
    
    result = completion.choices[0].message.content
    result_dict = json.loads(result)
    
    if result_dict["is_factual"] and result_dict["confidence_score"] >= 0.8:
        print(f"✅ Accuracy Test PASSED for question about {subject} with confidence score {result_dict['confidence_score']}")
    else:
        print(f"❌ Accuracy Test FAILED for question about {subject} with confidence score {result_dict['confidence_score']}")
        if result_dict["suggested_corrections"]:
            print("   Suggested Corrections:")
            for correction in result_dict["suggested_corrections"]:
                print(f"   - {correction}")
    
    return result


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
                    "overall_quality": number (0-1),
                    "answer_analysis": 
                    [
                        {
                            "answer": string,
                            "is_plausible": boolean,
                            "difficulty_level": number (1-10),
                            "explanation": string
                        }
                    ],
                    "suggested_improvements": array of strings
                }

                IMPORTANT RULES:
                1. Use double quotes for all property names and string values in the JSON response.
                2. For date-based questions:
                   - Answers within 1 month of the correct date are ALWAYS plausible
                   - Answers within 1 year of the correct date are ALWAYS plausible
                   - Answers within 5 years of the correct date are USUALLY plausible
                   - Answers more than 5 years away are NOT plausible
                3. For non-date questions, an answer is plausible if:
                   - It's close to the correct answer (e.g., a different city, a different person)
                   - It's a reasonable mistake someone might make
                   - It's in the same category or type as the correct answer
                4. An answer is not plausible if:
                   - It's obviously wrong (e.g. a different planet, a different century)
                   - The sentiment of the answer doesn't match the sentiment of the question
                   - It's completely unrelated to the subject matter
                5. For obviously not plausible answers:
                   - Set is_plausible to false
                   - Set difficulty_level to 2 or lower
                6. For plausible answers:
                   - Set is_plausible to true
                   - Set difficulty_level to 6 or higher
                7. Always include the suggested_improvements array, even if empty
                8. Set overall_quality to 0.7 or higher only if all answers are plausible
                9. Set overall_quality to 0.3 or lower if any answers are not plausible
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
                 
                 For date-based questions, remember:
                 - Answers within 1 month or 1 year of the correct date are ALWAYS plausible
                 - Answers within 5 years are USUALLY plausible
                 - Answers more than 5 years away are NOT plausible
                 
                 Provide your assessment using the JSON format specified above.
                 """
            }
        ]
    )

    result = completion.choices[0].message.content
    result_dict = json.loads(result)
    
    if result_dict["overall_quality"] >= 0.7:
        print(f"✅ Plausibility Test PASSED for question about {subject} with quality score {result_dict['overall_quality']}")
    else:
        print(f"❌ Plausibility Test FAILED for question about {subject} with quality score {result_dict['overall_quality']}")
        if result_dict["suggested_improvements"]:
            print("   Suggested Improvements:")
            for improvement in result_dict["suggested_improvements"]:
                print(f"   - {improvement}")

    return result


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
                    "is_well_balanced": boolean,
                    "balance_score": number (0-1),
                    "analysis": 
                    {
                        "length_balance": boolean,
                        "complexity_balance": boolean,
                        "format_balance": boolean
                    },
                    "reccomendations": array of strings
                }

                IMPORTANT RULES:
                1. Use double quotes for all property names and string values in the JSON response.
                2. Length balance: All answers should be within 20% of each other's length.
                3. Complexity balance: All answers should have similar levels of detail and complexity.
                4. Format balance: All answers should follow the same format (e.g., same capitalization, same level of formality).
                5. Set balance_score to 0.7 or higher only if all three balance criteria are met.
                6. Set balance_score to 0.5 or lower if any balance criteria are not met.
                7. Always include the reccomendations array, even if empty.
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

                Focus on these specific aspects:
                1. Length balance: Are all answers within 20% of each other's length?
                2. Complexity balance: Do all answers have similar levels of detail and complexity?
                3. Format balance: Do all answers follow the same format (e.g., same capitalization, same level of formality)?

                Provide your assessment using the JSON format specified above.
                """
            }
        ]
    )

    result = completion.choices[0].message.content
    result_dict = json.loads(result)
    
    if result_dict["balance_score"] >= 0.7:
        print(f"✅ Balance Test PASSED for question about {subject} with balance score {result_dict['balance_score']}")
    else:
        print(f"❌ Balance Test FAILED for question about {subject} with balance score {result_dict['balance_score']}")
        if result_dict["reccomendations"]:
            print("   Recommendations:")
            for recommendation in result_dict["reccomendations"]:
                print(f"   - {recommendation}")

    return result

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

