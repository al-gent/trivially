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
    
    Overall process: The correct answer is factual, the incorrect answers are not too obvious, and 
    all the questions are standardized in capitalization and length.
    Functions used:
    - verify_accuracy                   # implemented
    - evaluate_incorrect_answers        # implemented
    - evaluate_question_format          # not used
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
                You responsible for making sure the question and the correct answer are not obviously false. 
                You are focused on the overall factual accuracy of the question and the correct answer, and are not concerned about the details.
                If unsure, assume the question is true. Score each question & answer combo on a scale of 0 to 1, where 0 is false and 1 is true.

                Respond with a JSON object containing:
                { 
                    "is_factual": boolean,
                    "confidence_score": number (0-1),
                    "explanation": string,
                    "potential_improvements": array of strings
                }

                IMPORTANT RULES:
                1. Use double quotes for all property names and string values in the JSON response.
                2. Questions about 2025 can be true, even if the event is recent.
                3. A false question/answer pair should have a confidence score below 0.3, and look like this:
                    - Question: "What movie franchise is the TV series Andor a part of?"
                    - Answer: "Marvel Cinematic Universe"
                    - Confidence score: 0.2
                4. A true question/answer pair should have a confidence score of 0.5 or higher, and look like this:
                    - Question: "What movie franchise is the TV series Andor a part of?"
                    - Answer: "Star Wars"
                    - Confidence score: 0.9
                5. For questions/answers that have a confidence score below 0.3, set is_factual to false.
                6. For questions/answers that have a confidence score of 0.5 or higher, set is_factual to true.
                7. Ignore minor details and focus on the overall topic accuracy instead.
                8. When fact checking, consider topics that might have the same meaning (e.g. video games that are also TV series is true)
                9. Always include the "potential_improvements" array, even if empty.
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

                Is this question and answer not obviously false? 
                
                Provide your assessment using the JSON format specified above.
                """
            }
        ]
    )
    
    result = completion.choices[0].message.content
    result_dict = json.loads(result)
    
    if result_dict["is_factual"]:
        print(f"✅ Accuracy Test for question about {subject}")
    else:
        print(f"❌ Accuracy Test for question about {subject}")
        if result_dict["potential_improvements"]:
            print(f"QUESTION: {question}")
            print(f"CORRECT ANSWER: {correct_answer}")
            print("REASON FOR FALSE:")
            print(result_dict["explanation"])
            print("RECCOMENDATIONS:")
            for correction in result_dict["potential_improvements"]:
                print(f"    - {correction}")
    
    return result



def evaluate_incorrect_answers(question, correct_answer, incorrect_answers, subject):
    """
    Checks the quality of incorrect answers so that they are not too easy or obvious. The correct_answer is only used as context for the prompt. 
    
    Overall process: The correct answer is factual, the incorrect answers are not too obvious, and 
    all the questions are standardized in capitalization and length.
    Functions used:
    - verify_accuracy                   # implemented
    - evaluate_incorrect_answers        # implemented
    - evaluate_question_format          # not used
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
                You responsible for making sure the incorrect answers in a multiple-choice question are not too easy or obvious.
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
                    "potential_improvements": array of strings
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
                   - The sentiment of the answer doesn't match the sentiment of the question (e.g. a question about a terrorist attack is not plausible if the answer is a peace prize)
                   - It's completely unrelated to the subject matter
                5. For obviously not plausible answers:
                   - Set is_plausible to false
                   - Set difficulty_level to 2 or lower
                6. For plausible answers:
                   - Set is_plausible to true
                   - Set difficulty_level to 6 or higher
                7. Set overall_quality to 0.7 or higher only if all incorrect answers are plausible
                8. Set overall_quality to 0.5 if one incorrect answer is not plausible
                9. Set overall_quality to lower than 0.5 if more than one incorrect answers is not plausible
                10. Always include the potential_improvements array, even if empty
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

                 Are the incorrect answers plausible? Would they make the question too easy or too hard?
                 
                 Provide your assessment using the JSON format specified above.
                 """
            }
        ]
    )

    result = completion.choices[0].message.content
    result_dict = json.loads(result)
    
    if result_dict["overall_quality"] >= 0.7:
        print(f"✅ Plausibility Test for question about {subject} with quality score {result_dict['overall_quality']}")
    else:
        print(f"❌ Plausibility Test for question about {subject} with quality score {result_dict['overall_quality']}")
        if result_dict["potential_improvements"]:
            print(f"QUESTION: {question}")
            print(f"CORRECT ANSWER: {correct_answer}")
            print(f"INCORRECT ANSWERS: {incorrect_answers}")
            print("REASON FOR FALSE:")
            print(result_dict["answer_analysis"][0]["explanation"])
            print("RECCOMENDATIONS:")
            for improvement in result_dict["potential_improvements"]:
                print(f"    - {improvement}")

    return result



def evaluate_question_format(question, correct_answer, incorrect_answers, subject):
    """
    Checks the format of all answers in terms of capitalization and length. 
    
    Overall process: The correct answer is factual, the incorrect answers are not too obvious, and 
    all the questions are standardized in capitalization and length.
    Functions used:
    - verify_accuracy                   # implemented
    - evaluate_incorrect_answers        # implemented
    - evaluate_question_format          # not used
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
                You responsible for making sure that all the answers, both correct and incorrect, have the same capitalization patterns and are of similar length. 
                Respond with a JSON object containing:
                {
                    "is_same_format": boolean,
                    "analysis": 
                    {
                        "same_capitalization": boolean,
                        "similar_length": boolean
                    },
                    "potential_improvements": array of strings
                }

                IMPORTANT RULES:
                1. Use double quotes for all property names and string values in the JSON response.
                2. For same_capitalization: Answers should be in sentence case.
                    - Answers should start with a capital letter
                    – Proper nouns should be capitalized (not all answers need to have proper nouns)
                3. For similar_length: All answers should be within 40% of each other's word count.
                4. Set is_same_format to true only if all two criteria are met.
                5. Set is_same_format to false if any criteria are not met.
                6. Always include the potential_improvements array, even if empty.
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

                Is the format of all answers similar in terms of capitalization, punctuation, and length?

                Provide your assessment using the JSON format specified above.
                """
            }
        ]
    )

    result = completion.choices[0].message.content
    result_dict = json.loads(result)
    
    if result_dict["is_same_format"]:
        print(f"✅ Format Test for question about {subject}")
    else:
        print(f"❌ Format Test for question about {subject}")
        if result_dict["potential_improvements"]:
            print(f"Question: {question}")
            print(f"Correct Answer: {correct_answer}")
            print(f"Incorrect Answers: {incorrect_answers}")
            print("RECCOMENDATIONS:")
            for recommendation in result_dict["potential_improvements"]:
                print(f"    - {recommendation}")
            print()

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
    backup_topics = [key for key, _ in sorted(search_ratings.items(), key=lambda item: item[1], reverse=True)[n:2*n]]
    return chosen_topics, backup_topics



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

