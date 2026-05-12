import google.generativeai as genai
import os
import sys

sys.path.append('/tmp/pip_libs')

API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

print("Available models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
