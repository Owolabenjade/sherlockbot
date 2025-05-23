# tests/test_cv_service.py - Test CV analysis services
import os
import unittest
import tempfile
from unittest.mock import patch, MagicMock
from services.cv_service import (
    extract_text_from_cv,
    analyze_cv_structure,
    identify_sections,
    analyze_cv_basic,
    analyze_cv_advanced
)

class TestCVService(unittest.TestCase):
    
    def setUp(self):
        # Create a sample CV text for testing
        self.sample_cv_text = """
        JOHN DOE
        john.doe@example.com | (555) 123-4567 | linkedin.com/in/johndoe
        
        SUMMARY
        Experienced software engineer with 5+ years of expertise in Python, JavaScript, and cloud technologies.
        
        EXPERIENCE
        Senior Software Engineer
        ABC Tech, New York, NY
        June 2020 - Present
        • Led development of a microservices architecture that improved system scalability by 40%
        • Implemented CI/CD pipelines reducing deployment time by 30%
        • Mentored 3 junior developers on best practices
        
        Software Developer
        XYZ Solutions, Boston, MA
        January 2018 - May 2020
        • Developed RESTful APIs using Flask and Django
        • Reduced database query times by 25% through optimization
        • Collaborated with UX team on front-end development
        
        EDUCATION
        Bachelor of Science in Computer Science
        State University, 2017
        
        SKILLS
        • Programming: Python, JavaScript, Java
        • Web: React, Node.js, HTML/CSS
        • Database: PostgreSQL, MongoDB
        • Tools: Git, Docker, AWS
        
        CERTIFICATIONS
        • AWS Certified Developer
        • Certified Scrum Master
        
        LANGUAGES
        English (Native), Spanish (Intermediate)
        
        INTERESTS
        Hiking, Photography, Open Source Contributing
        """
        
        # Create a temporary file with CV content
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        self.temp_file.write(self.sample_cv_text.encode('utf-8'))
        self.temp_file.close()
        
        # Prepare cv_data for testing
        self.cv_data = {
            'full_text': self.sample_cv_text,
            'sections': {
                'summary': 'Experienced software engineer with 5+ years of expertise in Python, JavaScript, and cloud technologies.',
                'experience': 'Senior Software Engineer\nABC Tech...',
                'education': 'Bachelor of Science in Computer Science...',
                'skills': 'Programming: Python, JavaScript, Java...',
                'certifications': 'AWS Certified Developer...',
                'languages': 'English (Native), Spanish (Intermediate)',
                'interests': 'Hiking, Photography, Open Source Contributing'
            },
            'contact_info': {
                'email': 'john.doe@example.com',
                'phone': '(555) 123-4567',
                'linkedin': 'linkedin.com/in/johndoe'
            },
            'metrics': {
                'word_count': 200,
                'sentence_count': 20,
                'avg_sentence_length': 10,
                'bullet_points': 12
            }
        }
    
    def tearDown(self):
        # Remove the temporary file
        os.unlink(self.temp_file.name)
    
    def test_identify_sections(self):
        sections = identify_sections(self.sample_cv_text)
        self.assertIn('summary', sections)
        self.assertIn('experience', sections)
        self.assertIn('education', sections)
        self.assertIn('skills', sections)
    
    def test_analyze_cv_structure(self):
        structure = analyze_cv_structure(self.sample_cv_text)
        self.assertIn('sections', structure)
        self.assertIn('contact_info', structure)
        self.assertIn('metrics', structure)
        
        # Check if contact info was extracted
        self.assertIn('email', structure['contact_info'])
        self.assertEqual(structure['contact_info']['email'], 'john.doe@example.com')
    
    def test_analyze_cv_basic(self):
        result = analyze_cv_basic(self.cv_data)
        self.assertTrue(result['success'])
        self.assertIn('insights', result)
        self.assertGreaterEqual(len(result['insights']), 5)
    
    def test_analyze_cv_advanced(self):
        result = analyze_cv_advanced(self.cv_data)
        self.assertTrue(result['success'])
        self.assertIn('improvement_score', result)
        self.assertIn('insights', result)
        self.assertGreaterEqual(len(result['insights']), 7)
        
        # Check score is within expected range
        self.assertGreaterEqual(result['improvement_score'], 40)
        self.assertLessEqual(result['improvement_score'], 95)
        
        # Check if section scores are calculated
        self.assertIn('section_scores', result)
        self.assertIn('overall_structure', result['section_scores'])

if __name__ == '__main__':
    unittest.main()