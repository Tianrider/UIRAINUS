from google import genai
import json
import sys

client = genai.Client(
    api_key="AIzaSyCG2Pf3dZb43kUhHV5OH91MCQgFk-T07MI"
)

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config={
            "system_instruction": "Mulai sekarang anda adalah agenticAI yang memiliki kemampuan untuk melakukan API call ke Weather Data. OUtput anda harus dalam format JSON:   {  text: string, isCallWeatherApi: boolean, isFinalOutput:  boolean }"
        },
        contents="Apa cuaca di depok sekarang?",
    )

    print(response.text)
except Exception as e:
    print(f"⚠️ API Error: {type(e).__name__} - {str(e)}")
    print(json.dumps({
        "text": f"Error: Unable to get weather data due to API error - {str(e)}",
        "isCallWeatherApi": False,
        "isFinalOutput": True,
        "error": str(e),
        "error_type": type(e).__name__
    }))
    sys.exit(0)

# process response text - strip markdown code blocks if present
try:
    response_text = response.text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]  # Remove ```json
    if response_text.startswith("```"):
        response_text = response_text[3:]  # Remove ```
    if response_text.endswith("```"):
        response_text = response_text[:-3]  # Remove closing ```
    response_text = response_text.strip()

    response_json = json.loads(response_text)

    weather_api_result = None

    if response_json.get("isFinalOutput"): 
        print(response_json.get("text"))
        sys.exit(0)

    if response_json.get("isCallWeatherApi"):
        # Call the weather API
        weather_api_result = "{location: Depok; Weather: Rainy}"
        print(weather_api_result)
    else:
        print(response_json.get("text"))

    response2 = client.models.generate_content(
        model="gemini-2.5-flash",
        config={
            "system_instruction": "Mulai sekarang anda adalah agenticAI yang memiliki kemampuan untuk melakukan API call ke Weather Data. OUtput anda harus dalam format JSON:   {  text: string, isCallWeatherApi: boolean, isFinalOutput:  boolean }"
        },
        contents=(
            "Previous conversation:\n"
            "User: Apa cuaca di depok sekarang?\n"
            f"Assistant (initial model response): {response.text}\n\n"
            f"Weather API result: {weather_api_result}\n\n"
            "Based on the previous conversation and the weather API result, provide the final answer to the user. "
            "Return only a JSON object in the format: { text: string, isCallWeatherApi: boolean, isFinalOutput: boolean }"
        ),
    )

    print(response2.text)

    # Process second response
    response2_text = response2.text.strip()
    if response2_text.startswith("```json"):
        response2_text = response2_text[7:]
    if response2_text.startswith("```"):
        response2_text = response2_text[3:]
    if response2_text.endswith("```"):
        response2_text = response2_text[:-3]
    response2_text = response2_text.strip()

    response2_json = json.loads(response2_text)
    print("\nFinal Answer:")
    print(response2_json.get("text"))
    
except Exception as e:
    print(f"\n⚠️ Error during processing: {type(e).__name__} - {str(e)}")
    print(json.dumps({
        "text": f"Error: Processing failed - {str(e)}",
        "isCallWeatherApi": False,
        "isFinalOutput": True,
        "error": str(e),
        "error_type": type(e).__name__
    }))
    sys.exit(0)
