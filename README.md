# LangChain & ClickHouse: A Fully-Configurable Text-to-SQL Agent

This repository provides a complete, self-contained, and interactive demonstration of a powerful Text-to-SQL agent built with Python, LangChain, and ClickHouse. It is designed to serve as a proof-of-concept and a starting point for integrating natural language database queries into your applications.

The entire environment is containerized with Docker and is fully configurable via environment variables, ensuring perfect reproducibility and easy adaptation.

## ✨ Features

- **Natural Language to SQL:** Ask complex questions about your data in plain English.
- **Intelligent Reasoning:** The agent inspects the database schema to understand table relationships and automatically construct `JOIN` queries.
- **ClickHouse Integration:** Demonstrates a direct connection to a high-performance ClickHouse analytical database.
- **Fully Dockerized:** All services (ClickHouse & the Python app) are defined in a single `docker-compose.yml` for a one-command setup.
- **Configuration-Driven:** All settings (API keys, database credentials) are managed via a `.env` file, with no hardcoded values.
- **Interactive Demo:** The final script runs in an interactive loop, perfect for live demonstrations.
- **Verbose Output:** See the agent's entire thought process, from analyzing the schema to generating and executing the final SQL query.

---

## 🏛️ Architecture

This project uses a LangChain SQL Agent to orchestrate the process. The agent acts as a reasoning engine, using a Large Language Model (LLM) to understand the user's goal and a toolkit to interact with the database.

The data flow for a single query is as follows:

```mermaid
sequenceDiagram
    participant User
    participant App as Python Script (test_agent.py)
    participant Agent as LangChain SQL Agent
    participant OpenAI
    participant ClickHouse

    User->>+App: Asks question ("Which customer spent the most?")
    App->>+Agent: invoke(question)
    Agent->>+ClickHouse: Get table schema (e.g., table names, columns)
    ClickHouse-->>-Agent: Returns schema information
    Agent->>+OpenAI: "Here is the schema and the user's question. Write a SQL query."
    OpenAI-->>-Agent: Returns generated SQL string
    Agent->>+ClickHouse: Execute SQL query
    ClickHouse-->>-Agent: Returns raw data results
    Agent->>+OpenAI: "Here are the query results. Formulate a final, human-readable answer."
    OpenAI-->>-Agent: Returns natural language answer
    Agent-->>-App: Final Answer
    App-->>-User: Prints Final Answer to console
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) installed and running on your machine.
- An [OpenAI API Key](https://platform.openai.com/api-keys).

### Step 1: Clone and Configure the Project

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/langchain-clickhouse-sql-agent.git
    cd langchain-clickhouse-sql-agent
    ```

2.  **Create your environment file from the template:**
    Copy the example file to create your own local configuration.

    ```bash
    cp .env.example .env
    ```

3.  **Edit the `.env` file:**
    Open the newly created `.env` file and add your secret OpenAI API key. You can leave the `CLICKHOUSE` variables as they are for this demo.
    ```
    # .env
    OPENAI_API_KEY="sk-YourSecretOpenAIKeyGoesHere"
    CLICKHOUSE_DB="e_commerce_analytics"
    CLICKHOUSE_USER="default"
    CLICKHOUSE_PASSWORD="learn_password"
    ```

### Step 2: Set Up the ClickHouse Database

Before running the agent, you must start the ClickHouse server and populate it with the test data. This process is fully automated by the configuration you just set.

1.  **Start the ClickHouse Server:**
    This command will start the database container in the background, automatically creating the `e_commerce_analytics` database with the specified user and password.

    ```bash
    docker-compose up -d clickhouse-server
    ```

2.  **Connect to the ClickHouse Client:**
    This opens a command-line interface inside the running container.

    ```bash
    docker-compose exec clickhouse-server clickhouse-client -m
    ```

    _(The `-m` flag allows for pasting multi-line commands.)_

3.  **Run the Setup SQL Commands:**
    Paste each of the following SQL blocks into the client one by one and press Enter.

    - **Create the `customers` table:**

      ```sql
      CREATE TABLE e_commerce_analytics.customers
      (
          `customer_id` UUID,
          `name` String,
          `join_date` Date,
          `country` FixedString(2)
      )
      ENGINE = MergeTree
      ORDER BY (join_date, country);
      ```

    - **Create the `orders` table:**

      ```sql
      CREATE TABLE e_commerce_analytics.orders
      (
          `order_id` UUID,
          `customer_id` UUID,
          `product_name` String,
          `total_price` Decimal(10, 2),
          `order_date` DateTime
      )
      ENGINE = MergeTree
      ORDER BY (order_date, customer_id);
      ```

    - **Insert sample data:**

      ```sql
      -- Customer John Doe
      INSERT INTO e_commerce_analytics.customers VALUES ('00000000-0000-0000-0000-000000000001', 'John Doe', '2025-01-15', 'US');
      INSERT INTO e_commerce_analytics.orders VALUES (generateUUIDv4(), '00000000-0000-0000-0000-000000000001', 'Laptop', 1200.00, '2025-03-20 14:00:00');

      -- Customer Jane Smith (our top spender)
      INSERT INTO e_commerce_analytics.customers VALUES ('00000000-0000-0000-0000-000000000002', 'Jane Smith', '2025-02-10', 'DE');
      INSERT INTO e_commerce_analytics.orders VALUES (generateUUIDv4(), '00000000-0000-0000-0000-000000000002', 'Camera', 950.50, '2025-04-05 11:30:00');
      INSERT INTO e_commerce_analytics.orders VALUES (generateUUIDv4(), '00000000-0000-0000-0000-000000000002', 'Headphones', 250.00, '2025-04-10 09:00:00');

      -- Customer Ahmet Yilmaz
      INSERT INTO e_commerce_analytics.customers VALUES ('00000000-0000-0000-0000-000000000003', 'Ahmet Yilmaz', '2025-03-01', 'TR');
      INSERT INTO e_commerce_analytics.orders VALUES (generateUUIDv4(), '00000000-0000-0000-0000-000000000003', 'Keyboard', 75.25, '2025-05-01 18:00:00');
      ```

4.  **Exit the client** by typing `exit` and pressing Enter. Your database is now ready.

### Step 3: Run the Interactive Demo

1.  **Build the Test Application Image:**

    ```bash
    docker-compose build
    ```

2.  **Run the Interactive Script:**
    This command will start the application and attach your terminal to it, allowing you to type questions.
    ```bash
    docker-compose run -it --rm langchain-test-app
    ```

---

## 💡 How to Use

Once the script is running, you will see a prompt. Ask questions in natural language about the data. The agent is aware of both the `customers` and `orders` tables and can perform JOINs.

**Example Questions:**

- `Which customer spent the most money in total?`
- `How many orders has John Doe placed?`
- `List all products bought by customers from Germany (DE).`
- `What is the total revenue from all approved orders?` (Note: Our sample data has no `status` column, so the agent will correctly tell you it can't answer this).

Type `exit` to end the session.

## 🧹 Cleanup

When you are finished, you can stop all containers and remove the data volume with a single command:

```bash
docker-compose down -v
```
