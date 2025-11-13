from google import genai
from google.genai import types
from google.genai.types import Content, Part
import sys
import socket

def check_internet_connection():
    """Check if we can connect to the internet"""
    try:
        # Try to resolve Google's DNS
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def check_api_connection():
    """Check if we can resolve Gemini API hostname"""
    try:
        socket.gethostbyname("generativelanguage.googleapis.com")
        return True
    except socket.gaierror:
        return False

# Check connectivity before proceeding
print("Checking network connectivity...")
if not check_internet_connection():
    print("❌ ERROR: No internet connection detected!")
    print("   Please check your network connection and try again.")
    sys.exit(1)

if not check_api_connection():
    print("❌ ERROR: Cannot resolve Gemini API hostname!")
    print("   This might be due to:")
    print("   - DNS issues")
    print("   - Firewall/proxy blocking access")
    print("   - VPN interference")
    sys.exit(1)

print("✓ Network connectivity OK\n")

client = genai.Client(
    api_key="AIzaSyCG2Pf3dZb43kUhHV5OH91MCQgFk-T07MI"
)


# Specify predefined functions to exclude (optional)
excluded_functions = ["drag_and_drop"]

generate_content_config = genai.types.GenerateContentConfig(
    tools=[
        # 1. Computer Use tool with browser environment
        types.Tool(
            computer_use=types.ComputerUse(
                environment=types.Environment.ENVIRONMENT_BROWSER,
                # Optional: Exclude specific predefined functions
                excluded_predefined_functions=excluded_functions
                )
              ),
        # 2. Optional: Custom user-defined functions
        #types.Tool(
          # function_declarations=custom_functions
          #   )
          ],
  )

# Create the content with user message
contents=[
    Content(
        role="user",
        parts=[
            Part(text="Search for highly rated smart fridges with touchscreen, 2 doors, around 25 cu ft, priced below 4000 dollars on Google Shopping. Create a bulleted list of the 3 cheapest options in the format of name, description, price in an easy-to-read layout."),
        ],
    )
]

# Generate content with the configured settings
print("Sending request to Gemini API...")
print("Model: gemini-2.5-computer-use-preview-10-2025")
print("Task: Search for smart fridges on Google Shopping\n")

try:
    response = client.models.generate_content(
        model='gemini-2.5-computer-use-preview-10-2025',
        contents=contents,
        config=generate_content_config,
    )
    
    # Print the response output
    print("="*70)
    print("RESPONSE:")
    print("="*70)
    print(response)
    
except Exception as e:
    print(f"❌ ERROR: Failed to generate content")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    
    if "ConnectError" in str(type(e)):
        print("\n💡 TROUBLESHOOTING:")
        print("   1. Check your internet connection")
        print("   2. Try disabling VPN if active")
        print("   3. Check firewall settings")
        print("   4. Try using a different network")
    
    sys.exit(1)
