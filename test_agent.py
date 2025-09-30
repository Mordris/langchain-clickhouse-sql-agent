# clickhouse-playground/test_agent.py
import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

load_dotenv()
print("--- Starting LangChain ClickHouse Test ---")

# --- 1. CONFIGURATION ---
db_uri = "clickhouse://default:learn_password@clickhouse-server:8123/uk"

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not found in .env file.")
    exit()

# --- 2. DATABASE CONNECTION ---
try:
    print(f"Connecting to database: {db_uri}")
    db = SQLDatabase.from_uri(db_uri)
    print("Database dialect:", db.dialect)
    print("Usable tables:", db.get_usable_table_names())
    print("--- Connection Successful ---")
except Exception as e:
    print(f"ERROR: Failed to connect to the database. {e}")
    exit()

# --- 3. AGENT CREATION ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=True)
print("--- SQL Agent Created ---")

# --- 4. INTERACTIVE SESSION ---
print("\n--- Starting Interactive Demo Session ---")
print("Type your question and press Enter. Type 'exit' or 'quit' to end.")
print("-" * 50)

while True:
    try:
        question = input("\nAsk a question about the UK house prices dataset > ")

        if question.lower() in ['exit', 'quit']:
            print("Exiting demo. Goodbye!")
            break

        if not question.strip():
            continue

        print("\n...Agent is thinking...\n")

        response = agent_executor.invoke({"input": question})
        
        print("\n--- Agent Execution Complete ---")
        print("Final Answer:")
        print(response["output"])
        print("-" * 50)

    except Exception as e:
        print(f"\nERROR: Agent execution failed. {e}")
        print("-" * 50)