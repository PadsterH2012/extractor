#!/usr/bin/env python3
"""
PDF Extraction Confidence Tester
Tests extraction quality and provides confidence metrics before full processing
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
import fitz  # PyMuPDF
import numpy as np
from dataclasses import dataclass
import re
from datetime import datetime

@dataclass
class ConfidenceMetrics:
    overall_confidence: float
    text_extraction_confidence: float
    ocr_confidence: float
    layout_detection_confidence: float
    table_detection_confidence: float
    content_structure_confidence: float
    recommended_method: str
    issues_found: List[str]
    sample_extractions: List[Dict]

class PDFConfidenceTester:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(pdf_path)
        self.logger = logging.getLogger(__name__)
        
        # Test configuration
        self.test_pages = min(5, len(self.doc))  # Test first 5 pages or all if fewer
        self.sample_size = 3  # Number of sample extractions to show
        
    def run_comprehensive_test(self) -> ConfidenceMetrics:
        """Run all confidence tests and return comprehensive metrics"""
        self.logger.info(f"Running confidence tests on {self.pdf_path.name}")
        self.logger.info(f"Testing {self.test_pages} pages out of {len(self.doc)} total")
        
        # Run individual tests
        text_conf = self._test_text_extraction()
        ocr_conf = self._test_ocr_extraction()
        layout_conf = self._test_layout_detection()
        table_conf = self._test_table_detection()
        structure_conf = self._test_content_structure()
        
        # Collect issues
        issues = []
        issues.extend(text_conf.get('issues', []))
        issues.extend(ocr_conf.get('issues', []))
        issues.extend(layout_conf.get('issues', []))
        issues.extend(table_conf.get('issues', []))
        issues.extend(structure_conf.get('issues', []))
        
        # Calculate overall confidence
        weights = {
            'text': 0.3,
            'ocr': 0.2,
            'layout': 0.2,
            'table': 0.15,
            'structure': 0.15
        }
        
        overall = (
            text_conf['confidence'] * weights['text'] +
            ocr_conf['confidence'] * weights['ocr'] +
            layout_conf['confidence'] * weights['layout'] +
            table_conf['confidence'] * weights['table'] +
            structure_conf['confidence'] * weights['structure']
        )
        
        # Determine recommended method
        recommended = self._determine_best_method(text_conf, ocr_conf, layout_conf)
        
        # Collect sample extractions
        samples = []
        samples.extend(text_conf.get('samples', [])[:2])
        samples.extend(ocr_conf.get('samples', [])[:1])
        
        return ConfidenceMetrics(
            overall_confidence=overall,
            text_extraction_confidence=text_conf['confidence'],
            ocr_confidence=ocr_conf['confidence'],
            layout_detection_confidence=layout_conf['confidence'],
            table_detection_confidence=table_conf['confidence'],
            content_structure_confidence=structure_conf['confidence'],
            recommended_method=recommended,
            issues_found=issues,
            sample_extractions=samples
        )
    
    def _test_text_extraction(self) -> Dict:
        """Test text-based extraction confidence"""
        self.logger.info("Testing text extraction...")
        
        total_chars = 0
        extractable_pages = 0
        text_samples = []
        issues = []
        
        for page_num in range(self.test_pages):
            page = self.doc[page_num]
            text = page.get_text()
            
            total_chars += len(text)
            
            if len(text.strip()) > 50:  # Meaningful text threshold
                extractable_pages += 1
                
                # Collect sample
                if len(text_samples) < self.sample_size:
                    text_samples.append({
                        'page': page_num + 1,
                        'method': 'text_extraction',
                        'content': text[:300] + "..." if len(text) > 300 else text,
                        'char_count': len(text),
                        'word_count': len(text.split())
                    })
            else:
                issues.append(f"Page {page_num + 1}: Very little extractable text ({len(text)} chars)")
        
        # Calculate confidence
        if self.test_pages == 0:
            confidence = 0
        else:
            page_coverage = extractable_pages / self.test_pages
            avg_chars_per_page = total_chars / self.test_pages
            
            # Score based on coverage and content density
            if page_coverage > 0.8 and avg_chars_per_page > 500:
                confidence = 95
            elif page_coverage > 0.6 and avg_chars_per_page > 200:
                confidence = 80
            elif page_coverage > 0.4:
                confidence = 60
            elif page_coverage > 0.2:
                confidence = 40
            else:
                confidence = 20
        
        if confidence < 70:
            issues.append(f"Low text extraction confidence: {confidence}%")
        
        return {
            'confidence': confidence,
            'extractable_pages': extractable_pages,
            'total_chars': total_chars,
            'avg_chars_per_page': total_chars / self.test_pages if self.test_pages > 0 else 0,
            'samples': text_samples,
            'issues': issues
        }
    
    def _test_ocr_extraction(self) -> Dict:
        """Test OCR-based extraction confidence"""
        self.logger.info("Testing OCR extraction...")
        
        try:
            import pytesseract
            import cv2
            import numpy as np
        except ImportError:
            return {
                'confidence': 0,
                'samples': [],
                'issues': ['OCR dependencies not installed (pytesseract, opencv-python)']
            }
        
        ocr_samples = []
        confidence_scores = []
        issues = []
        
        for page_num in range(min(3, self.test_pages)):  # Test fewer pages for OCR (slower)
            try:
                page = self.doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale
                img_data = pix.tobytes("png")
                
                # Convert to OpenCV format
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Test OCR on full page
                ocr_data = pytesseract.image_to_data(
                    img, 
                    config=r'--oem 3 --psm 6',
                    output_type=pytesseract.Output.DICT
                )
                
                # Calculate confidence
                confidences = [c for c in ocr_data['conf'] if c > 0]
                page_confidence = sum(confidences) / len(confidences) if confidences else 0
                confidence_scores.append(page_confidence)
                
                # Extract text
                words = []
                for i, (text, conf) in enumerate(zip(ocr_data['text'], ocr_data['conf'])):
                    if conf > 30 and text.strip():
                        words.append(text)
                
                ocr_text = ' '.join(words)
                
                if len(ocr_samples) < self.sample_size:
                    ocr_samples.append({
                        'page': page_num + 1,
                        'method': 'ocr_extraction',
                        'content': ocr_text[:300] + "..." if len(ocr_text) > 300 else ocr_text,
                        'confidence': page_confidence,
                        'word_count': len(words)
                    })
                
                if page_confidence < 50:
                    issues.append(f"Page {page_num + 1}: Low OCR confidence ({page_confidence:.1f}%)")
                    
            except Exception as e:
                issues.append(f"Page {page_num + 1}: OCR failed - {str(e)}")
                confidence_scores.append(0)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            'confidence': avg_confidence,
            'page_confidences': confidence_scores,
            'samples': ocr_samples,
            'issues': issues
        }
    
    def _test_layout_detection(self) -> Dict:
        """Test layout detection (single vs multi-column)"""
        self.logger.info("Testing layout detection...")
        
        layout_results = []
        issues = []
        
        for page_num in range(self.test_pages):
            page = self.doc[page_num]
            
            # Get text blocks with positions
            blocks = page.get_text("dict")
            text_blocks = []
            page_width = 0
            
            for block in blocks.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    bbox = block.get("bbox", [0, 0, 0, 0])
                    x0, y0, x1, y1 = bbox
                    page_width = max(page_width, x1)
                    
                    if x1 - x0 > 50 and y1 - y0 > 10:  # Reasonable size
                        text_blocks.append({
                            'bbox': bbox,
                            'width': x1 - x0,
                            'x_center': (x0 + x1) / 2
                        })
            
            # Analyze layout
            layout_analysis = self._analyze_page_layout(text_blocks, page_width)
            layout_results.append({
                'page': page_num + 1,
                'layout_type': layout_analysis['type'],
                'confidence': layout_analysis['confidence'],
                'text_blocks': len(text_blocks)
            })
            
            if layout_analysis['confidence'] < 70:
                issues.append(f"Page {page_num + 1}: Uncertain layout detection ({layout_analysis['confidence']:.1f}%)")
        
        # Overall layout confidence
        avg_confidence = sum(r['confidence'] for r in layout_results) / len(layout_results) if layout_results else 0
        
        # Check consistency
        layout_types = [r['layout_type'] for r in layout_results]
        most_common = max(set(layout_types), key=layout_types.count) if layout_types else 'unknown'
        consistency = layout_types.count(most_common) / len(layout_types) if layout_types else 0
        
        if consistency < 0.8:
            issues.append(f"Inconsistent layout detection across pages (consistency: {consistency:.1%})")
        
        return {
            'confidence': avg_confidence,
            'dominant_layout': most_common,
            'layout_consistency': consistency,
            'page_results': layout_results,
            'issues': issues
        }
    
    def _analyze_page_layout(self, text_blocks: List[Dict], page_width: float) -> Dict:
        """Analyze layout of a single page"""
        if not text_blocks or page_width == 0:
            return {'type': 'unknown', 'confidence': 0}
        
        # Group blocks by horizontal position
        left_blocks = [b for b in text_blocks if b['x_center'] < page_width * 0.4]
        right_blocks = [b for b in text_blocks if b['x_center'] > page_width * 0.6]
        center_blocks = [b for b in text_blocks if page_width * 0.4 <= b['x_center'] <= page_width * 0.6]
        
        # Calculate content distribution
        left_content = len(left_blocks)
        right_content = len(right_blocks)
        center_content = len(center_blocks)
        total_blocks = len(text_blocks)
        
        # Determine layout type
        if left_content > 2 and right_content > 2 and center_content < total_blocks * 0.3:
            layout_type = 'two_column'
            # Confidence based on balance
            balance = 1 - abs(left_content - right_content) / max(left_content + right_content, 1)
            confidence = min(90, 60 + balance * 30)
        elif center_content > total_blocks * 0.6:
            layout_type = 'single_column'
            confidence = 85
        else:
            layout_type = 'mixed'
            confidence = 50
        
        return {
            'type': layout_type,
            'confidence': confidence,
            'left_blocks': left_content,
            'right_blocks': right_content,
            'center_blocks': center_content
        }
    
    def _test_table_detection(self) -> Dict:
        """Test table detection capabilities"""
        self.logger.info("Testing table detection...")
        
        table_indicators = [
            'Table', 'Chart', 'Matrix', 'Level', 'Dice', 'Roll',
            'AC', 'HD', 'HP', 'THAC0', 'Save', 'XP', 'Spell Level'
        ]
        
        detected_tables = []
        issues = []
        
        # Test with pdfplumber if available
        try:
            import pdfplumber
            
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num in range(self.test_pages):
                    if page_num < len(pdf.pages):
                        page = pdf.pages[page_num]
                        tables = page.extract_tables()
                        
                        for i, table in enumerate(tables):
                            if table and len(table) > 1:
                                detected_tables.append({
                                    'page': page_num + 1,
                                    'table_index': i,
                                    'rows': len(table),
                                    'columns': len(table[0]) if table else 0,
                                    'method': 'pdfplumber'
                                })
                                
        except ImportError:
            issues.append("pdfplumber not available for advanced table detection")
        except Exception as e:
            issues.append(f"Table extraction failed: {str(e)}")
        
        # Test text-based table detection
        for page_num in range(self.test_pages):
            page = self.doc[page_num]
            text = page.get_text()
            
            # Look for table indicators
            for indicator in table_indicators:
                if indicator.lower() in text.lower():
                    # Try to find structured data nearby
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if indicator.lower() in line.lower():
                            # Check next few lines for table-like structure
                            potential_table_lines = lines[i:i+10]
                            if self._looks_like_table(potential_table_lines):
                                detected_tables.append({
                                    'page': page_num + 1,
                                    'indicator': indicator,
                                    'context': line.strip(),
                                    'method': 'text_pattern'
                                })
                                break
        
        # Calculate confidence
        pages_with_tables = len(set(t['page'] for t in detected_tables))
        table_coverage = pages_with_tables / self.test_pages if self.test_pages > 0 else 0
        
        if table_coverage > 0.6:
            confidence = 90
        elif table_coverage > 0.4:
            confidence = 75
        elif table_coverage > 0.2:
            confidence = 60
        elif detected_tables:
            confidence = 45
        else:
            confidence = 30
            issues.append("Few or no tables detected - may miss structured data")
        
        return {
            'confidence': confidence,
            'detected_tables': len(detected_tables),
            'pages_with_tables': pages_with_tables,
            'table_coverage': table_coverage,
            'table_details': detected_tables[:5],  # Show first 5
            'issues': issues
        }
    
    def _looks_like_table(self, lines: List[str]) -> bool:
        """Check if lines look like they contain tabular data"""
        tabular_lines = 0
        
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if not line:
                continue
                
            # Count numeric/structured elements
            tokens = line.split()
            if len(tokens) >= 3:  # At least 3 columns
                numeric_tokens = sum(1 for token in tokens if any(c.isdigit() for c in token))
                if numeric_tokens >= 2:  # At least 2 numeric elements
                    tabular_lines += 1
        
        return tabular_lines >= 2  # At least 2 table-like lines
    
    def _test_content_structure(self) -> Dict:
        """Test content structure recognition"""
        self.logger.info("Testing content structure...")
        
        structure_elements = {
            'headings': 0,
            'paragraphs': 0,
            'lists': 0,
            'tables': 0
        }
        
        issues = []
        total_text_length = 0
        
        for page_num in range(self.test_pages):
            page = self.doc[page_num]
            text = page.get_text()
            total_text_length += len(text)
            
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect headings (ALL CAPS, numbered, etc.)
                if (line.isupper() and len(line) > 5 and len(line) < 80) or \
                   re.match(r'^\d+\.\s+[A-Z]', line) or \
                   (line.endswith(':') and len(line.split()) <= 6):
                    structure_elements['headings'] += 1
                
                # Detect lists
                elif re.match(r'^\s*[-*•]\s+', line) or \
                     re.match(r'^\s*\d+\)\s+', line) or \
                     re.match(r'^\s*[a-z]\)\s+', line):
                    structure_elements['lists'] += 1
                
                # Regular paragraphs
                elif len(line) > 20:
                    structure_elements['paragraphs'] += 1
        
        # Calculate structure confidence
        total_elements = sum(structure_elements.values())
        
        if total_elements == 0:
            confidence = 0
            issues.append("No structured content detected")
        else:
            # Good structure has mix of headings, paragraphs, some lists
            heading_ratio = structure_elements['headings'] / total_elements
            paragraph_ratio = structure_elements['paragraphs'] / total_elements
            
            if 0.05 <= heading_ratio <= 0.3 and paragraph_ratio >= 0.4:
                confidence = 85
            elif heading_ratio > 0 and paragraph_ratio > 0.2:
                confidence = 70
            elif paragraph_ratio > 0.5:
                confidence = 60
            else:
                confidence = 40
                issues.append("Irregular content structure detected")
        
        return {
            'confidence': confidence,
            'structure_elements': structure_elements,
            'total_elements': total_elements,
            'avg_text_per_page': total_text_length / self.test_pages if self.test_pages > 0 else 0,
            'issues': issues
        }
    
    def _determine_best_method(self, text_conf: Dict, ocr_conf: Dict, layout_conf: Dict) -> str:
        """Determine the best extraction method based on test results"""
        
        text_score = text_conf['confidence']
        ocr_score = ocr_conf['confidence']
        
        # Factor in layout complexity
        layout_type = layout_conf.get('dominant_layout', 'unknown')
        layout_penalty = 10 if layout_type == 'two_column' else 0
        
        # Adjust scores
        adjusted_text_score = text_score - layout_penalty
        adjusted_ocr_score = ocr_score
        
        if adjusted_text_score > 70 and adjusted_text_score > adjusted_ocr_score + 15:
            return "text"
        elif adjusted_ocr_score > 60 and adjusted_ocr_score > adjusted_text_score + 10:
            return "ocr"
        elif adjusted_text_score > 50:
            return "text"  # Prefer text when close
        elif adjusted_ocr_score > 40:
            return "ocr"
        else:
            return "manual_review_needed"

def run_quick_test(pdf_path: str, pages_to_test: int = 3) -> Dict:
    """Run a quick confidence test on just a few pages"""
    tester = PDFConfidenceTester(pdf_path)
    tester.test_pages = min(pages_to_test, len(tester.doc))
    
    # Run basic tests only
    text_conf = tester._test_text_extraction()
    layout_conf = tester._test_layout_detection()
    
    return {
        'quick_confidence': (text_conf['confidence'] + layout_conf['confidence']) / 2,
        'recommended_method': 'text' if text_conf['confidence'] > 60 else 'ocr',
        'text_confidence': text_conf['confidence'],
        'layout_confidence': layout_conf['confidence'],
        'issues': text_conf.get('issues', []) + layout_conf.get('issues', [])
    }

def generate_confidence_report(metrics: ConfidenceMetrics, output_path: str = None):
    """Generate a detailed confidence report"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'overall_assessment': {
            'confidence': metrics.overall_confidence,
            'grade': _confidence_to_grade(metrics.overall_confidence),
            'recommended_method': metrics.recommended_method
        },
        'detailed_scores': {
            'text_extraction': metrics.text_extraction_confidence,
            'ocr_extraction': metrics.ocr_confidence,
            'layout_detection': metrics.layout_detection_confidence,
            'table_detection': metrics.table_detection_confidence,
            'content_structure': metrics.content_structure_confidence
        },
        'issues_found': metrics.issues_found,
        'sample_extractions': metrics.sample_extractions,
        'recommendations': _generate_recommendations(metrics)
    }
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report

def _confidence_to_grade(confidence: float) -> str:
    """Convert confidence score to letter grade"""
    if confidence >= 90:
        return "A (Excellent)"
    elif confidence >= 80:
        return "B (Good)"
    elif confidence >= 70:
        return "C (Fair)"
    elif confidence >= 60:
        return "D (Poor)"
    else:
        return "F (Failed)"

def _generate_recommendations(metrics: ConfidenceMetrics) -> List[str]:
    """Generate actionable recommendations based on metrics"""
    recommendations = []
    
    if metrics.overall_confidence >= 80:
        recommendations.append("✅ PDF is ready for extraction with high confidence")
    
    if metrics.text_extraction_confidence < 60:
        recommendations.append("⚠️ Consider using OCR method due to low text extraction confidence")
    
    if metrics.ocr_confidence < 50 and metrics.text_extraction_confidence < 60:
        recommendations.append("🔍 Manual review strongly recommended - both methods show low confidence")
    
    if metrics.layout_detection_confidence < 70:
        recommendations.append("📋 Check multi-column layout handling - may need manual verification")
    
    if metrics.table_detection_confidence < 60:
        recommendations.append("📊 Tables may not be extracted properly - verify table content manually")
    
    if "two_column" in str(metrics.sample_extractions):
        recommendations.append("📖 Multi-column layout detected - ensure proper reading order")
    
    if len(metrics.issues_found) > 5:
        recommendations.append("⚠️ Multiple issues detected - consider processing in smaller sections")
    
    return recommendations

# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test PDF extraction confidence")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("-p", "--pages", type=int, default=5, help="Number of pages to test")
    parser.add_argument("-q", "--quick", action="store_true", help="Run quick test only")
    parser.add_argument("-o", "--output", help="Output report file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    try:
        if args.quick:
            results = run_quick_test(args.pdf_path, args.pages)
            print(f"\n=== QUICK CONFIDENCE TEST ===")
            print(f"Overall Confidence: {results['quick_confidence']:.1f}%")
            print(f"Recommended Method: {results['recommended_method']}")
            print(f"Text Confidence: {results['text_confidence']:.1f}%")
            print(f"Layout Confidence: {results['layout_confidence']:.1f}%")
            
            if results['issues']:
                print(f"\nIssues Found:")
                for issue in results['issues']:
                    print(f"  - {issue}")
        else:
            tester = PDFConfidenceTester(args.pdf_path)
            tester.test_pages = args.pages
            metrics = tester.run_comprehensive_test()
            
            # Generate report
            report = generate_confidence_report(metrics, args.output)
            
            print(f"\n=== COMPREHENSIVE CONFIDENCE TEST ===")
            print(f"Overall Confidence: {metrics.overall_confidence:.1f}% ({_confidence_to_grade(metrics.overall_confidence)})")
            print(f"Recommended Method: {metrics.recommended_method}")
            print(f"\nDetailed Scores:")
            print(f"  Text Extraction: {metrics.text_extraction_confidence:.1f}%")
            print(f"  OCR Extraction: {metrics.ocr_confidence:.1f}%")
            print(f"  Layout Detection: {metrics.layout_detection_confidence:.1f}%")
            print(f"  Table Detection: {metrics.table_detection_confidence:.1f}%")
            print(f"  Content Structure: {metrics.content_structure_confidence:.1f}%")
            
            if metrics.issues_found:
                print(f"\nIssues Found ({len(metrics.issues_found)}):")
                for issue in metrics.issues_found[:10]:  # Show first 10
                    print(f"  - {issue}")
            
            print(f"\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  {rec}")
            
            if args.output:
                print(f"\nDetailed report saved to: {args.output}")
    
    except Exception as e:
        logging.error(f"Test failed: {e}")
        exit(1)
