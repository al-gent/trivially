from functions import wiki_trending_today, generate_MC_question_with_answers, generate_MC_question_with_answers_v2, generate_MC_question_with_answers_v3, generate_MC_question_with_answers_v4, get_reddit


def run_system():
    questions = []
    questions2 = []
    questions3 = []
    questions4 = []
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
            print("1")

            # questions2.append(eval(generate_MC_question_with_answers2(titles[i], extracts[i], reddit_post_lists[i], reddit_text_lists[i])))

            # questions3.append(eval(generate_MC_question_with_answers3(titles[i], extracts[i], reddit_post_lists[i], reddit_text_lists[i])))
            # print("3")

            questions4.append(eval(generate_MC_question_with_answers_v4(titles[i], extracts[i], reddit_post_lists[i], reddit_text_lists[i])))
            print("4")

        except SyntaxError as e:
            print(f'Syntax Error, skipped question about {title}')
            continue
    # print(questions)
    for i in range(len(questions)):
        print(questions[i])
        # print("-vs-")
        # print(questions2[i])
        # print("-vs-")
        # print(questions3[i])
        print("-vs-")
        print(questions4[i])
        print("\n ====== \n")

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
