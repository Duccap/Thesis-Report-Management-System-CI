import unittest
from unittest.mock import patch, MagicMock
from processor import get_most_common_words

class TestProcessor(unittest.TestCase):

    @patch('processor.pdfplumber.open')
    def test_get_most_common_words(self, mock_pdf_open):
        # Arrange: Mock the pdfplumber.open to return a mock PDF object
        mock_pdf = mock_pdf_open.return_value.__enter__.return_value
        # Mock the PDF pages and their text content
        mock_pdf.pages = [MagicMock(), MagicMock()]
        mock_pdf.pages[0].extract_text.return_value = "This is a test."
        mock_pdf.pages[1].extract_text.return_value = "Another test."

        # Act: Call the get_most_common_words function with a dummy file location
        result = get_most_common_words('dummy_file_location')

        # Assert: Check if the result matches the expected output
        expected_words = ['This', 'is', 'a', 'Another']
        self.assertEqual(result, expected_words)

if __name__ == '__main__':
    unittest.main()