"""
University AI Policy Finder
This script searches for official university policies and extracts AI-related content.
"""

from browser_use import Agent, ChatGoogle, BrowserSession, Browser
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
    
    # print("Creating Steel session...")
    # session = client.sessions.create()
    # print(f"Session created at {session.session_viewer_url}")
    # cdp_url = f"wss://connect.steel.dev?apiKey={os.getenv('STEEL_API_KEY')}&sessionId={session.id}"
    
    session = Browser(
        executable_path="C:\\Users\\hadiw\\AppData\\Local\\ms-playwright\\chromium-1187\\chrome-win\\chrome.exe",
        user_data_dir="C:\\Users\\hadiw\\AppData\\Local\\Chromium\\User Data",
        profile_directory="Default"
    )

    # Initialize the LLM
    llm = ChatGoogle(model="gemini-flash-latest")
    
    # Comprehensive task prompt - dynamically generated based on university name
    task = f"""
    You will finish my netacad course in this url: 
    https://www.netacad.com/launch?id=9cbb116d-63d3-4254-a5f4-e579f3418ffb&tab=curriculum&view=96e63799-c720-527b-9008-056d3e0871e3

    To get 100% completion you MUST do: 
    1. Make sure all subtopics are marked as completed with green check marks.
    2. If there are quizzes, you MUST answer all questions correctly.
    3. Scroll through all the content to ensure it is marked as read.
    4. If there are any interactive activities, you MUST complete them.
    5. If there are any videos, you SKIP them to the end to make sure they are marked as watched.
    6. Finally, ensure that the course status shows 100% complete before exiting.

    IMPORTANT: You MUST follow all the steps to ensure full completion of the course.
    """
    
    # Create and run agent
    agent = Agent(
        task=task,
        llm=llm,
        # browser_session=BrowserSession(cdp_url=cdp_url),
        browser=session,
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