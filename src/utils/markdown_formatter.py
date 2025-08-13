"""
Markdown Formatter for CMU-Africa HR Bot
========================================

This module provides consistent Markdown formatting that works across all channels:
- Slack (supports limited Markdown)
- Email (converts to HTML)
- Web interface (renders Markdown)
- Terminal output (plain text readable)
"""

import re
from typing import List, Dict, Any

class MarkdownFormatter:
    """Handles consistent Markdown formatting across all communication channels"""
    
    @staticmethod
    def format_response(content: str, sources: List[Dict] = None) -> str:
        """
        Format a complete response with proper Markdown structure
        
        Args:
            content: Main response content
            sources: List of source documents
            
        Returns:
            Properly formatted Markdown response
        """
        # Clean up the main content
        formatted_content = MarkdownFormatter._clean_content(content)
        
        # Add sources section if provided
        if sources:
            sources_section = MarkdownFormatter._format_sources_section(sources)
            formatted_content += sources_section
        
        return formatted_content
    
    @staticmethod
    def _clean_content(content: str) -> str:
        """Clean and format the main content with proper line breaks"""
        # Start with the original content
        content = content.strip()
        
        # Remove specific formatting artifacts first
        content = re.sub(r'\(\\n\\n\)', '', content)  # Remove literal (\n\n)
        content = re.sub(r'\(\\n\)', '', content)     # Remove literal (\n)  
        content = re.sub(r'\\n\\n', '\n\n', content)  # Convert literal \n\n to actual line breaks
        content = re.sub(r'\\n', '\n', content)       # Convert literal \n to actual line breaks
        
        # Remove "Next Topic" sections and similar artifacts
        content = re.sub(r'\s*Next Topic[^\n]*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\s*We will continue[^\n]*', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\s*Stay tuned[^\n]*', '', content, flags=re.IGNORECASE)
        
        # Remove any remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # INTELLIGENT SECTION DETECTION AND FORMATTING
        # Detect common section patterns and add proper formatting
        
        # Pattern 1: "Benefits Available" or similar introductory phrases
        content = re.sub(r'(Employee Benefits|Benefits Available|Available Benefits)(\s+As a)', r'**\1**\n\n\2', content, flags=re.IGNORECASE)
        
        # Pattern 2: Common HR topics that should be section headers
        hr_topics = [
            'Retirement Savings', 'Health Insurance', 'Dental Coverage', 'Vision Coverage',
            'Life Insurance', 'Disability Insurance', 'Flexible Spending', 'Tuition Benefits',
            'Leave Policies', 'Vacation Policy', 'Sick Leave', 'Holidays', 'Holiday Schedule',
            'Professional Development', 'Training Programs', 'Contact Information',
            'Employee Assistance', 'Wellness Programs', 'Health and Welfare Benefits',
            'Employee Retention Bonus', 'Additional Benefits'
        ]
        
        for topic in hr_topics:
            # Add bold formatting and line breaks for section headers
            pattern = fr'(\.|^)\s*({re.escape(topic)})(\s+[A-Z])'
            replacement = fr'\1\n\n**\2**\n\n\3'
            content = re.sub(pattern, replacement, content)
        
        # Fix bold formatting - ensure it uses **text** format
        content = re.sub(r'\*([^*]+)\*(?!\*)', r'**\1**', content)  # Convert single * to **
        content = re.sub(r'<strong>([^<]+)</strong>', r'**\1**', content)  # Convert HTML bold
        
        # Ensure proper spacing around existing section headers
        content = re.sub(r'([.!?])\s*(\*\*[A-Z][^*]+\*\*)', r'\1\n\n\2', content)
        
        # Ensure proper spacing after bullet point sections before new headers
        content = re.sub(r'(• [^\n]+)\s*(\*\*[A-Z][^*]+\*\*)', r'\1\n\n\2', content)
        
        # Add line breaks before bullet points if they immediately follow text
        content = re.sub(r'([a-z.])\s*(• )', r'\1\n\n\2', content)
        
        # Clean up multiple consecutive line breaks but preserve double breaks
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove any remaining empty parentheses
        content = re.sub(r'\(\s*\)', '', content)
        
        # Final cleanup - ensure the content starts properly
        content = content.strip()
        
        return content
    
    @staticmethod
    def _format_sources_section(sources: List[Dict]) -> str:
        """Format sources section with clean Markdown"""
        if not sources:
            return ""
        
        # Process and deduplicate sources
        seen_sources = set()
        formatted_sources = []
        
        for doc in sources[:6]:  # Limit to 6 sources
            # Handle both document objects and dictionaries
            if hasattr(doc, 'metadata'):
                metadata = doc.metadata
            else:
                metadata = doc.get('metadata', {})
            
            filename = metadata.get('filename', 'Unknown Document')
            doc_type = metadata.get('type', 'document')
            
            # Clean filename
            clean_filename = filename.split('/')[-1].split('\\')[-1]
            source_id = f"{clean_filename}|{doc_type}"
            
            if source_id not in seen_sources:
                seen_sources.add(source_id)
                
                # Get document URL
                from src.utils.pdf_url_mapping import get_document_url
                url = get_document_url(filename, doc_type)
                
                # Create clean document name with appropriate emoji
                doc_name, emoji = MarkdownFormatter._get_document_display_name(clean_filename)
                
                # Format as Markdown link
                formatted_sources.append(f"• {emoji} [{doc_name}]({url})")
        
        if formatted_sources:
            return f"""

---

**📚 Reference Documents**

{chr(10).join(formatted_sources)}

*For additional assistance, contact the CMU-Africa HR Department.*"""
        
        return ""
    
    @staticmethod
    def _get_document_display_name(filename: str) -> tuple:
        """Get clean display name and appropriate emoji for document"""
        # Remove file extension
        name = filename.lower()
        
        if name.endswith('.pdf'):
            clean_name = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
            return clean_name, "📄"
        elif name.endswith('.html'):
            clean_name = filename.replace('.html', '').replace(' - Human Resources - Carnegie Mellon University', '')
            return clean_name, "🌐"
        elif name.endswith('.csv'):
            if 'cmu_africa' in name or 'africa_documents' in name:
                return "CMU-Africa Website", "🌐"
            else:
                clean_name = filename.replace('.csv', '').replace('-', ' ').replace('_', ' ').title()
                return clean_name, "📊"
        elif name.endswith('.txt'):
            clean_name = filename.replace('.txt', '').replace('-', ' ').replace('_', ' ').title()
            return clean_name, "📝"
        else:
            clean_name = filename.replace('-', ' ').replace('_', ' ').title()
            return clean_name, "📋"
    
    @staticmethod
    def format_for_slack(content: str) -> str:
        """
        Optimize Markdown for Slack's specific formatting support
        """
        # Slack supports basic Markdown but has some quirks
        # Convert **bold** to *bold* (Slack prefers single asterisks)
        content = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', content)
        
        # Ensure proper line breaks for Slack
        content = re.sub(r'\n\n', '\n\n', content)
        
        return content
    
    @staticmethod
    def format_for_email(content: str) -> str:
        """
        Keep markdown format for email (no conversion to HTML)
        """
        # Just clean up excessive line breaks and return markdown as-is
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content
    
    @staticmethod
    def create_professional_template(question: str, main_content: str, cmu_africa_priority: bool = True) -> str:
        """
        Create a professional response template with proper structure
        """
        template = f"""**Question:** {question}

**Response:**

{main_content}"""
        
        if cmu_africa_priority:
            template = f"""**CMU-Africa HR Assistant Response**

**Question:** {question}

{main_content}"""
        
        return template

# Convenience functions for common use cases
def format_bot_response(content: str, sources: List[Dict] = None, channel: str = "general") -> str:
    """
    Main function to format bot responses for any channel
    
    Args:
        content: The main response content
        sources: List of source documents
        channel: Target channel ("slack", "email", "web", or "general")
    
    Returns:
        Properly formatted response for the specified channel
    """
    formatter = MarkdownFormatter()
    
    # Format the basic response
    formatted = formatter.format_response(content, sources)
    
    # Apply channel-specific formatting
    if channel.lower() == "slack":
        return formatter.format_for_slack(formatted)
    elif channel.lower() == "email":
        return formatter.format_for_email(formatted)
    else:
        return formatted  # Default Markdown for web/general use

def clean_text_response(content: str) -> str:
    """Remove all formatting and return clean text"""
    # Remove Markdown formatting
    content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
    content = re.sub(r'\*([^*]+)\*', r'\1', content)
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    content = re.sub(r'#{1,6}\s*(.+)', r'\1', content)
    
    # Clean up line breaks
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()
