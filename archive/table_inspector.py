#!/usr/bin/env python3
"""
AD&D Table Inspector
Analyzes extracted content to find and improve table detection
"""

import json
import re
from pathlib import Path
from typing import List, Dict

def analyze_extracted_content(json_file: str):
    """Analyze the extracted content to find potential tables"""
    
    print(f"🔍 Analyzing extracted content from: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sections = data.get('sections', [])
    print(f"📄 Found {len(sections)} sections to analyze")
    
    # AD&D specific table patterns
    table_indicators = [
        # Combat tables
        'THAC0', 'Armor Class', 'To Hit', 'Saving Throw', 'Attack Roll',
        # Character tables  
        'Ability Score', 'Experience Points', 'Level', 'Hit Points',
        # Magic tables
        'Spell Level', 'Casting Time', 'Duration', 'Range',
        # Monster tables
        'Hit Dice', 'Armor Class', 'Movement', 'Attacks',
        # General tables
        'Table', 'Chart', 'Matrix', 'Random', 'Roll', 'Dice'
    ]
    
    potential_tables = []
    sections_with_tables = 0
    
    for i, section in enumerate(sections):
        content = section.get('content', '')
        page = section.get('page', 'Unknown')
        
        # Look for table indicators
        found_indicators = []
        for indicator in table_indicators:
            if indicator.lower() in content.lower():
                found_indicators.append(indicator)
        
        if found_indicators:
            # Analyze the content more deeply
            table_analysis = analyze_section_for_tables(content, found_indicators)
            
            if table_analysis['likely_tables']:
                sections_with_tables += 1
                potential_tables.append({
                    'section_index': i,
                    'page': page,
                    'indicators': found_indicators,
                    'analysis': table_analysis,
                    'content_preview': content[:200] + "..." if len(content) > 200 else content
                })
    
    print(f"\n📊 ANALYSIS RESULTS")
    print(f"={'='*50}")
    print(f"Sections with table indicators: {sections_with_tables}")
    print(f"Potential table sections found: {len(potential_tables)}")
    
    # Show top potential tables
    print(f"\n🔍 TOP POTENTIAL TABLES:")
    for i, table_info in enumerate(potential_tables[:10]):
        print(f"\n{i+1}. Page {table_info['page']} - Section {table_info['section_index']}")
        print(f"   Indicators: {', '.join(table_info['indicators'][:3])}")
        print(f"   Confidence: {table_info['analysis']['confidence']:.1f}%")
        print(f"   Table structures: {table_info['analysis']['table_count']}")
        print(f"   Preview: {table_info['content_preview'][:100]}...")
    
    # Show patterns found
    all_indicators = {}
    for table_info in potential_tables:
        for indicator in table_info['indicators']:
            all_indicators[indicator] = all_indicators.get(indicator, 0) + 1
    
    print(f"\n📈 MOST COMMON TABLE INDICATORS:")
    for indicator, count in sorted(all_indicators.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {indicator}: {count} sections")
    
    return potential_tables

def analyze_section_for_tables(content: str, indicators: List[str]) -> Dict:
    """Analyze a section to determine if it contains tables"""
    
    lines = content.split('\n')
    analysis = {
        'likely_tables': [],
        'table_count': 0,
        'confidence': 0,
        'patterns_found': []
    }
    
    # Pattern 1: Look for tabular data (multiple columns with alignment)
    tabular_lines = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check for multiple columns separated by spaces/tabs
        tokens = line.split()
        if len(tokens) >= 3:
            # Check if it has numbers or structured data
            numeric_tokens = sum(1 for token in tokens if any(c.isdigit() for c in token))
            if numeric_tokens >= 2:
                tabular_lines.append({
                    'line_number': i,
                    'content': line,
                    'tokens': tokens,
                    'numeric_tokens': numeric_tokens
                })
    
    if len(tabular_lines) >= 3:  # At least 3 rows of tabular data
        analysis['likely_tables'].append({
            'type': 'aligned_columns',
            'start_line': tabular_lines[0]['line_number'],
            'end_line': tabular_lines[-1]['line_number'],
            'row_count': len(tabular_lines)
        })
        analysis['table_count'] += 1
        analysis['patterns_found'].append('aligned_columns')
    
    # Pattern 2: Look for dice roll tables (d20, d100, etc.)
    dice_patterns = [
        r'\bd\d+\b',  # d20, d100, etc.
        r'\d+-\d+',   # ranges like 01-05, 15-20
        r'\d+\s*-\s*\d+',  # spaced ranges
    ]
    
    dice_table_lines = []
    for i, line in enumerate(lines):
        for pattern in dice_patterns:
            if re.search(pattern, line):
                dice_table_lines.append(i)
                break
    
    if len(dice_table_lines) >= 5:  # At least 5 lines with dice patterns
        analysis['likely_tables'].append({
            'type': 'dice_table',
            'lines_with_dice': len(dice_table_lines),
            'line_numbers': dice_table_lines[:10]  # First 10 lines
        })
        analysis['table_count'] += 1
        analysis['patterns_found'].append('dice_table')
    
    # Pattern 3: Combat tables (AC, THAC0, etc.)
    combat_patterns = [
        r'AC\s*\d+',
        r'THAC0\s*\d+',
        r'\d+\s*or\s*better',
        r'Level\s*\d+',
        r'HD\s*\d+'
    ]
    
    combat_lines = []
    for i, line in enumerate(lines):
        for pattern in combat_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                combat_lines.append(i)
                break
    
    if len(combat_lines) >= 3:
        analysis['likely_tables'].append({
            'type': 'combat_table',
            'combat_lines': len(combat_lines)
        })
        analysis['table_count'] += 1
        analysis['patterns_found'].append('combat_table')
    
    # Pattern 4: Level progression tables
    level_patterns = [
        r'Level\s*\d+',
        r'\d+st\s+Level',
        r'\d+nd\s+Level', 
        r'\d+rd\s+Level',
        r'\d+th\s+Level',
        r'Experience\s*Points?',
        r'XP\s*Required'
    ]
    
    level_lines = []
    for i, line in enumerate(lines):
        for pattern in level_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                level_lines.append(i)
                break
    
    if len(level_lines) >= 4:
        analysis['likely_tables'].append({
            'type': 'level_table',
            'level_lines': len(level_lines)
        })
        analysis['table_count'] += 1
        analysis['patterns_found'].append('level_table')
    
    # Calculate confidence
    confidence = 0
    if analysis['table_count'] > 0:
        confidence += 40  # Base confidence for finding table patterns
        confidence += min(30, analysis['table_count'] * 10)  # Bonus for multiple tables
        confidence += len(analysis['patterns_found']) * 5  # Bonus for pattern diversity
        
        # Bonus for specific AD&D indicators
        ad_d_indicators = ['THAC0', 'Armor Class', 'Hit Dice', 'Saving Throw']
        for indicator in indicators:
            if indicator in ad_d_indicators:
                confidence += 10
    
    analysis['confidence'] = min(100, confidence)
    
    return analysis

def extract_better_tables(json_file: str, output_file: str = None):
    """Re-extract tables with better detection for AD&D content"""
    
    print(f"🔧 Re-extracting tables with improved detection...")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sections = data.get('sections', [])
    total_tables_found = 0
    
    for section in sections:
        content = section.get('content', '')
        
        # Use our improved table analysis
        table_analysis = analyze_section_for_tables(content, [])
        
        if table_analysis['likely_tables']:
            # Extract the actual table data
            extracted_tables = []
            
            for table_info in table_analysis['likely_tables']:
                if table_info['type'] == 'aligned_columns':
                    table_data = extract_aligned_table(content, table_info)
                elif table_info['type'] == 'dice_table':
                    table_data = extract_dice_table(content)
                elif table_info['type'] == 'combat_table':
                    table_data = extract_combat_table(content)
                elif table_info['type'] == 'level_table':
                    table_data = extract_level_table(content)
                else:
                    table_data = None
                
                if table_data:
                    extracted_tables.append(table_data)
            
            section['tables'] = extracted_tables
            total_tables_found += len(extracted_tables)
    
    print(f"✅ Found {total_tables_found} tables with improved detection")
    
    # Save updated data
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved updated data to: {output_file}")
    
    return data

def extract_aligned_table(content: str, table_info: Dict) -> Dict:
    """Extract aligned column table"""
    lines = content.split('\n')
    start = table_info['start_line']
    end = table_info['end_line']
    
    table_lines = []
    for i in range(start, min(end + 1, len(lines))):
        line = lines[i].strip()
        if line:
            tokens = line.split()
            if len(tokens) >= 3:
                table_lines.append(tokens)
    
    if len(table_lines) >= 2:
        return {
            'type': 'aligned_columns',
            'headers': table_lines[0] if table_lines else [],
            'rows': table_lines[1:] if len(table_lines) > 1 else [],
            'row_count': len(table_lines) - 1,
            'column_count': len(table_lines[0]) if table_lines else 0
        }
    
    return None

def extract_dice_table(content: str) -> Dict:
    """Extract dice roll table"""
    lines = content.split('\n')
    dice_rows = []
    
    dice_pattern = r'(\d+[-–]\d+|\d+)\s+(.+)'
    
    for line in lines:
        line = line.strip()
        match = re.search(dice_pattern, line)
        if match:
            roll_range = match.group(1)
            result = match.group(2)
            dice_rows.append([roll_range, result])
    
    if len(dice_rows) >= 3:
        return {
            'type': 'dice_table',
            'headers': ['Roll', 'Result'],
            'rows': dice_rows,
            'row_count': len(dice_rows),
            'column_count': 2
        }
    
    return None

def extract_combat_table(content: str) -> Dict:
    """Extract combat-related table"""
    # This would need more sophisticated parsing
    # For now, return a basic structure
    return {
        'type': 'combat_table',
        'note': 'Combat table detected but needs manual parsing',
        'content_sample': content[:200]
    }

def extract_level_table(content: str) -> Dict:
    """Extract level progression table"""
    # Similar to combat table - would need more work
    return {
        'type': 'level_table', 
        'note': 'Level table detected but needs manual parsing',
        'content_sample': content[:200]
    }

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze and improve table extraction")
    parser.add_argument("json_file", help="Path to raw_extraction.json file")
    parser.add_argument("--extract", action="store_true", 
                       help="Re-extract tables with better detection")
    parser.add_argument("-o", "--output", help="Output file for improved extraction")
    
    args = parser.parse_args()
    
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        return
    
    # Analyze content
    potential_tables = analyze_extracted_content(str(json_path))
    
    if args.extract:
        output_file = args.output or str(json_path.parent / "improved_extraction.json")
        improved_data = extract_better_tables(str(json_path), output_file)
        
        print(f"\n🎯 IMPROVEMENT SUMMARY:")
        print("Run the analysis again on the improved file to see the difference!")

if __name__ == "__main__":
    main()