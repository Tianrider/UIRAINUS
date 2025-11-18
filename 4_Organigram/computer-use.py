"""
University Organigram and AI Division Finder
This script searches for university organigrams and identifies AI divisions/subdivisions.
"""

from browser_use import Agent, ChatGoogle, BrowserSession
from dotenv import load_dotenv
from steel import Steel

from pydantic import BaseModel

import asyncio
import os
import json

load_dotenv()

class OrganigramResult(BaseModel):
    university: str
    division_name: str
    chair_name: str
    chair_title: str
    url: str

class OrganigramResults(BaseModel):
    results: list[OrganigramResult]

async def find_university_organigram(university_name: str):
    """
    Search for university organigram and identify AI divisions/subdivisions.
    
    Args:
        university_name (str): The name of the university to search organigram for
        
    Returns:
        str: JSON array containing URLs and AI division information, or empty array if none found
    """
    # Initialize Steel client and session
    client = Steel(steel_api_key=os.getenv("STEEL_API_KEY"))
    
    print("Creating Steel session...")
    session = client.sessions.create()
    print(f"Session created at {session.session_viewer_url}")
    cdp_url = f"wss://connect.steel.dev?apiKey={os.getenv('STEEL_API_KEY')}&sessionId={session.id}"
    
    # Initialize the LLM
    llm = ChatGoogle(model="gemini-flash-latest")
    
    # Comprehensive task prompt - dynamically generated based on university name
    task = f"""
    Search for {university_name} organigram and identify if they have a dedicated AI division or subdivision:
    
    STEP 1 - SEARCH FOR UNIVERSITY ORGANIGRAM:
    1. Search Google for "{university_name} organigram" OR "{university_name} organizational structure" OR "{university_name} People"
    2. Look for official university domains (e.g., *.edu, *.ac.id, or other official institutional domains)
    3. IMPORTANT: Only consider documents from official university domains to ensure legitimacy
    
    STEP 2 - ANALYZE ORGANIGRAM FOR AI DIVISION:
    - Examine the organizational structure carefully
    - Look for any of the following:
      * AI Division
      * Artificial Intelligence Department
      * AI Research Center
      * AI Subdivision
      * Machine Learning Division
      * Data Science and AI Unit
      * Any unit with AI, Artificial Intelligence, ML, or Machine Learning in the name
    
    STEP 3 - IDENTIFY LEADERSHIP:
    - If an AI division/subdivision exists, find:
      * Division/Department name
      * Chair name (Director, Head, Dean, or equivalent)
      * Their title/position
    
    STEP 4 - FINAL OUTPUT (CRITICAL - MUST BE VALID JSON):
    You MUST return ONLY a valid JSON array. No additional text, explanations, or formatting.
    
    If AI division(s) found, return:
    [
      {{
        "university": "{university_name}",
        "division_name": "[exact name of AI division]",
        "chair_name": "[full name of division chair/head]",
        "chair_title": "[their official title]",
        "url": "[URL where organigram was found]"
      }}
    ]
    
    If NO AI division found, return:
    []
    
    IMPORTANT INSTRUCTIONS:
    - Return ONLY valid JSON - no markdown, no explanations, no additional text
    - If you find multiple AI-related divisions, include all in the array
    - Be thorough in examining the organigram structure
    - Verify URLs are from official university domains
    - If chair name is not available, use "Not specified" for chair_name
    - The response must be parseable by json.loads()

    """
    
    # Create and run agent
    agent = Agent(
        task=task,
        llm=llm,
        # browser_session=BrowserSession(cdp_url=cdp_url),
        use_vision=True,  # Enable vision to help with PDF reading
        output_model_schema=OrganigramResults
    )
    
    try:
        print(f"🔍 Starting {university_name} Organigram Search...\n")
        history = await agent.run()  # Allow more steps for thorough search
        
        final_result = history.final_result()
        if final_result:
            print(final_result)
            return final_result
        else:
            print("No final result extracted. Check the agent's actions above.")
            return None
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await agent.close()
        print("\n✓ Browser closed")


async def main():
    """
    Main function for standalone execution.
    Example usage when running this file directly.
    """
    # Default university name for standalone execution
    university_name = "Harvard University"
    await find_university_organigram(university_name)


if __name__ == "__main__":
    asyncio.run(main())