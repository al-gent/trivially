import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    # Connect to the database
    connection = psycopg2.connect(DATABASE_URL, sslmode="require")
    cursor = connection.cursor()

    # Fetch all rows from the questions table
    cursor.execute("""
        SELECT * FROM questions
        ORDER BY id DESC
        LIMIT 1;
    """)
    rows = cursor.fetchall()

    # Get column names from cursor description
    column_names = [desc[0] for desc in cursor.description]

    # Create DataFrame
    df = pd.DataFrame(rows, columns=column_names)

    # Print DataFrame contents
    print(df)

except Exception as e:
    print(f"Error fetching data: {e}")
finally:
    if cursor:
        cursor.close()
    if connection:
        connection.close()
