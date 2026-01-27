import os
import asyncio
import dotenv

from .tools import get_maps_mcp_toolset, get_bigquery_mcp_toolset

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from google.genai import types

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configuration
PROJECT_ID = "project2-283514"
DATASET_ID = "logistics_data"
TABLE_ID = "orders"
FULL_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Initialize Toolsets
maps_toolset = get_maps_mcp_toolset()
bq_toolset = get_bigquery_mcp_toolset()

# Define the Agent
root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='logistics_recovery_agent',
    instruction=f"""
You are an expert Retail Operations Recovery Agent.


Step 1: Get Data from BigQuery
- Use the 'execute_sql' tool.
- Pass the SQL string in the 'query' parameter.
- SQL to run: 
    SELECT order_id, warehouse_location, customer_address 
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` 
    WHERE status = 'Delayed' AND priority = 'High'

Step 2: Calculate Distances
- For each order, use the Maps 'compute_routes' tool.
- Parameters:
    origin: {{"address": warehouse_location}}
    destination: {{"address": customer_address}}
    travelMode: "DRIVE"

Step 3: Recommendation
- Distance > 500 miles (804,672 meters) -> "Upgrade to Air Shipping"
- Otherwise -> "Regional Express Ground"

Step 4: Output
- Provide a markdown table with: Order ID, Warehouse, Customer Address, Distance (miles), and Recommendation.
""",
    tools=[maps_toolset, bq_toolset]
) 

async def main():
    # Setup ADK Runner environment simplified
    # Note: Ensure root_agent is defined before this
    runner = Runner(
        app_name="logistics_app",
        agent=root_agent,  # The Runner takes the LlmAgent instance here
    )

    # Initial prompt
    user_input = "Identify high-priority delayed orders and suggest recovery shipping methods."
    content = types.Content(role="user", parts=[types.Part(text=user_input)])

    print("--- Starting Smart Logistics Agent ---\n")
    
    # We can run without explicitly passing session_id if we want a new default session
    async for event in runner.run_async(
        user_id="admin_user", 
        new_message=content
    ):
        if hasattr(event, 'content') and event.content.parts:
            print(event.content.parts[0].text)
