import os
import re
import difflib
from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS
from keyword_extractor import IELTSKeywordExtractor

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize keyword extractor
keyword_extractor = IELTSKeywordExtractor()

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
    import re
    
    # Regex patterns for parsing filenames
    # Pattern 1: IELTS 10 Test 1 Section 1.mp3
    pattern_section = re.compile(r'IELTS\s+(\d+)\s+Test\s+(\d+)\s+Section\s+(\d+)', re.IGNORECASE)
    # Pattern 2: ielts 1 Test 1.mp3 (Assuming generic fallback if section not found)
    pattern_test = re.compile(r'IELTS\s+(\d+)\s+Test\s+(\d+)', re.IGNORECASE)

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.lower().endswith('.mp3'):
                rel_path = os.path.relpath(os.path.join(root, file), BASE_DIR)
                if 'Cambridge IELTS' in rel_path:
                    # Default values
                    book_num = "Unknown"
                    test_num = "Unknown"
                    section_num = "All" # Default to All if not specified
                    
                    # Try to extract from filename first
                    match_section = pattern_section.search(file)
                    match_test = pattern_test.search(file)
                    
                    if match_section:
                        book_num = match_section.group(1)
                        test_num = match_section.group(2)
                        section_num = match_section.group(3)
                    elif match_test:
                        book_num = match_test.group(1)
                        test_num = match_test.group(2)
                        # section_num remains "All"
                    
                    # If regex failed on filename, try to guess from path (parent dirs)
                    if book_num == "Unknown":
                        parts = rel_path.split(os.sep)
                        for part in parts:
                            if 'Cambridge IELTS' in part:
                                # Extract number from "Cambridge IELTS 10"
                                m = re.search(r'(\d+)', part)
                                if m:
                                    book_num = m.group(1)
                                break
                    
                    audio_files.append({
                        'name': file,
                        'path': rel_path,
                        'book': f"Cambridge IELTS {book_num}",
                        'test': test_num,
                        'section': section_num
                    })
    
    # Sort files: Book -> Test -> Section
    def sort_key(x):
        try:
            b = int(x['book'].split()[-1]) if x['book'].split()[-1].isdigit() else 0
            t = int(x['test']) if x['test'].isdigit() else 0
            s = int(x['section']) if x['section'].isdigit() else 0
            return (b, t, s)
        except:
            return (0, 0, 0)

    audio_files.sort(key=sort_key)
    return audio_files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/materials')
def list_materials():
    materials = get_pdf_files()
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

@app.route('/api/evaluate/speaking', methods=['POST'])
def evaluate_speaking():
    # Placeholder for speaking evaluation
    # In a real app, this would process the audio file
    # For now, we return a mock score
    import random
    
    # Check if file is present
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
        
    score = round(random.uniform(5.0, 9.0), 1)
    feedback = [
        "Good pronunciation.",
        "Try to vary your intonation.",
        "Excellent vocabulary usage.",
        "Pacing was a bit fast.",
        "Clear and concise."
    ]
    
    return jsonify({
        'score': score,
        'feedback': random.choice(feedback)
    })

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
