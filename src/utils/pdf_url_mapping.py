"""
Document URL Mapping for CMU Africa HR Policy Bot
================================================

This module provides URL mappings for all documents in the knowledge base
so that source citations can include proper links to original documents.
"""

# PDF Document URLs
PDF_TO_URL_MAP = {
    "staff-handbook-africa.pdf": "https://www.cmu.edu/hr/assets/hr/staff-handbook-africa.pdf",
    "fwa-guidelines.pdf": "https://www.cmu.edu/hr/assets/rwanda/fwa-guidelines.pdf",
    "offboarding-checklist-employee.pdf": "https://www.cmu.edu/hr/assets/hr/restrict/offboarding-checklist-employee.pdf",
    "onboarding-checklist-cmu-africa.pdf": "https://www.cmu.edu/hr/service-center/assets/onboarding-checklist-cmu-africa.pdf",
    "hiring-process-2024.pdf": "https://www.africa.engineering.cmu.edu/_files/documents/faculty-staff/hiring-process-2024.pdf",
    "travel-guidelines-dec-2024.pdf": "https://www.africa.engineering.cmu.edu/_files/documents/faculty-staff/travel-guidelines-dec-2024.pdf",
    "2025-payroll-rwanda.pdf": "https://www.cmu.edu/hr/service-center/payroll/calendars/2025-payroll-rwanda.pdf",
    "quick-guide-mobile-installation-instructions.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-mobile-installation-instructions.pdf",
    "onboarding.pdf": "https://www.cmu.edu/my-workday-toolkit/self-service/system-guides/onboarding.pdf",
    "quick-guide-self-identification-instructions-disability.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-self-identification-instructions-disability.pdf",
    "update-contact-info.pdf": "https://www.cmu.edu/my-workday-toolkit/self-service/system-guides/update-contact-info.pdf",
    "quick-guide-change-legal-name.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-change-legal-name.pdf",
    "quick-guide-change-preferred-name.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-change-preferred-name.pdf",
    "change-government-id.pdf": "https://www.cmu.edu/my-workday-toolkit/self-service/system-guides/change-government-id.pdf",
    "change-work-space.pdf": "https://www.cmu.edu/my-workday-toolkit/self-service/system-guides/change-work-space.pdf",
    "quick-guide-payment-elections.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-payment-elections.pdf",
    "quick-guide-review-pay-slip.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-review-pay-slip.pdf",
    "submit-resignation.pdf": "https://www.cmu.edu/my-workday-toolkit/self-service/system-guides/submit-resignation.pdf",
    "career-profile.pdf": "https://www.cmu.edu/my-workday-toolkit/self-service/system-guides/career-profile.pdf",
    "quick-guide-time-tracking-employees.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-time-tracking-employees.pdf",
    "quick-guide-dependent-tuition-benefits.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-dependent-tuition-benefits.pdf",
    "quick-guide-employee-tuition-benefits.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-employee-tuition-benefits.pdf",
    "quick-guide-designate-beneficiary.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-designate-beneficiary.pdf",
    "quick-guide-change-benefits.pdf": "https://www.cmu.edu/my-workday-toolkit/quick-guides/restricted/quick-guide-change-benefits.pdf",
    "faq.pdf": "https://www.cmu.edu/hr/assets/hr/faq.pdf"
}

# HTML Document URLs
HTML_TO_URL_MAP = {
    "Disability Insurance - Human Resources - Carnegie Mellon University.html": "https://www.cmu.edu/hr/benefits/disability-insurance.html",
    "Employee HR Resources - Human Resources - Carnegie Mellon University.html": "https://www.cmu.edu/hr",
    "faculty_handbook.html": "https://www.cmu.edu/faculty-senate/faculty-handbook",
    "Student Workers - Human Resources - Carnegie Mellon University.html": "https://www.cmu.edu/hr/benefits/student-workers.html",
    "Africa - Human Resources - Carnegie Mellon University.html": "https://www.cmu.edu/hr/benefits/international/africa.html",
    "benefits.html": "https://www.cmu.edu/hr/benefits"
}

# Default URL for unknown documents - CMU Africa main site
UNKNOWN_DOCUMENT_DEFAULT_URL = "https://www.africa.engineering.cmu.edu/"
DATA_FILE_DEFAULT_URL = UNKNOWN_DOCUMENT_DEFAULT_URL

# CSV-specific mappings
CSV_TO_URL_MAP = {
    "complete_people_with_profiles.csv": "https://www.africa.engineering.cmu.edu/",
    "sample_staff_data.csv": "https://www.africa.engineering.cmu.edu/",
    "CMU_Africa_Documents.csv": "https://www.africa.engineering.cmu.edu/"
}

# TXT-specific mappings
TXT_TO_URL_MAP = {
    "cmu_africa_complete_profiles.txt": "https://www.africa.engineering.cmu.edu/"
}

def get_document_url(filename: str, document_type: str = None) -> str:
    """
    Get the URL for a document based on its filename and type.
    Uses reasonable defaults by document type, with CMU Africa as final fallback.
    
    Args:
        filename: The name of the document file
        document_type: The type of document (pdf, html, csv, txt)
    
    Returns:
        The URL for the document with appropriate defaults
    """
    # Remove path components if present
    clean_filename = filename.split('/')[-1].split('\\')[-1]
    
    # First, check if document is in our known mappings
    if clean_filename in PDF_TO_URL_MAP:
        return PDF_TO_URL_MAP[clean_filename]
    elif clean_filename in HTML_TO_URL_MAP:
        return HTML_TO_URL_MAP[clean_filename]
    elif clean_filename in CSV_TO_URL_MAP:
        return CSV_TO_URL_MAP[clean_filename]
    elif clean_filename in TXT_TO_URL_MAP:
        return TXT_TO_URL_MAP[clean_filename]
    
    # For unknown documents, use reasonable defaults by type
    # Determine document type if not provided
    if not document_type:
        if clean_filename.endswith('.pdf'):
            document_type = 'pdf'
        elif clean_filename.endswith('.html'):
            document_type = 'html'
        elif clean_filename.endswith('.csv'):
            document_type = 'csv'
        elif clean_filename.endswith('.txt'):
            document_type = 'txt'
    
    # Reasonable defaults by document type
    if document_type == 'pdf':
        return "https://www.cmu.edu/hr/assets"  # HR PDFs are likely here
    elif document_type == 'html':
        return "https://www.cmu.edu/hr"  # HR web pages
    elif document_type in ['csv', 'txt']:
        return DATA_FILE_DEFAULT_URL  # Data files → CMU Africa
    
    # Final fallback for truly unknown document types
    return UNKNOWN_DOCUMENT_DEFAULT_URL

def format_source_citation(filename: str, document_type: str = None, citation_number: int = 1) -> str:
    """
    Format a source citation with clickable HTML link and web icon.
    
    Args:
        filename: The name of the document file
        document_type: The type of document
        citation_number: The citation number to use
    
    Returns:
        Formatted HTML citation string with clickable link and icon
    """
    url = get_document_url(filename, document_type)
    clean_filename = filename.split('/')[-1].split('\\')[-1]
    
    # Create a clean document name
    if clean_filename.endswith('.pdf'):
        doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').title()
        icon = "📄"  # PDF icon
    elif clean_filename.endswith('.html'):
        doc_name = clean_filename.replace('.html', '').replace(' - Human Resources - Carnegie Mellon University', '')
        icon = "🌐"  # Web page icon
    elif clean_filename.endswith('.csv'):
        # Special handling for CMU Africa Documents CSV
        if 'cmu_africa' in clean_filename.lower() or 'africa_documents' in clean_filename.lower():
            doc_name = "CMU-Africa Website"
            icon = "🌐"  # Web icon for website
        else:
            doc_name = clean_filename.replace('.csv', '').replace('-', ' ').replace('_', ' ').title()
            icon = "📊"  # Data icon
    elif clean_filename.endswith('.txt'):
        doc_name = clean_filename.replace('.txt', '').replace('-', ' ').replace('_', ' ').title()
        icon = "📝"  # Text icon
    else:
        doc_name = clean_filename.replace('-', ' ').replace('_', ' ').title()
        icon = "📋"  # General document icon
    
    # Create clickable HTML link with icon - improved spacing
    if url == UNKNOWN_DOCUMENT_DEFAULT_URL and not any(clean_filename in mapping for mapping in [PDF_TO_URL_MAP, HTML_TO_URL_MAP, CSV_TO_URL_MAP, TXT_TO_URL_MAP]):
        return f'<p style="margin: 5px 0;">({citation_number}) {icon} <a href="{url}" target="_blank" style="color: #0066cc; text-decoration: none;"><strong>{doc_name}</strong></a> - <em>Visit for more information</em></p>'
    else:
        return f'<p style="margin: 5px 0;">({citation_number}) {icon} <a href="{url}" target="_blank" style="color: #0066cc; text-decoration: none;"><strong>{doc_name}</strong></a></p>'

def get_inline_source_link(filename: str, document_type: str = None) -> str:
    """
    Generate an inline hyperlinked "document source" for use within text.
    
    Args:
        filename: The name of the document file
        document_type: The type of document
    
    Returns:
        Inline hyperlinked text like <a href="url" target="_blank">document source</a>
    """
    url = get_document_url(filename, document_type)
    return f'<a href="{url}" target="_blank" style="color: #0066cc; text-decoration: none;">document source</a>'

def get_document_source_links(source_documents: list) -> dict:
    """
    Generate a mapping of document filenames to their source links for inline use.
    
    Args:
        source_documents: List of source documents from retrieval
    
    Returns:
        Dictionary mapping filenames to their "document source" links
    """
    source_links = {}
    seen_sources = set()
    
    for doc in source_documents:
        filename = doc.metadata.get('filename', doc.metadata.get('source', 'Unknown'))
        doc_type = doc.metadata.get('type', 'unknown')
        
        # Clean filename for consistent duplicate detection
        clean_filename = filename.split('/')[-1].split('\\')[-1]
        source_id = f"{clean_filename}|{doc_type}"
        
        # Avoid duplicate sources
        if source_id not in seen_sources:
            seen_sources.add(source_id)
            source_links[filename] = get_inline_source_link(filename, doc_type)
    
    return source_links

def get_sources_section(source_documents: list) -> str:
    """
    Generate a clean Markdown sources section for cross-platform compatibility.
    
    Args:
        source_documents: List of source documents from retrieval
    
    Returns:
        Formatted Markdown sources section string
    """
    if not source_documents:
        return ""
    
    # Separate documents by priority (prioritize official CMU documents)
    priority_docs = []
    website_docs = []
    seen_sources = set()
    
    for doc in source_documents[:6]:  # Limit to 6 sources for readability
        filename = doc.metadata.get('filename', doc.metadata.get('source', 'Unknown'))
        doc_type = doc.metadata.get('type', 'unknown')
        
        # Clean filename for consistent duplicate detection
        clean_filename = filename.split('/')[-1].split('\\')[-1]
        
        # Create a unique identifier to avoid true duplicates
        source_id = f"{clean_filename}|{doc_type}"
        
        # Avoid duplicate sources
        if source_id not in seen_sources:
            seen_sources.add(source_id)
            
            # Check if this is CMU Africa website (CSV files) - lower priority
            if ('cmu_africa' in clean_filename.lower() or 
                'africa_documents' in clean_filename.lower() or 
                clean_filename.endswith('.csv')):
                website_docs.append((filename, doc_type))
            else:
                priority_docs.append((filename, doc_type))
    
    # Build sources list with clean Markdown formatting
    sources = []
    
    # Add priority documents first (official PDFs and HTML pages)
    for filename, doc_type in priority_docs:
        url = get_document_url(filename, doc_type)
        clean_filename = filename.split('/')[-1].split('\\')[-1]
        
        # Create clean document name with emoji
        if clean_filename.endswith('.pdf'):
            doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').title()
            emoji = "📄"
        elif clean_filename.endswith('.html'):
            doc_name = clean_filename.replace('.html', '').replace(' - Human Resources - Carnegie Mellon University', '')
            emoji = "🌐"
        else:
            doc_name = clean_filename.replace('-', ' ').replace('_', ' ').title()
            emoji = "�"
        
        # Format as clean Markdown link
        sources.append(f"• {emoji} [{doc_name}]({url})")
    
    # Add CMU Africa website documents last
    for filename, doc_type in website_docs:
        url = get_document_url(filename, doc_type)
        sources.append(f"• 🌐 [CMU-Africa Website]({url})")
    
    if sources:
        # Create clean Markdown sources section with proper spacing
        sources_text = f"""

---

**📚 Reference Documents**

{chr(10).join(sources)}

*For additional assistance, contact the CMU-Africa HR Department.*"""
        return sources_text
    
    return ""

# Export the main functions
__all__ = ['get_document_url', 'format_source_citation', 'get_inline_source_link', 'get_document_source_links', 'get_sources_section', 'PDF_TO_URL_MAP', 'HTML_TO_URL_MAP']
