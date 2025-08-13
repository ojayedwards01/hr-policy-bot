"""
Simplified Slack Formatter for Clean, Professional Output
========================================================
"""

import re
from typing import List, Dict, Any

class SimpleSlackFormatter:
    """Simplified formatter specifically for clean Slack output"""
    
    @staticmethod
    def format_for_slack(content: str, sources: List[Dict] = None) -> str:
        """
        Simple, reliable Slack formatting that produces clean output
        """
        # Step 1: Clean the content first
        slack_content = SimpleSlackFormatter._clean_content(content)
        
        # Step 2: Apply simple Slack formatting
        slack_content = SimpleSlackFormatter._apply_simple_formatting(slack_content)
        
        # Step 3: Add sources section
        if sources:
            sources_text = SimpleSlackFormatter._format_sources(sources)
            slack_content += sources_text
        
        return slack_content.strip()
    
    @staticmethod
    def _clean_content(content: str) -> str:
        """Clean content and remove HTML artifacts"""
        
        # First, handle HTML tags with better structure preservation
        
        # Convert headers to clean text with line breaks
        content = re.sub(r'<h[1-6][^>]*>\s*(.*?)\s*</h[1-6]>', r'\n\1\n', content, flags=re.DOTALL)
        
        # Convert paragraphs to text with line breaks
        content = re.sub(r'<p[^>]*>\s*(.*?)\s*</p>', r'\1\n', content, flags=re.DOTALL)
        
        # Convert list items to bullet points
        content = re.sub(r'<li[^>]*>\s*(.*?)\s*</li>', r'• \1\n', content, flags=re.DOTALL)
        
        # Remove remaining list tags
        content = re.sub(r'</?ul[^>]*>', '\n', content)
        content = re.sub(r'</?ol[^>]*>', '\n', content)
        
        # Convert strong/bold tags to markdown
        content = re.sub(r'<strong[^>]*>\s*(.*?)\s*</strong>', r'*\1*', content, flags=re.DOTALL)
        content = re.sub(r'<b[^>]*>\s*(.*?)\s*</b>', r'*\1*', content, flags=re.DOTALL)
        
        # Convert links (preserve for Slack format later)
        content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>\s*(.*?)\s*</a>', r'LINK:\1|\2', content, flags=re.DOTALL)
        
        # Remove all remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Convert HTML entities
        content = content.replace('&nbsp;', ' ')
        content = content.replace('&amp;', '&')
        content = content.replace('&lt;', '<')
        content = content.replace('&gt;', '>')
        
        # Clean up markdown artifacts
        content = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', content)  # **bold** to *bold*
        content = re.sub(r'\*{3,}', '*', content)  # Multiple asterisks to single
        
        # Normalize whitespace
        content = re.sub(r'[ \t]+', ' ', content)  # Multiple spaces to single
        content = re.sub(r' *\n *', '\n', content)  # Remove spaces around newlines
        content = re.sub(r'\n{3,}', '\n\n', content)  # Max 2 consecutive newlines
        
        return content.strip()
    
    @staticmethod
    def _apply_simple_formatting(content: str) -> str:
        """Apply simple, consistent Slack formatting"""
        
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Empty lines
            if not line:
                formatted_lines.append('')
                continue
            
            # Headers - detect and format properly
            if SimpleSlackFormatter._is_header(line):
                header_text = SimpleSlackFormatter._clean_header(line)
                formatted_lines.append(f'*{header_text}*')
                formatted_lines.append('')  # Add space after header
                continue
            
            # Bullet points - clean format
            if line.startswith('•'):
                bullet_text = line[1:].strip()
                formatted_lines.append(f'• {bullet_text}')
                continue
            elif line.startswith('-') and len(line) > 1:
                bullet_text = line[1:].strip()
                formatted_lines.append(f'• {bullet_text}')
                continue
            elif line.startswith('*') and not (line.startswith('*') and line.endswith('*')):
                bullet_text = line[1:].strip()
                formatted_lines.append(f'• {bullet_text}')
                continue
            
            # Sub-bullet points (indented)
            if line.startswith('  ') and (line.strip().startswith('◦') or line.strip().startswith('-')):
                sub_text = re.sub(r'^\s*[◦\-]\s*', '', line)
                formatted_lines.append(f'  ◦ {sub_text}')
                continue
            
            # Convert LINK: format to Slack links
            if 'LINK:' in line:
                line = re.sub(r'LINK:([^|]+)\|([^|]+)', r'<\1|\2>', line)
            
            # Regular paragraphs
            formatted_lines.append(line)
        
        # Join and clean final spacing
        result = '\n'.join(formatted_lines)
        
        # Clean up multiple consecutive empty lines
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # Fix broken formatting artifacts
        result = re.sub(r'\*{2,}', '*', result)  # Multiple asterisks
        result = re.sub(r'\*\s*\*', '', result)  # Empty bold markers
        result = re.sub(r'^\*([^*]*)\*\*', r'*\1*', result, flags=re.MULTILINE)  # Fix broken bold
        
        # Ensure space after headers before content
        result = re.sub(r'(\*[^*]+\*)\n([^*\n•])', r'\1\n\n\2', result)
        
        # Ensure space after bullet groups
        result = re.sub(r'(• [^\n]+)\n([^•\n\s])', r'\1\n\n\2', result)
        
        return result
    
    @staticmethod
    def _is_header(line: str) -> bool:
        """Detect if line is a header"""
        # Look for common header patterns
        if re.match(r'^[A-Z][^.!?]*:?\s*$', line) and len(line.split()) <= 6:
            return True
        if line.isupper() and len(line.split()) <= 4:
            return True
        if line.endswith(':') and not line.startswith('•'):
            return True
        return False
    
    @staticmethod
    def _clean_header(line: str) -> str:
        """Clean header text"""
        # Remove common header artifacts
        line = re.sub(r'^#+\s*', '', line)  # Remove markdown headers
        line = re.sub(r'^\*+\s*|\s*\*+$', '', line)  # Remove asterisks
        line = line.strip(' :')  # Remove trailing colons/spaces
        return line
    
    @staticmethod
    def _format_sources(sources: List[Dict]) -> str:
        """Simple sources formatting"""
        if not sources:
            return ""
        
        from src.utils.pdf_url_mapping import get_document_url
        
        sources_list = []
        seen_sources = set()
        
        # Limit to 3 sources for clean presentation
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
                
                # Simple, clean name
                doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                
                # Simple Slack link format
                sources_list.append(f"<{url}|{doc_name}>")
        
        if sources_list:
            return f"""

---
*Reference Documents:*
{chr(10).join(f'• {source}' for source in sources_list)}"""
        
        return ""


def create_clean_slack_prompt(question: str, context: str) -> str:
    """Create a clean, focused prompt for Slack responses"""
    return f"""You are the CMU-Africa HR assistant. Provide a clear, well-organized response for Slack.

CRITICAL REQUIREMENTS:
1. Use ONLY plain text - no HTML, no markdown except *bold*
2. Structure with clear headers using *Header Text*
3. Use bullet points with • for lists
4. Use   ◦ for sub-points (2 spaces before ◦)
5. Keep responses comprehensive but well-organized
6. Focus ONLY on information that directly answers the question
7. Include specific steps, requirements, and details
8. Use professional, clear language

FORMATTING RULES:
- Headers: *Header Text* (followed by empty line)
- Main points: • Point text
- Sub-points:   ◦ Sub-point text (with 2 spaces before ◦)
- Important info: *Important Term* 
- No HTML tags, no complex formatting
- Double line breaks between major sections

Context: {context}
Question: {question}

Provide a comprehensive, well-structured response with clear headers and proper bullet point formatting."""