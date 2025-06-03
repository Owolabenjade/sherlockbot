# services/cv_service.py - Enhanced CV analysis service
import os
import uuid
import time
import requests
import PyPDF2
import docx
from datetime import datetime
import nltk
from nltk.tokenize import sent_tokenize
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle
from firebase_admin import storage
from services.firebase_service import download_file_from_storage, get_file_download_url
from utils.logger import get_logger
from config import Config

# Initialize logger
logger = get_logger()

# Download NLTK resources if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


def process_basic_review(storage_path):
    try:
        local_file_path = download_file_from_storage(storage_path)
        cv_data = extract_text_from_cv(local_file_path)
        cv_data['file_path'] = local_file_path

        if Config.CV_ANALYSIS_API_URL:
            review_result = call_cv_analysis_api(cv_data, 'basic')
        else:
            review_result = analyze_cv_basic(cv_data)

        review_result['cv_file_name'] = os.path.basename(storage_path)
        review_result['review_type'] = 'basic'
        review_result['success'] = True

        if os.path.exists(local_file_path):
            os.remove(local_file_path)

        return review_result

    except Exception as e:
        logger.error(f"Error in basic review processing: {str(e)}")
        return {'success': False, 'error': str(e)}


def process_advanced_review(storage_path):
    try:
        local_file_path = download_file_from_storage(storage_path)
        cv_data = extract_text_from_cv(local_file_path)
        cv_data['file_path'] = local_file_path

        if Config.CV_ANALYSIS_API_URL:
            review_result = call_cv_analysis_api(cv_data, 'advanced')
        else:
            review_result = analyze_cv_advanced(cv_data)

        report_path = generate_pdf_report(review_result, local_file_path)

        path_parts = storage_path.split('/')
        phone_number = path_parts[1] if len(path_parts) > 1 else 'unknown'

        report_folder = 'review-reports'
        report_filename = f"report_{int(time.time())}_{uuid.uuid4().hex[:8]}.pdf"
        report_storage_path = f"{report_folder}/{phone_number}/{report_filename}"

        bucket = storage.bucket()
        blob = bucket.blob(report_storage_path)
        blob.upload_from_filename(report_path)
        blob.content_type = 'application/pdf'

        download_url = get_file_download_url(report_storage_path)
        review_result['download_link'] = download_url

        review_result['cv_file_name'] = os.path.basename(storage_path)
        review_result['review_type'] = 'advanced'
        review_result['report_path'] = report_storage_path
        review_result['success'] = True

        if os.path.exists(local_file_path):
            os.remove(local_file_path)
        if os.path.exists(report_path):
            os.remove(report_path)

        return review_result

    except Exception as e:
        logger.error(f"Error in advanced review processing: {str(e)}")
        return {'success': False, 'error': str(e)}


def extract_text_from_cv(file_path):
    try:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            return extract_text_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        with open(file_path, 'rb') as f:
            text = str(f.read())
        return {'full_text': text}


def extract_text_from_pdf(file_path):
    try:
        text = ""

        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)

            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"

        cv_data = analyze_cv_structure(text)
        cv_data['full_text'] = text
        cv_data['metadata'] = {
            'page_count': num_pages,
            'file_type': 'pdf'
        }

        return cv_data

    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        raise e


def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        text = ""

        for para in doc.paragraphs:
            text += para.text + "\n"

        cv_data = analyze_cv_structure(text)
        cv_data['full_text'] = text
        cv_data['metadata'] = {
            'paragraph_count': len(doc.paragraphs),
            'file_type': 'docx'
        }

        return cv_data

    except Exception as e:
        logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
        raise e


def analyze_cv_structure(text):
    sentences = sent_tokenize(text)
    sections = identify_sections(text)
    contact_info = {
        'email': extract_email(text),
        'phone': extract_phone(text),
        'linkedin': extract_linkedin(text)
    }
    metrics = {
        'word_count': len(text.split()),
        'sentence_count': len(sentences),
        'avg_sentence_length': sum(len(s.split()) for s in sentences) / max(len(sentences), 1),
        'bullet_points': len(re.findall(r'•|\*|-', text))
    }

    return {
        'sections': sections,
        'contact_info': contact_info,
        'metrics': metrics,
        'sentences': sentences
    }


def identify_sections(text):
    sections = {}

    section_patterns = {
        'summary': r'(?i)(profile|summary|objective|about\s*me)',
        'experience': r'(?i)(experience|employment|work\s*history|professional\s*background)',
        'education': r'(?i)(education|qualification|academic|degree|university)',
        'skills': r'(?i)(skills|expertise|competencies|proficiencies|technical)',
        'projects': r'(?i)(projects|portfolio|works)',
        'certifications': r'(?i)(certifications|certificates|credentials)',
        'languages': r'(?i)(languages|language\s*proficiency)',
        'interests': r'(?i)(interests|hobbies|activities)'
    }

    lines = text.split('\n')
    current_section = None
    section_content = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        found_section = None
        for section_name, pattern in section_patterns.items():
            if re.search(f"^{pattern}.*$", line, re.IGNORECASE):
                found_section = section_name
                break

        if found_section:
            current_section = found_section
            section_content[current_section] = []
        elif current_section:
            section_content[current_section].append(line)

    for section_name, lines in section_content.items():
        sections[section_name] = '\n'.join(lines)

    return sections


def extract_email(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ''


def extract_phone(text):
    phone_pattern = r'(?:\+\d{1,3}[\s-]?)?\(?\d{3,4}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else ''


def extract_linkedin(text):
    linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+'
    match = re.search(linkedin_pattern, text)
    return match.group(0) if match else ''


def call_cv_analysis_api(cv_data, review_type):
    """
    Call external CV analysis API

    Args:
        cv_data (dict): CV data with text and structure
        review_type (str): Type of review (basic or advanced)

    Returns:
        dict: API response with review results
    """
    try:
        local_file_path = cv_data.get('file_path', None)
        if not local_file_path:
            logger.error("File path missing from CV data")
            return analyze_cv_fallback(cv_data, review_type)

        files = {
            'cv': (os.path.basename(local_file_path), open(local_file_path, 'rb'), 'application/octet-stream')
        }

        form_data = {
            'job_title': 'General Application',
            'job_description': 'CV review for job applications across various industries'
        }

        api_url = Config.CV_ANALYSIS_API_URL
        response = requests.post(
            api_url,
            files=files,
            data=form_data,
            timeout=60
        )

        # Close file after upload
        files['cv'][1].close()

        if response.status_code != 200:
            logger.error(f"API returned status {response.status_code}: {response.text}")
            return analyze_cv_fallback(cv_data, review_type)

        result = response.json()

        if review_type == 'basic':
            return process_basic_api_response(result)
        else:
            return process_advanced_api_response(result)

    except Exception as e:
        logger.error(f"Error calling CV analysis API: {str(e)}")
        return analyze_cv_fallback(cv_data, review_type)


def process_basic_api_response(result):
    insights = []
    for section, details in result.get('section_feedback', {}).items():
        if details.get('improvement_needed', False):
            insights.append(f"{section.upper()}: {details.get('suggestion', '')}")

    for suggestion in result.get('general_suggestions', []):
        insights.append(suggestion)

    return {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'insights': insights[:8],
        'api_provider': 'CV Analyzer API'
    }


def process_advanced_api_response(result):
    score = result.get('overall_score', 65)
    section_scores = {}

    for section, details in result.get('section_feedback', {}).items():
        section_scores[section] = details.get('score', 50)

    insights = []
    for section, details in result.get('section_feedback', {}).items():
        insights.append(f"{section.upper()}: {details.get('suggestion', '')}")

    if 'keyword_matches' in result:
        insights.append(f"KEYWORDS: Your CV matches {result.get('keyword_match_percentage', 0)}% of the job keywords. Consider adding more relevant keywords.")

    return {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'improvement_score': score,
        'section_scores': section_scores,
        'insights': insights,
        'api_provider': 'CV Analyzer API'
    }


def analyze_cv_fallback(cv_data, review_type):
    if review_type == 'basic':
        return analyze_cv_basic(cv_data)
    else:
        return analyze_cv_advanced(cv_data)


def analyze_cv_basic(cv_data):
    text = cv_data.get('full_text', '')
    sections = cv_data.get('sections', {})
    metrics = cv_data.get('metrics', {})

    insights = []

    if 'summary' not in sections:
        insights.append("Consider adding a professional summary at the top of your CV to highlight your key qualifications.")

    if 'experience' not in sections:
        insights.append("Your work experience section is missing or not clearly defined. This is a critical section for most CVs.")

    if 'education' not in sections:
        insights.append("Include your educational background with relevant details about degrees, institutions, and graduation dates.")

    if 'skills' not in sections:
        insights.append("A skills section would help highlight your key competencies relevant to your target roles.")

    contact_info = cv_data.get('contact_info', {})
    if not contact_info.get('email') and not contact_info.get('phone'):
        insights.append("Ensure your contact information is clearly visible at the top of your CV.")

    if text.find('%') == -1 and text.find('increased') == -1 and text.find('decreased') == -1:
        insights.append("Add quantifiable achievements with metrics (%, numbers, etc.) to make your accomplishments more impactful.")

    if metrics.get('bullet_points', 0) < 5:
        insights.append("Use bullet points to make your CV more scannable and highlight key accomplishments.")

    word_count = metrics.get('word_count', 0)
    if word_count < 300:
        insights.append("Your CV appears to be quite short. Consider adding more details about your experience and skills.")
    elif word_count > 1000:
        insights.append("Your CV may be too lengthy. Consider condensing it to 1-2 pages for better readability.")

    if 'experience' in sections:
        experience_text = sections['experience']
        if not any(word in experience_text.lower() for word in ['led', 'managed', 'developed', 'created', 'implemented']):
            insights.append("Use more action verbs in your experience section to showcase your impact.")

    general_insights = [
        "Use action verbs at the beginning of bullet points to create a stronger impression.",
        "Ensure consistent formatting throughout your CV.",
        "Tailor your CV for each job application to highlight the most relevant experience.",
        "Consider the order of your sections - put your strongest qualifications first.",
        "Proofread carefully for grammar and spelling errors.",
        "Avoid personal pronouns (I, me, my) in your CV.",
        "Use industry-specific keywords to pass through automated screening systems."
    ]

    while len(insights) < 5 and general_insights:
        insights.append(general_insights.pop(0))

    return {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'insights': insights,
        'api_provider': 'Internal Analysis'
    }


def analyze_cv_advanced(cv_data):
    text = cv_data.get('full_text', '')
    sections = cv_data.get('sections', {})
    metrics = cv_data.get('metrics', {})
    contact_info = cv_data.get('contact_info', {})

    score = 60

    section_scores = {}
    max_section_scores = {
        'overall_structure': 20,
        'content_quality': 20,
        'formatting': 15,
        'relevance': 15,
        'contact_info': 10,
        'language': 10,
        'keywords': 10
    }

    structure_score = 0
    essential_sections = ['summary', 'experience', 'education', 'skills']
    for section in essential_sections:
        if section in sections:
            structure_score += 5
    section_scores['overall_structure'] = structure_score

    content_score = 0
    word_count = metrics.get('word_count', 0)
    if 300 <= word_count <= 1000:
        content_score += 5

    if text.find('%') != -1 or text.find('increased') != -1 or text.find('decreased') != -1:
        content_score += 5

    if metrics.get('bullet_points', 0) >= 10:
        content_score += 5

    action_verbs = ['managed', 'led', 'developed', 'created', 'implemented', 'achieved', 'improved', 'reduced', 'increased']
    action_verb_count = sum(1 for verb in action_verbs if verb in text.lower())
    if action_verb_count >= 5:
        content_score += 5

    section_scores['content_quality'] = content_score

    formatting_score = 10
    if metrics.get('avg_sentence_length', 0) > 30:
        formatting_score -= 5

    section_scores['formatting'] = formatting_score

    section_scores['relevance'] = 10

    contact_score = 0
    if contact_info.get('email'):
        contact_score += 4
    if contact_info.get('phone'):
        contact_score += 4
    if contact_info.get('linkedin'):
        contact_score += 2

    section_scores['contact_info'] = contact_score

    section_scores['language'] = 8

    keywords_score = 5
    common_keywords = ['experienced', 'skilled', 'professional', 'team', 'leadership', 'results', 'success']
    keyword_count = sum(1 for keyword in common_keywords if keyword in text.lower())
    if keyword_count >= 3:
        keywords_score += 5

    section_scores['keywords'] = keywords_score

    total_score = sum(section_scores.values())
    score = min(max(int(total_score), 40), 95)

    insights = []

    if section_scores['overall_structure'] < 15:
        missing_sections = [s for s in essential_sections if s not in sections]
        if missing_sections:
            insights.append(f"STRUCTURE: Your CV is missing the following important sections: {', '.join(missing_sections)}. Add these to create a complete profile.")
        else:
            insights.append("STRUCTURE: Your CV includes the essential sections but could benefit from better organization. Consider a logical flow from most to least important information.")
    else:
        insights.append("STRUCTURE: Your CV has a good overall structure with all essential sections included.")

    if section_scores['content_quality'] < 15:
        insights.append("CONTENT: Your achievements need more specific metrics. Add numbers, percentages, and outcomes to make your impact clear.")
    else:
        insights.append("CONTENT: Your content effectively showcases your achievements with good use of metrics and specific examples.")

    if 'skills' in sections:
        insights.append("SKILLS: Your technical skills section is present. Consider organizing skills by category and indicating proficiency levels.")
    else:
        insights.append("SKILLS: Add a dedicated skills section to highlight your technical and soft skills. Group similar skills and indicate proficiency levels.")

    insights.append("LANGUAGE: Use more action verbs at the beginning of bullet points to create a stronger impression. Avoid repetitive language across bullet points.")

    insights.append("FORMATTING: Maintain consistent formatting with a clear hierarchy. Use no more than 3 font sizes throughout your document for better readability.")

    insights.append("RELEVANCE: Focus on your most recent and relevant experience. Older positions can be summarized briefly. Tailor your CV for specific job applications.")

    if 'education' in sections:
        insights.append("EDUCATION: Your education section is present. Ensure it includes degrees, institutions, graduation dates, and relevant coursework or achievements.")
    else:
        insights.append("EDUCATION: Add an education section with degrees, institutions, and graduation dates.")

    insights.append("KEYWORDS: Include more industry-specific keywords to pass through applicant tracking systems (ATS).")

    if section_scores['contact_info'] < 8:
        missing_contact = []
        if not contact_info.get('email'):
            missing_contact.append('email')
        if not contact_info.get('phone'):
            missing_contact.append('phone')
        if not contact_info.get('linkedin'):
            missing_contact.append('LinkedIn profile')

        if missing_contact:
            insights.append(f"CONTACT INFO: Add your {', '.join(missing_contact)} at the top of your CV for easy access.")
        else:
            insights.append("CONTACT INFO: Ensure your contact information is prominently displayed at the top of your CV.")
    else:
        insights.append("CONTACT INFO: Your contact information is well-presented at the top of your CV.")

    if word_count < 300:
        insights.append("LENGTH: Your CV is too short. Aim for 1-2 pages with comprehensive details of your experience and skills.")
    elif word_count > 1000:
        insights.append("LENGTH: Your CV is too long. Keep it to 1-2 pages for optimal readability by focusing on the most relevant information.")
    else:
        insights.append("LENGTH: Your CV has a good length for readability.")

    section_percentages = {
        section: int((score / max_section_scores[section]) * 100) for section, score in section_scores.items()
    }

    return {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'improvement_score': score,
        'section_scores': section_percentages,
        'insights': insights,
        'api_provider': 'Internal Analysis'
    }


def generate_pdf_report(review_result, cv_path):
    timestamp = int(time.time())
    report_filename = f"cv_review_report_{timestamp}.pdf"
    report_path = os.path.join('uploads', report_filename)
    os.makedirs('uploads', exist_ok=True)

    doc = SimpleDocTemplate(
        report_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=24,
        alignment=1,
        spaceAfter=24
    )

    heading_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontSize=18,
        spaceBefore=12,
        spaceAfter=6
    )

    subheading_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12
    )

    content = []

    content.append(Paragraph("CV Review Report", title_style))
    content.append(Spacer(1, 12))

    date_text = f"Generated on: {datetime.now().strftime('%d %B %Y')}"
    content.append(Paragraph(date_text, styles['Italic']))
    content.append(Spacer(1, 24))

    content.append(Paragraph("CV Improvement Score", heading_style))
    score = review_result.get('improvement_score', 0)
    content.append(Paragraph(f"{score}/100", subheading_style))
    content.append(Spacer(1, 12))

    if score < 50:
        score_text = "Your CV needs significant improvement to be competitive in the job market."
    elif score < 70:
        score_text = "Your CV is adequate but could benefit from several improvements."
    else:
        score_text = "Your CV is strong, with only minor improvements needed."

    content.append(Paragraph(score_text, body_style))
    content.append(Spacer(1, 24))

    section_scores = review_result.get('section_scores', None)
    if section_scores:
        content.append(Paragraph("CV Component Scores", heading_style))
        content.append(Spacer(1, 12))

        data = [
            ["Component", "Score"],
        ]

        for section, percentage in section_scores.items():
            display_name = ' '.join(word.capitalize() for word in section.split('_'))
            data.append([display_name, f"{percentage}%"])

        table = Table(data, colWidths=[300, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        content.append(table)
        content.append(Spacer(1, 24))

    content.append(Paragraph("Detailed Insights", heading_style))
    content.append(Spacer(1, 12))

    insights = review_result.get('insights', [])

    categories = {}

    for insight in insights:
        if ':' in insight:
            parts = insight.split(':', 1)
            category = parts[0].strip()
            detail = parts[1].strip()

            if category not in categories:
                categories[category] = []

            categories[category].append(detail)
        else:
            if 'GENERAL' not in categories:
                categories['GENERAL'] = []

            categories['GENERAL'].append(insight)

    for category, category_insights in categories.items():
        content.append(Paragraph(category, subheading_style))

        bullets = []
        for detail in category_insights:
            bullets.append(ListItem(Paragraph(detail, body_style)))

        content.append(ListFlowable(
            bullets,
            bulletType='bullet',
            leftIndent=20
        ))

        content.append(Spacer(1, 12))

    content.append(Spacer(1, 24))

    content.append(Paragraph("Next Steps", heading_style))
    content.append(Spacer(1, 6))

    next_steps = [
        "Review the insights and prioritize areas for improvement",
        "Update your CV based on the recommendations",
        "Tailor your CV for each job application",
        "Ask a colleague or mentor to review your updated CV",
        "Consider professional design services if formatting is an issue"
    ]

    bullets = []
    for step in next_steps:
        bullets.append(ListItem(Paragraph(step, body_style)))

    content.append(ListFlowable(
        bullets,
        bulletType='number',
        leftIndent=20
    ))

    doc.build(content)

    return report_path
