import os
import dotenv
import google.auth
import google.auth.transport.requests
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams 

# Constants
MAPS_MCP_URL = "https://mapstools.googleapis.com/mcp" 
BIGQUERY_MCP_URL = "https://bigquery.googleapis.com/mcp" 

def get_maps_mcp_toolset():
    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    maps_api_key = os.getenv('MAPS_API_KEY')
    
    if not maps_api_key:
        raise ValueError("MAPS_API_KEY not found in environment variables.")

    return MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=MAPS_MCP_URL,
            headers={
                "X-Goog-Api-Key": maps_api_key,
                "Content-Type": "application/json"
            }
        )
    )

def get_bigquery_mcp_toolset():   
    # Auth for BigQuery using Google Application Default Credentials
    credentials, project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )

    # Refresh credentials to ensure the OAuth token is active
    credentials.refresh(google.auth.transport.requests.Request())
        
    return MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=BIGQUERY_MCP_URL,
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "x-goog-user-project": project_id,
                "Content-Type": "application/json"
            }
        )
    )
