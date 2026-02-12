import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from typing import List, Dict, Tuple, Set

class IELTSKeywordExtractor:
    """
    Just-the-Word extraction system for IELTS Cambridge books.
    Extracts essential content words (nouns, verbs, adjectives, adverbs) 
    from questions to match against synonyms in texts.
    """
    
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger')
        
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger_eng')
        except LookupError:
            nltk.download('averaged_perceptron_tagger_eng')
        
        # Content word tags (nouns, verbs, adjectives, adverbs)
        self.content_tags = {
            'NN', 'NNS', 'NNP', 'NNPS',  # Nouns
            'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ',  # Verbs
            'JJ', 'JJR', 'JJS',  # Adjectives
            'RB', 'RBR', 'RBS'  # Adverbs
        }
        
        # Filler words to ignore
        self.filler_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'by', 
            'for', 'with', 'from', 'to', 'of', 'as', 'is', 'are', 'was', 
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'shall', 'this', 'that', 'these', 'those', 'i', 'you', 
            'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # IELTS-specific synonyms database
        self.synonym_db = self._build_synonym_db()
    
    def _build_synonym_db(self) -> Dict[str, Set[str]]:
        """Build a comprehensive synonym database for IELTS vocabulary"""
        return {
            'majority': {'most', 'largest part', 'main portion', 'bulk', 'greater part'},
            'energy': {'power', 'fuel', 'electricity', 'strength', 'vigor', 'force'},
            'generated': {'produced', 'created', 'made', 'manufactured', 'formed', 'yielded'},
            'electricity': {'power', 'electrical energy', 'current', 'voltage', 'electric power'},
            'increase': {'rise', 'grow', 'expand', 'boost', 'enhance', 'improve'},
            'decrease': {'reduce', 'decline', 'drop', 'fall', 'lower', 'diminish'},
            'significant': {'important', 'major', 'considerable', 'substantial', 'notable', 'meaningful'},
            'research': {'study', 'investigation', 'analysis', 'examination', 'survey', 'exploration'},
            'development': {'growth', 'progress', 'advancement', 'evolution', 'improvement', 'expansion'},
            'environment': {'surroundings', 'habitat', 'ecosystem', 'nature', 'conditions', 'context'},
            'technology': {'innovation', 'advancement', 'machinery', 'equipment', 'tools', 'systems'},
            'education': {'learning', 'schooling', 'instruction', 'teaching', 'training', 'knowledge'},
            'economy': {'financial system', 'economics', 'market', 'trade', 'commerce', 'industry'},
            'health': {'wellness', 'fitness', 'medical', 'healthcare', 'condition', 'well-being'},
            'population': {'inhabitants', 'residents', 'people', 'citizens', 'community', 'demographics'},
            'climate': {'weather', 'conditions', 'atmosphere', 'environment', 'temperature', 'seasons'},
            'transport': {'transportation', 'travel', 'movement', 'transit', 'conveyance', 'traffic'},
            'industry': {'manufacturing', 'production', 'business', 'commerce', 'trade', 'sector'},
            'agriculture': {'farming', 'cultivation', 'harvesting', 'crop production', 'land management'},
            'communication': {'interaction', 'contact', 'exchange', 'correspondence', 'connection'},
            'information': {'data', 'knowledge', 'facts', 'details', 'intelligence', 'material'},
            'problem': {'issue', 'challenge', 'difficulty', 'obstacle', 'concern', 'matter'},
            'solution': {'answer', 'resolution', 'fix', 'remedy', 'approach', 'method'},
            'benefit': {'advantage', 'gain', 'profit', 'improvement', 'value', 'merit'},
            'disadvantage': {'drawback', 'limitation', 'weakness', 'con', 'negative aspect'},
            'effect': {'impact', 'result', 'consequence', 'outcome', 'influence', 'repercussion'},
            'cause': {'reason', 'source', 'origin', 'factor', 'basis', 'root'},
            'process': {'procedure', 'method', 'system', 'approach', 'technique', 'operation'},
            'factor': {'element', 'component', 'aspect', 'consideration', 'variable', 'feature'},
            'level': {'standard', 'degree', 'grade', 'rank', 'status', 'position'},
            'rate': {'speed', 'pace', 'frequency', 'ratio', 'proportion', 'percentage'},
            'amount': {'quantity', 'volume', 'number', 'total', 'sum', 'measure'},
            'quality': {'standard', 'caliber', 'grade', 'condition', 'characteristic', 'feature'},
            'method': {'approach', 'technique', 'procedure', 'system', 'way', 'strategy'},
            'system': {'structure', 'framework', 'organization', 'arrangement', 'network', 'scheme'},
            'policy': {'rule', 'regulation', 'guideline', 'approach', 'strategy', 'procedure'},
            'change': {'transformation', 'modification', 'alteration', 'shift', 'variation', 'adjustment'},
            'improvement': {'enhancement', 'progress', 'advancement', 'development', 'upgrade'},
            'reduction': {'decrease', 'cut', 'lowering', 'diminishment', 'decline', 'drop'},
            'analysis': {'examination', 'study', 'investigation', 'review', 'assessment', 'evaluation'},
            'comparison': {'contrast', 'evaluation', 'assessment', 'review', 'examination'},
            'relationship': {'connection', 'link', 'association', 'correlation', 'interaction'},
            'purpose': {'aim', 'goal', 'objective', 'intention', 'function', 'reason'},
            'function': {'role', 'purpose', 'job', 'task', 'operation', 'activity'},
            'feature': {'characteristic', 'attribute', 'quality', 'aspect', 'element', 'property'},
            'aspect': {'feature', 'characteristic', 'element', 'facet', 'dimension', 'quality'},
            'element': {'component', 'factor', 'feature', 'aspect', 'part', 'ingredient'},
            'component': {'part', 'element', 'factor', 'feature', 'aspect', 'section'},
            'resource': {'supply', 'material', 'source', 'asset', 'reserve', 'stock'},
            'material': {'substance', 'matter', 'fabric', 'stuff', 'element', 'component'},
            'product': {'item', 'good', 'commodity', 'output', 'result', 'creation'},
            'service': {'facility', 'amenity', 'offering', 'provision', 'supply', 'assistance'},
            'activity': {'action', 'operation', 'process', 'function', 'task', 'work'},
            'operation': {'activity', 'process', 'procedure', 'function', 'action', 'work'},
            'management': {'administration', 'control', 'supervision', 'direction', 'leadership'},
            'organization': {'structure', 'system', 'arrangement', 'management', 'administration'},
            'structure': {'organization', 'system', 'arrangement', 'framework', 'construction'},
            'framework': {'structure', 'system', 'organization', 'scheme', 'outline', 'plan'},
            'strategy': {'plan', 'approach', 'method', 'tactic', 'scheme', 'policy'},
            'approach': {'method', 'strategy', 'way', 'technique', 'procedure', 'system'},
            'technique': {'method', 'approach', 'procedure', 'system', 'way', 'strategy'},
            'skill': {'ability', 'capability', 'competence', 'expertise', 'talent', 'proficiency'},
            'ability': {'skill', 'capability', 'capacity', 'competence', 'talent', 'power'},
            'knowledge': {'information', 'understanding', 'awareness', 'expertise', 'learning'},
            'experience': {'practice', 'knowledge', 'skill', 'background', 'history', 'exposure'},
            'opportunity': {'chance', 'possibility', 'prospect', 'opening', 'occasion', 'option'},
            'challenge': {'difficulty', 'problem', 'obstacle', 'test', 'trial', 'struggle'},
            'success': {'achievement', 'accomplishment', 'victory', 'triumph', 'win', 'progress'},
            'failure': {'defeat', 'loss', 'setback', 'disappointment', 'unsuccessful result'},
            'risk': {'danger', 'threat', 'hazard', 'peril', 'uncertainty', 'exposure'},
            'safety': {'security', 'protection', 'welfare', 'well-being', 'defense', 'shelter'},
            'security': {'safety', 'protection', 'defense', 'security measures', 'safeguards'},
            'protection': {'defense', 'shielding', 'safeguarding', 'security', 'preservation'},
            'preservation': {'conservation', 'protection', 'maintenance', 'saving', 'upkeep'},
            'conservation': {'preservation', 'protection', 'saving', 'maintenance', 'upkeep'},
            'maintenance': {'upkeep', 'preservation', 'care', 'support', 'service', 'repair'},
            'support': {'assistance', 'help', 'aid', 'backing', 'endorsement', 'encouragement'},
            'assistance': {'help', 'support', 'aid', 'service', 'backing', 'cooperation'},
            'cooperation': {'collaboration', 'partnership', 'teamwork', 'joint effort', 'coordination'},
            'collaboration': {'cooperation', 'partnership', 'teamwork', 'joint effort', 'coordination'},
            'partnership': {'collaboration', 'cooperation', 'alliance', 'association', 'joint venture'},
            'teamwork': {'collaboration', 'cooperation', 'joint effort', 'coordination', 'partnership'},
            'coordination': {'cooperation', 'collaboration', 'organization', 'management', 'harmony'},
            'harmony': {'agreement', 'balance', 'coordination', 'cooperation', 'unity', 'peace'},
            'balance': {'equilibrium', 'stability', 'harmony', 'proportion', 'symmetry', 'equality'},
            'stability': {'steadiness', 'security', 'firmness', 'reliability', 'consistency'},
            'consistency': {'regularity', 'uniformity', 'steadiness', 'reliability', 'constancy'},
            'reliability': {'dependability', 'trustworthiness', 'consistency', 'stability', 'steadiness'},
            'efficiency': {'effectiveness', 'productivity', 'performance', 'capability', 'competence'},
            'effectiveness': {'efficiency', 'success', 'productivity', 'performance', 'capability'},
            'productivity': {'efficiency', 'output', 'performance', 'effectiveness', 'capability'},
            'performance': {'productivity', 'achievement', 'effectiveness', 'efficiency', 'success'},
            'achievement': {'success', 'accomplishment', 'attainment', 'performance', 'result'},
            'accomplishment': {'achievement', 'success', 'attainment', 'performance', 'result'},
            'attainment': {'achievement', 'accomplishment', 'success', 'performance', 'result'},
            'result': {'outcome', 'consequence', 'effect', 'achievement', 'performance', 'success'},
            'outcome': {'result', 'consequence', 'effect', 'achievement', 'performance', 'success'},
            'consequence': {'result', 'outcome', 'effect', 'impact', 'repercussion', 'implication'},
            'impact': {'effect', 'consequence', 'outcome', 'result', 'influence', 'repercussion'},
            'influence': {'impact', 'effect', 'consequence', 'outcome', 'result', 'repercussion'},
            'repercussion': {'consequence', 'effect', 'impact', 'outcome', 'result', 'implication'},
            'implication': {'consequence', 'effect', 'impact', 'outcome', 'result', 'repercussion'}
        }
    
    def extract_keywords(self, question: str) -> Dict[str, List[str]]:
        """
        Extract just-the-words from an IELTS question.
        
        Args:
            question: The IELTS question text
            
        Returns:
            Dictionary containing:
            - 'keywords': List of extracted keywords
            - 'filtered_words': Words that were filtered out
            - 'pos_tags': POS tags for all words
            - 'synonyms': Synonyms for each keyword
        """
        # Clean and tokenize
        question = self._clean_text(question)
        tokens = word_tokenize(question)
        
        # Get POS tags
        pos_tags = pos_tag(tokens)
        
        # Extract content words
        keywords = []
        filtered_words = []
        keyword_synonyms = {}
        
        for word, tag in pos_tags:
            word_lower = word.lower()
            
            # Check if it's a content word and not a filler word
            if (tag in self.content_tags and 
                word_lower not in self.filler_words and
                len(word) > 1 and  # Skip single characters
                not word.isdigit()):  # Skip pure numbers
                
                keywords.append(word)
                
                # Get synonyms for this keyword
                synonyms = self._get_synonyms(word_lower)
                keyword_synonyms[word] = synonyms
            else:
                filtered_words.append(word)
        
        return {
            'keywords': keywords,
            'filtered_words': filtered_words,
            'pos_tags': pos_tags,
            'synonyms': keyword_synonyms
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean text for processing"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove question marks and other punctuation (keep important ones)
        text = re.sub(r'[^\w\s\-]', ' ', text)
        return text.strip()
    
    def _get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word from the database"""
        synonyms = []
        
        # Direct match
        if word in self.synonym_db:
            synonyms.extend(self.synonym_db[word])
        
        # Check if word is a synonym of another word
        for key, synonym_set in self.synonym_db.items():
            if word in synonym_set and key not in synonyms:
                synonyms.append(key)
        
        return list(set(synonyms))  # Remove duplicates
    
    def find_matches_in_text(self, keywords: List[str], text: str) -> Dict[str, List[Dict]]:
        """
        Find keyword matches and their synonyms in a text.
        
        Args:
            keywords: List of keywords to search for
            text: Text to search in
            
        Returns:
            Dictionary mapping each keyword to its matches
        """
        text_lower = text.lower()
        matches = {}
        
        for keyword in keywords:
            keyword_matches = []
            keyword_lower = keyword.lower()
            
            # Find direct matches
            if keyword_lower in text_lower:
                # Find all positions
                start = 0
                while True:
                    pos = text_lower.find(keyword_lower, start)
                    if pos == -1:
                        break
                    
                    # Get context around the match
                    context_start = max(0, pos - 50)
                    context_end = min(len(text), pos + len(keyword) + 50)
                    context = text[context_start:context_end]
                    
                    keyword_matches.append({
                        'type': 'direct',
                        'word': keyword,
                        'position': pos,
                        'context': context
                    })
                    start = pos + 1
            
            # Find synonym matches
            synonyms = self._get_synonyms(keyword_lower)
            for synonym in synonyms:
                if synonym.lower() in text_lower:
                    start = 0
                    while True:
                        pos = text_lower.find(synonym.lower(), start)
                        if pos == -1:
                            break
                        
                        context_start = max(0, pos - 50)
                        context_end = min(len(text), pos + len(synonym) + 50)
                        context = text[context_start:context_end]
                        
                        keyword_matches.append({
                            'type': 'synonym',
                            'word': synonym,
                            'original_keyword': keyword,
                            'position': pos,
                            'context': context
                        })
                        start = pos + 1
            
            matches[keyword] = keyword_matches
        
        return matches
    
    def analyze_question_text_match(self, question: str, text: str) -> Dict:
        """
        Complete analysis: extract keywords from question and find matches in text.
        
        Args:
            question: IELTS question
            text: Text to search for matches
            
        Returns:
            Complete analysis results
        """
        # Extract keywords
        extraction_result = self.extract_keywords(question)
        
        # Find matches
        matches = self.find_matches_in_text(extraction_result['keywords'], text)
        
        # Calculate match statistics
        total_keywords = len(extraction_result['keywords'])
        keywords_with_matches = sum(1 for k, m in matches.items() if m)
        match_coverage = (keywords_with_matches / total_keywords * 100) if total_keywords > 0 else 0
        
        return {
            'question': question,
            'text': text,
            'extraction': extraction_result,
            'matches': matches,
            'statistics': {
                'total_keywords': total_keywords,
                'keywords_with_matches': keywords_with_matches,
                'match_coverage': round(match_coverage, 2),
                'total_matches': sum(len(m) for m in matches.values())
            }
        }
    
    def get_keyword_summary(self, question: str) -> str:
        """
        Get a formatted summary of extracted keywords for quick reference.
        
        Args:
            question: IELTS question
            
        Returns:
            Formatted string with keywords and synonyms
        """
        result = self.extract_keywords(question)
        
        summary = f"Question: {question}\n\n"
        summary += f"Keywords ({len(result['keywords'])}):\n"
        
        for i, keyword in enumerate(result['keywords'], 1):
            synonyms = result['synonyms'].get(keyword, [])
            synonym_text = f" (Synonyms: {', '.join(synonyms[:3])})" if synonyms else ""
            summary += f"{i}. {keyword}{synonym_text}\n"
        
        summary += f"\nFiltered words ({len(result['filtered_words'])}): {', '.join(result['filtered_words'])}"
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    extractor = IELTSKeywordExtractor()
    
    # Example from the description
    question = "The majority of energy was generated by electricity."
    text = "Most power in the region was produced through electrical sources and other forms of generation."
    
    # Test extraction
    result = extractor.extract_keywords(question)
    print("Keyword Extraction:")
    print(f"Keywords: {result['keywords']}")
    print(f"Filtered: {result['filtered_words']}")
    print(f"Synonyms: {result['synonyms']}")
    
    # Test full analysis
    analysis = extractor.analyze_question_text_match(question, text)
    print(f"\nMatch Coverage: {analysis['statistics']['match_coverage']}%")
    print(f"Total Matches: {analysis['statistics']['total_matches']}")
    
    # Test summary
    print(f"\n{extractor.get_keyword_summary(question)}")
