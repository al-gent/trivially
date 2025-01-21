import psycopg2
import os
from dotenv import load_dotenv
from functions import wiki_trending_today, generate_MC_question_with_answers




def insert_data():
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    questions = []
    titles, extracts = wiki_trending_today(1)
    print('finished wikepedia')

    for i in range(len(titles)):
        questions.append(eval(generate_MC_question_with_answers(titles[i], extracts[i])))
    print(questions)

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
        cursor.execute("SELECT * FROM questions;")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Run the function
if __name__ == "__main__":
    insert_data()