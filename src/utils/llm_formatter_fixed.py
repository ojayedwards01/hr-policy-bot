
"""
Simple LLM-Based Intelligent Formatter
=====================================
Uses the LLM to intelligently convert content to appropriate formats
"""

from typing import List, Dict, Any
import re

class LLMFormatter:
    """LLM-based intelligent formatter for different platforms"""
    
    def __init__(self, llm):
        """Initialize with LLM instance"""
        self.llm = llm
    
    def format_for_slack(self, html_content: str, sources: List[Dict] = None, always_add_directory: bool = False) -> str:
        """Use LLM to convert HTML to clean, professional Slack format. Optionally always add the official directory link as a source."""
        # This function remains as it was, as it was not part of the problem.
        # ... (code for slack formatting is unchanged) ...
        cleaned_html = re.sub(r'(Reference Document[s]?|Source Document[s]?|See document[s]?|According to [^.,\n]+|As stated in [^.,\n]+|The document indicates|The policy states|\b[A-Z][a-z]+\.pdf\b|\b[A-Z][a-z]+\.txt\b|\b[A-Z][a-z]+\.csv\b|\b[A-Z][a-z]+ Handbook\b|\b[A-Z][a-z]+ Guide\b)[^\n]*', '', html_content, flags=re.IGNORECASE)
        prompt = f"""Convert this HTML content to clean, professional Slack format.

CRITICAL SLACK FORMATTING RULES:
- Use *text* for bold (single asterisks, NOT double)
- Use bullet points with simple bullets
- Convert links to <URL|Text> format (NOT markdown links)
- Remove all HTML tags completely
- Keep content well-structured with proper spacing
- Use double line breaks between sections
- Use clear section headings (e.g., *Faculty and Staff Profile*, *Travel and Conference Funding*)
- For contact info, use: *Contact Information* section with bullets

DOCUMENT REFERENCE PROHIBITION:
- NEVER include phrases like "According to Staff Handbook"
- NEVER say "As stated in document name"
- NEVER say "The document indicates" or "The policy states"
- NEVER mention specific document names in the content
- Just provide the information directly without attribution
- Remove any existing document references from the content

CRITICAL: DO NOT ADD ANY PREAMBLES
- DO NOT start with "Here is the converted content..."
- DO NOT say "Here's the Slack format..." 
- DO NOT add any introductory text
- Start DIRECTLY with the actual content
- Just return the converted content without any explanation

SLACK MARKDOWN SYNTAX:
- Bold: *bold text* (single asterisks)
- NOT: **bold text** (double asterisks - this shows literally in Slack)
- Links: <https://example.com|Link Text>
- NOT: [Link Text](https://example.com)

HTML Content to convert:
{cleaned_html}

Return ONLY the converted content with no preambles or explanations:"""
        try:
            response = self.llm.invoke(prompt)
            slack_content = response.content.strip()
            # Remove common preambles that the LLM might add
            preamble_patterns = [ "Here is the converted content", "Here's the converted content", "Slack format:" ]
            for pattern in preamble_patterns:
                if slack_content.lower().startswith(pattern.lower()):
                    slack_content = re.sub(f'^{re.escape(pattern)}:?', '', slack_content, flags=re.IGNORECASE).strip()
                    break
            
            slack_content = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', slack_content)
            slack_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', slack_content)
            slack_content = re.sub(r'<mailto:[^>|]+\|([^>]+)>', r'\1', slack_content)

            sources_text = self._format_slack_sources(sources, always_add_directory=always_add_directory)
            if sources_text:
                slack_content += sources_text
            return slack_content
        except Exception as e:
            fallback = re.sub(r'<[^>]+>', '', html_content)
            return fallback.strip()


    def format_professional_email(self, email_body: str, html_content: str, sources: List[Dict] = None) -> str:
        """
        Creates a full, professional, and robust HTML email response using a reliable template.
        This function replaces the previous complex and unreliable implementation.
        """
        
        # --- 1. Clean up the original query to display it nicely ---
        # Split the email body by common signature lines and take the first part.
        signature_triggers = ['best regards', 'sincerely', 'thank you', 'thanks', 'cheers', '--']
        query_part = email_body
        for trigger in signature_triggers:
            # Case-insensitive split
            parts = re.split(f'\\n{trigger}', email_body, flags=re.IGNORECASE)
            if len(parts) > 1:
                query_part = parts[0]
                break
        clean_query = query_part.strip()


        # --- 2. Convert the LLM's plain text/markdown answer to simple HTML ---
        answer_html = self._answer_to_html(html_content)


        # --- 3. Format sources into an HTML block (if they exist) ---
        # Do not show sources if the answer is a fallback "I don't know" message
        show_sources = sources and "i don't have that specific information" not in html_content.lower()
        sources_html = self._format_sources_for_email_html(sources) if show_sources else ""


        # --- 4. Construct the final HTML email using a clean, modern template ---
        # This template uses inline CSS for maximum compatibility with email clients.
        final_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CMU-Africa HR Response</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; line-height: 1.6; color: #374151; background-color: #f3f4f6; margin: 0; padding: 20px;">
    <div style="max-width: 650px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; overflow: hidden;">
        
        <!-- Header -->
        <div style="background-color: #990000; color: #ffffff; padding: 24px 32px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">CMU-Africa HR Assistant</h1>
        </div>

        <!-- Main Content -->
        <div style="padding: 32px;">
            <p style="font-size: 16px; margin-top: 0;">Dear Colleague,</p>
            <p style="margin-bottom: 24px;">Thank you for your query. Please find the response from our HR knowledge base below.</p>

            <!-- Original Query Box -->
            <div style="background-color: #f8fafc; border-left: 4px solid #b91c1c; padding: 16px 20px; margin-bottom: 24px; border-radius: 0 6px 6px 0;">
                <p style="margin: 0; font-weight: 600; color: #1e293b; margin-bottom: 8px;">Your Question:</p>
                <p style="margin: 0; font-style: italic; color: #475569;">"{clean_query}"</p>
            </div>

            <!-- LLM's Answer (converted to HTML) -->
            <div class="response-content">
                {answer_html}
            </div>

            <!-- Sources Section (conditional) -->
            {sources_html}

            <!-- Closing -->
            <div style="margin-top: 32px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <p style="margin-bottom: 20px;">If you have any further questions, please do not hesitate to ask.</p>
                
                <!-- Signature -->
                <div style="color: #6b7280;">
                    <p style="margin: 0; font-weight: 600; color: #1f2937;">Sincerely,</p>
                    <p style="margin: 4px 0 0 0;">CMU-Africa HR Department</p>
                    <p style="margin: 4px 0 0 0; font-size: 14px;">Carnegie Mellon University - Africa</p>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div style="background-color: #f1f5f9; padding: 20px 32px; text-align: center; font-size: 12px; color: #64748b;">
            <p style="margin: 0;">This is an automated response generated by the CMU-Africa HR Policy Assistant.</p>
        </div>
    </div>
</body>
</html>
"""
        return final_html.strip()

    def _answer_to_html(self, text_content: str) -> str:
        """Converts plain text or simple markdown from LLM to clean HTML for email."""
        if not text_content:
            return ""
        
        # Split content into paragraphs
        paragraphs = text_content.strip().split('\n\n')
        html_parts = []

        for p in paragraphs:
            p = p.strip()
            if not p:
                continue

            # Handle bullet points
            if p.startswith('• ') or p.startswith('- '):
                list_items = p.split('\n')
                html_parts.append('<ul style="padding-left: 20px; margin-top: 10px; margin-bottom: 10px;">')
                for item in list_items:
                    clean_item = item.strip().lstrip('•- ').strip()
                    if clean_item:
                        # Convert **bold** to <strong>
                        clean_item = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', clean_item)
                        html_parts.append(f'<li style="margin-bottom: 8px;">{clean_item}</li>')
                html_parts.append('</ul>')
            # Handle headers (lines with just bold text)
            elif re.fullmatch(r'\*\*.+\*\*', p):
                 header_text = p.strip('*')
                 html_parts.append(f'<h3 style="color: #1e3a8a; font-size: 18px; margin-top: 24px; margin-bottom: 12px;">{header_text}</h3>')
            # Handle regular paragraphs
            else:
                # Convert **bold** to <strong> within paragraphs
                p = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', p)
                html_parts.append(f'<p style="margin-top: 0; margin-bottom: 16px;">{p}</p>')

        return "\n".join(html_parts)
    
    def _format_sources_for_email_html(self, sources: List[Dict]) -> str:
        """Formats source documents into a clean HTML block for emails."""
        if not sources:
            return ""
        
        try:
            from src.utils.pdf_url_mapping import get_document_url
            sources_list = []
            seen_sources = set()
            
            for doc in sources[:3]:
                metadata = doc.metadata if hasattr(doc, 'metadata') else doc.get('metadata', {})
                filename = metadata.get('filename', 'Unknown')
                doc_type = metadata.get('type', 'unknown')
                clean_filename = filename.split('/')[-1].split('\\')[-1]
                
                if clean_filename not in seen_sources:
                    seen_sources.add(clean_filename)
                    url = get_document_url(filename, doc_type)
                    doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                    
                    sources_list.append(f"""
<li style="margin-bottom: 10px;">
    <a href="{url}" target="_blank" style="color: #1e40af; text-decoration: none; font-weight: 500; display: flex; align-items: center;">
        <span style="margin-right: 12px; font-size: 20px;">📄</span>{doc_name}
    </a>
</li>""")
            
            if sources_list:
                return f"""
<div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
    <h4 style="color: #1e3a8a; font-size: 16px; font-weight: 600; margin-top: 0; margin-bottom: 15px;">
        Reference Documents
    </h4>
    <ul style="margin: 0; padding: 0; list-style: none;">
        {''.join(sources_list)}
    </ul>
</div>"""
        except Exception:
            # In case of error, return empty string to not break the email
            return ""
        
        return ""

    def _format_slack_sources(self, sources: List[Dict], always_add_directory: bool = False) -> str:
        """Format sources for Slack - only document/source links as hyperlinks, never names or emails."""
        try:
            sources_list = []
            seen_sources = set()
            # Limit to 3 sources
            for doc in sources[:3] if sources else []:
                if hasattr(doc, 'metadata'):
                    metadata = doc.metadata
                else:
                    metadata = doc.get('metadata', {})
                filename = metadata.get('filename', 'Unknown')
                doc_type = metadata.get('type', 'unknown')
                clean_filename = filename.split('/')[-1].split('\\')[-1]
                if clean_filename not in seen_sources:
                    seen_sources.add(clean_filename)
                    try:
                        from src.utils.pdf_url_mapping import get_document_url
                        url = get_document_url(filename, doc_type)
                        doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                        if url and url.startswith(('http://', 'https://')):
                            sources_list.append(f"• <{url}|{doc_name}>")
                        else:
                            sources_list.append(f"• {doc_name}")
                    except Exception:
                        doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                        sources_list.append(f"• {doc_name}")
            # Always add the official directory link for name queries if requested
            if always_add_directory:
                sources_list.append("• <https://www.africa.engineering.cmu.edu/about/contact/directory/index.html|CMU-Africa Official Directory>")
            if sources_list:
                return "\n\n---\n*Reference Documents:*\n" + "\n".join(sources_list)
        except Exception:
            pass
        return ""
    

def create_llm_formatter(llm) -> LLMFormatter:
    """Create an LLM formatter instance"""
    return LLMFormatter(llm)