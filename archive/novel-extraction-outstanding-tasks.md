# Novel Extraction Outstanding Tasks

## Overview
This document tracks the remaining tasks to fully implement the novel extraction system for NPC pattern generation. While basic content type selection has been implemented, the core novel-specific processing features are still missing.

## Status Summary
- ✅ **Completed**: Content type selection UI, ISBN extraction, basic infrastructure
- ❌ **Missing**: Novel-specific processing, pattern extraction, ISBN blacklist, character identification

---

## Phase 1: Core Infrastructure (High Priority)

### Task 1.1: ISBN Blacklist System
**Status**: ✅ COMPLETED
**Priority**: High
**Estimated Time**: 2-3 hours

- [x] Create `rpger.extraction.blacklist` MongoDB collection
- [x] Implement ISBN duplicate checking before processing
- [x] Add warning UI when duplicate ISBN detected
- [x] Create blacklist entry creation on successful extraction
- [x] Test with sample ISBN numbers

**Files modified**:
- `Modules/pdf_processor.py` - Added blacklist checking and entry creation
- `ui/app.py` - Added duplicate warning error handling
- `ui/static/js/app.js` - Added duplicate warning modal UI

**Implementation Notes**:
- ISBN blacklist checking occurs before novel processing starts
- Duplicate ISBNs throw `ISBN_DUPLICATE` exception with details
- UI shows informative modal with processing history
- Blacklist entries include metadata for future pattern extraction features

### Task 1.2: Novel Processing Detection
**Status**: ✅ COMPLETED
**Priority**: High
**Estimated Time**: 1-2 hours

- [x] Add novel-specific processing branch in PDF processor
- [x] Create different extraction workflows for novel vs source material
- [x] Add novel processing flags and configuration
- [x] Update logging to distinguish novel processing

**Files modified**:
- `Modules/pdf_processor.py` - Added `_extract_novel_content()` method with narrative-focused processing

**Implementation Notes**:
- Novel processing uses `_extract_novel_content()` instead of `_extract_sections()`
- Novel-specific categorization: Chapter/Section, Dialogue, Description, Action, Internal Monologue, Narrative
- Chapter/section detection with regex patterns for "Chapter X", "Part X", etc.
- Narrative elements detection for future pattern extraction (dialogue markers, character mentions, action verbs, etc.)
- Different extraction confidence and logging for novel vs source material
- Foundation laid for character identification and pattern extraction in future tasks

---

## Phase 2: Character Identification System (High Priority)

### Task 2.1: Two-Pass Character Discovery
**Status**: ✅ COMPLETED
**Priority**: High
**Estimated Time**: 4-5 hours

- [x] Create character identification AI agent
- [x] Implement first pass: character discovery from text
- [x] Implement second pass: character validation
- [x] Add character filtering logic (remove non-characters)
- [x] Create character roster data structure

**Files created**:
- `Modules/novel_character_identifier.py` - New AI agent for character identification

**Files modified**:
- `Modules/pdf_processor.py` - Integrated character identification into novel processing workflow

**Implementation Notes**:
- **UPGRADED**: Comprehensive two-pass system: Discovery → Enhancement
- **First Pass**: Reads entire novel to find ALL characters with names, ages, descriptions
- **Second Pass**: Re-reads novel to enhance character profiles with relationships, arcs, quotes
- AI-powered with enhanced fallback regex-based discovery
- Supports OpenAI, Claude, and mock providers with comprehensive prompts
- Character data stored in extraction metadata and blacklist
- Enhanced UI display with detailed character profiles
- Comprehensive character roster with physical descriptions, personality, relationships, background
- Character information included in ISBN blacklist entries

### Task 2.2: Character Validation Logic
**Status**: Not Started
**Priority**: Medium
**Estimated Time**: 2-3 hours

- [ ] Develop AI prompts for character validation
- [ ] Implement false positive removal
- [ ] Add confidence scoring for identified characters
- [ ] Create character context preservation

---

## Phase 3: Pattern Extraction System (High Priority)

### Task 3.1: Pattern Extraction Framework
**Status**: Not Started
**Priority**: High
**Estimated Time**: 3-4 hours

- [ ] Create pattern extraction AI agent
- [ ] Implement physical description pattern extraction
- [ ] Implement dialogue pattern extraction
- [ ] Implement personality pattern extraction
- [ ] Implement behavior pattern extraction
- [ ] Implement voice characteristic extraction

**Files to create**:
- `Modules/novel_pattern_extractor.py` - New AI agent for pattern extraction

### Task 3.2: Pattern Storage System
**Status**: Not Started
**Priority**: High
**Estimated Time**: 2-3 hours

- [ ] Create MongoDB pattern collections schema
- [ ] Implement pattern storage logic
- [ ] Add pattern deduplication
- [ ] Create pattern metadata tracking

**Collections to create**:
- `rpger.patterns.physical_descriptions`
- `rpger.patterns.dialogue`
- `rpger.patterns.personality`
- `rpger.patterns.behavior`
- `rpger.patterns.voice`

---

## Phase 4: UI Enhancements (Medium Priority)

### Task 4.1: Novel Extraction Options UI
**Status**: Not Started
**Priority**: Medium
**Estimated Time**: 2-3 hours

- [ ] Add extraction options checkboxes to UI
- [ ] Implement "Select All" functionality
- [ ] Add extraction options to processing pipeline
- [ ] Update progress tracking for novel extraction

**Options to add**:
- [ ] Physical Descriptions
- [ ] Dialogue Patterns
- [ ] Personality Traits
- [ ] Behavior Patterns
- [ ] Voice Characteristics
- [ ] All of the above

### Task 4.2: Novel Processing Progress UI
**Status**: Not Started
**Priority**: Medium
**Estimated Time**: 1-2 hours

- [ ] Add multi-stage progress tracking
- [ ] Show character identification progress
- [ ] Show pattern extraction progress
- [ ] Add detailed status messages

---

## Phase 5: Advanced Features (Lower Priority)

### Task 5.1: Pattern Management Collections
**Status**: Not Started
**Priority**: Low
**Estimated Time**: 2-3 hours

- [ ] Create pattern combination tracking
- [ ] Implement usage statistics
- [ ] Add pattern template system
- [ ] Create role-specific pattern templates

**Collections to create**:
- `rpger.patterns.combinations`
- `rpger.patterns.usage_stats`
- `rpger.patterns.templates`

### Task 5.2: Extraction Session Logging
**Status**: Not Started
**Priority**: Low
**Estimated Time**: 1-2 hours

- [ ] Create extraction session tracking
- [ ] Log processing stages and timing
- [ ] Track extraction errors and failures
- [ ] Add session analytics

**Collections to create**:
- `rpger.extraction.sessions`
- `rpger.extraction.errors`

---

## Phase 6: Testing & Documentation (Medium Priority)

### Task 6.1: Novel Extraction Testing
**Status**: Not Started
**Priority**: Medium
**Estimated Time**: 2-3 hours

- [ ] Create test novels for extraction
- [ ] Test ISBN blacklist functionality
- [ ] Test character identification accuracy
- [ ] Test pattern extraction quality
- [ ] Validate MongoDB collection creation

### Task 6.2: Documentation Updates
**Status**: Not Started
**Priority**: Medium
**Estimated Time**: 1-2 hours

- [ ] Update README with novel extraction features
- [ ] Document new AI agents and their usage
- [ ] Create novel extraction workflow guide
- [ ] Update API documentation

---

## Bug Fixes Applied

### ✅ **Fix 1: ISBN Display in Analysis Results**
**Issue**: ISBN numbers weren't showing in the analysis results UI
**Solution**: Added ISBN extraction during analysis phase in `ui/app.py`
**Files Modified**: `ui/app.py`

### ✅ **Fix 2: Collection Name Generation for Novels**
**Issue**: Collection names were malformed for novels (e.g., "fanta_n/a_novel")
**Solution**: Special handling for novels to use `{prefix}_novel` format
**Files Modified**: `Modules/ai_game_detector.py`, `Modules/pdf_processor.py`

---

## Implementation Strategy

### Immediate Next Steps (Start Here):
1. ✅ **Task 1.1**: ISBN Blacklist System - Critical for preventing duplicates
2. ✅ **Task 1.2**: Novel Processing Detection - Foundation for different workflows
3. **Task 2.1**: Character Identification - Core novel extraction feature

### Dependencies:
- Task 2.1 depends on Task 1.2 (novel processing detection)
- Task 3.1 depends on Task 2.1 (character identification)
- Task 3.2 depends on Task 3.1 (pattern extraction)
- Task 4.1 depends on Task 3.1 (extraction options need pattern extraction)

### Estimated Total Time: 25-35 hours

---

## Notes
- All tasks should include appropriate error handling and logging
- Each phase should be tested before moving to the next
- MongoDB collections should follow the established naming convention
- AI prompts should be configurable and well-documented
- Consider memory usage for large novels during processing
