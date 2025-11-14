"""
University AI Models and Dataset Finder
This script uses Google Dork to search GitHub for AI models and datasets related to a specified university.
"""

from browser_use import Agent, ChatGoogle, BrowserSession
from dotenv import load_dotenv
from steel import Steel
import asyncio
import os

load_dotenv()


async def find_university_policy(university_name: str):
    """
    Use Google Dork to search GitHub for AI models and datasets related to a specified university.
    
    Args:
        university_name (str): The name of the university to search models and datasets for
        
    Returns:
        str: The final result containing found models and datasets or None if no results
    """
    # Initialize Steel client and session
    client = Steel(steel_api_key=os.getenv("STEEL_API_KEY"))
    
    print("Creating Steel session...")
    session = client.sessions.create()
    print(f"Session created at {session.session_viewer_url}")
    cdp_url = f"wss://connect.steel.dev?apiKey={os.getenv('STEEL_API_KEY')}&sessionId={session.id}"

    # Initialize the LLM
    llm = ChatGoogle(model="gemini-2.0-flash-lite")
    
    # Comprehensive task prompt - dynamically generated based on university name
    task = f"""
    Find AI models and datasets from GitHub related to {university_name} using Google Dork:
    
    STEP 1 - USE GOOGLE DORK TO SEARCH GITHUB:
    1. Go to Google (google.com) and use Google Dork syntax to search GitHub repositories
    2. Use these search queries (one at a time or combine):
       - site:github.com "{university_name}" "AI model"
       - site:github.com "{university_name}" dataset
       - site:github.com "{university_name}" "machine learning"
       - site:github.com "{university_name}" "deep learning"
       - site:github.com "{university_name}" checkpoint OR weights
       - site:github.com "{university_name}" model OR "neural network"
    3. Google will show GitHub repository links in the search results
    4. Scroll through Google search results to see multiple repositories at once
    
    STEP 2 - EXTRACT INFORMATION FROM GOOGLE SEARCH RESULTS (DO NOT OPEN EACH REPOSITORY):
    IMPORTANT: Extract information directly from Google search results page without clicking into individual repositories!
    For each GitHub repository link visible in Google search results, immediately collect:
    - Repository name and owner (from the Google result snippet or URL)
    - Full GitHub URL (from the Google search result link)
    - Repository description (shown in Google search snippet)
    - Any additional info visible in Google results (stars, language, etc.)
    
    STEP 3 - QUICK VERIFICATION FROM GOOGLE RESULTS:
    From the Google search results page, quickly identify GitHub repositories that:
    - Have descriptions mentioning "model", "dataset", "checkpoint", "weights", "data", "training data"
    - Are clearly related to {university_name} (check owner name, description, or repository name in URL)
    - Show indicators of containing models/datasets (keywords like "LLM", "NLP", "vision", "transformer", etc.)
    - Have GitHub URLs (github.com/username/repo-name format)
    
    STEP 4 - COLLECT MULTIPLE RESULTS AT ONCE:
    - Use the extract action to capture information from the entire Google search results page
    - Collect information for ALL relevant GitHub repositories visible on the first 2-3 pages of Google results
    - Do NOT click into individual repositories unless absolutely necessary for critical missing information
    - If repository description in Google results is sufficient, use that information directly
    - Extract GitHub URLs from Google results and note them for your final output
    
    STEP 5 - ONLY OPEN REPOSITORY IF NEEDED:
    Only open a GitHub repository page if:
    - The Google search result description is unclear or missing
    - You need to verify license information
    - You need to check for download links that aren't in the Google snippet
    - Limit opening to maximum 2-3 repositories total for additional details
    
    STEP 6 - IMMEDIATE OUTPUT FOR MATCHING REPOSITORIES:
    As soon as you find GitHub repositories that match {university_name} and contain models/datasets:
    - Immediately add them to your results list
    - Don't wait to open each one - use information from Google search results first
    - Build your results list progressively as you scroll through Google search results
    
    STEP 7 - FINAL OUTPUT:
    Provide a structured summary with:
    
    🤖 FOUND MODELS:
    - Model 1 Name: [repository name]
      Owner: [owner/org]
      URL: [GitHub URL]
      Type: [inferred from description: LLM, vision model, NLP model, etc.]
      Description: [from search results]
      Stars: [number]
      Last Updated: [date if available]
      Language: [if visible]
    
    📊 FOUND DATASETS:
    - Dataset 1 Name: [repository name]
      Owner: [owner/org]
      URL: [GitHub URL]
      Type: [inferred from description: text, image, multimodal, etc.]
      Description: [from search results]
      Stars: [number]
      Last Updated: [date if available]
      Language: [if visible]
    
    ⚠️ If NO models or datasets are found:
    - State clearly that no models or datasets were found
    - List what searches were attempted
    - Suggest alternative search terms
    
    CRITICAL EFFICIENCY INSTRUCTIONS:
    - DO NOT open each repository one by one - extract from Google search results page first!
    - Use Google Dork syntax (site:github.com) to efficiently search GitHub repositories
    - Use the Google search results page to collect information for multiple repositories simultaneously
    - Only open repository pages for 2-3 repositories maximum if you need additional details
    - Focus on repositories with clear descriptions in Google results that mention models/datasets
    - Extract information from the entire visible Google search results page at once using extract action
    - Build results progressively as you find matching repositories - don't wait until the end
    - If a repository clearly matches {university_name} from Google results, include it immediately
    - Try multiple Google Dork queries to get comprehensive results
    - IF YOU FOUND A CAPTCHA, SOLVE IT AND CONTINUE THE SEARCH

    !FINISH JOB AFTER COLLECTING INFORMATION FROM GOOGLE SEARCH RESULTS (aim for 5-10 repositories from Google search results pages)!

    """
    
    # Create and run agent
    agent = Agent(
        task=task,
        llm=llm,
        # browser_session=BrowserSession(cdp_url=cdp_url),
        use_vision=True,  # Enable vision to help with reading repository pages
    )
    
    try:
        print(f"🔍 Starting {university_name} Models and Datasets Search using Google Dork...\n")
        history = await agent.run(max_steps=1000)
        
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