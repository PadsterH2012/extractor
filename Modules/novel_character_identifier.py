"""
Novel Character Identifier - AI-powered two-pass character discovery system

This module implements a sophisticated character identification system for novels:
1. First Pass: Character Discovery - identifies potential characters from text
2. Second Pass: Character Validation - validates and filters the character list

The system is designed to extract character information for pattern generation
while avoiding false positives (places, objects, concepts mistaken for characters).
"""

import json
import logging
import os
import re
from typing import Dict, Any, List, Optional
from pathlib import Path


class NovelCharacterIdentifier:
    """AI-powered character identification for novels using two-pass analysis"""

    def __init__(self, ai_config: Dict[str, Any] = None, debug: bool = False):
        self.ai_config = ai_config or {"provider": "mock"}
        self.debug = debug or self.ai_config.get("debug", False)
        self.logger = logging.getLogger(__name__)

        # Initialize AI client
        self.ai_client = self._initialize_ai_client()

        # Character identification configuration - MEMORY OPTIMIZED APPROACH
        self.max_content_length = 800000   # Reduced from 1M to 800k chars for memory efficiency
        self.chunk_size = 120000           # Reduced from 200k to 120k chunks
        self.chunk_overlap = 5000          # Reduced from 20k to 5k overlap
        self.min_character_mentions = 2    # Reduced threshold to catch more characters
        self.confidence_threshold = 0.5    # Reduced threshold to be less strict
        self.max_candidates_per_chunk = 30 # Reduced from 50 to 30 candidates per chunk
        self.min_mentions_for_analysis = 3 # Require 3+ mentions for detailed analysis

    def _initialize_ai_client(self):
        """Initialize AI client based on configuration"""
        provider = self.ai_config.get("provider", "mock")

        if provider == "openai":
            return self._initialize_openai_client()
        elif provider in ["claude", "anthropic"]:
            return self._initialize_anthropic_client()
        elif provider == "openrouter":
            return self._initialize_openrouter_client()
        elif provider == "local":
            return self._initialize_local_client()
        else:
            return MockCharacterIdentifier()

    def _initialize_openai_client(self):
        """Initialize OpenAI client for character identification"""
        try:
            import openai
            from .ai_game_detector import OpenAIClient

            api_key = self.ai_config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                if self.debug:
                    print("⚠️  OpenAI API key not found, using mock client")
                return MockCharacterIdentifier()

            return OpenAICharacterClient(
                api_key=api_key,
                model=self.ai_config.get("model", "gpt-4"),
                max_tokens=self.ai_config.get("max_tokens", 2000),
                temperature=self.ai_config.get("temperature", 0.3),
                timeout=self.ai_config.get("timeout", 30)
            )

        except ImportError:
            if self.debug:
                print("⚠️  OpenAI library not available, using mock client")
            return MockCharacterIdentifier()

    def _initialize_anthropic_client(self):
        """Initialize Anthropic/Claude client for character identification"""
        try:
            import anthropic
            from .ai_game_detector import AnthropicClient

            api_key = self.ai_config.get("api_key") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
            if not api_key:
                if self.debug:
                    print("⚠️  Anthropic API key not found, using mock client")
                return MockCharacterIdentifier()

            return AnthropicCharacterClient(
                api_key=api_key,
                model=self.ai_config.get("model", "claude-3-sonnet-20240229"),
                max_tokens=self.ai_config.get("max_tokens", 2000),
                temperature=self.ai_config.get("temperature", 0.3),
                timeout=self.ai_config.get("timeout", 30)
            )

        except ImportError:
            if self.debug:
                print("⚠️  Anthropic library not available, using mock client")
            return MockCharacterIdentifier()

    def _initialize_openrouter_client(self):
        """Initialize OpenRouter client for character identification"""
        try:
            import openai

            api_key = self.ai_config.get("api_key") or os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                if self.debug:
                    print("⚠️  OpenRouter API key not found, using mock client")
                return MockCharacterIdentifier()

            return OpenRouterCharacterClient(
                api_key=api_key,
                model=self.ai_config.get("model", "anthropic/claude-3.5-sonnet"),
                max_tokens=self.ai_config.get("max_tokens", 2000),
                temperature=self.ai_config.get("temperature", 0.3),
                timeout=self.ai_config.get("timeout", 30)
            )

        except ImportError:
            if self.debug:
                print("⚠️  OpenAI library not available for OpenRouter, using mock client")
            return MockCharacterIdentifier()

    def _initialize_local_client(self):
        """Initialize local LLM client for character identification"""
        # TODO: Implement local LLM client
        if self.debug:
            print("⚠️  Local LLM not implemented yet, using mock client")
        return MockCharacterIdentifier()

    def identify_characters(self, sections: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        OPTIMIZED METHOD: Multi-stage character identification with chunking and filtering

        Args:
            sections: List of extracted novel sections
            metadata: Novel metadata (title, author, etc.)

        Returns:
            Dictionary with detailed character identification results
        """
        self.logger.info("🎭 Starting OPTIMIZED character identification")

        # Step 1: Combine and save full text (no truncation!)
        combined_text = self._combine_section_text_optimized(sections)

        if len(combined_text) < 100:
            return {
                "characters": [],
                "total_characters": 0,
                "processing_stages": {
                    "error": "Insufficient text content for character identification"
                }
            }

        # Step 2: Chunked Character Discovery (multiple AI calls on chunks)
        self.logger.info("📖 Step 1: Chunked character discovery across full novel")
        discovery_result = self._chunked_character_discovery(combined_text, metadata)

        # Step 3: Local filtering by mention frequency
        self.logger.info("🔍 Step 2: Local filtering by mention frequency")
        filtered_candidates = self._filter_candidates_by_mentions(
            discovery_result["all_candidates"], combined_text
        )

        # Step 4: Targeted character analysis for top candidates
        self.logger.info("🎯 Step 3: Targeted analysis of top candidates")
        final_characters = self._targeted_character_analysis(
            filtered_candidates, combined_text, metadata
        )

        # Compile final results
        final_result = {
            "characters": final_characters,
            "total_characters": len(final_characters),
            "processing_stages": {
                "discovery": discovery_result,
                "filtering": {
                    "candidates_found": len(discovery_result["all_candidates"]),
                    "candidates_filtered": len(filtered_candidates),
                    "filter_ratio": len(filtered_candidates) / max(len(discovery_result["all_candidates"]), 1)
                },
                "analysis": {
                    "characters_analyzed": len(filtered_candidates),
                    "characters_confirmed": len(final_characters)
                }
            },
            "metadata": {
                "novel_title": metadata.get("book_title", "Unknown"),
                "author": metadata.get("author", "Unknown"),
                "total_text_length": len(combined_text),
                "sections_analyzed": len(sections),
                "analysis_method": "optimized_chunked_discovery",
                "chunks_processed": discovery_result.get("chunks_processed", 0),
                "api_calls_made": discovery_result.get("api_calls_made", 0) + len(filtered_candidates)
            }
        }

        self.logger.info(f"🎭 OPTIMIZED character identification complete: {final_result['total_characters']} characters found")
        self.logger.info(f"📊 Processing stats: {discovery_result.get('chunks_processed', 0)} chunks, {final_result['metadata']['api_calls_made']} API calls")
        return final_result

    def _combine_section_text(self, sections: List[Dict[str, Any]]) -> str:
        """Combine text from all sections for analysis - ENTIRE NOVEL"""
        combined_text = ""

        self.logger.info(f"📖 Combining text from {len(sections)} sections for full novel analysis")

        for i, section in enumerate(sections):
            content = section.get("content", "")
            if content and content.strip():
                combined_text += content + "\n\n"

                # Log progress for large novels
                if i % 50 == 0 and i > 0:
                    self.logger.info(f"📖 Processed {i}/{len(sections)} sections ({len(combined_text):,} characters so far)")

        self.logger.info(f"📖 Full novel text combined: {len(combined_text):,} characters from {len(sections)} sections")

        # For character identification, we want the ENTIRE novel
        # Only limit if it's extremely large (over 200k characters)
        if len(combined_text) > self.max_content_length:
            self.logger.warning(f"📖 Novel is very large ({len(combined_text):,} chars), truncating to {self.max_content_length:,} chars for AI analysis")
            combined_text = combined_text[:self.max_content_length]
        else:
            self.logger.info(f"📖 Using complete novel text ({len(combined_text):,} characters) for character analysis")

        return combined_text

    def _combine_section_text_optimized(self, sections: List[Dict[str, Any]]) -> str:
        """MEMORY OPTIMIZED: Combine text from sections with memory management"""
        combined_text = ""

        self.logger.info(f"📖 Combining text from {len(sections)} sections for FULL novel analysis")

        for i, section in enumerate(sections):
            content = section.get("content", "")
            if content and content.strip():
                combined_text += content + "\n\n"

                # Log progress for large novels
                if i % 50 == 0 and i > 0:
                    self.logger.info(f"📖 Processed {i}/{len(sections)} sections ({len(combined_text):,} characters so far)")

                # MEMORY SAFETY: Check if we're approaching memory limits
                if len(combined_text) > self.max_content_length:
                    self.logger.warning(f"📖 Novel exceeds memory limit ({len(combined_text):,} chars > {self.max_content_length:,})")
                    self.logger.warning(f"📖 Truncating at section {i+1}/{len(sections)} to prevent memory issues")
                    combined_text = combined_text[:self.max_content_length]
                    break

        self.logger.info(f"📖 Full novel text combined: {len(combined_text):,} characters from {min(i+1, len(sections))} sections")

        # Log memory optimization status
        if len(combined_text) >= self.max_content_length:
            self.logger.info(f"🧠 Memory optimization: Using {self.max_content_length:,} chars (truncated for memory efficiency)")
        else:
            self.logger.info(f"📖 Using complete novel text ({len(combined_text):,} characters) for analysis")

        return combined_text

    def _chunked_character_discovery(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """OPTIMIZED: Discover characters using chunked processing with progress updates"""

        # Split text into overlapping chunks
        chunks = self._create_text_chunks(text)
        all_candidates = []
        api_calls_made = 0

        self.logger.info(f"📖 Processing {len(chunks)} chunks for character discovery")

        for i, chunk in enumerate(chunks):
            chunk_num = i + 1
            self.logger.info(f"📖 Processing chunk {chunk_num}/{len(chunks)} ({len(chunk):,} characters)")

            # Send progress update to UI (if callback available)
            if hasattr(self, 'progress_callback') and self.progress_callback:
                self.progress_callback('discovery', 'active', {
                    'chunks_processed': i,
                    'total_chunks': len(chunks),
                    'candidates_found': len(all_candidates),
                    'current_chunk': chunk_num,
                    'chunk_size': len(chunk)
                })

            try:
                # Build discovery prompt for this chunk
                prompt = self._build_chunk_discovery_prompt(chunk, metadata, chunk_num, len(chunks))

                # Get AI analysis for this chunk
                self.logger.info(f"🤖 Sending chunk {chunk_num} to AI for analysis...")
                ai_response = self.ai_client.discover_characters_comprehensive(prompt)
                api_calls_made += 1

                # Parse response
                if isinstance(ai_response, str):
                    result = json.loads(ai_response)
                else:
                    result = ai_response

                # Extract candidates from this chunk
                chunk_candidates = result.get("characters", [])
                all_candidates.extend(chunk_candidates)

                self.logger.info(f"✅ Chunk {chunk_num} found {len(chunk_candidates)} candidates (total: {len(all_candidates)})")

                # Send updated progress
                if hasattr(self, 'progress_callback') and self.progress_callback:
                    self.progress_callback('discovery', 'active', {
                        'chunks_processed': chunk_num,
                        'total_chunks': len(chunks),
                        'candidates_found': len(all_candidates),
                        'current_chunk': chunk_num,
                        'chunk_candidates': len(chunk_candidates)
                    })

            except Exception as e:
                self.logger.error(f"❌ Chunk {chunk_num} processing failed: {e}")
                # Continue with other chunks
                continue

        # Deduplicate candidates by name (case-insensitive)
        unique_candidates = self._deduplicate_candidates(all_candidates)

        self.logger.info(f"🎯 Discovery complete: {len(all_candidates)} total candidates, {len(unique_candidates)} unique")

        # Send completion update
        if hasattr(self, 'progress_callback') and self.progress_callback:
            self.progress_callback('discovery', 'completed', {
                'chunks_processed': len(chunks),
                'total_chunks': len(chunks),
                'candidates_found': len(unique_candidates),
                'total_candidates': len(all_candidates)
            })

        return {
            "all_candidates": unique_candidates,
            "chunks_processed": len(chunks),
            "api_calls_made": api_calls_made,
            "total_candidates": len(all_candidates),
            "unique_candidates": len(unique_candidates)
        }

    def _comprehensive_character_discovery(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        First pass: Comprehensive character discovery
        Read through entire novel to find ALL characters with names, descriptions, ages, relationships
        """

        self.logger.info("📖 Comprehensive character discovery - analyzing entire novel")

        # Build comprehensive discovery prompt
        prompt = self._build_comprehensive_discovery_prompt(text, metadata)

        # Get AI analysis
        try:
            ai_response = self.ai_client.discover_characters_comprehensive(prompt)

            # Parse response
            if isinstance(ai_response, str):
                result = json.loads(ai_response)
            else:
                result = ai_response

            # Validate response structure
            if not isinstance(result, dict) or "characters" not in result:
                raise ValueError("Invalid AI response structure")

            characters = result["characters"]
            self.logger.info(f"📖 Discovery found {len(characters)} characters")

            return {
                "characters": characters,
                "total_found": len(characters),
                "confidence": result.get("confidence", 0.5),
                "reasoning": result.get("reasoning", "AI comprehensive character discovery"),
                "status": "completed"
            }

        except Exception as e:
            self.logger.error(f"Comprehensive character discovery failed: {e}")
            return self._fallback_comprehensive_discovery(text)

    def _enhance_character_profiles(self, text: str, characters: List[Dict], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Second pass: Character enhancement and validation
        Re-read novel to add more details and validate character profiles
        """

        self.logger.info(f"🔍 Enhancing profiles for {len(characters)} characters")

        if not characters:
            return {
                "enhanced_characters": [],
                "enhancements_made": 0,
                "validation_confidence": 0.0,
                "status": "no_characters_to_enhance"
            }

        # Build enhancement prompt
        prompt = self._build_character_enhancement_prompt(text, characters, metadata)

        # Get AI enhancement
        try:
            ai_response = self.ai_client.enhance_character_profiles(prompt)

            # Parse response
            if isinstance(ai_response, str):
                result = json.loads(ai_response)
            else:
                result = ai_response

            # Validate response structure
            if not isinstance(result, dict) or "enhanced_characters" not in result:
                raise ValueError("Invalid AI enhancement response structure")

            enhanced_characters = result["enhanced_characters"]
            enhancements_made = len([char for char in enhanced_characters if char.get("enhanced", False)])

            self.logger.info(f"🔍 Enhanced {enhancements_made} character profiles")

            return {
                "enhanced_characters": enhanced_characters,
                "enhancements_made": enhancements_made,
                "validation_confidence": result.get("confidence", 0.5),
                "reasoning": result.get("reasoning", "AI character profile enhancement"),
                "status": "completed"
            }

        except Exception as e:
            self.logger.error(f"Character enhancement failed: {e}")
            return self._fallback_character_enhancement(characters)

    def _first_pass_character_discovery(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """First pass: Discover potential characters in the text"""

        self.logger.info("🔍 First pass: Character discovery")

        # Build discovery prompt
        prompt = self._build_discovery_prompt(text, metadata)

        # Get AI analysis
        try:
            ai_response = self.ai_client.discover_characters(prompt)

            # Parse response
            if isinstance(ai_response, str):
                result = json.loads(ai_response)
            else:
                result = ai_response

            # Validate response structure
            if not isinstance(result, dict) or "potential_characters" not in result:
                raise ValueError("Invalid AI response structure")

            return {
                "potential_characters": result["potential_characters"],
                "total_found": len(result["potential_characters"]),
                "confidence": result.get("confidence", 0.5),
                "reasoning": result.get("reasoning", "AI character discovery"),
                "status": "completed"
            }

        except Exception as e:
            self.logger.error(f"Character discovery failed: {e}")
            return self._fallback_character_discovery(text)

    def _second_pass_character_validation(self, text: str, potential_characters: List[Dict], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Second pass: Validate and filter potential characters"""

        self.logger.info(f"✅ Second pass: Validating {len(potential_characters)} potential characters")

        if not potential_characters:
            return {
                "validated_characters": [],
                "false_positives_removed": 0,
                "validation_confidence": 0.0,
                "status": "no_characters_to_validate"
            }

        # Build validation prompt
        prompt = self._build_validation_prompt(text, potential_characters, metadata)

        # Get AI validation
        try:
            ai_response = self.ai_client.validate_characters(prompt)

            # Parse response
            if isinstance(ai_response, str):
                result = json.loads(ai_response)
            else:
                result = ai_response

            # Validate response structure
            if not isinstance(result, dict) or "validated_characters" not in result:
                raise ValueError("Invalid AI validation response structure")

            validated_characters = result["validated_characters"]
            false_positives = len(potential_characters) - len(validated_characters)

            return {
                "validated_characters": validated_characters,
                "false_positives_removed": false_positives,
                "validation_confidence": result.get("confidence", 0.5),
                "reasoning": result.get("reasoning", "AI character validation"),
                "status": "completed"
            }

        except Exception as e:
            self.logger.error(f"Character validation failed: {e}")
            return self._fallback_character_validation(potential_characters)

    def _build_discovery_prompt(self, text: str, metadata: Dict[str, Any]) -> str:
        """Build AI prompt for character discovery"""

        title = metadata.get("book_title", "Unknown Novel")
        author = metadata.get("author", "Unknown Author")

        return f"""
TASK: Character Discovery in Novel Text

NOVEL INFORMATION:
Title: {title}
Author: {author}
Text Length: {len(text)} characters

INSTRUCTIONS:
Analyze the following novel text and identify ALL potential characters (people) mentioned in the story. Be comprehensive and aggressive in finding character names.

PRIORITY TARGETS (FIND THESE FIRST):
1. **Proper names** - Any capitalized words that could be person names (John, Mary, Gandalf, Aragorn, etc.)
2. **Names with titles** - Lord Blackwood, Captain Smith, Dr. Johnson, etc.
3. **Unique character names** - Fantasy/sci-fi names, unusual names, made-up names
4. **Characters with dialogue** - Anyone who speaks in the text
5. **Characters performing actions** - People who do things, move, think, etc.

SECONDARY TARGETS:
6. Characters described with physical traits
7. Characters mentioned by others
8. Minor characters who appear briefly
9. Characters referred to by relationship (if they have names elsewhere)

WHAT TO EXCLUDE:
1. Places, locations, cities, countries (unless clearly a person's name)
2. Objects, items, weapons, tools
3. Concepts, ideas, emotions
4. Organizations, groups (unless referring to specific people)
5. Animals (unless they are anthropomorphic characters)
6. Generic titles without names (e.g., "the king", "the woman", "her son" - UNLESS they have actual names)

BE AGGRESSIVE: If you see a capitalized word that could possibly be a person's name, include it. It's better to find too many potential characters than to miss obvious ones.

TEXT TO ANALYZE:
{text}

Please respond with a JSON object containing:
{{
    "potential_characters": [
        {{
            "name": "Character Name",
            "mentions": 5,
            "context": "Brief context where character appears",
            "confidence": 0.8,
            "evidence": "Quote or description showing this is a character"
        }}
    ],
    "confidence": 0.85,
    "reasoning": "Explanation of character identification approach"
}}

Focus on accuracy over completeness. It's better to miss a minor character than to include false positives.
"""

    def _build_comprehensive_discovery_prompt(self, text: str, metadata: Dict[str, Any]) -> str:
        """Build AI prompt for comprehensive character discovery"""

        title = metadata.get("book_title", "Unknown Novel")
        author = metadata.get("author", "Unknown Author")

        return f"""
TASK: Comprehensive Character Discovery in Novel

NOVEL INFORMATION:
Title: {title}
Author: {author}
Text Length: {len(text)} characters

INSTRUCTIONS:
Read through this entire novel text carefully and create a comprehensive character roster. Find EVERY character mentioned, no matter how briefly.

FOR EACH CHARACTER, EXTRACT:
1. **Name** - Full name, nickname, or title
2. **Age** - Approximate age if mentioned or can be inferred
3. **Physical Description** - Any physical traits mentioned
4. **Role/Relationship** - Their role in the story or relationship to other characters
5. **Personality Traits** - Any personality characteristics mentioned
6. **First Appearance** - Where they first appear in the text
7. **Importance** - Major, supporting, or minor character

SEARCH CRITERIA (BE THOROUGH):
✅ **Named Characters**: Any proper names (John, Mary, Gandalf, Sauron, etc.)
✅ **Titled Characters**: Lord Blackwood, Captain Smith, Dr. Johnson, etc.
✅ **Characters with Dialogue**: Anyone who speaks
✅ **Characters with Actions**: Anyone who performs actions
✅ **Characters Described**: Anyone with physical or personality descriptions
✅ **Characters Mentioned**: Anyone referenced by others
✅ **Family Members**: Parents, children, siblings with names
✅ **Minor Characters**: Shopkeepers, guards, servants with names
✅ **Fantasy Names**: Unusual or made-up character names

❌ **EXCLUDE**: Generic references like "the woman", "her son", "the guard" UNLESS they have actual names

NOVEL TEXT TO ANALYZE:
{text}

Please respond with a JSON object:
{{
    "characters": [
        {{
            "name": "Character Full Name",
            "age": "approximate age or 'unknown'",
            "physical_description": "any physical traits mentioned",
            "role": "protagonist/antagonist/supporting/minor",
            "relationship": "relationship to other characters",
            "personality": "personality traits mentioned",
            "first_appearance": "brief context of first appearance",
            "importance": "major/supporting/minor",
            "mentions": 5,
            "confidence": 0.9
        }}
    ],
    "confidence": 0.85,
    "reasoning": "Explanation of discovery approach and thoroughness"
}}

BE COMPREHENSIVE: Read carefully and find ALL named characters, even minor ones mentioned briefly.
"""

    def _build_character_enhancement_prompt(self, text: str, characters: List[Dict], metadata: Dict[str, Any]) -> str:
        """Build AI prompt for character profile enhancement"""

        title = metadata.get("book_title", "Unknown Novel")
        character_list = "\n".join([f"- {char['name']}: {char.get('role', 'Unknown role')}"
                                   for char in characters])

        return f"""
TASK: Character Profile Enhancement for Novel "{title}"

DISCOVERED CHARACTERS:
{character_list}

INSTRUCTIONS:
Re-read the novel text and enhance each character's profile with additional details found in the text.

FOR EACH CHARACTER, ADD/ENHANCE:
1. **Additional Physical Details** - More complete physical description
2. **Personality Expansion** - More personality traits and characteristics
3. **Relationships** - Connections to other characters
4. **Character Arc** - How they change or develop
5. **Key Quotes** - Important things they say
6. **Key Actions** - Important things they do
7. **Background** - Any backstory or history mentioned
8. **Validation** - Confirm this is actually a character (not a place/object)

NOVEL TEXT FOR REFERENCE:
{text[:3000]}...

Please respond with a JSON object:
{{
    "enhanced_characters": [
        {{
            "name": "Character Name",
            "age": "age or age range",
            "physical_description": "complete physical description",
            "personality": "comprehensive personality profile",
            "role": "protagonist/antagonist/supporting/minor",
            "relationships": ["relationship1", "relationship2"],
            "character_arc": "how they develop/change",
            "key_quotes": ["quote1", "quote2"],
            "key_actions": ["action1", "action2"],
            "background": "backstory or history",
            "importance": "major/supporting/minor",
            "confidence": 0.9,
            "enhanced": true,
            "validation_status": "confirmed_character"
        }}
    ],
    "confidence": 0.85,
    "reasoning": "Enhancement approach and validation decisions"
}}

VALIDATE: Ensure each entry is actually a character (person) and not a place, object, or concept.
"""

    def _build_validation_prompt(self, text: str, potential_characters: List[Dict], metadata: Dict[str, Any]) -> str:
        """Build AI prompt for character validation"""

        title = metadata.get("book_title", "Unknown Novel")
        character_list = "\n".join([f"- {char['name']}: {char.get('context', 'No context')}"
                                   for char in potential_characters])

        return f"""
TASK: Character Validation for Novel "{title}"

POTENTIAL CHARACTERS TO VALIDATE:
{character_list}

INSTRUCTIONS:
Review each potential character and determine if they are actually characters (people) in the story.

VALIDATION CRITERIA:
✅ KEEP if the entity is:
- A person/human character in the story
- An anthropomorphic character (talking animals, etc.)
- A character with dialogue, actions, or personality
- Someone who plays a role in the narrative

❌ REMOVE if the entity is:
- A place, location, or geographical feature
- An object, item, or concept
- An organization or group name
- A title without a specific person
- A false positive from the discovery phase

NOVEL TEXT FOR REFERENCE:
{text[:2000]}...

Please respond with a JSON object:
{{
    "validated_characters": [
        {{
            "name": "Character Name",
            "character_type": "protagonist|antagonist|supporting|minor",
            "confidence": 0.9,
            "validation_reason": "Why this is confirmed as a character",
            "role_in_story": "Brief description of their role"
        }}
    ],
    "confidence": 0.85,
    "reasoning": "Overall validation approach and decisions made"
}}

Be strict in validation - only include entities you are confident are actual characters.
"""

    def _fallback_character_discovery(self, text: str) -> Dict[str, Any]:
        """Fallback character discovery using regex patterns"""

        self.logger.warning("Using fallback character discovery")

        # Simple regex-based character discovery
        potential_characters = []

        # Find proper nouns that might be characters
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', text)

        # Count mentions and filter
        name_counts = {}
        for name in proper_nouns:
            if len(name) > 2 and name not in ['The', 'And', 'But', 'For', 'Chapter', 'Page']:
                name_counts[name] = name_counts.get(name, 0) + 1

        # Keep names mentioned multiple times
        for name, count in name_counts.items():
            if count >= self.min_character_mentions:
                potential_characters.append({
                    "name": name,
                    "mentions": count,
                    "context": "Fallback discovery - proper noun with multiple mentions",
                    "confidence": 0.5,
                    "evidence": f"Mentioned {count} times in text"
                })

        return {
            "potential_characters": potential_characters,
            "total_found": len(potential_characters),
            "confidence": 0.5,
            "reasoning": "Fallback regex-based character discovery",
            "status": "fallback_completed"
        }

    def _fallback_character_validation(self, potential_characters: List[Dict]) -> Dict[str, Any]:
        """Fallback character validation using simple heuristics"""

        self.logger.warning("Using fallback character validation")

        validated_characters = []

        # Simple validation: keep characters with high mention counts
        for char in potential_characters:
            mentions = char.get("mentions", 0)
            confidence = char.get("confidence", 0.5)

            # Keep if mentioned frequently or high confidence
            if mentions >= self.min_character_mentions or confidence >= self.confidence_threshold:
                validated_characters.append({
                    "name": char["name"],
                    "character_type": "unknown",
                    "confidence": confidence,
                    "validation_reason": f"Fallback validation - {mentions} mentions",
                    "role_in_story": "Unknown role"
                })

        false_positives = len(potential_characters) - len(validated_characters)

        return {
            "validated_characters": validated_characters,
            "false_positives_removed": false_positives,
            "validation_confidence": 0.5,
            "reasoning": "Fallback heuristic-based validation",
            "status": "fallback_completed"
        }

    def _fallback_comprehensive_discovery(self, text: str) -> Dict[str, Any]:
        """Fallback comprehensive character discovery using enhanced regex patterns"""

        self.logger.warning(f"Using fallback comprehensive character discovery on {len(text):,} characters")

        characters = []

        # Enhanced regex patterns for character names
        name_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Proper names (John, Mary Smith)
            r'\b(Lord|Lady|Sir|Dr|Captain|King|Queen|Prince|Princess|Master|Mistress)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Titled characters
            r'"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"',  # Names in quotes
            r'\b([A-Z][a-z]*[aeiou][a-z]*)\b',  # Fantasy-style names (often end in vowels)
            r'\b([A-Z][a-z]+(?:\'[A-Z][a-z]+)*)\b',  # Names with apostrophes (D'Artagnan)
        ]

        # Common words to exclude (not character names)
        exclude_words = {
            'The', 'And', 'But', 'For', 'Chapter', 'Page', 'Book', 'Part', 'Section',
            'He', 'She', 'It', 'They', 'We', 'You', 'I', 'This', 'That', 'These', 'Those',
            'When', 'Where', 'Why', 'How', 'What', 'Who', 'Which', 'Then', 'Now', 'Here',
            'There', 'Yes', 'No', 'Not', 'All', 'Some', 'Many', 'Few', 'One', 'Two', 'Three',
            'First', 'Second', 'Third', 'Last', 'Next', 'Before', 'After', 'During', 'While',
            'Good', 'Bad', 'Great', 'Small', 'Large', 'Big', 'Little', 'Old', 'New', 'Young'
        }

        # Find all potential character names
        potential_names = set()
        self.logger.info("📖 Scanning for character names with enhanced patterns...")

        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle titled characters (Lord, Lady, etc.)
                    if len(match) == 2:
                        name = f"{match[0]} {match[1]}".strip()
                    else:
                        name = ' '.join(filter(None, match)).strip()
                else:
                    name = match.strip()

                # Filter out obvious non-names
                if (len(name) > 2 and
                    name not in exclude_words and
                    not name.isupper() and  # Skip ALL CAPS words
                    not name.isdigit() and  # Skip numbers
                    not any(char.isdigit() for char in name)):  # Skip words with numbers
                    potential_names.add(name)

        self.logger.info(f"📖 Found {len(potential_names)} potential character names")

        # Count mentions and create character profiles
        for name in potential_names:
            # Count exact matches (case insensitive)
            count = len(re.findall(rf'\b{re.escape(name)}\b', text, re.IGNORECASE))

            if count >= self.min_character_mentions:
                # Determine importance based on mention frequency
                if count >= 20:
                    importance = "major"
                    role = "protagonist/antagonist"
                elif count >= 8:
                    importance = "supporting"
                    role = "supporting"
                else:
                    importance = "minor"
                    role = "minor"

                characters.append({
                    "name": name,
                    "age": "unknown",
                    "physical_description": "Not specified in fallback analysis",
                    "role": role,
                    "relationship": "unknown",
                    "personality": "Not specified in fallback analysis",
                    "first_appearance": f"Mentioned {count} times throughout the novel",
                    "importance": importance,
                    "mentions": count,
                    "confidence": 0.7 if count >= 10 else 0.6
                })

        # Sort by mention count (most mentioned first)
        characters.sort(key=lambda x: x["mentions"], reverse=True)

        self.logger.info(f"📖 Fallback discovery found {len(characters)} characters")

        return {
            "characters": characters,
            "total_found": len(characters),
            "confidence": 0.7,
            "reasoning": f"Fallback regex-based comprehensive discovery from {len(text):,} characters",
            "status": "fallback_completed"
        }

    def _fallback_character_enhancement(self, characters: List[Dict]) -> Dict[str, Any]:
        """Fallback character enhancement using simple heuristics"""

        self.logger.warning("Using fallback character enhancement")

        enhanced_characters = []

        for char in characters:
            enhanced_char = char.copy()
            enhanced_char.update({
                "physical_description": enhanced_char.get("physical_description", "Not specified"),
                "personality": "Not specified in fallback analysis",
                "relationships": [],
                "character_arc": "Not analyzed in fallback mode",
                "key_quotes": [],
                "key_actions": [],
                "background": "Not specified",
                "enhanced": False,
                "validation_status": "fallback_validated"
            })
            enhanced_characters.append(enhanced_char)

        return {
            "enhanced_characters": enhanced_characters,
            "enhancements_made": 0,
            "validation_confidence": 0.6,
            "reasoning": "Fallback enhancement - limited analysis",
            "status": "fallback_completed"
        }

    def _create_text_chunks(self, text: str) -> List[str]:
        """MEMORY OPTIMIZED: Create smaller chunks with minimal overlap"""
        chunks = []
        text_length = len(text)

        # MEMORY OPTIMIZATION: Reduce chunk size and overlap
        optimized_chunk_size = 120000  # Reduced from 200k to 120k
        optimized_overlap = 5000       # Reduced from 20k to 5k

        self.logger.info(f"📦 Creating memory-optimized chunks from {text_length:,} characters")
        self.logger.info(f"📦 Chunk size: {optimized_chunk_size:,}, Overlap: {optimized_overlap:,}")

        if text_length <= optimized_chunk_size:
            # Text is small enough to process as single chunk
            self.logger.info(f"📦 Text fits in single chunk ({text_length:,} chars)")
            return [text]

        start = 0
        chunk_count = 0
        max_chunks = 20  # SAFETY LIMIT: Never create more than 20 chunks

        while start < text_length and chunk_count < max_chunks:
            end = min(start + optimized_chunk_size, text_length)

            # Try to break at sentence boundaries to avoid cutting mid-sentence
            if end < text_length:
                # Look for sentence endings within the last 500 characters (reduced from 1000)
                search_start = max(end - 500, start)
                sentence_endings = []
                for i in range(search_start, end):
                    if text[i] in '.!?':
                        sentence_endings.append(i)

                if sentence_endings:
                    # Use the last sentence ending
                    end = sentence_endings[-1] + 1

            chunk = text[start:end]
            chunks.append(chunk)
            chunk_count += 1

            self.logger.info(f"📦 Created chunk {chunk_count}: {len(chunk):,} chars (start: {start:,}, end: {end:,})")

            # FIXED: Prevent infinite loop by ensuring we always advance
            if end >= text_length:
                # We've reached the end, break out
                break

            # Move start position with minimal overlap, but ensure we advance
            next_start = end - optimized_overlap
            if next_start <= start:
                # If overlap would cause us to go backwards or stay in place, just advance
                next_start = start + optimized_chunk_size

            start = next_start

            # Safety check: if we're not making progress, break
            if start >= text_length:
                break

        # Safety warning if we hit the chunk limit
        if chunk_count >= max_chunks and start < text_length:
            self.logger.warning(f"⚠️  Hit safety limit of {max_chunks} chunks, some text may be skipped")
            self.logger.warning(f"⚠️  Processed {start:,}/{text_length:,} characters ({start/text_length*100:.1f}%)")

        total_chunk_chars = sum(len(chunk) for chunk in chunks)
        memory_multiplier = total_chunk_chars / text_length
        self.logger.info(f"📦 Created {len(chunks)} chunks, total chars: {total_chunk_chars:,} (memory multiplier: {memory_multiplier:.2f}x)")

        return chunks

    def _build_chunk_discovery_prompt(self, chunk: str, metadata: Dict[str, Any],
                                    chunk_num: int, total_chunks: int) -> str:
        """Build AI prompt for character discovery in a text chunk"""

        title = metadata.get("book_title", "Unknown Novel")
        author = metadata.get("author", "Unknown Author")

        return f"""
TASK: Character Discovery in Novel Text Chunk

NOVEL INFORMATION:
Title: {title}
Author: {author}
Chunk: {chunk_num}/{total_chunks}
Chunk Length: {len(chunk)} characters

INSTRUCTIONS:
Analyze this chunk of novel text and identify ALL potential characters (people) mentioned.
This is chunk {chunk_num} of {total_chunks}, so focus on finding characters in this section.

FIND THESE CHARACTER TYPES:
✅ **Named Characters**: Any proper names (John, Mary, Gandalf, Sauron, etc.)
✅ **Titled Characters**: Lord Blackwood, Captain Smith, Dr. Johnson, etc.
✅ **Characters with Dialogue**: Anyone who speaks
✅ **Characters with Actions**: Anyone who performs actions
✅ **Characters Described**: Anyone with physical descriptions
✅ **Fantasy Names**: Unusual or made-up character names
✅ **Minor Characters**: Briefly mentioned characters with names

❌ **EXCLUDE**: Generic references like "the woman", "her son", "the guard" without names

FOR EACH CHARACTER FOUND:
- Extract their name
- Note any physical description
- Note their role or relationship
- Count approximate mentions in this chunk
- Assess confidence this is a real character

TEXT CHUNK TO ANALYZE:
{chunk[:50000]}{"..." if len(chunk) > 50000 else ""}

Respond with JSON:
{{
    "characters": [
        {{
            "name": "Character Name",
            "physical_description": "any description found",
            "role": "their role or relationship",
            "chunk_mentions": 3,
            "confidence": 0.9,
            "evidence": "brief quote showing this is a character"
        }}
    ],
    "chunk_summary": "brief summary of this chunk's content"
}}

BE THOROUGH: Find all named characters in this chunk, even minor ones.
"""

    def _deduplicate_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Remove duplicate candidates by name (case-insensitive)"""
        seen_names = set()
        unique_candidates = []

        for candidate in candidates:
            name = candidate.get("name", "").strip().lower()
            if name and name not in seen_names:
                seen_names.add(name)
                unique_candidates.append(candidate)

        return unique_candidates

    def _filter_candidates_by_mentions(self, candidates: List[Dict], full_text: str) -> List[Dict]:
        """Filter candidates by counting mentions in full text with progress updates"""

        self.logger.info(f"🔍 Filtering {len(candidates)} candidates by mention frequency")

        # Send initial progress update
        if hasattr(self, 'progress_callback') and self.progress_callback:
            self.progress_callback('filtering', 'active', {
                'candidates_to_filter': len(candidates),
                'candidates_filtered': 0,
                'filter_ratio': 0.0
            })

        filtered_candidates = []
        full_text_lower = full_text.lower()

        for i, candidate in enumerate(candidates):
            name = candidate.get("name", "").strip()
            if not name:
                continue

            # Count mentions in full text (case-insensitive)
            name_lower = name.lower()
            mention_count = full_text_lower.count(name_lower)

            # Also try variations (first name only, last name only)
            name_parts = name.split()
            if len(name_parts) > 1:
                for part in name_parts:
                    if len(part) > 2:  # Skip short words like "of", "the"
                        part_count = full_text_lower.count(part.lower())
                        mention_count = max(mention_count, part_count)

            # Update candidate with mention count
            candidate["total_mentions"] = mention_count
            candidate["mention_frequency"] = mention_count / len(full_text) * 100000  # per 100k chars

            # Filter by minimum mentions
            if mention_count >= self.min_mentions_for_analysis:
                filtered_candidates.append(candidate)

            # Send progress update every 10 candidates
            if (i + 1) % 10 == 0 or i == len(candidates) - 1:
                if hasattr(self, 'progress_callback') and self.progress_callback:
                    filter_ratio = len(filtered_candidates) / max(i + 1, 1)
                    self.progress_callback('filtering', 'active', {
                        'candidates_processed': i + 1,
                        'candidates_to_filter': len(candidates),
                        'candidates_filtered': len(filtered_candidates),
                        'filter_ratio': filter_ratio,
                        'current_candidate': name
                    })

        # Sort by mention count (descending)
        filtered_candidates.sort(key=lambda x: x.get("total_mentions", 0), reverse=True)

        self.logger.info(f"🔍 Filtered to {len(filtered_candidates)} candidates with {self.min_mentions_for_analysis}+ mentions")

        # Send completion update
        if hasattr(self, 'progress_callback') and self.progress_callback:
            final_ratio = len(filtered_candidates) / max(len(candidates), 1)
            self.progress_callback('filtering', 'completed', {
                'candidates_processed': len(candidates),
                'candidates_filtered': len(filtered_candidates),
                'filter_ratio': final_ratio
            })

        return filtered_candidates

    def _targeted_character_analysis(self, candidates: List[Dict], full_text: str,
                                   metadata: Dict[str, Any]) -> List[Dict]:
        """Perform targeted analysis on filtered candidates with progress updates"""

        self.logger.info(f"🎯 Performing targeted analysis on {len(candidates)} candidates")

        # Send initial progress update
        if hasattr(self, 'progress_callback') and self.progress_callback:
            self.progress_callback('analysis', 'active', {
                'candidates_to_analyze': len(candidates),
                'characters_confirmed': 0,
                'current_character': 'Starting analysis...'
            })

        final_characters = []

        for i, candidate in enumerate(candidates):
            name = candidate.get("name", "")
            mentions = candidate.get("total_mentions", 0)

            self.logger.info(f"🎯 Analyzing character {i+1}/{len(candidates)}: {name} ({mentions} mentions)")

            # Send progress update for current character
            if hasattr(self, 'progress_callback') and self.progress_callback:
                self.progress_callback('analysis', 'active', {
                    'candidates_analyzed': i,
                    'candidates_to_analyze': len(candidates),
                    'characters_confirmed': len(final_characters),
                    'current_character': name,
                    'current_mentions': mentions
                })

            try:
                # Build targeted analysis prompt
                prompt = self._build_targeted_analysis_prompt(candidate, full_text, metadata)

                # Get AI analysis
                self.logger.info(f"🤖 Sending {name} to AI for detailed analysis...")
                ai_response = self.ai_client.enhance_character_profiles(prompt)

                # Parse response
                if isinstance(ai_response, str):
                    result = json.loads(ai_response)
                else:
                    result = ai_response

                # Extract enhanced character data
                enhanced_character = result.get("character", {})
                if enhanced_character and enhanced_character.get("is_valid_character", True):
                    # Merge with original candidate data
                    enhanced_character.update({
                        "total_mentions": mentions,
                        "mention_frequency": candidate.get("mention_frequency", 0),
                        "discovery_confidence": candidate.get("confidence", 0.5)
                    })
                    final_characters.append(enhanced_character)
                    self.logger.info(f"✅ Confirmed character: {name}")
                else:
                    self.logger.info(f"❌ Rejected candidate: {name}")

                # Send updated progress
                if hasattr(self, 'progress_callback') and self.progress_callback:
                    self.progress_callback('analysis', 'active', {
                        'candidates_analyzed': i + 1,
                        'candidates_to_analyze': len(candidates),
                        'characters_confirmed': len(final_characters),
                        'current_character': name,
                        'status': 'confirmed' if enhanced_character.get("is_valid_character", True) else 'rejected'
                    })

            except Exception as e:
                self.logger.error(f"❌ Analysis failed for {name}: {e}")
                # Include candidate with basic info on error
                candidate["analysis_error"] = str(e)
                final_characters.append(candidate)

        self.logger.info(f"🎯 Targeted analysis complete: {len(final_characters)} characters confirmed")

        # Send completion update
        if hasattr(self, 'progress_callback') and self.progress_callback:
            self.progress_callback('analysis', 'completed', {
                'candidates_analyzed': len(candidates),
                'characters_confirmed': len(final_characters),
                'current_character': 'Analysis complete'
            })

        return final_characters

    def _build_targeted_analysis_prompt(self, candidate: Dict, full_text: str,
                                      metadata: Dict[str, Any]) -> str:
        """Build prompt for targeted character analysis"""

        name = candidate.get("name", "")
        mentions = candidate.get("total_mentions", 0)
        title = metadata.get("book_title", "Unknown Novel")

        # Extract relevant text sections mentioning this character
        relevant_sections = self._extract_character_mentions(name, full_text, max_sections=5)

        return f"""
TASK: Detailed Character Analysis for "{name}"

NOVEL: {title}
CHARACTER: {name}
MENTIONS FOUND: {mentions}

INSTRUCTIONS:
Analyze the following text sections that mention "{name}" and create a detailed character profile.

DETERMINE:
1. Is this actually a character (person) or something else?
2. Physical description
3. Personality traits
4. Role in the story
5. Relationships to other characters
6. Character development/arc

RELEVANT TEXT SECTIONS:
{relevant_sections}

Respond with JSON:
{{
    "character": {{
        "name": "{name}",
        "is_valid_character": true,
        "physical_description": "detailed description",
        "personality": "personality traits",
        "role": "protagonist/antagonist/supporting/minor",
        "relationships": ["list of relationships"],
        "character_arc": "how they develop",
        "key_quotes": ["important quotes"],
        "importance": "major/supporting/minor",
        "confidence": 0.9
    }},
    "analysis_notes": "reasoning for character validation"
}}

If this is NOT a character (place, object, etc.), set "is_valid_character": false.
"""

    def _extract_character_mentions(self, character_name: str, text: str, max_sections: int = 5) -> str:
        """Extract text sections that mention a specific character"""

        sections = []
        text_lower = text.lower()
        name_lower = character_name.lower()

        # Find all positions where the character is mentioned
        positions = []
        start = 0
        while True:
            pos = text_lower.find(name_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1

        # Extract context around each mention
        for i, pos in enumerate(positions[:max_sections]):
            # Extract 500 characters before and after the mention
            start = max(0, pos - 500)
            end = min(len(text), pos + len(character_name) + 500)

            section = text[start:end]
            sections.append(f"Section {i+1}:\n{section}\n")

        return "\n".join(sections)


class MockCharacterIdentifier:
    """Mock character identifier for testing and fallback"""

    def discover_characters(self, prompt: str) -> Dict[str, Any]:
        """Mock character discovery"""

        # Extract some sample character names from the prompt for demo
        text_section = prompt.split("TEXT TO ANALYZE:")[-1] if "TEXT TO ANALYZE:" in prompt else prompt

        # Simple mock discovery
        mock_characters = [
            {
                "name": "Elena",
                "mentions": 8,
                "context": "Main protagonist, appears in dialogue and action scenes",
                "confidence": 0.9,
                "evidence": "Has dialogue and performs actions throughout the text"
            },
            {
                "name": "Marcus",
                "mentions": 5,
                "context": "Supporting character, interacts with protagonist",
                "confidence": 0.8,
                "evidence": "Mentioned in conversations and has speaking lines"
            },
            {
                "name": "The Council",
                "mentions": 3,
                "context": "Governing body mentioned in political discussions",
                "confidence": 0.4,
                "evidence": "Referenced as an organization, not individual character"
            }
        ]

        return {
            "potential_characters": mock_characters,
            "confidence": 0.75,
            "reasoning": "Mock character discovery for testing purposes"
        }

    def validate_characters(self, prompt: str) -> Dict[str, Any]:
        """Mock character validation"""

        # Mock validation - remove obvious non-characters
        validated_characters = [
            {
                "name": "Elena",
                "character_type": "protagonist",
                "confidence": 0.9,
                "validation_reason": "Clear protagonist with dialogue and actions",
                "role_in_story": "Main character driving the narrative"
            },
            {
                "name": "Marcus",
                "character_type": "supporting",
                "confidence": 0.8,
                "validation_reason": "Supporting character with speaking role",
                "role_in_story": "Ally/companion to the protagonist"
            }
            # Note: "The Council" removed as it's an organization, not a character
        ]

        return {
            "validated_characters": validated_characters,
            "confidence": 0.85,
            "reasoning": "Mock validation - removed organizational entities, kept individual characters"
        }

    def discover_characters_comprehensive(self, prompt: str) -> Dict[str, Any]:
        """Mock comprehensive character discovery"""

        # Enhanced mock characters with more details
        comprehensive_characters = [
            {
                "name": "Thomas Covenant",
                "age": "30s",
                "physical_description": "Tall, lean man with dark hair and intense eyes",
                "role": "protagonist",
                "relationship": "Main character, unbeliever",
                "personality": "Cynical, self-doubting, but ultimately heroic",
                "first_appearance": "Opening chapter as the central figure",
                "importance": "major",
                "mentions": 45,
                "confidence": 0.95
            },
            {
                "name": "Lord Foul",
                "age": "ancient",
                "physical_description": "Malevolent entity of corruption and despair",
                "role": "antagonist",
                "relationship": "Primary enemy of the Land",
                "personality": "Evil, manipulative, seeks destruction",
                "first_appearance": "Referenced early as the Despiser",
                "importance": "major",
                "mentions": 25,
                "confidence": 0.90
            },
            {
                "name": "Lena",
                "age": "young woman",
                "physical_description": "Beautiful young woman of the Land",
                "role": "supporting",
                "relationship": "Love interest, victim of Covenant's actions",
                "personality": "Innocent, trusting, later becomes complex",
                "first_appearance": "Early in Covenant's journey to the Land",
                "importance": "supporting",
                "mentions": 18,
                "confidence": 0.85
            },
            {
                "name": "Saltheart Foamfollower",
                "age": "ancient",
                "physical_description": "Giant with sea-green hair and deep wisdom",
                "role": "supporting",
                "relationship": "Covenant's friend and guide",
                "personality": "Wise, loyal, tragic figure",
                "first_appearance": "During Covenant's travels",
                "importance": "supporting",
                "mentions": 22,
                "confidence": 0.88
            },
            {
                "name": "High Lord Elena",
                "age": "adult",
                "physical_description": "Powerful leader with commanding presence",
                "role": "supporting",
                "relationship": "Leader of the Council of Lords",
                "personality": "Strong-willed, determined, complex motivations",
                "first_appearance": "In the Council chambers",
                "importance": "supporting",
                "mentions": 15,
                "confidence": 0.82
            }
        ]

        return {
            "characters": comprehensive_characters,
            "confidence": 0.85,
            "reasoning": "Mock comprehensive discovery with detailed character profiles"
        }

    def enhance_character_profiles(self, prompt: str) -> Dict[str, Any]:
        """Mock character profile enhancement - OPTIMIZED FORMAT"""

        # Check if this is a targeted analysis prompt (contains specific character name)
        if "TASK: Detailed Character Analysis for" in prompt:
            # Extract character name from prompt
            lines = prompt.split('\n')
            character_name = "Unknown"
            for line in lines:
                if line.startswith('CHARACTER:'):
                    character_name = line.replace('CHARACTER:', '').strip()
                    break

            # Return targeted analysis format
            return {
                "character": {
                    "name": character_name,
                    "is_valid_character": True,
                    "physical_description": f"Detailed description of {character_name} from the novel",
                    "personality": f"Complex personality traits of {character_name}",
                    "role": "major" if character_name in ["Thomas Covenant", "Lord Foul"] else "supporting",
                    "relationships": [f"Connected to other characters in the story"],
                    "character_arc": f"Development and growth of {character_name} throughout the story",
                    "key_quotes": [f"Important quotes from {character_name}"],
                    "importance": "major" if character_name in ["Thomas Covenant", "Lord Foul"] else "supporting",
                    "confidence": 0.9
                },
                "analysis_notes": f"Confirmed {character_name} as a valid character through targeted analysis"
            }

        # Fallback to old format for compatibility
        enhanced_characters = [
            {
                "name": "Thomas Covenant",
                "age": "30s",
                "physical_description": "Tall, lean man with dark hair, intense eyes, and a missing finger",
                "personality": "Cynical writer struggling with disbelief, self-loathing, but possesses hidden courage and moral strength",
                "role": "protagonist",
                "relationships": ["Lena (complicated relationship)", "Foamfollower (friendship)", "Elena (complex connection)"],
                "character_arc": "From cynical unbeliever to reluctant hero who accepts responsibility",
                "key_quotes": ["I don't believe in you", "Hellfire and bloody damnation"],
                "key_actions": ["Summoned to the Land", "Struggles with his role as the Unbeliever", "Faces Lord Foul"],
                "background": "Writer from our world, suffers from leprosy, divorced",
                "importance": "major",
                "confidence": 0.95,
                "enhanced": True,
                "validation_status": "confirmed_character"
            },
            {
                "name": "Lord Foul",
                "age": "ancient",
                "physical_description": "Malevolent entity of corruption, appears in various forms of decay and despair",
                "personality": "Pure evil, manipulative, seeks the destruction of all creation",
                "role": "antagonist",
                "relationships": ["Thomas Covenant (primary enemy)", "The Land (seeks to destroy)"],
                "character_arc": "Constant threat throughout the series, growing in power",
                "key_quotes": ["I am the Despiser", "You will serve me in the end"],
                "key_actions": ["Summons Covenant to the Land", "Corrupts and destroys", "Manipulates events"],
                "background": "Ancient evil entity, the Despiser, enemy of all life",
                "importance": "major",
                "confidence": 0.90,
                "enhanced": True,
                "validation_status": "confirmed_character"
            },
            {
                "name": "Lena",
                "age": "young woman",
                "physical_description": "Beautiful young woman with flowing hair and innocent features",
                "personality": "Initially innocent and trusting, becomes complex and tragic figure",
                "role": "supporting",
                "relationships": ["Thomas Covenant (victim/love interest)", "Atiaran (mother)"],
                "character_arc": "From innocent girl to complex woman shaped by trauma",
                "key_quotes": ["You are the Unbeliever", "I have waited for you"],
                "key_actions": ["First to meet Covenant", "Becomes central to his guilt", "Shapes his character development"],
                "background": "Daughter of Atiaran, lives in Mithil Stonedown",
                "importance": "supporting",
                "confidence": 0.85,
                "enhanced": True,
                "validation_status": "confirmed_character"
            }
        ]

        return {
            "enhanced_characters": enhanced_characters,
            "confidence": 0.88,
            "reasoning": "Mock enhancement with detailed character development and relationships"
        }


# AI Client Classes for different providers
class OpenAICharacterClient:
    """OpenAI client for character identification"""

    def __init__(self, api_key: str, model: str = "gpt-4", max_tokens: int = 2000,
                 temperature: float = 0.3, timeout: int = 30):
        import openai
        self.client = openai.OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def discover_characters(self, prompt: str) -> Dict[str, Any]:
        """Character discovery using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert literary analyst specializing in character identification. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ OpenAI character discovery error: {e}")
            return self._fallback_response()

    def validate_characters(self, prompt: str) -> Dict[str, Any]:
        """Character validation using OpenAI"""
        return self.discover_characters(prompt)  # Same method, different prompt

    def discover_characters_comprehensive(self, prompt: str) -> Dict[str, Any]:
        """Comprehensive character discovery using OpenAI"""
        return self.discover_characters(prompt)  # Same method, enhanced prompt

    def enhance_character_profiles(self, prompt: str) -> Dict[str, Any]:
        """Character profile enhancement using OpenAI"""
        return self.discover_characters(prompt)  # Same method, enhancement prompt

    def _fallback_response(self) -> Dict[str, Any]:
        """Fallback response for API errors"""
        return {
            "potential_characters": [],
            "validated_characters": [],
            "confidence": 0.0,
            "reasoning": "API error - fallback response"
        }


class AnthropicCharacterClient:
    """Anthropic/Claude client for character identification"""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229",
                 max_tokens: int = 2000, temperature: float = 0.3, timeout: int = 30):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def discover_characters(self, prompt: str) -> Dict[str, Any]:
        """Character discovery using Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return json.loads(response.content[0].text)
        except Exception as e:
            print(f"❌ Claude character discovery error: {e}")
            return self._fallback_response()

    def validate_characters(self, prompt: str) -> Dict[str, Any]:
        """Character validation using Claude"""
        return self.discover_characters(prompt)  # Same method, different prompt

    def discover_characters_comprehensive(self, prompt: str) -> Dict[str, Any]:
        """Comprehensive character discovery using Claude"""
        return self.discover_characters(prompt)  # Same method, enhanced prompt

    def enhance_character_profiles(self, prompt: str) -> Dict[str, Any]:
        """Character profile enhancement using Claude"""
        return self.discover_characters(prompt)  # Same method, enhancement prompt

    def _fallback_response(self) -> Dict[str, Any]:
        """Fallback response for API errors"""
        return {
            "potential_characters": [],
            "validated_characters": [],
            "confidence": 0.0,
            "reasoning": "API error - fallback response"
        }


class OpenRouterCharacterClient:
    """OpenRouter client for character identification"""

    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet",
                 max_tokens: int = 2000, temperature: float = 0.3, timeout: int = 30):
        import openai
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=timeout
        )
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def discover_characters(self, prompt: str) -> Dict[str, Any]:
        """Character discovery using OpenRouter"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert literary analyst specializing in character identification. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            # Check if response has content
            if not response.choices or len(response.choices) == 0:
                print(f"❌ OpenRouter API returned no choices")
                return self._fallback_response()

            content = response.choices[0].message.content
            if not content or not content.strip():
                print(f"❌ OpenRouter API returned empty content")
                return self._fallback_response()

            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ OpenRouter character discovery JSON parse error: {e}")
            return self._fallback_response()
        except Exception as e:
            print(f"❌ OpenRouter character discovery error: {e}")
            return self._fallback_response()

    def validate_characters(self, prompt: str) -> Dict[str, Any]:
        """Character validation using OpenRouter"""
        return self.discover_characters(prompt)  # Same method, different prompt

    def discover_characters_comprehensive(self, prompt: str) -> Dict[str, Any]:
        """Comprehensive character discovery using OpenRouter"""
        return self.discover_characters(prompt)  # Same method, enhanced prompt

    def enhance_character_profiles(self, prompt: str) -> Dict[str, Any]:
        """Character profile enhancement using OpenRouter"""
        return self.discover_characters(prompt)  # Same method, enhancement prompt

    def _fallback_response(self) -> Dict[str, Any]:
        """Fallback response for API errors"""
        return {
            "potential_characters": [],
            "validated_characters": [],
            "confidence": 0.0,
            "reasoning": "OpenRouter API error - fallback response"
        }