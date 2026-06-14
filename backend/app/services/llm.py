import json

from app.config import settings
from app.schemas.document import LLMOutput

from google import genai
from google.genai import types

# A clear set of instructions for the AI to understand its job.
# We are processing documents (like invoices, contracts, or general texts).
# This gives the model the 'rules' of what we want it to do.
SYSTEM_PROMPT = (
    "You are a professional document analyst and AI assistant. Your job is to read the provided text "
    "and extract key information into a structured format.\n"
    "Please analyze the document and provide:\n"
    "1. A concise summary of the document.\n"
    "2. The classification (e.g., 'Invoice', 'Contract', 'General', etc.).\n"
    "3. Your confidence score between 0.0 and 1.0 about the accuracy of your extraction.\n"
    "4. A list of important key points found in the document.\n"
    "5. Any potential risks or warnings to be aware of."
)

def _fallback_llm_output(text: str) -> LLMOutput:
    """
    This function is called if the AI fails or the API key is missing.
    It returns a safe, default structure (our Pydantic model) so our application doesn't crash.
    """
    # Grab just the first 200 characters of the text as a basic summary.
    snippet = text.strip().replace("\\n", " ")[:200]
    
    # We create an instance (an object) of the LLMOutput class/model.
    return LLMOutput(
        summary=snippet or "No content provided.",
        classification="Unknown",
        confidence=0.0,
        key_points=[],
        risks=[],
    )

def call_llm(text: str) -> LLMOutput:
    """
    Calls the Google Gemini API to analyze the document text.
    It asks the AI to return data that matches our LLMOutput schema.
    
    ⚠️  IMPORTANT: Google Gemini Free Tier Quotas
    =====================================
    Google limits FREE tier users to prevent abuse:
    - Requests Per Minute (RPM): About 15 requests per minute
    - Tokens Per Minute (TPM): About 1 million tokens per minute
    - Requests Per Day: Limited total per day
    
    When you hit these limits, you get a "429 RESOURCE_EXHAUSTED" error.
    This means: "Slow down! You're sending requests too fast!"
    
    ✅ Solution:
    1. Wait 60 seconds and try again
    2. Check your quota: https://ai.dev/rate-limit
    3. Upgrade to a PAID plan for higher limits
    4. Our app has a FALLBACK function that returns safe data when Gemini is unavailable
    """
    # Check if the API key is provided in the configuration (.env file)
    # The 'settings' object automatically loads variables from our .env file.
    if not settings.gemini_api_key:
        print("Warning: No Gemini API key provided. Using fallback.")
        # If we don't have a key, we call our fallback function instead of crashing.
        return _fallback_llm_output(text)

    try:
        # 1. Initialize the Gemini client using the API key from our settings.
        # This is an object instantiation. We create a 'Client' object that knows how to securely talk to Google.
        client = genai.Client(api_key=settings.gemini_api_key)
        
        # 2. Tell the AI how to format its response. 
        # We enforce that the response must be JSON, and we give it our Pydantic model's JSON schema!
        # This is essentially the blueprint of what fields we expect.
        schema = LLMOutput.model_json_schema()
        # The 'title' field is sometimes added by Pydantic but not supported by Google's SDK.
        if "title" in schema:
            del schema["title"]

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2, # Low temperature = less creative, more precise and factual
            response_mime_type="application/json",
            response_schema=schema
        )

        # 3. Call the Gemini model. We use the model specified in our settings (e.g. "gemini-2.5-flash").
        # This is a function/method call! We are asking the client to 'do something' and wait for the result.
        response = client.models.generate_content(
            model=settings.llm_model, 
            contents=text,
            config=config
        )
        
        # 4. Grab the text response and convert the JSON string into a Python dictionary.
        # json.loads means 'load string'. It turns the raw JSON text into a usable dictionary.
        raw_json = response.text
        parsed_data = json.loads(raw_json)
        
        # 5. Return the validated Pydantic model. 
        # The '**' unwraps the dictionary and passes its key-value pairs as arguments to the LLMOutput model!
        # This creates a new instance (object) of LLMOutput.
        return LLMOutput(**parsed_data)
        
    except Exception as e:
        # Catch any errors (like network failures or bad data) so the app doesn't crash.
        error_str = str(e)
        
        # Check if the error is a 429 (quota exceeded / rate limit)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            # This means: "You sent too many requests to Google!" or "Your free tier quota is used up!"
            # On the free tier, Google Gemini has limits:
            # - Only a few requests per minute
            # - Only a limited number of tokens (words) per day
            # Solution: Wait 60 seconds, then try again. Or upgrade to a paid plan.
            print(f"API Quota Exceeded (429 Error): You've hit Google's free tier limits.")
            print(f"Please wait 60 seconds before trying again, or check your API quota at https://ai.dev/rate-limit")
        else:
            print(f"Error calling Gemini API: {e}")
        
        # We call the fallback function to return safe default values so users still see something.
        return _fallback_llm_output(text)
