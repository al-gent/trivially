import psycopg2
import os
from dotenv import load_dotenv
import json
from functions import wiki_trending_today, generate_MC_question_with_answers, get_reddit, choose_best_topics, generate_MC_question_with_answers_v4, verify_accuracy, evaluate_incorrect_answers, evaluate_question_format

def validate_question(title, extract, reddit_posts, reddit_texts, max_attempts=3, is_backup=False):
    attempt = 0
    question_passed = False
    question_data = None

    while attempt < max_attempts and not question_passed:
        try:
            question_data = eval(generate_MC_question_with_answers_v4(title, extract, reddit_posts, reddit_texts))

            question = question_data[0]
            correct_answer = question_data[1]
            incorrect_answers = question_data[2:5]
            subject = question_data[8]
            
            # First run accuracy test
            accuracy_result = json.loads(verify_accuracy(question, correct_answer, extract, subject))
            
            # Only proceed with plausibility test if accuracy test passes
            if accuracy_result["is_factual"]:
                plausibility_result = json.loads(evaluate_incorrect_answers(question, correct_answer, incorrect_answers, subject))
                
                if plausibility_result["overall_quality"] >= 0.7:
                    question_passed = True
                    print(f"PASS: Tests passed for {'backup ' if is_backup else ''}question about {subject}")
                else:
                    print(f"FAIL: Plausibility test failed for {'backup ' if is_backup else ''}question about {subject} (attempt {attempt + 1}/{max_attempts})")
                    attempt += 1
            else:
                print(f"FAIL: Accuracy test failed for {'backup ' if is_backup else ''}question about {subject} (attempt {attempt + 1}/{max_attempts})")
                attempt += 1
        
        except SyntaxError as e:
            print(f"Syntax Error, skipped {'backup ' if is_backup else ''}question about {title}.\n {e}")
            attempt += 1
            continue
        
    return question_passed, question_data


def insert_data():
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    questions = []
    titles, extracts = wiki_trending_today(30)
    title_extract_d = {title: extract for title, extract in zip(titles, extracts)}
    print('finished wikepedia')

    selected_titles, backup_titles = choose_best_topics(titles)
    print(f'selected {len(selected_titles)} titles')

    reddit_post_lists = []
    reddit_text_lists = []
    for title in selected_titles:
        post, text, date = get_reddit(title)
        reddit_post_lists.append(post)
        reddit_text_lists.append(text)

    print('finished reddit')

    i = 0
    while i < len(selected_titles):
        title = selected_titles[i]
        extract = title_extract_d[title]
        reddit_posts = reddit_post_lists[i]
        reddit_texts = reddit_text_lists[i]

        # Try to generate a valid question
        question_passed, question_data = validate_question(title, extract, reddit_posts, reddit_texts)

        if question_passed:
            questions.append(question_data)
        
        # All attempts failed, try a different topic
        if not question_passed and backup_titles:
            print(f"All attempts failed for {title}, trying backup topic...")
            backup_title = backup_titles.pop(0)

            backup_posts, backup_texts, backup_dates = get_reddit(backup_title)
            
            question_passed, question_data = validate_question(backup_title, title_extract_d[backup_title], backup_posts, backup_texts, is_backup=True)

            if question_passed:
                questions.append(question_data)
        
        i += 1
    
    # Add verified questions to the database
    if questions:
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
            print(f"Successfully inserted {len(questions)} questions into the database!")

        except Exception as e:
            print(f"Error inserting data: {e}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    else:
        print("No valid questions were generated to insert into the database.")

# Run the function
if __name__ == "__main__":
    insert_data()
