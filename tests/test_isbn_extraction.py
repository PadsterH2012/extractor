import unittest
from pathlib import Path
import tempfile
import re  # Add import for regex debugging

# Mock PyMuPDF document for testing
class MockDocument:
    def __init__(self, metadata=None, pages_text=None):
        self.metadata = metadata or {}
        self.pages_text = pages_text or []
        self.name = "mock_document.pdf"
        
    def __len__(self):
        return len(self.pages_text)
    
    def __getitem__(self, index):
        if index < len(self.pages_text):
            return MockPage(self.pages_text[index])
        raise IndexError("Page index out of range")
    
    def close(self):
        pass

class MockPage:
    def __init__(self, text):
        self.text = text
        self.rect = type('obj', (object,), {'width': 612})  # Standard page width
        
    def get_text(self, mode=None):
        if mode == "dict":
            return {"blocks": []}  # Simplified for testing
        return self.text

# Import the module under test
try:
    from Modules.pdf_processor import MultiGamePDFProcessor
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from Modules.pdf_processor import MultiGamePDFProcessor


class TestISBNExtraction(unittest.TestCase):
    """Test cases for ISBN extraction functionality"""

    def setUp(self):
        """Set up test environment"""
        self.processor = MultiGamePDFProcessor(debug=True)

    def test_validate_isbn_10(self):
        """Test ISBN-10 validation"""
        # Valid ISBN-10
        self.assertTrue(self.processor._validate_isbn_10("0306406152"))
        self.assertTrue(self.processor._validate_isbn_10("0131103628"))
        self.assertTrue(self.processor._validate_isbn_10("080442957X"))
        
        # Invalid ISBN-10
        self.assertFalse(self.processor._validate_isbn_10("0306406151"))  # Wrong check digit
        self.assertFalse(self.processor._validate_isbn_10("030640615"))   # Too short
        self.assertFalse(self.processor._validate_isbn_10("03064061521"))  # Too long
        self.assertFalse(self.processor._validate_isbn_10("030640615A"))  # Invalid character

    def test_validate_isbn_13(self):
        """Test ISBN-13 validation"""
        # Valid ISBN-13
        self.assertTrue(self.processor._validate_isbn_13("9780306406157"))
        self.assertTrue(self.processor._validate_isbn_13("9780131103627"))
        
        # Invalid ISBN-13
        self.assertFalse(self.processor._validate_isbn_13("9780306406158"))  # Wrong check digit
        self.assertFalse(self.processor._validate_isbn_13("978030640615"))   # Too short
        self.assertFalse(self.processor._validate_isbn_13("97803064061579"))  # Too long
        self.assertFalse(self.processor._validate_isbn_13("978030640615X"))  # Invalid character

    def test_find_isbns_in_text(self):
        """Test finding ISBNs in text"""
        # Debug the regex pattern matching directly
        isbn13_text = "ISBN-13: 978-0-306-40615-7"
        
        # Test each pattern manually
        patterns = [
            r'ISBN(?:-10)?[\s:]*(\d[\d\s-]{8}[\dXx])',
            r'ISBN-13[\s:]*(\d[\d\s-]{11}\d)',
            r'(?<!\d)(\d[\d\s-]{8}[\dXx])(?!\d)',
            r'(?<!\d)(\d[\d\s-]{11}\d)(?!\d)',
        ]
        
        print("\nDEBUG: Testing ISBN detection patterns")
        for i, pattern in enumerate(patterns):
            matches = list(re.finditer(pattern, isbn13_text, re.IGNORECASE))
            print(f"Pattern {i+1}: '{pattern}'")
            print(f"  Matches: {len(matches)}")
            for j, match in enumerate(matches):
                print(f"  Match {j+1}: {match.group(0)} -> {match.group(1)}")
        
        # Test with ISBN-10
        text_with_isbn10 = "This book has ISBN: 0-306-40615-2 on the copyright page"
        result = self.processor._find_isbns_in_text(text_with_isbn10)
        print(f"ISBN-10 test: {result}")
        self.assertIn("isbn_10", result)
        self.assertEqual(result["isbn_10"], "0306406152")
        
        # Test with ISBN-13
        text_with_isbn13 = "ISBN-13: 978-0-306-40615-7"
        result = self.processor._find_isbns_in_text(text_with_isbn13)
        print(f"ISBN-13 test: {result}")
        self.assertIn("isbn_13", result)
        self.assertEqual(result["isbn_13"], "9780306406157")
        
        # Test with both formats
        text_with_both = """
        ISBN-10: 0-306-40615-2
        ISBN-13: 978-0-306-40615-7
        """
        result = self.processor._find_isbns_in_text(text_with_both)
        self.assertIn("isbn_10", result)
        self.assertIn("isbn_13", result)
        self.assertEqual(result["isbn_10"], "0306406152")
        self.assertEqual(result["isbn_13"], "9780306406157")
        
        # Test with no ISBN
        text_without_isbn = "This text has no ISBN number in it."
        result = self.processor._find_isbns_in_text(text_without_isbn)
        self.assertEqual(result, {})

    def test_extract_isbn_from_metadata(self):
        """Test extracting ISBN from document metadata"""
        # Create a mock document with ISBN in metadata
        doc = MockDocument(metadata={
            "subject": "Fantasy RPG Book with ISBN-13: 978-0-306-40615-7",
            "keywords": "fantasy, rpg"
        })
        
        # Print the metadata for debugging
        print("\nDEBUG: Metadata content:")
        for key, value in doc.metadata.items():
            print(f"  {key}: {value}")
        
        # Debug the regex matching on metadata
        for field in ["subject", "keywords"]:
            if field in doc.metadata:
                print(f"\nTesting patterns on {field}: '{doc.metadata[field]}'")
                patterns = [
                    r'ISBN(?:-10)?[\s:]*(\d[\d\s-]{8}[\dXx])',
                    r'ISBN-13[\s:]*(\d[\d\s-]{11}\d)',
                    r'(?<!\d)(\d[\d\s-]{8}[\dXx])(?!\d)',
                    r'(?<!\d)(\d[\d\s-]{11}\d)(?!\d)',
                ]
                for i, pattern in enumerate(patterns):
                    matches = list(re.finditer(pattern, doc.metadata[field], re.IGNORECASE))
                    print(f"  Pattern {i+1}: '{pattern}'")
                    print(f"    Matches: {len(matches)}")
                    for j, match in enumerate(matches):
                        print(f"    Match {j+1}: {match.group(0)} -> {match.group(1)}")
        
        result = self.processor._extract_isbn(doc, Path("test.pdf"))
        print(f"Metadata extraction result: {result}")
        self.assertEqual(result["isbn"], "9780306406157")
        self.assertEqual(result["isbn_13"], "9780306406157")
        self.assertEqual(result["source"], "pdf_metadata")

    def test_extract_isbn_from_content(self):
        """Test extracting ISBN from document content"""
        # Create a mock document with ISBN in content
        doc = MockDocument(
            metadata={},  # No metadata
            pages_text=[
                "Title page with no ISBN",
                "Copyright page\nISBN-10: 0-306-40615-2",
                "Table of contents"
            ]
        )
        
        result = self.processor._extract_isbn(doc, Path("test.pdf"))
        self.assertEqual(result["isbn"], "0306406152")
        self.assertEqual(result["isbn_10"], "0306406152")
        self.assertEqual(result["source"], "content_page_2")

    def test_update_isbn_data(self):
        """Test updating ISBN data dictionary"""
        isbn_data = {"isbn_10": None, "isbn_13": None, "isbn": None, "source": None}
        
        # Test with ISBN-10
        self.processor._update_isbn_data(isbn_data, {"isbn_10": "0306406152"}, "test")
        self.assertEqual(isbn_data["isbn"], "0306406152")
        self.assertEqual(isbn_data["source"], "test")
        
        # Test with ISBN-13 (should override ISBN-10 as primary)
        self.processor._update_isbn_data(isbn_data, {"isbn_13": "9780306406157"}, "another_test")
        self.assertEqual(isbn_data["isbn"], "9780306406157")  # ISBN-13 is now primary
        self.assertEqual(isbn_data["source"], "test")  # Source unchanged since already set


if __name__ == '__main__':
    unittest.main()