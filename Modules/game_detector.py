#!/usr/bin/env python3
"""
Game Type Detection Module
Automatically detects RPG game type from PDF content and filenames
"""

import re
from typing import Dict, Optional, Tuple
from pathlib import Path
from .game_configs import GAME_CONFIGS, get_game_config, get_supported_games

class GameDetector:
    """Detects game type from PDF content and filenames"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.detection_cache = {}
    
    def detect_game_type_from_content(self, sample_text: str) -> Tuple[str, Dict[str, int]]:
        """
        Detect game type from PDF content using keyword analysis
        
        Args:
            sample_text: Text content to analyze
            
        Returns:
            Tuple of (detected_game_type, scores_dict)
        """
        if not sample_text:
            return "D&D", {}
        
        sample_lower = sample_text.lower()
        
        # Score each game type based on keyword matches
        game_scores = {}
        for game_type in get_supported_games():
            config = get_game_config(game_type)
            score = 0
            
            for keyword in config.get("detection_keywords", []):
                keyword_lower = keyword.lower()
                # Count occurrences, with bonus for exact matches
                count = sample_lower.count(keyword_lower)
                if count > 0:
                    # Bonus for longer, more specific keywords
                    keyword_bonus = len(keyword.split()) * 2
                    score += count * (1 + keyword_bonus)
            
            game_scores[game_type] = score
            
            if self.debug:
                print(f"  {game_type}: {score} points")
        
        # Return game type with highest score, default to D&D
        if game_scores and max(game_scores.values()) > 0:
            best_game = max(game_scores, key=game_scores.get)
            return best_game, game_scores
        
        return "D&D", game_scores
    
    def detect_game_type_from_filename(self, filename: str) -> Optional[str]:
        """
        Detect game type from filename
        
        Args:
            filename: PDF filename to analyze
            
        Returns:
            Detected game type or None if not found
        """
        filename_lower = filename.lower()
        
        # Direct game name matches
        game_patterns = {
            "D&D": [
                r"d&d", r"dnd", r"dungeons?\s*&?\s*dragons?", r"ad&d",
                r"advanced\s+dungeons?\s*&?\s*dragons?"
            ],
            "Pathfinder": [
                r"pathfinder", r"pf\d*", r"paizo"
            ],
            "Call of Cthulhu": [
                r"call\s*of\s*cthulhu", r"coc\d*", r"chaosium"
            ],
            "Vampire": [
                r"vampire", r"vtm", r"world\s*of\s*darkness", r"masquerade"
            ],
            "Werewolf": [
                r"werewolf", r"wta", r"apocalypse", r"garou"
            ],
            "Cyberpunk": [
                r"cyberpunk", r"cp\d+", r"night\s*city"
            ],
            "Shadowrun": [
                r"shadowrun", r"sr\d*"
            ]
        }
        
        for game_type, patterns in game_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    if self.debug:
                        print(f"  Filename match: {game_type} (pattern: {pattern})")
                    return game_type
        
        return None
    
    def detect_edition_from_filename(self, filename: str, game_type: str) -> Optional[str]:
        """
        Detect edition from filename
        
        Args:
            filename: PDF filename to analyze
            game_type: Already detected game type
            
        Returns:
            Detected edition or None if not found
        """
        filename_lower = filename.lower()
        config = get_game_config(game_type)
        supported_editions = config.get("editions", [])
        
        # Edition patterns
        edition_patterns = {
            "1st": [r"1st", r"1e", r"first", r"original"],
            "2nd": [r"2nd", r"2e", r"second"],
            "3rd": [r"3rd", r"3e", r"third"],
            "3.5": [r"3\.5", r"35", r"three\.five"],
            "4th": [r"4th", r"4e", r"fourth"],
            "5th": [r"5th", r"5e", r"fifth"],
            "6th": [r"6th", r"6e", r"sixth"],
            "7th": [r"7th", r"7e", r"seventh"],
            "2020": [r"2020", r"twenty\s*twenty"],
            "RED": [r"red"],
            "V20": [r"v20", r"20th", r"twentieth"],
            "V5": [r"v5", r"fifth"],
            "W20": [r"w20"],
            "W5": [r"w5"]
        }
        
        for edition, patterns in edition_patterns.items():
            if edition in supported_editions:
                for pattern in patterns:
                    if re.search(pattern, filename_lower):
                        if self.debug:
                            print(f"  Edition match: {edition} (pattern: {pattern})")
                        return edition
        
        return None
    
    def detect_book_from_filename(self, filename: str, game_type: str, edition: str) -> Optional[str]:
        """
        Detect book type from filename
        
        Args:
            filename: PDF filename to analyze
            game_type: Already detected game type
            edition: Already detected edition
            
        Returns:
            Detected book abbreviation or None if not found
        """
        filename_lower = filename.lower()
        config = get_game_config(game_type)
        available_books = config.get("books", {}).get(edition, [])
        
        # Direct book abbreviation matches
        for book in available_books:
            if book.lower() in filename_lower:
                if self.debug:
                    print(f"  Book match: {book}")
                return book
        
        # Common book patterns
        book_patterns = {
            "DMG": [r"dungeon\s*master", r"dm\s*guide", r"dmg"],
            "PHB": [r"player", r"phb", r"handbook"],
            "MM": [r"monster\s*manual", r"mm", r"bestiary"],
            "Core": [r"core", r"rulebook", r"basic"],
            "Keeper": [r"keeper", r"gm", r"gamemaster"],
            "Investigator": [r"investigator", r"player"]
        }
        
        for book_abbrev, patterns in book_patterns.items():
            if book_abbrev in available_books:
                for pattern in patterns:
                    if re.search(pattern, filename_lower):
                        if self.debug:
                            print(f"  Book pattern match: {book_abbrev} (pattern: {pattern})")
                        return book_abbrev
        
        return None
    
    def detect_from_pdf_path(self, pdf_path: Path, sample_content: str = "", 
                           force_game_type: Optional[str] = None,
                           force_edition: Optional[str] = None) -> Dict[str, str]:
        """
        Comprehensive detection from PDF path and content
        
        Args:
            pdf_path: Path to PDF file
            sample_content: Sample text content from PDF
            force_game_type: Override game type detection
            force_edition: Override edition detection
            
        Returns:
            Dictionary with detected metadata
        """
        filename = pdf_path.stem
        
        if self.debug:
            print(f"Detecting game info for: {filename}")
        
        # Detect game type
        if force_game_type:
            game_type = force_game_type
            if self.debug:
                print(f"  Forced game type: {game_type}")
        else:
            # Try filename first
            game_type = self.detect_game_type_from_filename(filename)
            
            # If not found in filename, try content
            if not game_type and sample_content:
                if self.debug:
                    print("  Analyzing content for game type...")
                game_type, scores = self.detect_game_type_from_content(sample_content)
                if self.debug:
                    print(f"  Content detection result: {game_type}")
            
            # Default fallback
            if not game_type:
                game_type = "D&D"
                if self.debug:
                    print("  Using default: D&D")
        
        # Detect edition
        if force_edition:
            edition = force_edition
            if self.debug:
                print(f"  Forced edition: {edition}")
        else:
            edition = self.detect_edition_from_filename(filename, game_type)
            if not edition:
                # Use first available edition for the game
                config = get_game_config(game_type)
                editions = config.get("editions", ["1st"])
                edition = editions[0]
                if self.debug:
                    print(f"  Using default edition: {edition}")
        
        # Detect book
        book = self.detect_book_from_filename(filename, game_type, edition)
        if not book:
            # Generate from filename
            safe_name = "".join(c for c in filename if c.isalnum() or c in "_-")[:20]
            book = safe_name.upper()[:5] if safe_name else "CORE"
            if self.debug:
                print(f"  Generated book name: {book}")
        
        # Generate collection name
        config = get_game_config(game_type)
        prefix = config.get("collection_prefix", "unknown")
        edition_clean = edition.replace(".", "").lower()
        book_clean = book.lower()
        collection_name = f"{prefix}_{edition_clean}_{book_clean}"
        
        result = {
            "game_type": game_type,
            "edition": edition,
            "book": book,
            "collection_name": collection_name,
            "filename": filename
        }
        
        if self.debug:
            print(f"  Final result: {result}")
        
        return result
    
    def validate_detection(self, game_type: str, edition: str, book: str) -> bool:
        """
        Validate that detected game info is supported
        
        Args:
            game_type: Detected game type
            edition: Detected edition
            book: Detected book
            
        Returns:
            True if combination is valid
        """
        if game_type not in GAME_CONFIGS:
            return False
        
        config = GAME_CONFIGS[game_type]
        
        if edition not in config.get("editions", []):
            return False
        
        supported_books = config.get("books", {}).get(edition, [])
        if book not in supported_books:
            # Allow unknown books for flexibility
            return True
        
        return True
    
    def get_detection_confidence(self, game_type: str, edition: str, book: str, 
                               filename: str, content_scores: Dict[str, int] = None) -> float:
        """
        Calculate confidence score for detection
        
        Args:
            game_type: Detected game type
            edition: Detected edition  
            book: Detected book
            filename: Original filename
            content_scores: Scores from content analysis
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.0
        
        # Base confidence for valid configuration
        if self.validate_detection(game_type, edition, book):
            confidence += 0.3
        
        # Filename detection bonus
        if self.detect_game_type_from_filename(filename):
            confidence += 0.3
        
        if self.detect_edition_from_filename(filename, game_type):
            confidence += 0.2
        
        if self.detect_book_from_filename(filename, game_type, edition):
            confidence += 0.2
        
        # Content analysis bonus
        if content_scores and game_type in content_scores:
            max_score = max(content_scores.values()) if content_scores.values() else 0
            if max_score > 0:
                content_confidence = min(content_scores[game_type] / max_score, 1.0)
                confidence = max(confidence, content_confidence)
        
        return min(confidence, 1.0)
