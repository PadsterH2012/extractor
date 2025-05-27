#!/usr/bin/env python3
"""
AI-Powered Content Categorization Module
Uses AI to dynamically categorize content based on context and game system
"""

import json
import logging
from typing import Dict, List, Any, Optional

class AICategorizer:
    """AI-powered content categorization based on game context"""

    def __init__(self, ai_config: Dict[str, Any] = None, debug: bool = False):
        self.ai_config = ai_config or {"provider": "mock"}
        self.debug = debug or self.ai_config.get("debug", False)
        self.logger = logging.getLogger(__name__)

        # Initialize AI client with configuration
        self.ai_client = self._initialize_ai_client()

        # Category cache for performance
        self.category_cache = {}

    def _initialize_ai_client(self):
        """Initialize AI client based on configuration"""
        # Import the AI client classes from the game detector module
        from .ai_game_detector import MockAIClient, OpenAIClient, AnthropicClient, LocalLLMClient

        provider = self.ai_config.get("provider", "mock")

        if self.debug:
            print(f"🤖 Initializing AI categorizer: {provider}")

        # Use the same client classes as the game detector
        if provider == "openai":
            try:
                import os
                api_key = self.ai_config.get("api_key") or os.getenv("OPENAI_API_KEY")
                if api_key:
                    client_config = {"api_key": api_key}
                    if self.ai_config.get("base_url"):
                        client_config["base_url"] = self.ai_config["base_url"]
                    return OpenAIClient(client_config, self.ai_config)
            except:
                pass

        elif provider in ["claude", "anthropic"]:
            try:
                import os
                api_key = self.ai_config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    return AnthropicClient(api_key, self.ai_config)
            except:
                pass

        elif provider == "local":
            try:
                import os
                base_url = self.ai_config.get("base_url") or os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
                model = self.ai_config.get("model") or os.getenv("LOCAL_LLM_MODEL", "llama2")
                return LocalLLMClient(base_url, model, self.ai_config)
            except:
                pass

        # Default to mock client
        return MockAIClient(self.ai_config)

    def categorize_content(self, content: str, game_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered content categorization

        Args:
            content: Text content to categorize
            game_metadata: Game system metadata from AI detection

        Returns:
            Dictionary with category, confidence, and reasoning
        """

        # Check cache first
        cache_key = self._generate_cache_key(content, game_metadata)
        if cache_key in self.category_cache:
            return self.category_cache[cache_key]

        # Perform AI categorization
        result = self._perform_ai_categorization(content, game_metadata)

        # Cache result
        self.category_cache[cache_key] = result

        return result

    def _perform_ai_categorization(self, content: str, game_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Perform AI-based categorization"""

        # Temporary workaround: Use smart fallback categorization for now
        # TODO: Fix Claude API categorization response parsing
        if self.ai_config.get("provider") in ["claude", "anthropic"]:
            if self.debug:
                print("🔄 Using smart fallback categorization for Claude (temporary)")
            return self._smart_fallback_categorization(content, game_metadata)

        # Build categorization prompt
        prompt = self._build_categorization_prompt(content, game_metadata)

        # Get AI analysis
        ai_response = self.ai_client.categorize(prompt)

        # Parse and validate response
        return self._parse_categorization_response(ai_response, game_metadata)

    def _build_categorization_prompt(self, content: str, game_metadata: Dict[str, Any]) -> str:
        """Build AI prompt for content categorization"""

        # Truncate content if too long
        max_content = 2000
        if len(content) > max_content:
            content = content[:max_content] + "..."

        prompt = f"""
You are an expert in {game_metadata['game_type']} {game_metadata['edition']} Edition content analysis.

GAME CONTEXT:
- Game System: {game_metadata['game_type']}
- Edition: {game_metadata['edition']}
- Book Type: {game_metadata['book_type']}
- Publisher: {game_metadata.get('publisher', 'Unknown')}

CONTENT TO CATEGORIZE:
{content}

Analyze this content and determine the most appropriate category. Consider the game system's unique characteristics and terminology.

For {game_metadata['game_type']} {game_metadata['edition']}, typical categories might include:

GENERAL CATEGORIES (applicable to most RPGs):
- Character Creation
- Combat Rules
- Magic/Spells
- Equipment/Items
- Skills/Abilities
- Rules/Mechanics
- Tables/Charts
- Lore/Setting
- NPCs/Characters
- Adventures/Scenarios

GAME-SPECIFIC CATEGORIES:
{self._get_game_specific_categories(game_metadata)}

Provide your analysis in JSON format:
{{
    "primary_category": "Most appropriate category name",
    "secondary_categories": ["List of other relevant categories"],
    "confidence": 0.95,
    "reasoning": "Brief explanation of categorization decision",
    "key_topics": ["List of main topics/concepts found"],
    "game_specific_elements": ["Game-specific terminology or mechanics identified"],
    "content_type": "Type of content (rules, description, table, example, etc.)"
}}

Focus on accuracy and provide confidence scores based on how clearly the content fits the category.
"""

        return prompt

    def _get_game_specific_categories(self, game_metadata: Dict[str, Any]) -> str:
        """Get game-specific category suggestions"""

        game_type = game_metadata['game_type']

        if game_type == "D&D":
            return """
D&D SPECIFIC:
- Classes (Fighter, Wizard, Cleric, etc.)
- Races (Human, Elf, Dwarf, etc.)
- Spells by Level (1st Level Spells, 2nd Level Spells, etc.)
- Monsters/Creatures
- Treasure/Magic Items
- Dungeon Design
- Campaign Setting
- Saving Throws
- THAC0/Attack Tables (1st/2nd Ed)
- Feats (3rd+ Ed)
"""

        elif game_type == "Pathfinder":
            return """
PATHFINDER SPECIFIC:
- Classes (Barbarian, Bard, Oracle, etc.)
- Archetypes
- Feats
- Spells by Level
- Creatures/Bestiary
- Combat Maneuvers
- Skill System
- Magic Items
- Adventure Paths
- Golarion Setting
"""

        elif game_type == "Call of Cthulhu":
            return """
CALL OF CTHULHU SPECIFIC:
- Investigator Creation
- Skills System
- Sanity/Madness
- Mythos Creatures
- Spells/Rituals
- Investigation Rules
- Chase Rules
- Occupations
- Equipment (1920s/Modern)
- Scenarios/Adventures
- Keeper Advice
"""

        elif game_type == "Vampire":
            return """
VAMPIRE SPECIFIC:
- Clans
- Disciplines
- Blood Pool/Vitae
- Humanity/Path
- Generation
- Coteries
- Camarilla/Sabbat
- Masquerade
- Feeding
- Combat (Frenzy, Torpor)
- Storyteller Advice
"""

        elif game_type == "Werewolf":
            return """
WEREWOLF SPECIFIC:
- Tribes
- Auspices
- Gifts
- Rage/Gnosis
- Renown
- Pack Dynamics
- Umbra/Spirit World
- Garou Forms
- Rites
- Caerns
- Storyteller Advice
"""

        else:
            return "Game-specific categories will be determined based on content analysis."

    def _parse_categorization_response(self, ai_response: Any, game_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate AI categorization response"""

        try:
            # Handle empty or None responses
            if not ai_response:
                self.logger.warning("AI returned empty response for categorization")
                return self._fallback_categorization(game_metadata)

            # Handle string responses
            if isinstance(ai_response, str):
                # Check if string is empty or whitespace
                if not ai_response.strip():
                    self.logger.warning("AI returned empty string for categorization")
                    return self._fallback_categorization(game_metadata)

                try:
                    result = json.loads(ai_response)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse AI categorization JSON: {e}")
                    if self.debug:
                        self.logger.error(f"Raw AI response: '{ai_response}'")
                    return self._fallback_categorization(game_metadata)
            else:
                result = ai_response

            # Validate that result is a dictionary
            if not isinstance(result, dict):
                self.logger.error(f"AI categorization result is not a dictionary: {type(result)}")
                return self._fallback_categorization(game_metadata)

            # Validate and set defaults
            validated = {
                "primary_category": result.get("primary_category", "General"),
                "secondary_categories": result.get("secondary_categories", []),
                "confidence": float(result.get("confidence", 0.5)),
                "reasoning": result.get("reasoning", "AI categorization"),
                "key_topics": result.get("key_topics", []),
                "game_specific_elements": result.get("game_specific_elements", []),
                "content_type": result.get("content_type", "description"),
                "categorization_method": "ai_analysis"
            }

            # Ensure confidence is in valid range
            if not 0.0 <= validated["confidence"] <= 1.0:
                validated["confidence"] = 0.5

            return validated

        except Exception as e:
            self.logger.error(f"Failed to parse AI categorization: {e}")
            if self.debug:
                import traceback
                self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return self._fallback_categorization(game_metadata)

    def _smart_fallback_categorization(self, content: str, game_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Smart fallback categorization based on content analysis"""

        content_lower = content.lower()

        # Analyze content for category indicators
        if any(term in content_lower for term in ["spell", "magic", "cast", "enchant", "incantation"]):
            return {
                "primary_category": "Spells/Magic",
                "secondary_categories": ["Rules"],
                "confidence": 0.7,
                "reasoning": "Content contains spell or magic-related terminology",
                "key_topics": ["spells", "magic", "casting"],
                "game_specific_elements": ["spell levels", "components"],
                "content_type": "rules",
                "categorization_method": "smart_fallback"
            }

        elif any(term in content_lower for term in ["combat", "attack", "damage", "armor", "weapon", "hit points"]):
            return {
                "primary_category": "Combat",
                "secondary_categories": ["Rules"],
                "confidence": 0.7,
                "reasoning": "Content contains combat-related terminology",
                "key_topics": ["combat", "attack", "damage"],
                "game_specific_elements": ["armor class", "hit points"],
                "content_type": "rules",
                "categorization_method": "smart_fallback"
            }

        elif any(term in content_lower for term in ["character", "class", "race", "ability", "stats", "level"]):
            return {
                "primary_category": "Character Creation",
                "secondary_categories": ["Classes", "Races"],
                "confidence": 0.6,
                "reasoning": "Content appears to be about character creation",
                "key_topics": ["character", "abilities", "stats"],
                "game_specific_elements": ["ability scores", "classes"],
                "content_type": "description",
                "categorization_method": "smart_fallback"
            }

        elif any(term in content_lower for term in ["equipment", "item", "treasure", "gear", "cost", "weight"]):
            return {
                "primary_category": "Equipment",
                "secondary_categories": ["Treasure"],
                "confidence": 0.6,
                "reasoning": "Content contains equipment or treasure references",
                "key_topics": ["equipment", "items", "gear"],
                "game_specific_elements": ["cost", "weight"],
                "content_type": "description",
                "categorization_method": "smart_fallback"
            }

        else:
            return {
                "primary_category": "General",
                "secondary_categories": [],
                "confidence": 0.4,
                "reasoning": "Smart fallback - general content classification",
                "key_topics": [],
                "game_specific_elements": [],
                "content_type": "description",
                "categorization_method": "smart_fallback"
            }

    def _fallback_categorization(self, game_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback categorization when AI fails"""

        return {
            "primary_category": "General",
            "secondary_categories": [],
            "confidence": 0.1,
            "reasoning": "AI categorization failed, using fallback",
            "key_topics": [],
            "game_specific_elements": [],
            "content_type": "unknown",
            "categorization_method": "fallback"
        }

    def _generate_cache_key(self, content: str, game_metadata: Dict[str, Any]) -> str:
        """Generate cache key for categorization results"""

        # Use hash of content + game context for caching
        content_hash = hash(content[:500])  # First 500 chars
        game_context = f"{game_metadata['game_type']}_{game_metadata['edition']}_{game_metadata['book_type']}"

        return f"{game_context}_{content_hash}"

    def suggest_categories_for_game(self, game_metadata: Dict[str, Any]) -> List[str]:
        """Suggest possible categories for a specific game system"""

        prompt = f"""
List the most common content categories found in {game_metadata['game_type']} {game_metadata['edition']} Edition {game_metadata['book_type']} books.

Provide a comprehensive list of categories that would be useful for organizing content from this type of book.

Return as JSON array of category names:
["Category 1", "Category 2", "Category 3", ...]
"""

        try:
            ai_response = self.ai_client.categorize(prompt)
            if isinstance(ai_response, str):
                categories = json.loads(ai_response)
            else:
                categories = ai_response

            return categories if isinstance(categories, list) else []

        except Exception as e:
            self.logger.error(f"Failed to get category suggestions: {e}")
            return ["General", "Rules", "Character", "Combat", "Magic", "Equipment"]

    def analyze_content_themes(self, content_sections: List[Dict[str, Any]],
                             game_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze themes across multiple content sections"""

        # Combine content for theme analysis
        combined_content = "\n".join([
            section.get("content", "")[:500] for section in content_sections[:10]
        ])

        prompt = f"""
Analyze the themes and topics in this {game_metadata['game_type']} {game_metadata['edition']} content.

CONTENT SAMPLE:
{combined_content}

Identify:
1. Main themes and topics
2. Game-specific mechanics mentioned
3. Content distribution across categories
4. Unique elements or special focus areas

Provide analysis in JSON format:
{{
    "main_themes": ["List of primary themes"],
    "mechanics_found": ["Game mechanics identified"],
    "category_distribution": {{"Category": "percentage"}},
    "unique_elements": ["Special or unusual content found"],
    "content_focus": "Overall focus of the material",
    "complexity_level": "Basic/Intermediate/Advanced"
}}
"""

        try:
            ai_response = self.ai_client.categorize(prompt)
            if isinstance(ai_response, str):
                return json.loads(ai_response)
            return ai_response

        except Exception as e:
            self.logger.error(f"Theme analysis failed: {e}")
            return {
                "main_themes": [],
                "mechanics_found": [],
                "category_distribution": {},
                "unique_elements": [],
                "content_focus": "Unknown",
                "complexity_level": "Unknown"
            }


class MockAIClient:
    """Mock AI client for categorization - replace with actual AI implementation"""

    def categorize(self, prompt: str) -> Dict[str, Any]:
        """Mock categorization - replace with actual AI call"""

        prompt_lower = prompt.lower()

        # Simple mock categorization based on keywords
        if "spell" in prompt_lower or "magic" in prompt_lower:
            return {
                "primary_category": "Spells/Magic",
                "secondary_categories": ["Rules"],
                "confidence": 0.8,
                "reasoning": "Content contains spell or magic-related terminology",
                "key_topics": ["spells", "magic", "casting"],
                "game_specific_elements": ["spell levels", "components"],
                "content_type": "rules"
            }

        elif "combat" in prompt_lower or "attack" in prompt_lower:
            return {
                "primary_category": "Combat",
                "secondary_categories": ["Rules"],
                "confidence": 0.8,
                "reasoning": "Content contains combat-related terminology",
                "key_topics": ["combat", "attack", "damage"],
                "game_specific_elements": ["armor class", "hit points"],
                "content_type": "rules"
            }

        elif "character" in prompt_lower or "class" in prompt_lower:
            return {
                "primary_category": "Character Creation",
                "secondary_categories": ["Classes"],
                "confidence": 0.7,
                "reasoning": "Content appears to be about character creation",
                "key_topics": ["character", "abilities", "stats"],
                "game_specific_elements": ["ability scores", "classes"],
                "content_type": "description"
            }

        else:
            return {
                "primary_category": "General",
                "secondary_categories": [],
                "confidence": 0.5,
                "reasoning": "Mock analysis - no clear category indicators",
                "key_topics": [],
                "game_specific_elements": [],
                "content_type": "description"
            }
