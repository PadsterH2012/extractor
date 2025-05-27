#!/usr/bin/env python3
"""
Database Content Enhancement Tool
Retroactively applies text quality enhancement to existing database content
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

# Add the Modules directory to the path
sys.path.append(str(Path(__file__).parent / 'Modules'))

try:
    from text_quality_enhancer import TextQualityEnhancer
    from mongodb_manager import MongoDBManager
    from chromadb_manager import ChromaDBManager
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseContentEnhancer:
    """Tool for enhancing existing database content with text quality improvements"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.text_enhancer = TextQualityEnhancer(config)
        
        # Initialize database managers
        self.mongodb_manager = None
        self.chromadb_manager = None
        
        # Enhancement statistics
        self.stats = {
            'total_documents': 0,
            'enhanced_documents': 0,
            'skipped_documents': 0,
            'total_improvements': 0,
            'average_improvement': 0.0,
            'errors': 0
        }
    
    def connect_databases(self, mongodb_config: Optional[Dict] = None, chromadb_config: Optional[Dict] = None):
        """Connect to databases"""
        try:
            if mongodb_config:
                self.mongodb_manager = MongoDBManager(mongodb_config)
                logger.info("✅ Connected to MongoDB")
            
            if chromadb_config:
                self.chromadb_manager = ChromaDBManager(chromadb_config)
                logger.info("✅ Connected to ChromaDB")
                
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def analyze_content_quality(self, collection_name: str, limit: int = 100) -> Dict[str, Any]:
        """Analyze the quality of existing content in a collection"""
        if not self.mongodb_manager:
            raise ValueError("MongoDB not connected")
        
        logger.info(f"🔍 Analyzing content quality in collection: {collection_name}")
        
        # Get sample documents
        documents = self.mongodb_manager.find(collection_name, {}, limit=limit)
        
        quality_analysis = {
            'collection': collection_name,
            'total_documents': len(documents),
            'quality_scores': [],
            'issues_found': {},
            'recommendations': []
        }
        
        for doc in documents:
            content = doc.get('content', '')
            if not content or len(content.strip()) < 50:
                continue
            
            # Assess current quality
            metrics = self.text_enhancer._assess_text_quality(content)
            quality_analysis['quality_scores'].append({
                'document_id': str(doc.get('_id', 'unknown')),
                'score': metrics.overall_score,
                'grade': metrics.grade,
                'issues': metrics.issues_found,
                'word_count': metrics.word_count
            })
            
            # Aggregate issues
            for issue in metrics.issues_found:
                if issue not in quality_analysis['issues_found']:
                    quality_analysis['issues_found'][issue] = 0
                quality_analysis['issues_found'][issue] += 1
        
        # Calculate statistics
        if quality_analysis['quality_scores']:
            scores = [item['score'] for item in quality_analysis['quality_scores']]
            quality_analysis['average_score'] = sum(scores) / len(scores)
            quality_analysis['min_score'] = min(scores)
            quality_analysis['max_score'] = max(scores)
            
            # Generate recommendations
            if quality_analysis['average_score'] < 80:
                quality_analysis['recommendations'].append("Collection would benefit from text quality enhancement")
            if quality_analysis['min_score'] < 60:
                quality_analysis['recommendations'].append("Some documents have very poor quality and need immediate attention")
            if 'High spelling error rate' in quality_analysis['issues_found']:
                quality_analysis['recommendations'].append("Spell checking enhancement recommended")
            if 'OCR artifact' in str(quality_analysis['issues_found']):
                quality_analysis['recommendations'].append("OCR cleanup enhancement recommended")
        
        return quality_analysis
    
    def enhance_collection(self, collection_name: str, 
                          dry_run: bool = True, 
                          min_quality_threshold: float = 75.0,
                          aggressive_cleanup: bool = False,
                          batch_size: int = 10) -> Dict[str, Any]:
        """Enhance all content in a collection"""
        if not self.mongodb_manager:
            raise ValueError("MongoDB not connected")
        
        logger.info(f"🚀 {'DRY RUN: ' if dry_run else ''}Enhancing collection: {collection_name}")
        logger.info(f"   Min quality threshold: {min_quality_threshold}%")
        logger.info(f"   Aggressive cleanup: {aggressive_cleanup}")
        logger.info(f"   Batch size: {batch_size}")
        
        # Get all documents
        documents = self.mongodb_manager.find(collection_name, {})
        self.stats['total_documents'] = len(documents)
        
        enhancement_results = {
            'collection': collection_name,
            'dry_run': dry_run,
            'enhanced_documents': [],
            'skipped_documents': [],
            'errors': [],
            'summary': {}
        }
        
        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
            
            for doc in batch:
                try:
                    result = self._enhance_document(doc, min_quality_threshold, aggressive_cleanup, dry_run)
                    
                    if result['enhanced']:
                        enhancement_results['enhanced_documents'].append(result)
                        self.stats['enhanced_documents'] += 1
                        self.stats['total_improvements'] += result['improvement']
                    else:
                        enhancement_results['skipped_documents'].append(result)
                        self.stats['skipped_documents'] += 1
                        
                except Exception as e:
                    error_info = {
                        'document_id': str(doc.get('_id', 'unknown')),
                        'error': str(e)
                    }
                    enhancement_results['errors'].append(error_info)
                    self.stats['errors'] += 1
                    logger.error(f"❌ Error processing document {error_info['document_id']}: {e}")
        
        # Calculate summary statistics
        if self.stats['enhanced_documents'] > 0:
            self.stats['average_improvement'] = self.stats['total_improvements'] / self.stats['enhanced_documents']
        
        enhancement_results['summary'] = self.stats.copy()
        
        logger.info(f"✅ Enhancement {'simulation' if dry_run else 'process'} complete!")
        logger.info(f"   Total documents: {self.stats['total_documents']}")
        logger.info(f"   Enhanced: {self.stats['enhanced_documents']}")
        logger.info(f"   Skipped: {self.stats['skipped_documents']}")
        logger.info(f"   Errors: {self.stats['errors']}")
        if self.stats['enhanced_documents'] > 0:
            logger.info(f"   Average improvement: +{self.stats['average_improvement']:.1f}%")
        
        return enhancement_results
    
    def _enhance_document(self, doc: Dict, min_threshold: float, aggressive: bool, dry_run: bool) -> Dict[str, Any]:
        """Enhance a single document"""
        doc_id = str(doc.get('_id', 'unknown'))
        content = doc.get('content', '')
        
        if not content or len(content.strip()) < 50:
            return {
                'document_id': doc_id,
                'enhanced': False,
                'reason': 'Content too short or empty',
                'before_score': 0,
                'after_score': 0,
                'improvement': 0
            }
        
        # Assess current quality
        before_metrics = self.text_enhancer._assess_text_quality(content)
        
        # Skip if already high quality
        if before_metrics.overall_score >= min_threshold:
            return {
                'document_id': doc_id,
                'enhanced': False,
                'reason': f'Already high quality ({before_metrics.overall_score:.1f}%)',
                'before_score': before_metrics.overall_score,
                'after_score': before_metrics.overall_score,
                'improvement': 0
            }
        
        # Enhance the content
        enhancement_result = self.text_enhancer.enhance_text_quality(content, aggressive=aggressive)
        quality_summary = self.text_enhancer.get_quality_summary(enhancement_result)
        
        # Prepare update data
        update_data = {
            'content': enhancement_result.cleaned_text,
            'text_quality_enhanced': True,
            'text_quality_before': quality_summary['before'],
            'text_quality_after': quality_summary['after'],
            'text_quality_improvement': quality_summary['improvement'],
            'enhancement_timestamp': datetime.now().isoformat(),
            'enhancement_aggressive': aggressive
        }
        
        # Update database if not dry run
        if not dry_run:
            self.mongodb_manager.updateOne(
                doc.get('collection_name', 'unknown'),
                {'_id': doc['_id']},
                {'$set': update_data}
            )
        
        return {
            'document_id': doc_id,
            'enhanced': True,
            'before_score': quality_summary['before']['score'],
            'after_score': quality_summary['after']['score'],
            'improvement': quality_summary['improvement']['score_change'],
            'corrections_made': quality_summary['improvement']['corrections_made'],
            'grade_change': quality_summary['improvement']['grade_change'],
            'update_data': update_data if dry_run else None
        }
    
    def generate_report(self, analysis_results: Dict, enhancement_results: Dict = None) -> str:
        """Generate a comprehensive report"""
        report = []
        report.append("=" * 80)
        report.append("📊 DATABASE CONTENT QUALITY REPORT")
        report.append("=" * 80)
        
        # Analysis section
        report.append(f"\n🔍 QUALITY ANALYSIS - {analysis_results['collection']}")
        report.append("-" * 50)
        report.append(f"Total documents analyzed: {analysis_results['total_documents']}")
        
        if analysis_results['quality_scores']:
            report.append(f"Average quality score: {analysis_results['average_score']:.1f}%")
            report.append(f"Quality range: {analysis_results['min_score']:.1f}% - {analysis_results['max_score']:.1f}%")
            
            # Grade distribution
            grades = {}
            for item in analysis_results['quality_scores']:
                grade = item['grade']
                grades[grade] = grades.get(grade, 0) + 1
            
            report.append(f"Grade distribution: {dict(sorted(grades.items()))}")
        
        # Issues found
        if analysis_results['issues_found']:
            report.append(f"\n🚨 Common Issues Found:")
            for issue, count in sorted(analysis_results['issues_found'].items(), key=lambda x: x[1], reverse=True):
                report.append(f"   • {issue}: {count} documents")
        
        # Recommendations
        if analysis_results['recommendations']:
            report.append(f"\n💡 Recommendations:")
            for rec in analysis_results['recommendations']:
                report.append(f"   • {rec}")
        
        # Enhancement results
        if enhancement_results:
            report.append(f"\n🚀 ENHANCEMENT RESULTS")
            report.append("-" * 50)
            summary = enhancement_results['summary']
            report.append(f"Total documents: {summary['total_documents']}")
            report.append(f"Enhanced: {summary['enhanced_documents']}")
            report.append(f"Skipped: {summary['skipped_documents']}")
            report.append(f"Errors: {summary['errors']}")
            
            if summary['enhanced_documents'] > 0:
                report.append(f"Average improvement: +{summary['average_improvement']:.1f}%")
                
                # Show some examples
                report.append(f"\n📈 Top Improvements:")
                enhanced_docs = sorted(enhancement_results['enhanced_documents'], 
                                     key=lambda x: x['improvement'], reverse=True)
                for i, doc in enumerate(enhanced_docs[:5]):
                    report.append(f"   {i+1}. Document {doc['document_id']}: "
                                f"{doc['before_score']:.1f}% → {doc['after_score']:.1f}% "
                                f"(+{doc['improvement']:.1f}%, {doc['grade_change']})")
        
        report.append("\n" + "=" * 80)
        return "\n".join(report)

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhance existing database content quality")
    parser.add_argument("--collection", required=True, help="Collection name to enhance")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze, don't enhance")
    parser.add_argument("--dry-run", action="store_true", help="Simulate enhancement without updating")
    parser.add_argument("--aggressive", action="store_true", help="Use aggressive cleanup mode")
    parser.add_argument("--threshold", type=float, default=75.0, help="Minimum quality threshold")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    parser.add_argument("--limit", type=int, default=100, help="Limit for analysis")
    
    args = parser.parse_args()
    
    # Initialize enhancer
    enhancer = DatabaseContentEnhancer()
    
    # Connect to databases (you'll need to configure these)
    mongodb_config = {
        'connection_string': 'mongodb://localhost:27017/',
        'database_name': 'rpger'
    }
    
    try:
        enhancer.connect_databases(mongodb_config=mongodb_config)
        
        # Analyze content quality
        print("🔍 Analyzing content quality...")
        analysis_results = enhancer.analyze_content_quality(args.collection, limit=args.limit)
        
        enhancement_results = None
        if not args.analyze_only:
            # Enhance content
            print("🚀 Enhancing content...")
            enhancement_results = enhancer.enhance_collection(
                args.collection,
                dry_run=args.dry_run,
                min_quality_threshold=args.threshold,
                aggressive_cleanup=args.aggressive,
                batch_size=args.batch_size
            )
        
        # Generate and display report
        report = enhancer.generate_report(analysis_results, enhancement_results)
        print(report)
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"content_enhancement_report_{args.collection}_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"❌ Enhancement failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
