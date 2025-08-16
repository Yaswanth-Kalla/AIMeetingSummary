import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load env
load_dotenv()

# Configure Gemini with API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# A fake meeting transcript
transcript = """
Alice: We need to finalize the project timeline by Friday.
Bob: I'll update the design doc by tomorrow.
Charlie: I'll prepare the demo slides.
"""

# Custom instruction
instruction = "Summarize the key action items from this meeting."

# Initialize Gemini model (flash is faster/cheaper; pro is better for reasoning)
model = genai.GenerativeModel("gemini-1.5-flash")

# Send request
response = model.generate_content(
    f"{instruction}\n\nTranscript:\n{transcript}"
)

print("\n=== Meeting Summary ===")
print(response.text)
