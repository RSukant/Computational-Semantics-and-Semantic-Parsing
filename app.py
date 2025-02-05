import spacy
import sqlite3
import streamlit as st
import spacy.cli
spacy.cli.download("en_core_web_sm")

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Database setup
DB_NAME = "knowledge_base.db"

# Create and initialize the database
def create_sample_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        grade TEXT
    )""")

    cursor.execute("DELETE FROM students")  # Clear existing data
    
    # Insert sample data
    cursor.executemany("INSERT INTO students (name, age, grade) VALUES (?, ?, ?)", [
        ("Alice", 20, "A"),
        ("Bob", 22, "B"),
        ("Charlie", 21, "C")
    ])

    conn.commit()
    conn.close()

# Function to generate SQL query
def generate_sql_query(question):
    doc = nlp(question.lower())
    
    # Connect to DB to fetch column names
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(students)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()

    conditions = []  # To store the conditions based on the question
    columns_to_select = []  # Columns to be selected in the query
    age = None  # Store the detected age
    person_name = None  # Store the detected person's name
    grade = None  # Store the detected grade

    # Detect names using spaCy's NER
    for ent in doc.ents:
        if ent.label_ == "PERSON":  # Detect name using NER
            person_name = ent.text.capitalize()

    # Fallback: If no PERSON entity is found, check for capitalized words
    if not person_name:
        for token in doc:
            if token.text.istitle():  # Check for capitalized words (potential names)
                person_name = token.text.capitalize()
                break

    # Detect age and other conditions
    for token in doc:
        if token.pos_ == "NUM":  # Detect numeric values for age
            age = token.text
        elif token.text in columns:  # Detect if any column names are mentioned
            columns_to_select.append(token.text)

    # Default columns to select if none are mentioned
    if not columns_to_select:
        columns_to_select = ['name', 'age', 'grade']

    # Generate the SELECT clause
    sql_query = f"SELECT {', '.join(columns_to_select)} FROM students"

    # Add conditions for name and/or age if detected
    if person_name:
        conditions.append(f"name = '{person_name}'")
    if age:
        conditions.append(f"age = {age}")

    # Add the WHERE clause if any condition exists
    if conditions:
        sql_query += " WHERE " + " AND ".join(conditions)

    return sql_query

# Function to execute SQL query
def execute_query(sql_query):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        conn.close()
        return str(e)

# Streamlit Interface
st.title("Semantic Parser: Natural Language to SQL Query")
st.markdown("""
Enter a natural language question, and this tool will generate an SQL query and execute it on the database.
""")

create_sample_db()

question = st.text_input("Enter your question:", "")

if question:
    sql_query = generate_sql_query(question)
    st.write("### Generated SQL Query:")
    st.code(sql_query)

    results = execute_query(sql_query)

    st.write("### Query Results:")
    st.write(results)