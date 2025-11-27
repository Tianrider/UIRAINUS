"""
University AI Policy Finder
This script searches for official university policies and extracts AI-related content.
"""

from browser_use import Agent, ChatGoogle, BrowserSession
from dotenv import load_dotenv
from steel import Steel
from pydantic import BaseModel
import asyncio
import os

load_dotenv()

class PolicyDocument(BaseModel):
    university: str
    policy_title: str
    url: str
    document_type: str
    publishing_date: str
    department: str

class PolicyResults(BaseModel):
    results: list[PolicyDocument]


async def find_university_policy(university_name: str):
    """
    Search for official policy documents from a specified university.
    
    Args:
        university_name (str): The name of the university to search policies for
        
    Returns:
        str: The final result containing found policies or None if no results
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
    Find all official policy documents from {university_name}:
    
    STEP 1 - SEARCH FOR OFFICIAL POLICIES:
    1. Search Google for "{university_name} ["Policy" from where the university is based native language]" For example: "Policy" for english speaking university, or "Aturan" for Indonesian etc.
    2. Look for official university domains (e.g., *.edu, *.ac.id, or other official institutional domains)
    3. IMPORTANT: Only consider documents from official university domains to ensure legitimacy
    
    STEP 2 - VERIFY LEGITIMACY:
    - Check that the URL is from the official university domain
    - Verify it's from an official university department or administrative unit
    - Look for policy documents, regulations, or official announcements
    - Acceptable document types: PDF, official web pages with policy content
    
    STEP 3 - COLLECT POLICY FILES:
    - Create a list of all policy document URLs found
    - For each document, note:
      * Document title
      * Full URL
      * Document type (PDF, webpage, etc.)
      * Publishing date if available
      * Department/unit that published it
    
    STEP 4 - FINAL OUTPUT (CRITICAL - MUST BE VALID JSON):
    You MUST return ONLY a valid JSON array. No additional text, explanations, or formatting.
    
    If policy document(s) found, return:
    [
      {{
        "university": "{university_name}",
        "policy_title": "[exact title of policy document]",
        "url": "[full URL of the policy document]",
        "document_type": "[PDF/webpage/etc]",
        "publishing_date": "[date if available, otherwise 'Not specified']",
        "department": "[issuing department/unit, otherwise 'Not specified']"
      }}
    ]
    
    If NO official policies are found, return:
    []
    
    IMPORTANT INSTRUCTIONS:
    - Return ONLY valid JSON - no markdown, no explanations, no additional text
    - If you find multiple policy documents, include all in the array
    - Be thorough but verify URLs are from official university domains
    - If a PDF cannot be opened, note it and try alternative methods
    - Extract the EXACT text, do not paraphrase
    - Use extract action to get the quote from the document
    - Keep quotes in their original language
    - The response must be parseable by json.loads()
    """
    
    # Create and run agent
    agent = Agent(
        task=task,
        llm=llm,
        # browser_session=BrowserSession(cdp_url=cdp_url),
        use_vision=True,  # Enable vision to help with PDF reading
        output_model_schema=PolicyResults,
        browser={"headless": True}
    )
    
    try:
        print(f"🔍 Starting {university_name} AI Policy Search...\n")
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
    await find_university_policy(university_name)


if __name__ == "__main__":
    asyncio.run(main())