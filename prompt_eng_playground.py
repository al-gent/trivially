from functions import wiki_trending_today, generate_MC_question_with_answers, get_reddit


def run_system():
    questions = []
    titles, extracts = wiki_trending_today(10)

    print('finished wikepedia')

    reddit_post_lists = []
    reddit_text_lists = []
    for title in titles:
        post, text, date = get_reddit(title)
        reddit_post_lists.append(post)
        reddit_text_lists.append(text)

    print('finished reddit')

    for i in range(len(titles)):
        try:
            questions.append(eval(generate_MC_question_with_answers(titles[i], extracts[i], reddit_post_lists[i], reddit_text_lists[i])))
        except SyntaxError as e:
            print(f'Syntax Error, skipped question about {title}')
            continue
    print(questions)

    # try:
    #     # Connect to the database
    #     connection = psycopg2.connect(DATABASE_URL, sslmode="require")
    #     cursor = connection.cursor()

    #     # Insert data into the table
    #     for question in questions:
    #         cursor.execute("""
    #             INSERT INTO questions (q, ca, ica1, ica2, ica3, category, difficulty, rating, subject)
    #             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    #         """, question)

    #     # Commit the transaction
    #     connection.commit()

    #     print("Data inserted successfully!")
    # except Exception as e:
    #     print(f"Error inserting data: {e}")
    # finally:

    #     if cursor:
    #         cursor.close()
    #     if connection:
    #         connection.close()


# Run the function
if __name__ == "__main__":
    run_system()
