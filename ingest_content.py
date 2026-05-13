import os
import json
import sys
import re
from pathlib import Path

# Add temporary libs to sys.path
sys.path.append('/tmp/pip_libs')

try:
    from pypdf import PdfReader
    import google.generativeai as genai
except ImportError as e:
    print(f"Note: Some dependencies are missing ({e}). AI analysis and PDF reading may be limited.")
    PdfReader = None
    genai = None

# API KEY - User should set this in environment
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment. Script will only extract text without AI analysis.")

def extract_text_from_pdf(pdf_path):
    print(f"Extracting text from {pdf_path}...")
    if PdfReader is None:
        print(f"Error: pypdf is not installed. Cannot read {pdf_path}")
        return ""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def generate_mock_content(file_info):
    print(f"Generating mock content for {file_info['book']}...")
    return {
      "book": file_info['book'],
      "tests": [
        {
          "test_number": 1,
          "reading": [
            { "passage_number": 1, "title": "The Rise of Silicon Valley", "content": "Sample content about technology..." },
            { "passage_number": 2, "title": "Marine Biology in the Pacific", "content": "Sample content about whales..." }
          ],
          "listening": [
            { "section_number": 1, "transcript": "Man: Hello, I'd like to book a flight. Woman: Of course..." }
          ],
          "writing": [
            { "task_number": 1, "prompt": "Describe the graph showing carbon emissions." },
            { "task_number": 2, "prompt": "Is social media good for teenagers? Discuss." }
          ]
        }
      ]
    }

def identify_content_with_ai(text, file_info, model=None):
    if not API_KEY or model is None:
        return generate_mock_content(file_info)

    print(f"Analyzing content for {file_info['book']} with Gemini...")
    
    # Process the first 30k characters to identify the structure
    sample_text = text[:30000]
    
    prompt = f"""
    You are an expert IELTS content extractor. Analyze the following text extracted from {file_info['book']}.
    Extract the following into a structured JSON format:
    1. Reading Passages: Titles and full content for 3 passages.
    2. Listening Transcripts: Full transcripts for 4 sections.
    3. Writing Tasks: Task 1 and Task 2 prompts.
    
    Text snippet:
    {sample_text}
    
    Return ONLY valid JSON in this format:
    {{
      "book": "...",
      "tests": [
        {{
          "test_number": 1,
          "reading": [{{ "passage_number": 1, "title": "...", "content": "..." }}],
          "listening": [{{ "section_number": 1, "transcript": "..." }}],
          "writing": [{{ "task_number": 1, "prompt": "..." }}]
        }}
      ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # Attempt to find JSON in markdown or plain text
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"error": "No JSON found in response"}
    except Exception as e:
        print(f"AI Analysis failed: {e}")
        return generate_mock_content(file_info)

def main(base_dir=None, data_dir=None, model=None):
    if base_dir is None:
        base_dir = "/Users/seungwonlee/EnglishPython"
    if data_dir is None:
        data_dir = os.path.join(base_dir, "data")
        
    os.makedirs(data_dir, exist_ok=True)
    
    all_content = []
    
    # Iterate through Cambridge IELTS 01 - 15
    for i in range(1, 16):
        book_json_path = os.path.join(data_dir, f"book_{i:02d}.json")
        
        # Check if already processed
        if os.path.exists(book_json_path):
            print(f"Skipping Cambridge IELTS {i:02d} - already processed.")
            with open(book_json_path, "r") as f:
                content = json.load(f)
                all_content.append(content)
            continue

        book_dir = os.path.join(base_dir, f"Cambridge IELTS {i:02d}")
        if not os.path.exists(book_dir):
            continue
            
        pdfs = sorted([f for f in os.listdir(book_dir) if f.endswith(".pdf")])
        if not pdfs:
            continue
            
        combined_text = ""
        for pdf_name in pdfs:
            pdf_path = os.path.join(book_dir, pdf_name)
            combined_text += extract_text_from_pdf(pdf_path) + "\n"
            
        if combined_text.strip():
            file_info = {"book": f"Cambridge IELTS {i:02d}", "name": "Combined PDF"}
            content = identify_content_with_ai(combined_text, file_info, model=model)
            all_content.append(content)
            
            # Save intermediate result
            with open(book_json_path, "w") as f:
                json.dump(content, f, indent=2)
                    
    # Final combined output (re-scan data directory to ensure all existing books are included)
    all_content = []
    for i in range(1, 16):
        book_json_path = os.path.join(data_dir, f"book_{i:02d}.json")
        if os.path.exists(book_json_path):
            with open(book_json_path, "r") as f:
                all_content.append(json.load(f))

    with open(os.path.join(data_dir, "lessons.json"), "w") as f:
        json.dump(all_content, f, indent=2)
    
    print(f"Ingestion complete. Combined {len(all_content)} books into lessons.json.")

if __name__ == "__main__":
    if genai:
        genai.configure(api_key=API_KEY)
        # Use a global model if available
        model = genai.GenerativeModel('gemini-flash-latest')
    else:
        model = None
    main(model=model)
