"""
LLM-Powered Slack Formatter - Smart & Simple
============================================
Use LLM intelligence to convert HTML to perfect Slack format
"""

class LLMSlackFormatter:
    """Use LLM to intelligently convert content to Slack format"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def format_for_slack(self, html_content: str, sources: list = None) -> str:
        """
        Use LLM to convert HTML content to perfect Slack formatting
        This is much better than regex hell!
        """
        
        # Create a smart prompt for the LLM
        conversion_prompt = f"""You are a professional Slack formatting expert. Convert the following HTML content to clean, professional Slack format.

SLACK FORMATTING RULES:
- Headers: Use *Header Text* (bold with asterisks)
- Bullet points: Use • for main points
- Sub-bullets: Use   ◦ for sub-points (2 spaces before ◦)
- Important terms: *Important* (bold)
- Links: <URL|Display Text> format
- Line breaks: Double line breaks between sections
- NO HTML tags in output
- Clean, professional, easy to read

CRITICAL: 
- Remove ALL HTML tags completely
- Convert <h2>, <h3> to *Header Text*
- Convert <li> to • Point text
- Convert <strong> to *bold text*
- Convert <a href="url">text</a> to <url|text>
- Convert <p> to clean paragraphs with proper spacing
- Make it look professional for Slack users

HTML CONTENT TO CONVERT:
{html_content}

OUTPUT: Clean Slack-formatted text (no HTML tags, just clean Slack formatting):"""

        try:
            # Let the LLM do the intelligent conversion
            response = self.llm.invoke(conversion_prompt)
            slack_formatted = response.content.strip()
            
            # Add sources if provided
            if sources:
                sources_text = self._format_sources_llm(sources)
                slack_formatted += sources_text
            
            return slack_formatted
            
        except Exception as e:
            # Fallback to basic text stripping if LLM fails
            import re
            fallback = re.sub(r'<[^>]+>', '', html_content)
            return fallback.strip()
    
    def _format_sources_llm(self, sources: list) -> str:
        """Use LLM to format sources nicely"""
        if not sources:
            return ""
        
        # Simple sources - no need for LLM here
        from src.utils.pdf_url_mapping import get_document_url
        
        sources_list = []
        seen_sources = set()
        
        for doc in sources[:3]:  # Limit to 3 sources
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
                
                # Clean document name
                doc_name = clean_filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ').title()
                
                # Slack link format
                sources_list.append(f"<{url}|{doc_name}>")
        
        if sources_list:
            return f"""

---
*Reference Documents:*
{chr(10).join(f'• {source}' for source in sources_list)}"""
        
        return ""


def create_simple_slack_prompt(question: str, context: str) -> str:
    """Create a prompt that tells LLM to output clean Slack format directly"""
    return f"""You are the CMU-Africa HR assistant. Provide a clear, professional response directly formatted for Slack.

IMPORTANT: Output your response in CLEAN SLACK FORMAT - no HTML tags!

SLACK FORMATTING RULES:
- Headers: *Header Text* (bold with asterisks, followed by empty line)
- Main points: • Point text
- Sub-points:   ◦ Sub-point text (2 spaces before ◦)
- Important terms: *Important Term* (bold)
- Links: <URL|Display Text> format for clickable links
- Sections: Separated by double line breaks
- Professional tone, well-organized structure

AUDIENCE: CMU-Africa faculty and staff in Kigali, Rwanda

FOCUS: Only information directly relevant to the question. Be comprehensive but focused.

Context: {context}
Question: {question}

Provide a well-structured Slack response with clear headers, bullet points, and proper formatting:"""
