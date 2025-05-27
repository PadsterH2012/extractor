#!/usr/bin/env python3
"""
Game-Aware Content Categorization Module
Categorizes extracted content based on game type and book type
"""

from typing import Dict, List
from .game_configs import get_game_config, DEFAULT_CATEGORIES

class GameAwareCategorizer:
    """Categorizes content based on game type and book context"""
    
    def __init__(self):
        self.category_cache = {}
    
    def categorize_content(self, content: str, game_type: str, book_type: str) -> str:
        """
        Categorize content based on game type and book type
        
        Args:
            content: Text content to categorize
            game_type: Game system (D&D, Pathfinder, etc.)
            book_type: Book abbreviation (DMG, PHB, etc.)
            
        Returns:
            Category name
        """
        content_lower = content.lower()
        
        # Get game-specific categories
        categories = self._get_categories_for_game_and_book(game_type, book_type)
        
        # Score each category
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(content_lower.count(keyword.lower()) for keyword in keywords)
            category_scores[category] = score
        
        # Return highest scoring category
        if category_scores and max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        
        return "General"
    
    def _get_categories_for_game_and_book(self, game_type: str, book_type: str) -> Dict[str, List[str]]:
        """Get category definitions for specific game and book combination"""
        
        cache_key = f"{game_type}_{book_type}"
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]
        
        categories = {}
        
        # Game-specific and book-specific categories
        if game_type == "D&D":
            categories = self._get_dnd_categories(book_type)
        elif game_type == "Pathfinder":
            categories = self._get_pathfinder_categories(book_type)
        elif game_type == "Call of Cthulhu":
            categories = self._get_coc_categories(book_type)
        elif game_type in ["Vampire", "Werewolf"]:
            categories = self._get_wod_categories(game_type, book_type)
        elif game_type == "Cyberpunk":
            categories = self._get_cyberpunk_categories(book_type)
        elif game_type == "Shadowrun":
            categories = self._get_shadowrun_categories(book_type)
        else:
            categories = DEFAULT_CATEGORIES.copy()
        
        self.category_cache[cache_key] = categories
        return categories
    
    def _get_dnd_categories(self, book_type: str) -> Dict[str, List[str]]:
        """Get D&D-specific categories"""
        
        if "DMG" in book_type or "Dungeon Master" in book_type:
            return {
                "Combat": ["combat", "attack", "armor", "weapon", "damage", "thac0", "armor class", "initiative", "surprise"],
                "Magic": ["spell", "magic", "magical", "enchant", "potion", "scroll", "wand", "staff", "artifact"],
                "Monsters": ["monster", "creature", "encounter", "bestiary", "hit dice", "morale", "treasure type"],
                "Treasure": ["treasure", "gem", "gold", "coins", "magical items", "artifact", "hoard"],
                "Campaign": ["campaign", "adventure", "world", "setting", "dungeon", "wilderness"],
                "Tables": ["table", "chart", "random", "generation", "roll", "dice", "percentile"],
                "Rules": ["rule", "procedure", "mechanic", "system", "optional", "variant"],
                "NPCs": ["npc", "non-player", "hireling", "henchman", "follower"]
            }
        
        elif "PHB" in book_type or "Player" in book_type:
            return {
                "Character Creation": ["character", "ability", "race", "class", "generation", "stats", "background"],
                "Spells": ["spell", "magic", "cast", "level", "duration", "range", "component", "school"],
                "Equipment": ["equipment", "armor", "weapon", "gear", "item", "cost", "weight"],
                "Combat": ["combat", "attack", "damage", "thac0", "armor class", "saving throw"],
                "Skills": ["skill", "thief", "ability", "proficiency", "check", "modifier"],
                "Classes": ["fighter", "wizard", "cleric", "thief", "ranger", "paladin", "druid"],
                "Races": ["human", "elf", "dwarf", "halfling", "gnome", "half-elf", "half-orc"],
                "Rules": ["rule", "procedure", "mechanic", "playing", "turn", "round"]
            }
        
        elif "Monster Manual" in book_type or "MM" in book_type:
            return {
                "Monsters": ["monster", "creature", "beast", "dragon", "undead", "humanoid", "giant"],
                "Combat": ["armor class", "hit dice", "attack", "damage", "special attack", "special defense"],
                "Special Abilities": ["special", "ability", "magic", "spell", "breath weapon", "gaze"],
                "Ecology": ["habitat", "ecology", "behavior", "organization", "diet", "intelligence"],
                "Treasure": ["treasure", "treasure type", "hoard", "lair"]
            }
        
        else:
            return {
                "Combat": ["combat", "attack", "armor", "weapon", "damage", "thac0"],
                "Magic": ["spell", "magic", "magical", "potion"],
                "Character": ["character", "ability", "race", "class"],
                "Rules": ["rule", "system", "mechanic"],
                "Tables": ["table", "chart", "random"]
            }
    
    def _get_pathfinder_categories(self, book_type: str) -> Dict[str, List[str]]:
        """Get Pathfinder-specific categories"""
        
        if "Core" in book_type:
            return {
                "Combat": ["combat", "attack", "damage", "armor class", "base attack bonus", "cmb", "cmd"],
                "Spells": ["spell", "magic", "caster level", "spell resistance", "school", "descriptor"],
                "Character": ["character", "class", "race", "feat", "skill", "ability score"],
                "Equipment": ["equipment", "weapon", "armor", "magic item", "cost", "craft"],
                "Classes": ["barbarian", "bard", "cleric", "druid", "fighter", "monk", "paladin", "ranger", "rogue", "sorcerer", "wizard"],
                "Rules": ["rule", "mechanic", "system", "check", "dc"],
                "Feats": ["feat", "prerequisite", "benefit", "normal", "special"]
            }
        
        elif "Bestiary" in book_type:
            return {
                "Creatures": ["creature", "monster", "animal", "outsider", "undead", "construct"],
                "Combat": ["ac", "hp", "attack", "damage", "special attack", "special quality"],
                "Special Abilities": ["special", "ability", "spell-like", "supernatural", "extraordinary"],
                "Ecology": ["environment", "organization", "treasure", "advancement"],
                "Templates": ["template", "acquired", "inherited", "cr"]
            }
        
        else:
            return {
                "Combat": ["combat", "attack", "damage", "ac", "bab"],
                "Spells": ["spell", "magic", "caster level"],
                "Character": ["character", "class", "race", "feat"],
                "Equipment": ["equipment", "weapon", "armor"],
                "Rules": ["rule", "mechanic", "system"]
            }
    
    def _get_coc_categories(self, book_type: str) -> Dict[str, List[str]]:
        """Get Call of Cthulhu-specific categories"""
        
        return {
            "Investigation": ["investigate", "clue", "research", "library", "evidence", "search"],
            "Sanity": ["sanity", "madness", "horror", "fear", "phobia", "mania", "indefinite insanity"],
            "Skills": ["skill", "characteristic", "ability", "roll", "check", "difficulty"],
            "Mythos": ["mythos", "cthulhu", "elder", "great old one", "outer god", "deep one"],
            "Combat": ["combat", "weapon", "damage", "hit points", "dodge", "fight"],
            "Occupations": ["occupation", "credit rating", "contacts", "skills", "equipment"],
            "Rules": ["rule", "mechanic", "system", "keeper", "luck", "push"],
            "Scenarios": ["scenario", "handout", "map", "npc", "plot", "investigation"]
        }
    
    def _get_wod_categories(self, game_type: str, book_type: str) -> Dict[str, List[str]]:
        """Get World of Darkness-specific categories"""
        
        if game_type == "Vampire":
            return {
                "Character": ["character", "clan", "generation", "embrace", "sire", "childe"],
                "Disciplines": ["discipline", "power", "level", "blood", "vitae"],
                "Social": ["social", "politics", "sect", "camarilla", "sabbat", "anarch"],
                "Combat": ["combat", "blood", "frenzy", "torpor", "final death"],
                "Supernatural": ["supernatural", "kindred", "kine", "masquerade", "breach"],
                "Rules": ["rule", "system", "mechanic", "storyteller", "difficulty"]
            }
        
        elif game_type == "Werewolf":
            return {
                "Character": ["character", "tribe", "auspice", "breed", "rank"],
                "Gifts": ["gift", "spirit", "gnosis", "rage", "renown"],
                "Social": ["social", "pack", "sept", "caern", "kinfolk"],
                "Combat": ["combat", "rage", "frenzy", "silver", "crinos"],
                "Supernatural": ["supernatural", "garou", "umbra", "spirit", "gaia"],
                "Rules": ["rule", "system", "mechanic", "storyteller", "difficulty"]
            }
        
        return DEFAULT_CATEGORIES.copy()
    
    def _get_cyberpunk_categories(self, book_type: str) -> Dict[str, List[str]]:
        """Get Cyberpunk-specific categories"""
        
        return {
            "Character": ["character", "role", "lifepath", "stats", "skills"],
            "Skills": ["skill", "check", "difficulty", "modifier", "specialization"],
            "Combat": ["combat", "weapon", "damage", "armor", "initiative"],
            "Netrunning": ["netrunner", "netspace", "ice", "daemon", "virus", "program"],
            "Equipment": ["equipment", "cyberware", "weapon", "armor", "vehicle"],
            "Corporations": ["corpo", "corporation", "arasaka", "militech", "biotechnica"],
            "Rules": ["rule", "system", "mechanic", "referee", "difficulty"]
        }
    
    def _get_shadowrun_categories(self, book_type: str) -> Dict[str, List[str]]:
        """Get Shadowrun-specific categories"""
        
        return {
            "Character": ["character", "archetype", "metatype", "priority", "karma"],
            "Skills": ["skill", "test", "threshold", "modifier", "specialization"],
            "Combat": ["combat", "weapon", "damage", "armor", "initiative"],
            "Matrix": ["matrix", "decker", "program", "ice", "node", "cyberdeck"],
            "Magic": ["magic", "spell", "spirit", "astral", "mage", "shaman"],
            "Equipment": ["equipment", "gear", "weapon", "armor", "vehicle", "drone"],
            "Corporations": ["corp", "corporation", "megacorp", "johnson", "shadowrun"],
            "Rules": ["rule", "system", "mechanic", "gamemaster", "target number"]
        }
    
    def get_all_categories_for_game(self, game_type: str) -> List[str]:
        """Get all possible categories for a game type"""
        
        config = get_game_config(game_type)
        all_categories = set()
        
        # Get categories from all books for this game
        books = config.get("books", {})
        for edition, book_list in books.items():
            for book in book_list:
                categories = self._get_categories_for_game_and_book(game_type, book)
                all_categories.update(categories.keys())
        
        return sorted(list(all_categories))
    
    def suggest_category(self, content: str, game_type: str, book_type: str, 
                        confidence_threshold: float = 0.1) -> Dict[str, float]:
        """
        Suggest categories with confidence scores
        
        Args:
            content: Text content to categorize
            game_type: Game system
            book_type: Book abbreviation
            confidence_threshold: Minimum confidence to include
            
        Returns:
            Dictionary of category -> confidence score
        """
        content_lower = content.lower()
        categories = self._get_categories_for_game_and_book(game_type, book_type)
        
        # Calculate scores for all categories
        category_scores = {}
        total_keywords = 0
        
        for category, keywords in categories.items():
            score = 0
            for keyword in keywords:
                count = content_lower.count(keyword.lower())
                score += count
                total_keywords += count
            
            category_scores[category] = score
        
        # Convert to confidence scores
        if total_keywords == 0:
            return {"General": 1.0}
        
        confidences = {}
        for category, score in category_scores.items():
            confidence = score / total_keywords if total_keywords > 0 else 0
            if confidence >= confidence_threshold:
                confidences[category] = confidence
        
        # Ensure at least one category
        if not confidences:
            best_category = max(category_scores, key=category_scores.get)
            confidences[best_category] = 0.1
        
        return confidences
