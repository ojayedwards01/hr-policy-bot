"""
Universal Text Formatter for CMU-Africa HR Bot
=============================================

Professional, executive-level formatter for top-tier organizational communication
"""

import re
from typing import List, Dict, Any

class UniversalFormatter:
    """Professional formatter for executive-level output with proper styling and hierarchy"""
    
    @staticmethod
    def format_for_slack(content: str, sources: List[Dict] = None) -> str:
        """Professional Slack formatting using html-slacker library for accurate conversion"""
        
        try:
            from htmlslacker import HTMLSlacker
        except ImportError:
            # Fallback to basic formatting if library not available
            content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
            content = re.sub(r'\*\*(.*?)\*\*', r'*\1*', content)  # Convert **bold** to *bold*
            content = re.sub(r'\n{3,}', '\n\n', content)  # Clean excessive line breaks
            if sources:
                sources_text = UniversalFormatter._format_sources_for_slack(sources)
                content += sources_text
            return content.strip()
        
        # Clean up excessive line breaks but preserve intentional spacing
        content = re.sub(r'\n{4,}', '\n\n', content)
        content = content.strip()
        
        # Use html-slacker for professional HTML to Slack conversion
        slacker = HTMLSlacker()
        
        # Convert HTML content to Slack markdown
        slack_content = slacker.convert(content)
        
        # Post-processing cleanup to fix common issues
        slack_content = re.sub(r'\n{3,}', '\n\n', slack_content)  # Fix excessive line breaks
        slack_content = re.sub(r'  +', ' ', slack_content)  # Fix multiple spaces
        slack_content = slack_content.strip()
        
        # Remove any existing emoji headers before adding new ones (prevent duplicates)
        slack_content = re.sub(r'📋 (\*[^*]*Step \d+[^*]*\*)', r'\1', slack_content)
        slack_content = re.sub(r'⚠️ (\*[^*]*Important[^*]*\*)', r'\1', slack_content)
        slack_content = re.sub(r'📞 (\*[^*]*Contact[^*]*\*)', r'\1', slack_content)
        
        # Add professional emoji headers for key sections (only once)
        if 'Step 1' in slack_content or 'Step 2' in slack_content:
            slack_content = re.sub(r'(\*[^*]*Step \d+[^*]*\*)', r'📋 \1', slack_content)
        
        if 'Important' in slack_content:
            slack_content = re.sub(r'(\*[^*]*Important[^*]*\*)', r'⚠️ \1', slack_content)
        
        if 'Contact' in slack_content:
            slack_content = re.sub(r'(\*[^*]*Contact[^*]*\*)', r'📞 \1', slack_content)
        
        # Remove any existing reference sections to prevent duplicates
        slack_content = re.sub(r'\n\n📚 \*Reference Documents\*\n.*$', '', slack_content, flags=re.DOTALL)
        
        # Add professional sources section with enhanced formatting (only once)
        if sources:
            sources_text = UniversalFormatter._format_sources_for_slack(sources)
            slack_content += sources_text
        
        return slack_content.strip()
    
    @staticmethod
    def format_for_email(content: str, sources: List[Dict] = None) -> str:
        """Professional email formatting with clear structure"""
        
        # Clean up excessive line breaks
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()
        
        # Add professional sources section
        if sources:
            sources_text = UniversalFormatter._format_sources_for_email(sources)
            content += sources_text
        
        return content
    
    @staticmethod
    def format_for_web(content: str, sources: List[Dict] = None) -> str:
        """Professional web formatting with executive-level HTML styling"""
        
        # Content should already be in HTML format from the LLM
        content = content.strip()
        
        # Apply professional styling to the content
        content = UniversalFormatter._enhance_html_styling(content)
        
        # Add professionally formatted sources section
        if sources:
            sources_text = UniversalFormatter._format_sources_for_web(sources)
            content += sources_text
        
        return content
    
    @staticmethod
    def format_universal_text(content: str, sources: List[Dict] = None) -> str:
        """Professional universal formatting with clear hierarchy"""
        
        # Clean up excessive line breaks and whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()
        
        # Add professional sources section
        if sources:
            sources_text = UniversalFormatter._format_sources_universal(sources)
            content += sources_text
        
        return content
    
    @staticmethod
    def _enhance_html_styling(content: str) -> str:
        """Apply professional executive-level styling to HTML content"""
        
        # Wrap in professional container
        styled_content = f"""
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #2c3e50; max-width: 800px; margin: 0 auto; padding: 20px;">
{content}
</div>"""
        
        # Enhance headers with professional styling
        styled_content = re.sub(
            r'<h2>([^<]+)</h2>', 
            r'<h2 style="color: #1e3a8a; font-size: 24px; font-weight: 700; margin: 30px 0 15px 0; border-bottom: 2px solid #3b82f6; padding-bottom: 8px;">\1</h2>', 
            styled_content
        )
        
        styled_content = re.sub(
            r'<h3>([^<]+)</h3>', 
            r'<h3 style="color: #1e40af; font-size: 20px; font-weight: 600; margin: 25px 0 12px 0; border-left: 4px solid #3b82f6; padding-left: 12px;">\1</h3>', 
            styled_content
        )
        
        # Enhance paragraphs
        styled_content = re.sub(
            r'<p>([^<]+)</p>', 
            r'<p style="margin: 15px 0; line-height: 1.7; color: #374151;">\1</p>', 
            styled_content
        )
        
        # Enhance lists with proper indentation
        styled_content = re.sub(
            r'<ul>', 
            r'<ul style="margin: 20px 0; padding-left: 0; list-style: none;">', 
            styled_content
        )
        
        styled_content = re.sub(
            r'<li>', 
            r'<li style="margin: 10px 0; padding-left: 20px; position: relative; line-height: 1.6;"><span style="position: absolute; left: 0; top: 0; color: #3b82f6; font-weight: bold;">•</span>', 
            styled_content
        )
        
        styled_content = re.sub(r'</li>', r'</li>', styled_content)
        
        # Enhance strong tags
        styled_content = re.sub(
            r'<strong>([^<]+)</strong>', 
            r'<strong style="color: #1e40af; font-weight: 700;">\1</strong>', 
            styled_content
        )
        
        return styled_content
    
    @staticmethod
    def _format_sources_for_web(sources: List[Dict]) -> str:
        """Professional sources for web - clean and minimal"""
        if not sources:
            return ""
        
        from src.utils.pdf_url_mapping import get_document_url
        
        sources_list = []
        seen_sources = set()
        
        # Show up to 3 key sources for clean presentation
        for doc in sources[:3]:
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
            else:
                metadata = doc.get('metadata', {})
            
            filename = metadata.get('filename', 'Unknown')
            doc_type = metadata.get('type', 'unknown')
            clean_filename = filename.split('/')[-1].split('\\')[-1]
            
            if clean_filename not in seen_sources:
                seen_sources.add(clean_filename)
                url = get_document_url(filename, doc_type)
                
                # Professional clean name
                doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                
                # Professional HTML format - clean and minimal
                sources_list.append(f'''
    <li style="margin: 8px 0; padding: 10px; background-color: #f8fafc; border-radius: 4px;">
        <a href="{url}" target="_blank" style="color: #1e40af; text-decoration: none; font-weight: 500; display: flex; align-items: center;">
            <span style="margin-right: 8px;">📄</span>
            {doc_name}
        </a>
    </li>''')
        
        if sources_list:
            return f"""

<div style="margin-top: 30px; padding: 20px; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 6px;">
    <h4 style="color: #374151; font-size: 16px; font-weight: 600; margin: 0 0 15px 0;">
        📚 Reference Documents
    </h4>
    <ul style="margin: 0; padding: 0; list-style: none;">
        {chr(10).join(sources_list)}
    </ul>
</div>"""
        
        return ""
    
    @staticmethod
    def _format_sources_for_slack(sources: List[Dict]) -> str:
        """Professional sources for Slack - matches web quality with clickable links"""
        if not sources:
            return ""
        
        from src.utils.pdf_url_mapping import get_document_url
        
        sources_list = []
        seen_sources = set()
        
        # Show up to 3 key sources for clean presentation
        for doc in sources[:3]:
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
            else:
                metadata = doc.get('metadata', {})
            
            filename = metadata.get('filename', 'Unknown')
            doc_type = metadata.get('type', 'unknown')
            clean_filename = filename.split('/')[-1].split('\\')[-1]
            
            if clean_filename not in seen_sources:
                seen_sources.add(clean_filename)
                url = get_document_url(filename, doc_type)
                
                # Professional clean name
                doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                
                # Slack format with proper clickable links
                sources_list.append(f"  • <{url}|{doc_name}>")
        
        if sources_list:
            return f"""


📚 *Reference Documents*
{chr(10).join(sources_list)}"""
        
        return ""
    
    @staticmethod
    def _format_sources_for_email(sources: List[Dict]) -> str:
        """Professional sources for email - clean and minimal"""
        if not sources:
            return ""
        
        from src.utils.pdf_url_mapping import get_document_url
        
        sources_list = []
        seen_sources = set()
        
        # Show up to 3 key sources for clean presentation
        for doc in sources[:3]:
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
            else:
                metadata = doc.get('metadata', {})
            
            filename = metadata.get('filename', 'Unknown')
            doc_type = metadata.get('type', 'unknown')
            clean_filename = filename.split('/')[-1].split('\\')[-1]
            
            if clean_filename not in seen_sources:
                seen_sources.add(clean_filename)
                url = get_document_url(filename, doc_type)
                
                # Professional clean name
                doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                
                # Email format - clean with markdown links
                sources_list.append(f"• [{doc_name}]({url})")
        
        if sources_list:
            return f"""

**📚 Reference Documents**
{chr(10).join(sources_list)}"""
        
        return ""
    
    @staticmethod
    def _format_sources_universal(sources: List[Dict]) -> str:
        """Professional sources for universal text - clean and minimal"""
        if not sources:
            return ""
        
        from src.utils.pdf_url_mapping import get_document_url
        
        sources_list = []
        seen_sources = set()
        
        # Show up to 3 key sources for clean presentation
        for doc in sources[:3]:
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
            else:
                metadata = doc.get('metadata', {})
            
            filename = metadata.get('filename', 'Unknown')
            doc_type = metadata.get('type', 'unknown')
            clean_filename = filename.split('/')[-1].split('\\')[-1]
            
            if clean_filename not in seen_sources:
                seen_sources.add(clean_filename)
                url = get_document_url(filename, doc_type)
                
                # Professional clean name
                doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                
                # Universal format - clean and professional
                sources_list.append(f"• {doc_name}: {url}")
        
        if sources_list:
            return f"""

📚 Reference Documents
{chr(10).join(sources_list)}"""
        
        return ""


def format_response(content: str, sources: List[Dict] = None, platform: str = "universal") -> str:
    """
    Professional, executive-level formatting that creates top-tier organizational communication
    
    Args:
        content: The main response content
        sources: List of source documents  
        platform: Target platform ("slack", "email", "web", "universal")
    
    Returns:
        Professionally formatted response suitable for executive-level communication
    """
    formatter = UniversalFormatter()
    
    if platform.lower() == "slack":
        return formatter.format_for_slack(content, sources)
    elif platform.lower() == "email":
        return formatter.format_for_email(content, sources)
    elif platform.lower() == "web":
        return formatter.format_for_web(content, sources)
    else:
        return formatter.format_universal_text(content, sources)
