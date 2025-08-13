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
        """
        Use LLM to intelligently format content for Slack - much better than regex!
        """
        # This is a fallback method - the bot should use LLM directly
        # But if called, use simple cleanup
        import re
        
        # Basic HTML removal
        slack_content = re.sub(r'<[^>]+>', '', content)
        
        # Add sources if provided
        if sources:
            from src.utils.llm_slack_formatter import LLMSlackFormatter
            # Create a dummy LLM formatter for sources only
            # Note: This is a fallback, bot should handle this directly
            try:
                formatter = LLMSlackFormatter(None)
                sources_text = formatter._format_sources_llm(sources)
                slack_content += sources_text
            except:
                pass  # Skip sources if error
        
        return slack_content.strip()
    
    @staticmethod
    def _html_to_clean_slack(html_content: str) -> str:
        """Convert HTML to clean text with Slack-appropriate structure and professional spacing"""
        
        # Remove HTML wrapper divs and styling
        content = re.sub(r'<div[^>]*>', '', html_content)
        content = re.sub(r'</div>', '', content)
        
        # Convert headers to Slack format with proper spacing - ensure clean conversion
        content = re.sub(r'<h2[^>]*>\s*(.*?)\s*</h2>', r'*\1*\n\n', content, flags=re.DOTALL)
        content = re.sub(r'<h3[^>]*>\s*(.*?)\s*</h3>', r'*\1*\n\n', content, flags=re.DOTALL)
        content = re.sub(r'<h4[^>]*>\s*(.*?)\s*</h4>', r'*\1*\n\n', content, flags=re.DOTALL)
        
        # Convert paragraphs with proper professional spacing
        content = re.sub(r'<p[^>]*>\s*(.*?)\s*</p>', r'\1\n\n', content, flags=re.DOTALL)
        
        # Convert lists properly with spacing
        content = re.sub(r'<ul[^>]*>', '\n', content)
        content = re.sub(r'</ul>', '\n\n', content)
        content = re.sub(r'<li[^>]*>\s*(.*?)\s*</li>', r'• \1\n', content, flags=re.DOTALL)
        
        # Convert strong/bold tags
        content = re.sub(r'<strong[^>]*>\s*(.*?)\s*</strong>', r'*\1*', content, flags=re.DOTALL)
        
        # Convert links to Slack format
        content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>\s*(.*?)\s*</a>', r'<\1|\2>', content, flags=re.DOTALL)
        
        # Remove any remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up whitespace and ensure proper structure
        content = re.sub(r'[ \t]+', ' ', content)  # Normalize spaces
        content = re.sub(r' +\n', '\n', content)  # Remove trailing spaces
        content = re.sub(r'\n{4,}', '\n\n\n', content)  # Max triple spacing
        
        return content.strip()
    
    @staticmethod
    def _apply_slack_formatting(content: str) -> str:
        """Apply professional Slack formatting rules with proper paragraph spacing and readability"""
        
        # Clean up any existing broken formatting
        content = re.sub(r'\*{3,}', '*', content)  # Fix multiple asterisks
        content = re.sub(r'\*\s*\*', '*', content)  # Fix spaced asterisks
        
        # Add emoji headers for key sections (clean approach)
        lines = content.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
                
            # Main headers - add spacing after emoji headers
            if line.startswith('*') and line.endswith('*') and len(line) > 2:
                header_text = line[1:-1].strip()
                
                # Apply appropriate emoji based on content
                if any(word in header_text.lower() for word in ['step', 'stage', 'phase']):
                    formatted_lines.append(f'📋 *{header_text}*')
                    formatted_lines.append('')  # Add spacing after headers
                elif any(word in header_text.lower() for word in ['important', 'note', 'warning', 'attention']):
                    formatted_lines.append(f'⚠️ *{header_text}*')
                    formatted_lines.append('')
                elif any(word in header_text.lower() for word in ['contact', 'reach', 'email', 'phone']):
                    formatted_lines.append(f'📞 *{header_text}*')
                    formatted_lines.append('')
                elif any(word in header_text.lower() for word in ['timeline', 'schedule', 'deadline']):
                    formatted_lines.append(f'⏰ *{header_text}*')
                    formatted_lines.append('')
                elif any(word in header_text.lower() for word in ['tip', 'recommendation', 'advice']):
                    formatted_lines.append(f'💡 *{header_text}*')
                    formatted_lines.append('')
                elif any(word in header_text.lower() for word in ['insurance', 'coverage', 'health']):
                    formatted_lines.append(f'🏥 *{header_text}*')
                    formatted_lines.append('')
                else:
                    formatted_lines.append(f'📌 *{header_text}*')
                    formatted_lines.append('')
            
            # Bullet points - ensure they have breathing room
            elif line.startswith('•'):
                formatted_lines.append(line)
                # Add spacing after bullet points for readability - check if next line exists and isn't a bullet
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('•'):
                    formatted_lines.append('')
                
            # Regular content - preserve paragraph spacing
            else:
                formatted_lines.append(line)
        
        # Rejoin and clean up professional spacing
        content = '\n'.join(formatted_lines)
        
        # Ensure professional spacing between sections (allow triple spacing for major sections)
        content = re.sub(r'\n{5,}', '\n\n\n', content)  # Max 3 line breaks for major sections
        content = re.sub(r'^\n+', '', content)  # Remove leading newlines
        content = re.sub(r'\n+$', '', content)  # Remove trailing newlines
        
        # Add proper spacing after bullet point groups
        content = re.sub(r'(• .*?)\n([^•\n\s])', r'\1\n\n\2', content)
        
        # Ensure spacing before new sections (emoji headers)
        content = re.sub(r'([^*\n])\n([📋📞⏰💡🏥📌]\s\*)', r'\1\n\n\2', content)
        
        # Add spacing after bullet lists before next content
        content = re.sub(r'(• [^\n]*)\n([📋📞⏰💡🏥📌])', r'\1\n\n\2', content)
        
        # Add professional spacing between major sections
        content = re.sub(r'([.!?])\n([📋📞⏰💡🏥📌])', r'\1\n\n\2', content)
        
        return content
    
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
        """Clean, professional sources for Slack with proper formatting and clear presentation"""
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
                
                # Clean Slack format with proper clickable links and spacing
                sources_list.append(f"📄 <{url}|{doc_name}>")
        
        if sources_list:
            return f"""

---

📚 *Reference Documents*

{chr(10).join(sources_list)}

---"""
        
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
