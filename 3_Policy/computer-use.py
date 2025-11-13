"""
University AI Policy Finder
This script searches for official university policies and extracts AI-related content.
"""

from browser_use import Agent, ChatGoogle, BrowserSession
from dotenv import load_dotenv
from steel import Steel
import asyncio
import os

load_dotenv()


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
    1. Search Google for "{university_name} policy" OR "{university_name} official policy"
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
    
    STEP 4 - FINAL OUTPUT:
    Provide a structured summary with:
    
    📋 FOUND POLICIES:
    - Policy 1 Name: [title]
      URL: [full URL]
      Type: [PDF/webpage]
      Date: [if available]
      Department: [issuing unit]
    
    ⚠️ If NO official policies are found:
    - State clearly that no official AI policies were found
    - List what searches were attempted
    - Suggest the university may not have published AI-specific policies yet
    
    IMPORTANT INSTRUCTIONS:
    - Be thorough but verify URLs are from official university domains
    - If a PDF cannot be opened, note it and try alternative methods
    - Extract the EXACT text, do not paraphrase
    - Use extract action to get the quote from the document
    - Keep quotes in their original language

    !FINISH JOB AFTER 1 POLICY IS FOUND!

    """
    
    # Create and run agent
    agent = Agent(
        task=task,
        llm=llm,
        # browser_session=BrowserSession(cdp_url=cdp_url),
        use_vision=True,  # Enable vision to help with PDF reading
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