"""
Extraction Service
=================
This service handles the extraction layer responsibilities:
- Loading extraction rules from configuration
- Applying rules to text blocks
- Extracting candidate matches using simple string matching and structural detection

This service implements the extraction v0 contract with keyword, phrase, and structural rules only.
No business logic, risk judgment, optimization, or LLM is used.
"""

import json
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.models.data_models import TextBlock, ExtractionCandidate


class ExtractionService:
    """
    Service class for handling data extraction v0.
    
    This service defines the contract for extracting information from text blocks
    using simple pattern matching rules.
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialize the extraction service.
        
        Args:
            rules_path: Optional path to rules JSON file. If not provided, uses default.
        """
        if rules_path is None:
            # Default to rules_v0.json in the same directory
            current_dir = Path(__file__).parent
            rules_path = str(current_dir / "rules" / "rules_v0.json")
        
        self.rules_path = rules_path
        self.rules: List[Dict[str, Any]] = []
        self._load_rules()
    
    def load_rules(self) -> None:
        """
        Load extraction rules from the rules file.
        This method is called automatically during initialization.
        """
        self._load_rules()
    
    def _load_rules(self) -> None:
        """
        Internal method to load rules from JSON file.
        
        Raises:
            FileNotFoundError: If rules file does not exist
            ValueError: If rules file is invalid
        """
        if not os.path.exists(self.rules_path):
            raise FileNotFoundError(f"Rules file not found: {self.rules_path}")
        
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            if 'rules' not in rules_data:
                raise ValueError("Rules file must contain 'rules' array")
            
            self.rules = rules_data['rules']
            
            # Validate rule structure
            for rule in self.rules:
                if 'rule_id' not in rule or 'rule_type' not in rule:
                    raise ValueError("Each rule must have 'rule_id' and 'rule_type'")
                
                rule_type = rule['rule_type']
                if rule_type not in ['keyword', 'phrase', 'structural']:
                    raise ValueError(f"Invalid rule_type: {rule_type}. Must be keyword, phrase, or structural")
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in rules file: {e}")
    
    def extract(self, text_blocks: List[TextBlock]) -> List[ExtractionCandidate]:
        """
        Extract candidates from text blocks using loaded rules.
        
        Args:
            text_blocks: List of TextBlock objects to extract from
            
        Returns:
            List of ExtractionCandidate objects representing matches
        """
        candidates = []
        
        for block in text_blocks:
            block_candidates = self._extract_from_block(block)
            candidates.extend(block_candidates)
        
        return candidates
    
    def _extract_from_block(self, block: TextBlock) -> List[ExtractionCandidate]:
        """
        Extract candidates from a single text block.
        
        Args:
            block: TextBlock to extract from
            
        Returns:
            List of ExtractionCandidate objects found in this block
        """
        candidates = []
        text = block.normalized_text
        
        for rule in self.rules:
            rule_type = rule['rule_type']
            
            if rule_type == 'keyword':
                matches = self._match_keywords(rule, text)
            elif rule_type == 'phrase':
                matches = self._match_phrases(rule, text)
            elif rule_type == 'structural':
                matches = self._match_structural(rule, text)
            else:
                continue
            
            # Convert matches to ExtractionCandidate objects
            for match in matches:
                candidate = ExtractionCandidate(
                    rule_id=rule['rule_id'],
                    rule_type=rule_type,
                    extracted_text=match['text'],
                    block_id=block.block_id,
                    match_position=match['position'],
                    confidence=1.0,
                    metadata=match.get('metadata')
                )
                candidates.append(candidate)
        
        return candidates
    
    def _match_keywords(self, rule: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """
        Match keywords in text using simple string matching.
        
        Args:
            rule: Rule dictionary with 'keywords' list
            text: Text to search in
            
        Returns:
            List of match dictionaries with 'text' and 'position'
        """
        matches = []
        keywords = rule.get('keywords', [])
        case_sensitive = rule.get('case_sensitive', False)
        
        search_text = text if case_sensitive else text.lower()
        
        for keyword in keywords:
            search_keyword = keyword if case_sensitive else keyword.lower()
            
            # Find all occurrences
            start = 0
            while True:
                position = search_text.find(search_keyword, start)
                if position == -1:
                    break
                
                matches.append({
                    'text': keyword,
                    'position': position,
                    'metadata': {'matched_keyword': keyword}
                })
                
                start = position + 1
        
        return matches
    
    def _match_phrases(self, rule: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """
        Match phrases in text using simple string matching.
        
        Args:
            rule: Rule dictionary with 'phrases' list
            text: Text to search in
            
        Returns:
            List of match dictionaries with 'text' and 'position'
        """
        matches = []
        phrases = rule.get('phrases', [])
        case_sensitive = rule.get('case_sensitive', False)
        
        search_text = text if case_sensitive else text.lower()
        
        for phrase in phrases:
            search_phrase = phrase if case_sensitive else phrase.lower()
            
            # Find all occurrences
            start = 0
            while True:
                position = search_text.find(search_phrase, start)
                if position == -1:
                    break
                
                matches.append({
                    'text': phrase,
                    'position': position,
                    'metadata': {'matched_phrase': phrase}
                })
                
                start = position + 1
        
        return matches
    
    def _match_structural(self, rule: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """
        Match structural patterns in text using basic pattern detection.
        
        Args:
            rule: Rule dictionary with 'pattern' and pattern-specific fields
            text: Text to search in
            
        Returns:
            List of match dictionaries with 'text' and 'position'
        """
        matches = []
        pattern_type = rule.get('pattern', '')
        
        if pattern_type == 'date':
            # Match date patterns (MM/DD/YYYY or similar)
            date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
            matches.extend(self._match_regex_pattern(date_pattern, text, 'date'))
        
        elif pattern_type == 'currency':
            # Match currency amounts ($###,###.##)
            currency_pattern = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
            matches.extend(self._match_regex_pattern(currency_pattern, text, 'currency'))
        
        elif pattern_type == 'line_start':
            # Match lines that start with specific label prefixes
            label_prefixes = rule.get('label_prefixes', [])
            lines = text.split('\n')
            
            for line_idx, line in enumerate(lines):
                line_stripped = line.strip()
                for prefix in label_prefixes:
                    if line_stripped.startswith(prefix):
                        # Calculate position in original text
                        position = sum(len(lines[i]) + 1 for i in range(line_idx))
                        
                        matches.append({
                            'text': line_stripped,
                            'position': position,
                            'metadata': {
                                'matched_prefix': prefix,
                                'line_number': line_idx + 1
                            }
                        })
                        break
        
        return matches
    
    def _match_regex_pattern(self, pattern: str, text: str, pattern_name: str) -> List[Dict[str, Any]]:
        """
        Match a regex pattern in text.
        
        Args:
            pattern: Regex pattern string
            text: Text to search in
            pattern_name: Name of the pattern for metadata
            
        Returns:
            List of match dictionaries with 'text' and 'position'
        """
        matches = []
        for match in re.finditer(pattern, text):
            matches.append({
                'text': match.group(),
                'position': match.start(),
                'metadata': {'pattern_type': pattern_name}
            })
        
        return matches

