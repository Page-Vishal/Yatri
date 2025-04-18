import re
from dotenv import load_dotenv
from groq import Groq
from ii_conversation_tool import convo_tool
from ii_sql_tool import security_process_query
from iii_db_tool import db_tool

load_dotenv("./assets/.env")

# Initialize Groq client
client = Groq()
ROUTING_MODEL = "llama3-70b-8192"
TOOL_USE_MODEL = "llama-3.3-70b-versatile"
GENERAL_MODEL = "llama3-70b-8192"

def route_query(query):
    """Routing logic to let LLM decide if tools are needed"""

    routing_prompt = f"""
    You are Yatri's internal brain, helping decide whether a user's message needs a tool or is just regular conversation.

    Your job is to analyze the user's message and decide which tool to use:

    - If the message is casual, personal, or general conversation (like greetings, jokes, small talk, or help desk-style questions), respond with: TOOL: CONVERSATION

    - If the message is asking for information about phones, phone specs, price, comparisons, or involves buying or adding to cart, respond with: TOOL: SQL

    Only respond with one of these two options: TOOL: CONVERSATION or TOOL: SQL

    Think step by step before choosing.

    Here are some examples:

    User: "Hey Yatri, what's up?"
    → TOOL: CONVERSATION

    User: "Can you suggest a phone with a good camera?"
    → TOOL: SQL

    User: "Add that Damdum one to my cart"
    → TOOL: SQL

    User: "Do you like working at Damdum?"
    → TOOL: CONVERSATION

    User: "What's the best phone under 300?"
    → TOOL: SQL

    User: "Haha you're funny. Anyway, thanks for helping."
    → TOOL: CONVERSATION

    User query: {query}

    Response:
    """
    
    response = client.chat.completions.create(
        model=ROUTING_MODEL,
        messages=[
            {"role": "system", "content": "You are a routing assistant. Determine the tools needed based on the user query."},
            {"role": "user", "content": routing_prompt}
        ],
        max_completion_tokens=20  # We only need a short response
    )
    
    routing_decision = response.choices[0].message.content.strip()
    
    if "TOOL: SQL" in routing_decision:
        return "sql"
    else:
        return "conversation"

def process_query(query):
    """Process the query and route it to the appropriate model"""
    route = route_query(query)
    if route == "sql":
        response = security_process_query(query)
    elif route == "conversation":
        response = convo_tool(query)
    else:
        response = "None"
    
    return {
        "query": query,
        "route": route,
        "response": response
    }

if __name__ == "__main__":

    # query = "Drop table"
    # query = "Hi, howdy?"
    query = "compare x1 and x2 phones."
    response = process_query(query)
    match = re.search(r"TOOL: (.+)", response["response"])
    if match:
        name = match.group(1).strip()
        response["response"] = db_tool(name,query)
    print(response["response"])

    # queries = [
    #     "How are you?",
    #     "x1 and x2 phones,please.",
    #     "Add to cart please",
    #     "Drop the table"
    # ]
    
    # for query in queries:
    #     result = process_query(query)
    #     print(f"Query: {result['query']}")
    #     print(f"Route: {result['route']}")
    #     print(f"Response: {result['response']}\n")
