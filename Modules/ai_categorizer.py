#!/usr/bin/env python3
"""
AI-Powered Content Categorization Module
Uses AI to dynamically categorize content based on context and game system
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional

class AICategorizer:
    """AI-powered content categorization based on game context"""

    def __init__(self, ai_config: Dict[str, Any] = None, debug: bool = False):
        self.ai_config = ai_config or {"provider": "mock"}
        self.debug = debug or self.ai_config.get("debug", False)
        self.logger = logging.getLogger(__name__)

        # Initialize AI client with configuration
        self.ai_client = self._initialize_ai_client()

        # Token tracking attributes
        self._current_session_id = None
        self._pricing_data = None

        # Category cache for performance
        self.category_cache = {}

        # Batch processing settings
        self.batch_size = 5  # Process 5 pages at once
        self.use_batching = True

        # Performance optimization settings
        self.enable_smart_caching = True
        self.cache_hit_count = 0
        self.total_requests = 0

    def set_session_tracking(self, session_id: str, pricing_data: Dict = None):
        """Set session ID and pricing data for token tracking"""
        self._current_session_id = session_id
        self._pricing_data = pricing_data

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

        elif provider == "openrouter":
            try:
                import os
                from .ai_game_detector import OpenRouterClient
                api_key = self.ai_config.get("api_key") or os.getenv("OPENROUTER_API_KEY")
                if api_key:
                    return OpenRouterClient(api_key, self.ai_config)
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

        # Performance tracking
        self.total_requests += 1

        # Check cache first
        cache_key = self._generate_cache_key(content, game_metadata)
        if cache_key in self.category_cache:
            self.cache_hit_count += 1
            cache_hit_rate = (self.cache_hit_count / self.total_requests) * 100
            if self.debug:
                print(f"🔄 Cache hit! Rate: {cache_hit_rate:.1f}% ({self.cache_hit_count}/{self.total_requests})")
            return self.category_cache[cache_key]

        # Perform AI categorization
        if self.debug:
            cache_hit_rate = (self.cache_hit_count / self.total_requests) * 100
            print(f"🤖 AI categorization needed. Cache rate: {cache_hit_rate:.1f}% ({self.cache_hit_count}/{self.total_requests})")

        result = self._perform_ai_categorization(content, game_metadata)

        # Cache result
        self.category_cache[cache_key] = result

        return result

    def categorize_batch(self, content_list: List[str], game_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Categorize multiple content pieces in a single API call for better performance"""

        if not content_list:
            return []

        # Check cache for all items first
        results = []
        uncached_indices = []
        uncached_content = []

        for i, content in enumerate(content_list):
            cache_key = self._generate_cache_key(content, game_metadata)
            if cache_key in self.category_cache:
                results.append(self.category_cache[cache_key])
                if self.debug:
                    print(f"🔄 Using cached categorization for batch item {i+1}")
            else:
                results.append(None)  # Placeholder
                uncached_indices.append(i)
                uncached_content.append(content)

        # Process uncached items in batch
        if uncached_content:
            if self.debug:
                print(f"🔄 Batch categorizing {len(uncached_content)} items")

            batch_results = self._perform_batch_categorization(uncached_content, game_metadata)

            # Fill in the results and cache them
            for idx, result in zip(uncached_indices, batch_results):
                results[idx] = result
                cache_key = self._generate_cache_key(content_list[idx], game_metadata)
                self.category_cache[cache_key] = result

        return results

    def _perform_batch_categorization(self, content_list: List[str], game_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform AI-based batch categorization for multiple content pieces"""

        # Temporary workaround: Use smart fallback categorization for now
        # TODO: Fix Claude API categorization response parsing
        if self.ai_config.get("provider") in ["claude", "anthropic"]:
            if self.debug:
                print("🔄 Using smart fallback categorization for Claude (temporary)")
            return [self._smart_fallback_categorization(content, game_metadata) for content in content_list]

        # Build batch categorization prompt
        prompt = self._build_batch_categorization_prompt(content_list, game_metadata)

        # Get AI analysis
        ai_response = self.ai_client.categorize(prompt)

        # Parse and validate response
        return self._parse_batch_categorization_response(ai_response, game_metadata, len(content_list))

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

    def _parse_batch_categorization_response(self, ai_response: Any, game_metadata: Dict[str, Any], expected_count: int) -> List[Dict[str, Any]]:
        """Parse and validate AI batch categorization response"""

        try:
            # Handle empty or None responses
            if not ai_response:
                self.logger.warning("AI returned empty response for batch categorization")
                return [self._fallback_categorization(game_metadata) for _ in range(expected_count)]

            # Handle string responses
            if isinstance(ai_response, str):
                if not ai_response.strip():
                    self.logger.warning("AI returned empty string for batch categorization")
                    return [self._fallback_categorization(game_metadata) for _ in range(expected_count)]

                try:
                    result = json.loads(ai_response)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse AI batch categorization JSON: {e}")
                    return [self._fallback_categorization(game_metadata) for _ in range(expected_count)]
            else:
                result = ai_response

            # Validate that result is a list
            if not isinstance(result, list):
                self.logger.error(f"AI batch categorization result is not a list: {type(result)}")
                return [self._fallback_categorization(game_metadata) for _ in range(expected_count)]

            # Validate count matches expected
            if len(result) != expected_count:
                self.logger.warning(f"AI returned {len(result)} results, expected {expected_count}")
                # Pad or truncate as needed
                while len(result) < expected_count:
                    result.append(self._fallback_categorization(game_metadata))
                result = result[:expected_count]

            # Validate each result
            validated_results = []
            for i, item in enumerate(result):
                if not isinstance(item, dict):
                    self.logger.warning(f"Batch item {i+1} is not a dictionary, using fallback")
                    validated_results.append(self._fallback_categorization(game_metadata))
                    continue

                # Validate and set defaults for each item
                validated = {
                    "primary_category": item.get("primary_category", "General"),
                    "secondary_categories": item.get("secondary_categories", []),
                    "confidence": float(item.get("confidence", 0.5)),
                    "reasoning": item.get("reasoning", "AI batch categorization"),
                    "key_topics": item.get("key_topics", []),
                    "game_specific_elements": item.get("game_specific_elements", []),
                    "content_type": item.get("content_type", "description"),
                    "categorization_method": "ai_batch_analysis"
                }

                # Ensure confidence is in valid range
                if not 0.0 <= validated["confidence"] <= 1.0:
                    validated["confidence"] = 0.5

                validated_results.append(validated)

            return validated_results

        except Exception as e:
            self.logger.error(f"Failed to parse AI batch categorization: {e}")
            if self.debug:
                import traceback
                self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return [self._fallback_categorization(game_metadata) for _ in range(expected_count)]

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

    def _build_batch_categorization_prompt(self, content_list: List[str], game_metadata: Dict[str, Any]) -> str:
        """Build AI prompt for batch content categorization"""

        # Truncate each content piece if too long
        max_content_per_item = 800  # Smaller per item to fit multiple in one prompt
        truncated_content = []

        for i, content in enumerate(content_list):
            if len(content) > max_content_per_item:
                content = content[:max_content_per_item] + "..."
            truncated_content.append(f"CONTENT {i+1}:\n{content}")

        combined_content = "\n\n".join(truncated_content)

        prompt = f"""
You are an expert in {game_metadata['game_type']} {game_metadata['edition']} Edition content analysis.

GAME CONTEXT:
- Game System: {game_metadata['game_type']}
- Edition: {game_metadata['edition']}
- Book Type: {game_metadata['book_type']}
- Publisher: {game_metadata.get('publisher', 'Unknown')}

BATCH CONTENT TO CATEGORIZE:
{combined_content}

Analyze each content piece and determine the most appropriate category for each. Consider the game system's unique characteristics and terminology.

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

Provide your analysis in JSON format as an array of categorization objects:
[
    {{
        "primary_category": "Most appropriate category name for content 1",
        "secondary_categories": ["List of other relevant categories"],
        "confidence": 0.95,
        "reasoning": "Brief explanation of categorization decision",
        "key_topics": ["List of main topics/concepts found"],
        "game_specific_elements": ["Game-specific terminology or mechanics identified"],
        "content_type": "Type of content (rules, description, table, example, etc.)"
    }},
    {{
        "primary_category": "Most appropriate category name for content 2",
        "secondary_categories": ["List of other relevant categories"],
        "confidence": 0.95,
        "reasoning": "Brief explanation of categorization decision",
        "key_topics": ["List of main topics/concepts found"],
        "game_specific_elements": ["Game-specific terminology or mechanics identified"],
        "content_type": "Type of content (rules, description, table, example, etc.)"
    }}
]

Focus on accuracy and provide confidence scores based on how clearly each content fits its category.
Return exactly {len(content_list)} categorization objects in the array.
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
        """Generate intelligent cache key for categorization results"""

        # Normalize content for better cache hits
        normalized_content = content.lower().strip()

        # Remove common variations that don't affect categorization
        normalized_content = re.sub(r'\s+', ' ', normalized_content)  # Normalize whitespace
        normalized_content = re.sub(r'page\s+\d+', '', normalized_content)  # Remove page numbers
        normalized_content = re.sub(r'\d+', 'NUM', normalized_content)  # Normalize numbers

        # Use semantic content patterns for better cache hits
        content_patterns = []

        # Check for common content patterns
        if 'spell' in normalized_content or 'magic' in normalized_content:
            content_patterns.append('magic_content')
        if 'combat' in normalized_content or 'attack' in normalized_content:
            content_patterns.append('combat_content')
        if 'character' in normalized_content or 'class' in normalized_content:
            content_patterns.append('character_content')
        if 'equipment' in normalized_content or 'item' in normalized_content:
            content_patterns.append('equipment_content')

        # Use pattern-based caching for similar content
        if content_patterns:
            pattern_key = '_'.join(sorted(content_patterns))
            content_signature = f"{pattern_key}_{len(normalized_content)//100}"  # Group by content length
        else:
            # Fallback to content hash for unique content
            content_signature = str(hash(normalized_content[:300]))

        game_context = f"{game_metadata['game_type']}_{game_metadata['edition']}_{game_metadata['book_type']}"

        return f"{game_context}_{content_signature}"

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
