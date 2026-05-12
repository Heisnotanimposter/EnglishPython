import os
import re
import json
import difflib
from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS
import google.generativeai as genai
import sys
from collections import Counter
from keyword_extractor import IELTSKeywordExtractor
from search_engine import IELTSProjectSearch

# Add temporary libs to sys.path
sys.path.append('/tmp/pip_libs')

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-flash-latest')
else:
    model = None

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize keyword extractor and search engine
keyword_extractor = IELTSKeywordExtractor()
search_engine = IELTSProjectSearch()

def get_pdf_files():
    pdf_files = []
    # Walk through the directory to find PDF files
    # We are looking for 'Cambridge IELTS *' and 'TOEFL' directories
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.lower().endswith('.pdf'):
                # Get relative path
                rel_path = os.path.relpath(os.path.join(root, file), BASE_DIR)
                # Filter to only include relevant directories
                if 'Cambridge IELTS' in rel_path or 'TOEFL' in rel_path:
                    pdf_files.append({
                        'name': file,
                        'path': rel_path,
                        'category': 'IELTS' if 'Cambridge' in rel_path else 'TOEFL'
                    })
    return pdf_files

def get_audio_files():
    audio_files = []
    
    # Regex patterns for parsing filenames
    pattern_section = re.compile(r'Test\s*(\d+)[_\s]+Section\s*(\d+)', re.IGNORECASE)
    pattern_test = re.compile(r'Test\s*(\d+)', re.IGNORECASE)
    pattern_track = re.compile(r'Track\s*(\d+)', re.IGNORECASE)

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.lower().endswith('.mp3'):
                rel_path = os.path.relpath(os.path.join(root, file), BASE_DIR)
                if 'Cambridge IELTS' in rel_path:
                    book_name = "Cambridge IELTS Unknown"
                    test_num = "Unknown"
                    section_num = "All"
                    
                    # Extract book from path
                    parts = rel_path.split(os.sep)
                    for part in parts:
                        if 'Cambridge IELTS' in part:
                            book_name = part
                            break
                    
                    # Try to extract from filename
                    match_section = pattern_section.search(file)
                    match_test = pattern_test.search(file)
                    match_track = pattern_track.search(file)
                    
                    if match_section:
                        test_num = match_section.group(1)
                        section_num = match_section.group(2)
                    elif match_test:
                        test_num = match_test.group(1)
                        if match_track:
                             section_num = match_track.group(1)
                    elif match_track:
                        section_num = match_track.group(1)
                    
                    audio_files.append({
                        'name': file,
                        'path': rel_path,
                        'book': book_name,
                        'test': test_num,
                        'section': section_num
                    })
    
    # Sort files: Book -> Test -> Section
    def sort_key(x):
        try:
            # Extract numbers for sorting
            b_match = re.search(r'(\d+)', x['book'])
            b = int(b_match.group(1)) if b_match else 0
            t = int(x['test']) if x['test'].isdigit() else 0
            s = int(x['section']) if x['section'].isdigit() else 0
            return (b, t, s)
        except:
            return (0, 0, 0)

    audio_files.sort(key=sort_key)
    print(f"Found {len(audio_files)} audio files")
    return audio_files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/materials')
def list_materials():
    materials = get_pdf_files()
    print(f"Found {len(materials)} PDF materials")
    return jsonify(materials)

@app.route('/api/audio')
def list_audio():
    audio = get_audio_files()
    return jsonify(audio)

@app.route('/pdfs/<path:filename>')
def serve_pdf(filename):
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return "Invalid path", 400
    
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "File not found", 404

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    if '..' in filename or filename.startswith('/'):
        return "Invalid path", 400
    
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "File not found", 404


@app.route('/api/dictation/compare', methods=['POST'])
def compare_transcripts():
    """Compare user transcription with reference transcript and categorize errors"""
    try:
        data = request.get_json()
        user_text = data.get('user_text', '').strip()
        reference_text = data.get('reference_text', '').strip()
        
        if not user_text or not reference_text:
            return jsonify({'error': 'Both user_text and reference_text are required'}), 400
        
        # Normalize texts for comparison (lowercase, remove extra spaces)
        user_normalized = normalize_text(user_text)
        reference_normalized = normalize_text(reference_text)
        
        # Generate diff
        user_lines = user_normalized.split('\n')
        reference_lines = reference_normalized.split('\n')
        
        # Use difflib for word-level comparison
        user_words = user_normalized.split()
        reference_words = reference_normalized.split()
        
        # Create HTML with error highlighting
        user_html, reference_html, errors = create_comparison_html(
            user_text, reference_text, user_words, reference_words
        )
        
        return jsonify({
            'user_html': user_html,
            'reference_html': reference_html,
            'errors': errors,
            'accuracy': calculate_accuracy(user_words, reference_words),
            'total_words_user': len(user_words),
            'total_words_reference': len(reference_words)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def normalize_text(text):
    """Normalize text for comparison"""
    # Lowercase, remove extra whitespace, preserve sentence structure
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

def create_comparison_html(user_text, reference_text, user_words, reference_words):
    """Create HTML with highlighted differences and categorize errors"""
    errors = []
    
    # Use SequenceMatcher for word-by-word comparison
    matcher = difflib.SequenceMatcher(None, user_words, reference_words)
    
    user_html_parts = []
    reference_html_parts = []
    user_pos = 0
    ref_pos = 0
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # Matching words
            user_segment = ' '.join(user_words[i1:i2])
            ref_segment = ' '.join(reference_words[j1:j2])
            user_html_parts.append(f'<span class="correct-word">{escape_html(user_segment)}</span>')
            reference_html_parts.append(f'<span class="correct-word">{escape_html(ref_segment)}</span>')
        elif tag == 'replace':
            # Different words
            user_segment = ' '.join(user_words[i1:i2])
            ref_segment = ' '.join(reference_words[j1:j2])
            
            error_type = categorize_error(user_segment, ref_segment)
            errors.append({
                'user_word': user_segment,
                'correct_word': ref_segment,
                'category': error_type,
                'position': user_pos
            })
            
            error_class = f'{error_type}-error'
            user_html_parts.append(f'<span class="error-word {error_class}">{escape_html(user_segment)}</span>')
            reference_html_parts.append(f'<span class="correct-word">{escape_html(ref_segment)}</span>')
        elif tag == 'delete':
            # Words in user text but not in reference
            user_segment = ' '.join(user_words[i1:i2])
            errors.append({
                'user_word': user_segment,
                'correct_word': '',
                'category': 'listening',
                'position': user_pos
            })
            user_html_parts.append(f'<span class="error-word listening-error">{escape_html(user_segment)}</span>')
        elif tag == 'insert':
            # Words in reference but not in user text
            ref_segment = ' '.join(reference_words[j1:j2])
            errors.append({
                'user_word': '',
                'correct_word': ref_segment,
                'category': 'listening',
                'position': user_pos
            })
            reference_html_parts.append(f'<span class="correct-word">{escape_html(ref_segment)}</span>')
        
        user_pos += (i2 - i1)
        ref_pos += (j2 - j1)
    
    # Also check for common grammatical errors
    additional_errors = check_grammar_errors(user_text, reference_text)
    errors.extend(additional_errors)
    
    user_html = ' '.join(user_html_parts)
    reference_html = ' '.join(reference_html_parts)
    
    # Add line breaks for readability
    user_html = user_html.replace('. ', '.<br>')
    reference_html = reference_html.replace('. ', '.<br>')
    
    return user_html, reference_html, errors

def categorize_error(user_word, correct_word):
    """Categorize error type"""
    user_lower = user_word.lower().strip()
    correct_lower = correct_word.lower().strip()
    
    # Spelling errors (similar words, typos)
    similarity = difflib.SequenceMatcher(None, user_lower, correct_lower).ratio()
    if similarity > 0.7 and similarity < 1.0:
        return 'spelling'
    
    # Common homophones
    homophones = {
        'their': 'there', 'they\'re': 'there', 'there': 'their',
        'its': 'it\'s', 'it\'s': 'its',
        'your': 'you\'re', 'you\'re': 'your',
        'too': 'to', 'to': 'too',
        'hear': 'here', 'here': 'hear'
    }
    if user_lower in homophones and homophones[user_lower] == correct_lower:
        return 'spelling'
    
    # Grammar errors (articles, prepositions)
    articles = ['a', 'an', 'the']
    prepositions = ['in', 'on', 'at', 'by', 'for', 'with', 'from', 'to']
    
    if (user_lower in articles or user_lower in prepositions) or \
       (correct_lower in articles or correct_lower in prepositions):
        return 'grammar'
    
    # Vocabulary errors (completely different words)
    if similarity < 0.5:
        return 'vocabulary'
    
    # Default to listening if unclear
    return 'listening'

def check_grammar_errors(user_text, reference_text):
    """Check for common grammatical errors"""
    errors = []
    
    # Check for missing articles
    user_sentences = re.split(r'[.!?]', user_text)
    ref_sentences = re.split(r'[.!?]', reference_text)
    
    # Simple checks for common patterns
    patterns_to_check = [
        (r'\b(a|an|the)\s+(\w+)', 'article'),
        (r'\b(in|on|at|by|for|with)\s+(\w+)', 'preposition'),
    ]
    
    # This is a simplified check - in production, use a proper grammar checker
    return errors

def calculate_accuracy(user_words, reference_words):
    """Calculate accuracy percentage"""
    if not reference_words:
        return 0.0
    
    matcher = difflib.SequenceMatcher(None, user_words, reference_words)
    matches = sum(i2 - i1 for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag == 'equal')
    
    return round((matches / len(reference_words)) * 100, 2)

def escape_html(text):
    """Escape HTML special characters"""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))

@app.route('/api/keywords/extract', methods=['POST'])
def extract_keywords():
    """Extract keywords from an IELTS question"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question text is required'}), 400
        
        result = keyword_extractor.extract_keywords(question)
        
        return jsonify({
            'question': question,
            'keywords': result['keywords'],
            'filtered_words': result['filtered_words'],
            'synonyms': result['synonyms'],
            'summary': keyword_extractor.get_keyword_summary(question)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords/analyze', methods=['POST'])
def analyze_question_text():
    """Analyze question and text for keyword matches"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        text = data.get('text', '').strip()
        
        if not question or not text:
            return jsonify({'error': 'Both question and text are required'}), 400
        
        analysis = keyword_extractor.analyze_question_text_match(question, text)
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords/matches', methods=['POST'])
def find_keyword_matches():
    """Find matches for specific keywords in text"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', [])
        text = data.get('text', '').strip()
        
        if not keywords or not text:
            return jsonify({'error': 'Both keywords and text are required'}), 400
        
        matches = keyword_extractor.find_matches_in_text(keywords, text)
        
        return jsonify({
            'keywords': keywords,
            'text': text,
            'matches': matches,
            'total_matches': sum(len(m) for m in matches.values())
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords/synonyms/<word>')
def get_synonyms(word):
    """Get synonyms for a specific word"""
    try:
        synonyms = keyword_extractor._get_synonyms(word.lower())
        return jsonify({
            'word': word,
            'synonyms': synonyms
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lessons')
def get_lessons():
    """Serve the ingested lesson data"""
    data_path = os.path.join(BASE_DIR, 'data', 'lessons.json')
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/api/vocabulary')
def get_vocabulary():
    """Serve the analyzed vocabulary frequency data"""
    data_path = os.path.join(BASE_DIR, 'data', 'vocabulary.json')
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/api/analyze/pdf', methods=['POST'])
def analyze_pdf():
    """Extract text from uploaded PDF and analyze keyword frequencies"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are supported'}), 400

    if PdfReader is None:
        return jsonify({'error': 'PDF processing library (pypdf) not available'}), 500

    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        if not text.strip():
            return jsonify({'error': 'Could not extract text from PDF'}), 400

        # Extract keyword frequencies
        clean_text = keyword_extractor._clean_text(text)
        words = clean_text.lower().split()
        
        word_counts = Counter()
        for word in words:
            if (word not in keyword_extractor.filler_words and 
                len(word) > 2 and 
                not word.isdigit()):
                word_counts[word] += 1
        
        total_content_words = sum(word_counts.values())
        
        results = []
        for word, count in word_counts.most_common(100):
            ratio = (count / total_content_words) * 100 if total_content_words > 0 else 0
            results.append({
                'word': word,
                'count': count,
                'ratio': round(ratio, 2),
                'synonyms': keyword_extractor._get_synonyms(word)[:3]
            })
            
        return jsonify({
            'filename': file.filename,
            'total_words': len(words),
            'unique_keywords': len(word_counts),
            'frequencies': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluate/speaking', methods=['POST'])
def evaluate_speaking():
    """Evaluate speaking attempt using AI or mock feedback"""
    # Note: In a production app, we would use Speech-to-Text here.
    # For this simulation, we'll assume a transcript is provided or mock it.
    transcript = request.form.get('transcript', '')
    
    if not model:
        import random
        feedback_options = [
            "Good fluency, but watch your pronunciation of 'th' sounds.",
            "You used a nice range of vocabulary. Try to speak a bit faster.",
            "Great work! Your grammar was mostly correct.",
            "Try to expand more on your answers to reach a higher band score."
        ]
        return jsonify({
            "score": random.choice([5.5, 6.0, 6.5, 7.0]),
            "feedback": random.choice(feedback_options)
        })
    
    prompt = f"""
    Evaluate the following IELTS speaking transcript. Provide a band score (0-9) and constructive feedback.
    Focus on:
    1. Fluency and Coherence
    2. Lexical Resource
    3. Grammatical Range and Accuracy
    4. Pronunciation (based on transcript clues like filler words)
    
    Transcript: "{transcript if transcript else 'The user spoke for 30 seconds but no transcript was generated. Evaluate based on typical Band 6 performance.'}"
    
    Return ONLY JSON:
    {{
      "score": 6.5,
      "feedback": "..."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return jsonify(json.loads(match.group()))
        return jsonify({"score": 6.0, "feedback": "AI analysis completed but format was unexpected."})
    except Exception as e:
        return jsonify({"score": 6.0, "feedback": f"AI error: {str(e)}"})

@app.route('/api/search')
def search():
    """Unified search across Cambridge and Guardian content"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    results = search_engine.search(query)
    return jsonify(results)

@app.route('/api/guardian/list')
def list_guardian_articles():
    """List all ingested Guardian articles"""
    path = os.path.join(BASE_DIR, 'data', 'guardian_articles.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/api/generate/questions', methods=['POST'])
def generate_questions():
    """Generate IELTS-style questions from any text using Gemini"""
    if not model:
        return jsonify({'error': 'Gemini API not configured'}), 503
        
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        title = data.get('title', 'Article')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
            
        prompt = f"""
        You are an expert IELTS examiner. Generate 4 high-quality reading comprehension questions (Multiple Choice) for the following article.
        
        Article Title: {title}
        Content: {content[:4000]} 

        Return ONLY JSON in this format:
        {{
          "title": "{title}",
          "questions": [
            {{
              "id": 1,
              "question": "...",
              "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
              "answer": "A"
            }}
          ]
        }}
        """
        
        response = model.generate_content(prompt)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return jsonify(json.loads(match.group()))
        return jsonify({'error': 'Failed to parse AI response'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluate/answer', methods=['POST'])
def evaluate_answer():
    """Evaluate a user's answer and provide reasoning"""
    if not model:
        return jsonify({'error': 'Gemini API not configured'}), 503
        
    try:
        data = request.get_json()
        question = data.get('question', '')
        user_answer = data.get('user_answer', '')
        correct_answer = data.get('correct_answer', '')
        context = data.get('context', '')
        
        prompt = f"""
        Evaluate this IELTS reading answer.
        Question: {question}
        User's Answer: {user_answer}
        Correct Answer: {correct_answer}
        Context snippet: {context}
        
        Explain WHY the correct answer is {correct_answer} and if the user's reasoning was correct.
        
        Return ONLY JSON:
        {{
          "is_correct": {str(user_answer == correct_answer).lower()},
          "explanation": "..."
        }}
        """
        
        response = model.generate_content(prompt)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return jsonify(json.loads(match.group()))
        return jsonify({'explanation': f"The correct answer is {correct_answer}."})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluate/speaking', methods=['POST'])
def evaluate_speaking():
    """Evaluate a user's speaking audio using Gemini."""
    if not model:
        return jsonify({'error': 'Gemini API not configured'}), 503
        
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
        
    try:
        audio_file = request.files['audio']
        audio_data = audio_file.read()
        
        prompt = """
        You are an expert IELTS Speaking examiner. Evaluate the provided audio response for a Part 2 speaking task.
        
        Criteria:
        1. Fluency and Coherence (Band 0-9)
        2. Lexical Resource (Band 0-9)
        3. Grammatical Range and Accuracy (Band 0-9)
        4. Pronunciation (Band 0-9)
        
        Provide an overall band score and detailed feedback on strengths and areas for improvement.
        
        Return ONLY JSON:
        {
          "overall_score": 7.0,
          "scores": {
            "fluency": "7.0",
            "lexical": "7.5",
            "grammar": "6.5",
            "pronunciation": "7.0"
          },
          "analysis": {
            "strengths": "...",
            "improvements": "..."
          }
        }
        """
        
        # Using multimodal capabilities of Gemini 1.5
        response = model.generate_content([
            prompt,
            {
                "mime_type": "audio/wav",
                "data": audio_data
            }
        ])
        
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return jsonify(json.loads(match.group()))
        return jsonify({'error': 'Failed to parse AI response'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
