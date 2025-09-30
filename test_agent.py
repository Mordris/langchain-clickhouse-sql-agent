import os
import sys
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

load_dotenv()
print("--- Starting LangChain ClickHouse Test ---")

# --- 1. CONFIGURATION (NOW FULLY DYNAMIC) ---
# Load all database credentials from environment variables
db_user = os.getenv("CLICKHOUSE_USER", "default")
db_password = os.getenv("CLICKHOUSE_PASSWORD", "learn_password")
db_host = "clickhouse-server"  # This is the Docker service name
db_port = os.getenv("CLICKHOUSE_PORT", "8123")
db_name = os.getenv("CLICKHOUSE_DB", "e_commerce_analytics")

# Construct the database URI from the variables
db_uri = f"clickhouse://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: OPENAI_API_KEY not found in .env file.")
    sys.exit(1)

# --- 2. DATABASE CONNECTION ---
try:
    print(f"Connecting to database: clickhouse://{db_user}:***@{db_host}:{db_port}/{db_name}")
    db = SQLDatabase.from_uri(db_uri)
    print("Database dialect:", db.dialect)
    print("Usable tables:", db.get_usable_table_names())
    print("--- Connection Successful ---")
except Exception as e:
    print(f"ERROR: Failed to connect to the database. {e}")
    sys.exit(1)

# --- 3. AGENT CREATION ---
try:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    agent_executor = create_sql_agent(
        llm=llm, 
        toolkit=toolkit, 
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
        max_execution_time=60
    )
    print("--- SQL Agent Created ---")
except Exception as e:
    print(f"ERROR: Failed to create SQL agent. {e}")
    sys.exit(1)

# --- 4. HELPER FUNCTIONS ---
def is_data_query(question, llm, db):
    """Use LLM to determine if the question is a legitimate database query"""
    classification_prompt = f"""You are a query classifier for a database assistant. 

Database name: {db_name}
Available tables: {', '.join(db.get_usable_table_names())}

Analyze this user input and determine if it's a legitimate database query or just casual conversation.

User input: "{question}"

Respond with ONLY one word:
- "QUERY" if this is asking for data, statistics, information from the database, or wants to query/analyze the data
- "CHAT" if this is a greeting, casual conversation, personal statement, off-topic question, or not related to querying the database

Examples:
- "hi" -> CHAT
- "what's the average price?" -> QUERY
- "I'm feeling lonely" -> CHAT
- "show me top 10 records" -> QUERY
- "how are you?" -> CHAT
- "which town has highest sales?" -> QUERY

Your response (one word only):"""

    try:
        response = llm.invoke(classification_prompt)
        # Handle different response formats
        if hasattr(response, 'content'):
            result = response.content.strip().upper()
        elif isinstance(response, str):
            result = response.strip().upper()
        else:
            result = str(response).strip().upper()
        
        return "QUERY" in result
    except Exception as e:
        # If classification fails, be conservative and allow the query
        print(f"⚠️  Classification failed: {e}")
        return True

def format_response(response):
    """Format the agent response in a user-friendly way"""
    if isinstance(response, dict):
        output = response.get("output", "")
    else:
        output = str(response)
    
    # Clean up common agent artifacts
    output = output.replace("```sql", "").replace("```", "").strip()
    
    return output

# --- 5. INTERACTIVE SESSION ---
print("\n" + "=" * 60)
print("    📊 DATABASE QUERY ASSISTANT")
print("=" * 60)
print(f"\nConnected to database: {db_name}")
print(f"Available tables: {', '.join(db.get_usable_table_names())}")
print("\nAsk questions about the data in natural language.")
print("Type 'exit', 'quit', or 'q' to end the session.")
print("Type 'help' to see example questions.")
print("-" * 60)

consecutive_errors = 0
max_consecutive_errors = 3

while True:
    try:
        question = input("\n💬 > ").strip()
        
        # Handle exit commands
        if question.lower() in ['exit', 'quit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        # Handle empty input
        if not question:
            continue
        
        # Handle help command
        if question.lower() in ['help', '?']:
            print("\n📖 Example questions:")
            print("  • What are the column names in [table_name]?")
            print("  • How many records are in [table_name]?")
            print("  • What is the average/sum/count of [column_name]?")
            print("  • Show me the top 10 records from [table_name]")
            print("  • Filter data by specific conditions")
            continue
        
        # Check for greetings and casual conversation
        if not is_data_query(question, llm, db):
            print("\n👋 Hello! I'm here to help you query the database.")
            print("💡 Ask me questions about the data, like:")
            print("   - Statistical queries (averages, counts, sums)")
            print("   - Data filtering and searching")
            print("   - Table structure information")
            consecutive_errors = 0
            continue
        
        print("\n🔍 Processing your query...\n")
        
        # Execute the agent
        try:
            response = agent_executor.invoke({"input": question})
            answer = format_response(response)
            
            print("\n" + "=" * 60)
            print("📈 RESULT:")
            print("=" * 60)
            print(answer)
            print("-" * 60)
            
            # Reset error counter on success
            consecutive_errors = 0
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Query interrupted by user.")
            raise
            
        except Exception as agent_error:
            consecutive_errors += 1
            error_msg = str(agent_error).lower()
            
            print("\n" + "=" * 60)
            print("⚠️  QUERY FAILED")
            print("=" * 60)
            
            # Provide user-friendly error messages
            if "timeout" in error_msg or "timed out" in error_msg:
                print("⏱️  The query took too long to execute.")
                print("💡 Try simplifying your question or adding filters to reduce data.")
            elif "syntax" in error_msg or "parse" in error_msg:
                print("❌ There was a problem understanding your question.")
                print("💡 Try rephrasing it more clearly or use simpler terms.")
            elif "not found" in error_msg or "no such" in error_msg or "doesn't exist" in error_msg:
                print("❌ The requested table or column doesn't exist.")
                print(f"💡 Available tables: {', '.join(db.get_usable_table_names())}")
            elif "permission" in error_msg or "access denied" in error_msg:
                print("❌ Permission denied for this operation.")
            else:
                print("❌ Unable to process your query.")
                print("💡 Try rephrasing or asking a different question.")
            
            if consecutive_errors >= max_consecutive_errors:
                print(f"\n⚠️  Multiple consecutive errors detected. Connection may be unstable.")
                print("💡 Consider restarting the session if issues persist.")
                consecutive_errors = 0
            
            print("-" * 60)
    
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted. Goodbye!")
        break
    
    except Exception as outer_error:
        print(f"\n❌ Unexpected error: {type(outer_error).__name__}")
        print("💡 The session will continue. Type 'exit' to quit.")
        consecutive_errors += 1
        
        if consecutive_errors >= max_consecutive_errors:
            print(f"\n⚠️  Too many errors. Exiting for safety.")
            break

print("\n--- Session Ended ---")