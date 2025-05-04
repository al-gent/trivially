import psycopg2
import os
from dotenv import load_dotenv
from functions import wiki_trending_today, generate_MC_question_with_answers, get_reddit, choose_best_topics

def insert_data():
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    questions = []
    titles, extracts = wiki_trending_today(30)
    title_extract_d = {title: extract for title, extract in zip(titles,extracts)}
    print('finished wikepedia')

    selected_titles = choose_best_topics(titles)
    print(f'selected {len(selected_titles)} titles')

    reddit_post_lists =[]
    reddit_text_lists =[]
    for title in selected_titles:
        post, text, date = get_reddit(title)
        reddit_post_lists.append(post)
        reddit_text_lists.append(text)

    print('finished reddit')

    for i,t in enumerate(selected_titles):
        try:
            questions.append(eval(generate_MC_question_with_answers(t, title_extract_d[t], reddit_post_lists[i], reddit_text_lists[i])))
        except SyntaxError as e:
            print(f'Syntax Error, skipped question about {title}')
            continue
    print(questions[0])

    
    try:
        # Connect to the database
        connection = psycopg2.connect(DATABASE_URL, sslmode="require")
        cursor = connection.cursor()

        # Insert data into the table
        for question in questions:
            cursor.execute("""
                INSERT INTO questions (q, ca, ica1, ica2, ica3, category, difficulty, rating, subject)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, question)

        # Commit the transaction
        connection.commit()

        print("Data inserted successfully!")
    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:

        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Run the function
if __name__ == "__main__":
    insert_data()