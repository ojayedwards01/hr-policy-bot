"""
LLM-Based Intelligent Formatter
===============================
Uses the LLM to intelligently convert content to appropriate formats
Much simpler than regex-based approaches!
"""

from typing import List, Dict, Any

class LLMFormatter:
    """LLM-based intelligent formatter for different platforms"""
    
    def __init__(self, llm):
        """Initialize with LLM instance"""
        self.llm = llm
    
    def format_for_slack(self, html_content: str, sources: List[Dict] = None) -> str:
        """Use LLM to convert HTML to clean Slack format"""
        
        prompt = f"""Convert this HTML content to clean, professional Slack format.

CRITICAL SLACK FORMATTING RULES:
- Use *text* for bold (single asterisks, NOT double)
- Use • for bullet points  
- Use   ◦ for sub-points (2 spaces before ◦)
- Convert links to <URL|Text> format (NOT markdown links)
- Remove all HTML tags completely
- Keep content well-structured with proper spacing
- Use double line breaks between sections

DOCUMENT REFERENCE PROHIBITION:
- NEVER include phrases like "According to Staff Handbook"
- NEVER say "As stated in [document name]"
- NEVER say "The document indicates" or "The policy states"
- NEVER mention specific document names in the content
- Just provide the information directly without attribution
- Remove any existing document references from the content

SLACK MARKDOWN SYNTAX:
- Bold: *bold text* (single asterisks)
- NOT: **bold text** (double asterisks - this shows literally in Slack)
- Links: <https://example.com|Link Text>
- NOT: [Link Text](https://example.com)

EXAMPLE CONVERSION:
HTML: <h2>Travel Requirements</h2><p>You must <strong>complete</strong> the <a href="https://example.com">form</a>.</p>
Slack: *Travel Requirements*

You must *complete* the <https://example.com|form>.

HTML Content to convert:
{html_content}

Convert to proper Slack format (use single asterisks for bold, <URL|Text> for links, and remove any document references):""""""

        try:
            response = self.llm.invoke(prompt)
            slack_content = response.content.strip()
            
            # Post-process to fix any remaining markdown issues
            # Fix double asterisks to single asterisks
            import re
            slack_content = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', slack_content)
            
            # Fix markdown links to Slack format
            slack_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', slack_content)
            
            # Add sources if provided
            if sources:
                sources_text = self._format_slack_sources(sources)
                slack_content += sources_text
            
            return slack_content
            
        except Exception as e:
            # Fallback: simple HTML tag removal
            import re
            fallback = re.sub(r'<[^>]+>', '', html_content)
            return fallback.strip()
    
    def format_for_email(self, html_content: str, sources: List[Dict] = None) -> str:
        """Use LLM to convert HTML to professional email format"""
        
        prompt = f"""Convert this HTML content to a professional email format.

EMAIL FORMATTING RULES:
- Start with a professional greeting if appropriate
- Use clear subject-like headers
- Use proper paragraphs with line breaks
- Convert links to descriptive text with URLs
- Use bullet points with - or bullets
- Keep professional, formal tone
- End with helpful closing if appropriate
- Remove all HTML tags
- Structure like a proper business email

HTML Content to convert:
{html_content}

Convert to professional email format:"""

        try:
            response = self.llm.invoke(prompt)
            email_content = response.content.strip()
            
            # Add sources if provided
            if sources:
                sources_text = self._format_email_sources(sources)
                email_content += sources_text
            
            return email_content
            
        except Exception as e:
            # Fallback: simple HTML tag removal
            import re
            fallback = re.sub(r'<[^>]+>', '', html_content)
            return fallback.strip()
    
    def _format_slack_sources(self, sources: List[Dict]) -> str:
        """Format sources for Slack - simple document names only"""
        if not sources:
            return ""
        
        try:
            sources_list = []
            seen_sources = set()
            
            # Limit to 3 sources
            for doc in sources[:3]:
                if hasattr(doc, 'metadata'):
                    metadata = doc.metadata
                else:
                    metadata = doc.get('metadata', {})
                
                filename = metadata.get('filename', 'Unknown')
                clean_filename = filename.split('/')[-1].split('\\')[-1]
                
                if clean_filename not in seen_sources:
                    seen_sources.add(clean_filename)
                    
                    # Clean name for display
                    doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                    
                    # Simple document name without URL
                    sources_list.append(doc_name)
            
            if sources_list:
                return f"""

---
*Reference Documents:*
{chr(10).join(f'• {source}' for source in sources_list)}"""
                
        except Exception:
            pass
            
        return ""
    
    def _format_email_sources(self, sources: List[Dict]) -> str:
        """Format sources for email"""
        if not sources:
            return ""
        
        try:
            from src.utils.pdf_url_mapping import get_document_url
            
            sources_list = []
            seen_sources = set()
            
            # Limit to 3 sources
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
                    
                    # Clean name
                    doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                    
                    # Email format with visible URL
                    sources_list.append(f"• {doc_name}: {url}")
            
            if sources_list:
                return f"""

Reference Documents:
{chr(10).join(sources_list)}"""
                
        except Exception:
            pass
            
        return ""


def create_llm_formatter(llm) -> LLMFormatter:
    """Create an LLM formatter instance"""
    return LLMFormatter(llm)
