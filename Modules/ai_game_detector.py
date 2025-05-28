#!/usr/bin/env python3
"""
AI-Powered Game Detection Module
Uses AI agents to intelligently analyze PDF content and determine game metadata
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import fitz  # PyMuPDF

class AIGameDetector:
    """AI-powered game type detection from PDF content analysis"""

    def __init__(self, ai_config: Dict[str, Any] = None, debug: bool = False):
        self.ai_config = ai_config or {"provider": "mock"}
        self.debug = debug or self.ai_config.get("debug", False)
        self.logger = logging.getLogger(__name__)

        # Initialize AI client with full configuration
        self.ai_client = self._initialize_ai_client()

        # Analysis configuration
        self.analysis_pages = self.ai_config.get("analysis_pages", 25)  # First 25 pages to analyze for better book identification
        self.max_content_length = self.ai_config.get("max_tokens", 4000) // 2  # Reserve half for response

    def _initialize_ai_client(self):
        """Initialize AI client based on provider and configuration"""
        provider = self.ai_config.get("provider", "mock")

        if self.debug:
            print(f"🤖 Initializing AI client: {provider}")
            if self.ai_config.get("model"):
                print(f"🤖 Model: {self.ai_config['model']}")

        # Initialize based on provider
        if provider == "openai":
            return self._initialize_openai_client()
        elif provider in ["claude", "anthropic"]:
            return self._initialize_anthropic_client()
        elif provider == "openrouter":
            return self._initialize_openrouter_client()
        elif provider == "local":
            return self._initialize_local_client()
        else:
            return MockAIClient(self.ai_config)

    def _initialize_openai_client(self):
        """Initialize OpenAI client"""
        try:
            import openai

            # Get API key from config or environment
            api_key = self.ai_config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️  OpenAI API key not found. Set OPENAI_API_KEY environment variable or use --ai-api-key")
                return MockAIClient(self.ai_config)

            base_url = self.ai_config.get("base_url") or os.getenv("OPENAI_BASE_URL")

            client_config = {"api_key": api_key}
            if base_url:
                client_config["base_url"] = base_url

            return OpenAIClient(client_config, self.ai_config)

        except ImportError:
            print("⚠️  OpenAI package not installed. Run: pip install openai")
            return MockAIClient(self.ai_config)

    def _initialize_anthropic_client(self):
        """Initialize Anthropic/Claude client"""
        try:
            import anthropic

            # Get API key from config or environment
            api_key = self.ai_config.get("api_key") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
            if not api_key:
                print("⚠️  Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or use --ai-api-key")
                return MockAIClient(self.ai_config)

            return AnthropicClient(api_key, self.ai_config)

        except ImportError:
            print("⚠️  Anthropic package not installed. Run: pip install anthropic")
            return MockAIClient(self.ai_config)

    def _initialize_openrouter_client(self):
        """Initialize OpenRouter client"""
        try:
            import openai

            # Get API key from config or environment
            api_key = self.ai_config.get("api_key") or os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                print("⚠️  OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable or use --ai-api-key")
                return MockAIClient(self.ai_config)

            return OpenRouterClient(api_key, self.ai_config)

        except ImportError:
            print("⚠️  OpenAI package not installed (required for OpenRouter). Run: pip install openai")
            return MockAIClient(self.ai_config)

    def _initialize_local_client(self):
        """Initialize local LLM client"""
        base_url = self.ai_config.get("base_url") or os.getenv("LOCAL_LLM_URL", "http://localhost:11434")
        model = self.ai_config.get("model") or os.getenv("LOCAL_LLM_MODEL", "llama2")

        return LocalLLMClient(base_url, model, self.ai_config)

    def extract_analysis_content(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract content from first pages for AI analysis"""

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            doc = fitz.open(str(pdf_path))

            # Extract text from first pages
            extracted_content = {
                "filename": pdf_path.name,
                "total_pages": len(doc),
                "analysis_pages": [],
                "combined_text": "",
                "metadata": doc.metadata
            }

            # Extract content from first N pages
            pages_to_analyze = min(self.analysis_pages, len(doc))

            for page_num in range(pages_to_analyze):
                page = doc[page_num]
                page_text = page.get_text()

                page_info = {
                    "page_number": page_num + 1,
                    "text": page_text,
                    "word_count": len(page_text.split()),
                    "has_images": len(page.get_images()) > 0
                }

                extracted_content["analysis_pages"].append(page_info)
                extracted_content["combined_text"] += f"\n--- Page {page_num + 1} ---\n{page_text}"

            # Increase content length to capture more text for better book detection
            # Look for book title in first 10000 characters to capture table of contents and chapter titles
            if len(extracted_content["combined_text"]) > 10000:
                extracted_content["combined_text"] = extracted_content["combined_text"][:10000]
                extracted_content["truncated"] = True

            doc.close()

            if self.debug:
                print(f"📄 Extracted {pages_to_analyze} pages, {len(extracted_content['combined_text'])} characters")
                # Show first 500 characters for debugging
                preview = extracted_content['combined_text'][:500]
                print(f"📝 Content preview: {preview}...")

            return extracted_content

        except Exception as e:
            raise Exception(f"Failed to extract PDF content: {e}")

    def analyze_game_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """Main method: AI-powered analysis of PDF to determine game metadata"""

        self.logger.info(f"🤖 AI analyzing: {pdf_path.name}")

        # Extract content for analysis
        content = self.extract_analysis_content(pdf_path)

        # Perform AI analysis
        ai_result = self._perform_ai_analysis(content)

        # Validate and enhance result
        validated_result = self._validate_ai_result(ai_result, pdf_path)

        # Generate collection name
        validated_result["collection_name"] = self._generate_collection_name(validated_result)

        if self.debug:
            print(f"🎯 AI Detection Result: {validated_result['game_type']} {validated_result['edition']} {validated_result['book_type']}")
            print(f"🎯 Confidence: {validated_result['confidence']:.2f}")

        return validated_result

    def _perform_ai_analysis(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Send content to AI for analysis"""

        try:
            # Construct AI prompt
            prompt = self._build_analysis_prompt(content)

            # Send to AI (this would be actual AI call)
            ai_response = self.ai_client.analyze(prompt)

            # Parse AI response
            if isinstance(ai_response, str):
                result = json.loads(ai_response)
            else:
                result = ai_response

            # Validate that we have a proper response
            if not isinstance(result, dict):
                self.logger.error(f"AI response is not a dictionary: {type(result)}")
                return self._fallback_analysis(content)

            return result

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response as JSON: {e}")
            if self.debug:
                self.logger.error(f"Raw AI response: {ai_response}")
            return self._fallback_analysis(content)
        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
            if self.debug:
                import traceback
                self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return self._fallback_analysis(content)

    def _build_analysis_prompt(self, content: Dict[str, Any]) -> str:
        """Build comprehensive AI analysis prompt"""

        prompt = f"""
You are an expert in tabletop RPG systems with encyclopedic knowledge of game books, editions, and publishers.

CRITICAL: Read the actual content below carefully and determine the EXACT book title and type from what is written in the text.

Analyze this RPG book content from the first {len(content['analysis_pages'])} pages and determine the game metadata.

    READ THE CONTENT CAREFULLY: Identify the exact book title from the text itself. Do not use assumptions or patterns.

FILENAME: {content['filename']}
TOTAL PAGES: {content['total_pages']}
PDF METADATA: {content.get('metadata', {})}

ACTUAL BOOK CONTENT TO ANALYZE:
{content['combined_text']}

INSTRUCTIONS:
1. READ the actual text content above carefully
2. Look for the book title, edition information, and publisher details in the text
3. Identify what type of book this is based on the content (Player's Handbook, Dungeon Master's Guide, Monster Manual, etc.)
4. Pay attention to phrases like "Players", "Dungeon Master", "monsters", "character creation", etc.
5. Base your analysis ONLY on what you can read in the provided text content

Please analyze and provide the following information in JSON format:

{{
    "game_type": "The RPG system name (e.g., 'D&D', 'Pathfinder', 'Call of Cthulhu', 'Vampire', etc.)",
    "game_full_name": "Full official name of the game system",
    "edition": "Specific edition (e.g., '1st', '2nd', '3rd', '3.5', '4th', '5th', '6th', '7th', '2020', 'RED', 'V20', 'V5')",
    "book_type": "Type of book (e.g., 'PHB', 'DMG', 'MM', 'Core', 'Keeper', 'Bestiary')",
    "book_full_name": "Full title of the book",
    "publisher": "Publisher name (e.g., 'TSR', 'Wizards of the Coast', 'Paizo', 'Chaosium')",
    "publication_year": "Year of publication (if determinable)",
    "core_mechanics": ["List of key game mechanics mentioned"],
    "confidence": 0.95,
    "reasoning": "Brief explanation of how you determined this information",
    "detected_categories": ["List of content categories found"],
    "language": "Primary language of the content"
}}

DETECTION GUIDELINES:

1. GAME SYSTEM IDENTIFICATION:
   - Look for title pages, headers, copyright notices
   - Identify unique terminology and mechanics
   - Consider publisher and design patterns
   - Common systems: D&D, Pathfinder, Call of Cthulhu, Vampire, Werewolf, Cyberpunk, Shadowrun, Traveller, GURPS, Savage Worlds

2. EDITION DETECTION:
   - D&D: THAC0 = 1st/2nd, d20 system = 3rd/3.5/4th, advantage/disadvantage = 5th
   - Pathfinder: Look for 1st vs 2nd edition mechanics
   - Call of Cthulhu: 6th vs 7th edition rules differences
   - Vampire: Different editions have distinct terminology
   - Traveller: Classic = original GDW, Mongoose = Mongoose Publishing, T5 = Marc Miller

3. BOOK TYPE CLASSIFICATION:
   Determine the book type from the actual title and content you read:
   - If the title contains "Player's Handbook" or similar → "PHB"
   - If the title contains "Dungeon Master's Guide" or similar → "DMG"
   - If the title contains "Monster Manual" or similar → "MM"
   - If the title contains "Unearthed Arcana" → "UA"
   - If the title contains "Fiend Folio" → "FF"
   - If the title contains "Deities & Demigods" → "DDG"
   - For other books, use the most appropriate abbreviation based on the actual title you see

4. CONFIDENCE SCORING:
   - 0.9-1.0: Clear identification with multiple confirming factors
   - 0.7-0.9: Strong identification with some uncertainty
   - 0.5-0.7: Reasonable guess with limited information
   - 0.0-0.5: Uncertain identification, may need human review

Provide your analysis as valid JSON only, no additional text.
"""

        return prompt

    def _validate_ai_result(self, ai_result: Dict[str, Any], pdf_path: Path) -> Dict[str, Any]:
        """Validate and enhance AI analysis result"""

        # Handle case where AI result might be incomplete or malformed
        if not isinstance(ai_result, dict):
            ai_result = {}

        # Set defaults for missing fields with robust fallbacks
        validated = {
            "game_type": ai_result.get("game_type", "Unknown"),
            "game_full_name": ai_result.get("game_full_name", ai_result.get("game_type", "Unknown")),
            "edition": ai_result.get("edition", "Unknown"),
            "book_type": ai_result.get("book_type", ai_result.get("book", "Core")),  # Try 'book' as fallback
            "book_full_name": ai_result.get("book_full_name", pdf_path.stem),
            "publisher": ai_result.get("publisher", "Unknown"),
            "publication_year": ai_result.get("publication_year"),
            "core_mechanics": ai_result.get("core_mechanics", []),
            "confidence": float(ai_result.get("confidence", 0.5)),
            "reasoning": ai_result.get("reasoning", "AI analysis"),
            "detected_categories": ai_result.get("detected_categories", []),
            "language": ai_result.get("language", "English"),
            "detection_method": "ai_analysis",
            "filename": pdf_path.name
        }

        # Validate confidence score
        if not 0.0 <= validated["confidence"] <= 1.0:
            validated["confidence"] = 0.5

        # Clean up game type
        validated["game_type"] = self._normalize_game_type(validated["game_type"])

        # Generate collection prefix
        validated["collection_prefix"] = self._generate_collection_prefix(validated["game_type"])

        return validated

    def _normalize_game_type(self, game_type: str) -> str:
        """Normalize game type names to standard format"""

        # Handle None or empty game_type
        if not game_type:
            return "Unknown"

        game_type_lower = game_type.lower()

        # Common normalizations
        if any(term in game_type_lower for term in ["d&d", "dungeons", "dragons", "advanced dungeons"]):
            return "D&D"
        elif "pathfinder" in game_type_lower:
            return "Pathfinder"
        elif "cthulhu" in game_type_lower:
            return "Call of Cthulhu"
        elif "vampire" in game_type_lower:
            return "Vampire"
        elif "werewolf" in game_type_lower:
            return "Werewolf"
        elif "cyberpunk" in game_type_lower:
            return "Cyberpunk"
        elif "shadowrun" in game_type_lower:
            return "Shadowrun"
        elif "traveller" in game_type_lower:
            return "Traveller"
        elif "gurps" in game_type_lower:
            return "GURPS"
        elif "savage" in game_type_lower:
            return "Savage Worlds"
        else:
            return game_type.title()

    def _generate_collection_prefix(self, game_type: str) -> str:
        """Generate collection prefix from game type"""

        # Handle None or empty game_type
        if not game_type:
            return "unknown"

        prefix_map = {
            "D&D": "dnd",
            "Pathfinder": "pf",
            "Call of Cthulhu": "coc",
            "Vampire": "vtm",
            "Werewolf": "wta",
            "Cyberpunk": "cp",
            "Shadowrun": "sr",
            "Traveller": "traveller",
            "GURPS": "gurps",
            "Savage Worlds": "sw"
        }

        return prefix_map.get(game_type, game_type.lower().replace(" ", "")[:5])

    def _generate_collection_name(self, metadata: Dict[str, Any]) -> str:
        """Generate collection name from AI-detected metadata"""

        prefix = metadata.get("collection_prefix", "unknown")
        edition = metadata.get("edition", "unknown")
        book_type = metadata.get("book_type", "core")
        content_type = metadata.get("content_type", "source_material")

        # Handle None values and clean up strings
        if edition is None or (isinstance(edition, str) and edition.lower() in ["unknown", "n/a", "none"]):
            edition = "unknown"
        else:
            edition = str(edition).replace(".", "").lower()

        if book_type is None:
            book_type = "core"
        else:
            book_type = str(book_type).lower()

        # Special handling for novels - they don't have meaningful editions
        if content_type == "novel":
            # For novels, use a simpler naming scheme: prefix_novel
            # This avoids issues with "N/A" editions and meaningless book types
            return f"{prefix}_novel"
        else:
            # For source material, use the traditional scheme
            return f"{prefix}_{edition}_{book_type}"

    def _fallback_analysis(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when AI fails"""

        return {
            "game_type": "Unknown",
            "game_full_name": "Unknown RPG System",
            "edition": "Unknown",
            "book_type": "Core",
            "book_full_name": content["filename"],
            "publisher": "Unknown",
            "publication_year": None,
            "core_mechanics": [],
            "confidence": 0.1,
            "reasoning": "AI analysis failed, using fallback",
            "detected_categories": [],
            "language": "Unknown",
            "detection_method": "fallback"
        }


class OpenAIClient:
    """OpenAI API client for game detection"""

    def __init__(self, client_config: Dict[str, str], ai_config: Dict[str, Any]):
        import openai
        self.client = openai.OpenAI(**client_config)
        self.ai_config = ai_config
        self.model = ai_config.get("model", "gpt-4")
        self.max_tokens = ai_config.get("max_tokens", 4000)
        self.temperature = ai_config.get("temperature", 0.1)
        self.timeout = ai_config.get("timeout", 30)

    def analyze(self, prompt: str) -> Dict[str, Any]:
        """Analyze content using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert RPG book analyzer. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return self._fallback_response()

    def categorize(self, prompt: str) -> Dict[str, Any]:
        """Categorize content using OpenAI API"""
        return self.analyze(prompt)  # Same method for both operations

    def _fallback_response(self) -> Dict[str, Any]:
        return {
            "game_type": "Unknown",
            "confidence": 0.1,
            "reasoning": "OpenAI API error, using fallback"
        }


class AnthropicClient:
    """Anthropic/Claude API client for game detection"""

    def __init__(self, api_key: str, ai_config: Dict[str, Any]):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.ai_config = ai_config
        self.model = ai_config.get("model", "claude-3-sonnet-20240229")
        self.max_tokens = min(ai_config.get("max_tokens", 4000), 4096)  # Ensure we don't exceed Claude's limit
        self.temperature = ai_config.get("temperature", 0.1)

    def analyze(self, prompt: str) -> Dict[str, Any]:
        """Analyze content using Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nRespond with valid JSON only."}
                ]
            )

            # Check if response has content
            if not response.content or len(response.content) == 0:
                print(f"❌ Anthropic API returned empty content")
                return self._fallback_response()

            response_text = response.content[0].text

            # Check if response text is empty
            if not response_text or not response_text.strip():
                print(f"❌ Anthropic API returned empty text")
                return self._fallback_response()

            return json.loads(response_text)

        except json.JSONDecodeError as e:
            print(f"❌ Anthropic API JSON parse error: {e}")
            return self._fallback_response()
        except Exception as e:
            print(f"❌ Anthropic API error: {e}")
            return self._fallback_response()

    def categorize(self, prompt: str) -> Dict[str, Any]:
        """Categorize content using Anthropic API"""
        return self.analyze(prompt)  # Same method for both operations

    def _fallback_response(self) -> Dict[str, Any]:
        return {
            "game_type": "Unknown",
            "confidence": 0.1,
            "reasoning": "Anthropic API error, using fallback"
        }


class LocalLLMClient:
    """Local LLM client (Ollama, etc.) for game detection"""

    def __init__(self, base_url: str, model: str, ai_config: Dict[str, Any]):
        self.base_url = base_url
        self.model = model
        self.ai_config = ai_config
        self.max_tokens = ai_config.get("max_tokens", 4000)
        self.temperature = ai_config.get("temperature", 0.1)

    def analyze(self, prompt: str) -> Dict[str, Any]:
        """Analyze content using local LLM"""
        try:
            import requests

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{prompt}\n\nRespond with valid JSON only.",
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=self.ai_config.get("timeout", 60)
            )

            if response.status_code == 200:
                result = response.json()
                return json.loads(result["response"])
            else:
                print(f"❌ Local LLM error: {response.status_code}")
                return self._fallback_response()

        except Exception as e:
            print(f"❌ Local LLM error: {e}")
            return self._fallback_response()

    def categorize(self, prompt: str) -> Dict[str, Any]:
        """Categorize content using local LLM"""
        return self.analyze(prompt)  # Same method for both operations

    def _fallback_response(self) -> Dict[str, Any]:
        return {
            "game_type": "Unknown",
            "confidence": 0.1,
            "reasoning": "Local LLM error, using fallback"
        }


class OpenRouterClient:
    """OpenRouter API client for game detection"""

    def __init__(self, api_key: str, ai_config: Dict[str, Any]):
        import openai
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.ai_config = ai_config
        # Don't default to Claude - require explicit model selection
        self.model = ai_config.get("model")
        if not self.model:
            raise ValueError("OpenRouter requires explicit model selection. Please specify a model in ai_config.")

        # Debug logging to show what model is being used
        if ai_config.get("debug"):
            print(f"🤖 Game detector using OpenRouter model: {self.model}")

        self.max_tokens = ai_config.get("max_tokens", 4000)
        self.temperature = ai_config.get("temperature", 0.1)
        self.timeout = ai_config.get("timeout", 30)

    def analyze(self, prompt: str) -> Dict[str, Any]:
        """Analyze content using OpenRouter API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert RPG book analyzer. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
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
            print(f"❌ OpenRouter API JSON parse error: {e}")
            return self._fallback_response()
        except Exception as e:
            print(f"❌ OpenRouter API error: {e}")
            return self._fallback_response()

    def categorize(self, prompt: str) -> Dict[str, Any]:
        """Categorize content using OpenRouter API"""
        return self.analyze(prompt)  # Same method for both operations

    def _fallback_response(self) -> Dict[str, Any]:
        return {
            "game_type": "Unknown",
            "confidence": 0.1,
            "reasoning": "OpenRouter API error, using fallback"
        }


class MockAIClient:
    """Mock AI client for testing and fallback"""

    def __init__(self, ai_config: Dict[str, Any] = None):
        self.ai_config = ai_config or {}

    def analyze(self, prompt: str) -> Dict[str, Any]:
        """Mock AI analysis for game detection"""
        return self._analyze_content(prompt)

    def categorize(self, prompt: str) -> Dict[str, Any]:
        """Mock AI categorization for content classification"""
        return self._categorize_content(prompt)

    def _analyze_content(self, prompt: str) -> Dict[str, Any]:
        """Mock AI analysis with improved content-based detection"""

        prompt_lower = prompt.lower()

        # Debug: Show what we're analyzing
        if self.ai_config.get("debug", False):
            print(f"🔍 Mock AI analyzing content (first 300 chars): {prompt_lower[:300]}...")

        # Look for actual book title mentions in the content
        book_title_indicators = {
            "player's handbook": "PHB",
            "players handbook": "PHB",
            "player handbook": "PHB",
            "dungeon master's guide": "DMG",
            "dungeon masters guide": "DMG",
            "dungeon master guide": "DMG",
            "monster manual": "MM",
            "fiend folio": "FF",
            "deities & demigods": "DDG",
            "unearthed arcana": "UA",
            "oriental adventures": "OA",
            "wilderness survival guide": "WSG",
            "dungeoneer's survival guide": "DSG"
        }

        # Check for explicit book title mentions
        detected_book_type = None
        detected_book_name = None

        for title, book_type in book_title_indicators.items():
            if title in prompt_lower:
                detected_book_type = book_type
                detected_book_name = title.title()
                if self.ai_config.get("debug", False):
                    print(f"📖 Found explicit book title: '{title}' -> {book_type}")
                break

        # Enhanced keyword detection for D&D
        if any(term in prompt_lower for term in ["dungeons", "d&d", "ad&d", "thac0", "advanced dungeons"]):

            # Use detected book title if found, otherwise analyze content
            if detected_book_type:
                book_type = detected_book_type
                book_full_name = detected_book_name

                # Set appropriate categories based on book type
                if book_type == "PHB":
                    detected_categories = ["Character Creation", "Classes", "Races", "Spells", "Equipment"]
                elif book_type == "DMG":
                    detected_categories = ["Campaign", "Treasure", "Magic Items", "Rules", "Tables"]
                elif book_type == "MM":
                    detected_categories = ["Monsters", "Bestiary", "Combat"]
                elif book_type == "UA":
                    detected_categories = ["New Classes", "New Spells", "Optional Rules", "Character Options", "Supplements"]
                elif book_type == "FF":
                    detected_categories = ["Monsters", "Bestiary", "New Creatures"]
                elif book_type == "DDG":
                    detected_categories = ["Deities", "Mythology", "Planes", "Religion"]
                else:
                    detected_categories = ["Rules", "Reference"]

                if self.ai_config.get("debug", False):
                    print(f"✅ Using detected book title: {book_full_name} ({book_type})")
                    print(f"📂 Categories: {detected_categories}")

            else:
                # Fallback to content analysis if no explicit title found
                if self.ai_config.get("debug", False):
                    print("🔍 No explicit book title found, analyzing content keywords...")

                # Player's Handbook indicators
                phb_keywords = [
                    "player", "character creation", "ability scores", "races", "classes",
                    "fighter", "wizard", "cleric", "thief", "magic-user", "elf", "dwarf", "halfling",
                    "strength", "intelligence", "wisdom", "dexterity", "constitution", "charisma",
                    "hit points", "experience points", "level", "spells per day"
                ]
                phb_matches = [term for term in phb_keywords if term in prompt_lower]

                # Dungeon Master's Guide indicators
                dmg_keywords = [
                    "dungeon master", "dm", "referee", "treasure", "monsters", "encounter",
                    "adventure", "campaign", "npc", "magic items", "artifacts", "planes",
                    "psionics", "random tables", "wilderness", "dungeon design"
                ]
                dmg_matches = [term for term in dmg_keywords if term in prompt_lower]

                # Monster Manual indicators
                mm_keywords = [
                    "monster manual", "bestiary", "creatures", "dragons", "undead", "demons",
                    "armor class", "hit dice", "attacks", "damage", "special abilities",
                    "treasure type", "alignment", "frequency", "organization"
                ]
                mm_matches = [term for term in mm_keywords if term in prompt_lower]

                # Debug output
                if self.ai_config.get("debug", False):
                    if phb_matches:
                        print(f"🎯 PHB keywords found ({len(phb_matches)}): {phb_matches[:5]}")
                    if dmg_matches:
                        print(f"🎯 DMG keywords found ({len(dmg_matches)}): {dmg_matches[:5]}")
                    if mm_matches:
                        print(f"🎯 MM keywords found ({len(mm_matches)}): {mm_matches[:5]}")

                # Determine book type based on highest score (most keyword matches)
                scores = {
                    "PHB": len(phb_matches),
                    "DMG": len(dmg_matches),
                    "MM": len(mm_matches)
                }

                # Find the book type with the highest score
                best_book = max(scores, key=scores.get)

                if scores[best_book] > 0:  # Only if we found at least one match
                    if best_book == "PHB":
                        book_type = "PHB"
                        book_full_name = "Player's Handbook"
                        detected_categories = ["Character Creation", "Classes", "Races", "Spells", "Equipment"]
                    elif best_book == "DMG":
                        book_type = "DMG"
                        book_full_name = "Dungeon Masters Guide"
                        detected_categories = ["Campaign", "Treasure", "Magic Items", "Rules", "Tables"]
                    elif best_book == "MM":
                        book_type = "MM"
                        book_full_name = "Monster Manual"
                        detected_categories = ["Monsters", "Bestiary", "Combat"]

                    if self.ai_config.get("debug", False):
                        print(f"🏆 Best match: {best_book} with {scores[best_book]} keywords")
                else:
                    # No clear indicators found
                    book_type = "Core"
                    book_full_name = "Unknown Book"
                    detected_categories = ["General"]

            # Determine edition more accurately
            edition = "1st"
            publisher = "TSR"
            pub_year = "1978"
            mechanics = ["THAC0", "Saving Throws", "Armor Class"]

            if "thac0" in prompt_lower or "tsr" in prompt_lower:
                edition = "1st"
                publisher = "TSR"
                pub_year = "1978"
            elif any(term in prompt_lower for term in ["2nd edition", "2e", "ad&d 2nd"]):
                edition = "2nd"
                publisher = "TSR"
                pub_year = "1989"
            elif any(term in prompt_lower for term in ["3rd edition", "3e", "d20", "wizards of the coast"]):
                edition = "3rd"
                publisher = "Wizards of the Coast"
                pub_year = "2000"
                mechanics = ["d20", "Base Attack Bonus", "Skills"]
            elif any(term in prompt_lower for term in ["5th edition", "5e", "advantage", "disadvantage"]):
                edition = "5th"
                publisher = "Wizards of the Coast"
                pub_year = "2014"
                mechanics = ["d20", "Advantage/Disadvantage", "Proficiency Bonus"]

            return {
                "game_type": "D&D",
                "game_full_name": "Dungeons & Dragons",
                "edition": edition,
                "book_type": book_type,
                "book_full_name": book_full_name,
                "publisher": publisher,
                "publication_year": pub_year,
                "core_mechanics": mechanics,
                "confidence": 0.8,
                "reasoning": f"Mock analysis detected D&D {edition} Edition {book_type} based on content keywords",
                "detected_categories": detected_categories,
                "language": "English"
            }

        elif "pathfinder" in prompt_lower:
            return {
                "game_type": "Pathfinder",
                "game_full_name": "Pathfinder Roleplaying Game",
                "edition": "2nd" if "three action" in prompt_lower else "1st",
                "book_type": "Core",
                "book_full_name": "Core Rulebook",
                "publisher": "Paizo Publishing",
                "publication_year": "2019" if "three action" in prompt_lower else "2009",
                "core_mechanics": ["d20", "Three Action Economy"] if "three action" in prompt_lower else ["d20", "Base Attack Bonus"],
                "confidence": 0.85,
                "reasoning": "Mock analysis based on Pathfinder keywords",
                "detected_categories": ["Character Creation", "Combat", "Spells"],
                "language": "English"
            }

        elif "cthulhu" in prompt_lower:
            return {
                "game_type": "Call of Cthulhu",
                "game_full_name": "Call of Cthulhu",
                "edition": "7th",
                "book_type": "Keeper",
                "book_full_name": "Keeper Rulebook",
                "publisher": "Chaosium",
                "publication_year": "2014",
                "core_mechanics": ["Percentile Dice", "Sanity", "Skill Checks"],
                "confidence": 0.8,
                "reasoning": "Mock analysis based on Call of Cthulhu keywords",
                "detected_categories": ["Investigation", "Sanity", "Skills"],
                "language": "English"
            }

        return {
            "game_type": "Unknown",
            "game_full_name": "Unknown RPG System",
            "edition": "Unknown",
            "book_type": "Core",
            "book_full_name": "Unknown Book",
            "publisher": "Unknown",
            "publication_year": None,
            "core_mechanics": [],
            "confidence": 0.3,
            "reasoning": "Mock analysis - no clear indicators found",
            "detected_categories": [],
            "language": "English"
        }

    def _categorize_content(self, prompt: str) -> Dict[str, Any]:
        """Mock categorization with improved keyword detection"""

        prompt_lower = prompt.lower()

        # Enhanced keyword detection for categorization
        if any(term in prompt_lower for term in ["spell", "magic", "cast", "enchant"]):
            return {
                "primary_category": "Spells/Magic",
                "secondary_categories": ["Rules"],
                "confidence": 0.8,
                "reasoning": "Mock analysis - content contains spell or magic-related terminology",
                "key_topics": ["spells", "magic", "casting"],
                "game_specific_elements": ["spell levels", "components"],
                "content_type": "rules"
            }

        elif any(term in prompt_lower for term in ["combat", "attack", "damage", "armor", "weapon"]):
            return {
                "primary_category": "Combat",
                "secondary_categories": ["Rules"],
                "confidence": 0.8,
                "reasoning": "Mock analysis - content contains combat-related terminology",
                "key_topics": ["combat", "attack", "damage"],
                "game_specific_elements": ["armor class", "hit points"],
                "content_type": "rules"
            }

        elif any(term in prompt_lower for term in ["character", "class", "race", "ability", "stats"]):
            return {
                "primary_category": "Character Creation",
                "secondary_categories": ["Classes", "Races"],
                "confidence": 0.7,
                "reasoning": "Mock analysis - content appears to be about character creation",
                "key_topics": ["character", "abilities", "stats"],
                "game_specific_elements": ["ability scores", "classes"],
                "content_type": "description"
            }

        elif any(term in prompt_lower for term in ["monster", "creature", "beast", "dragon"]):
            return {
                "primary_category": "Monsters",
                "secondary_categories": ["Bestiary"],
                "confidence": 0.8,
                "reasoning": "Mock analysis - content contains monster or creature references",
                "key_topics": ["monsters", "creatures", "encounters"],
                "game_specific_elements": ["hit dice", "armor class"],
                "content_type": "description"
            }

        elif any(term in prompt_lower for term in ["treasure", "item", "equipment", "gear"]):
            return {
                "primary_category": "Equipment",
                "secondary_categories": ["Treasure"],
                "confidence": 0.7,
                "reasoning": "Mock analysis - content contains equipment or treasure references",
                "key_topics": ["equipment", "items", "gear"],
                "game_specific_elements": ["cost", "weight"],
                "content_type": "description"
            }

        else:
            return {
                "primary_category": "General",
                "secondary_categories": [],
                "confidence": 0.5,
                "reasoning": "Mock analysis - no clear category indicators found",
                "key_topics": [],
                "game_specific_elements": [],
                "content_type": "description"
            }
