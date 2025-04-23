import re
import sys
import os

def process_md_file(input_file, output_file):
    """
    Process a markdown file to ensure each section has exactly one source after it.
    Each section should be followed by a source, and sources should be placed directly
    after the relevant paragraph.
    """
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove AI-generated markers like (字数：xxx) and all variations
    ai_marker_patterns = [
        r'[（\(](?:字数|字符数|总字数|word count)[:：]\s*\d+\s*[）\)]',
        r'[（\(]全文(?:共|约)?\s*\d+\s*字[）\)]',
        r'[（\(]约\s*\d+\s*字[）\)]',
        r'[（\(]\d+\s*(?:字|words?)[）\)]'
    ]
    
    for pattern in ai_marker_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Clean up any resulting empty lines (but preserve paragraph structure)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    
    # First, collect all sources in the document
    sources_pattern = r'(\*\*来源:\*\*\s*(?:- .*(?:\n|$))+)'
    all_sources = re.findall(sources_pattern, content)
    
    # Extract individual source items
    individual_sources = []
    for source_block in all_sources:
        source_items = re.findall(r'- (.*?)(?:\n|$)', source_block)
        for item in source_items:
            if item.strip():
                individual_sources.append(item.strip())
    
    # Temporarily remove all source blocks from content
    content_without_sources = re.sub(sources_pattern, '', content)
    
    # Split content into sections based on headings and blank lines
    sections = []
    current_lines = []
    lines = content_without_sources.split('\n')
    
    for i, line in enumerate(lines):
        # Start of a new section with heading
        if line.startswith('#'):
            if current_lines:
                sections.append('\n'.join(current_lines))
                current_lines = []
            current_lines.append(line)
        # Empty line could be a section separator
        elif not line.strip() and i < len(lines) - 1 and lines[i+1].startswith('#'):
            if current_lines:
                sections.append('\n'.join(current_lines))
                current_lines = []
        else:
            current_lines.append(line)
    
    # Add the last section
    if current_lines:
        sections.append('\n'.join(current_lines))
    
    # Filter out empty sections
    sections = [s for s in sections if s.strip()]
    
    # Check if a section is part of the references section
    def is_reference_section(section):
        # Check for common reference section headings
        if re.search(r'#+ (?:参考资料|参考文献|引用|References|Sources)', section, re.IGNORECASE):
            return True
        
        # Check for sections that contain multiple formatted references
        reference_links_count = len(re.findall(r'- .*? - (?:https?://|www\.)', section))
        if reference_links_count >= 2:
            return True
            
        return False
    
    # Check if a section is metadata that doesn't need a source
    def is_metadata_section(section):
        metadata_patterns = [
            r'报告日期', r'发布日期', r'更新时间', r'生成时间', 
            r'作者[:：]', r'编辑[:：]', r'摘要[:：]', r'简介[:：]'
        ]
        for pattern in metadata_patterns:
            if re.search(pattern, section):
                return True
        return False
    
    # Identify the reference section index
    reference_section_index = -1
    for i, section in enumerate(sections):
        if is_reference_section(section):
            reference_section_index = i
            break
    
    # Function to match source to section content
    def find_best_source_for_section(section, available_sources):
        if not available_sources:
            return None
        
        section_text = section.lower()
        scores = []
        
        for source in available_sources:
            source_text = source.lower()
            score = 0
            
            # Extract key terms from the section
            # Company/organization names
            section_orgs = re.findall(r'([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*)', section)
            section_orgs += re.findall(r'([\u4e00-\u9fff]+(?:公司|集团|科技|智能|教育|开发|研究院|平台))', section)
            
            # Numbers and statistics
            section_numbers = re.findall(r'(\d+(?:\.\d+)?(?:%|亿|万|美元|元|￥|\$))', section)
            
            # Year mentions
            section_years = re.findall(r'(20\d\d)', section)
            
            # Score based on organization match
            for org in section_orgs:
                org = org.lower()
                if org in source_text:
                    score += 15
            
            # Score based on numbers/statistics match
            for num in section_numbers:
                if num in source_text:
                    score += 10
            
            # Score based on year match
            for year in section_years:
                if year in source_text:
                    score += 5
            
            # Technology terms
            tech_terms = ["ai", "人工智能", "模型", "算法", "agent", "llm", "大模型", 
                          "机器学习", "深度学习", "芯片", "gpu", "神经网络", "transformer"]
            
            for term in tech_terms:
                if term in section_text and term in source_text:
                    score += 3
            
            # Check for specific domains/site mentions
            if "www" in source_text or ".com" in source_text or ".cn" in source_text:
                domain_match = re.search(r'([a-zA-Z0-9]+\.[a-zA-Z0-9]+\.[a-z]+)', source_text)
                if domain_match and domain_match.group(1) in section_text:
                    score += 20
            
            scores.append((source, score))
        
        # Sort by score in descending order
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return the best matching source
        if scores and scores[0][1] > 0:
            return scores[0][0]
        elif available_sources:
            # Fallback to first available source if no good match
            return available_sources[0]
        return None
    
    # Function to extract URL from source text
    def extract_url_from_source(source_text):
        # Handle case where URL might end with a closing parenthesis
        # First try to find complete URL
        url_match = re.search(r'(https?://[^\s]+)', source_text)
        if url_match:
            url = url_match.group(1)
            # Remove ending parenthesis if it's not part of the URL structure
            if url.endswith(')') and '(' not in url[url.rfind('/'):]:
                url = url[:-1]
            return url
        
        # Try to find domain.tld pattern
        domain_match = re.search(r'([^\s]+\.(?:com|net|org|cn|io|ai|html)[^\s]*)', source_text)
        if domain_match:
            url = domain_match.group(1)
            # Remove ending parenthesis if it's not part of the URL path
            if url.endswith(')') and '(' not in url[url.rfind('/'):]:
                url = url[:-1]
            return url
        
        # If both fails, find text after the last dash or space
        if " - " in source_text:
            url = source_text.split(" - ")[-1].strip()
            # Remove ending parenthesis if it exists and is not balanced
            if url.endswith(')') and url.count('(') < url.count(')'):
                url = url[:-1]
            return url
        
        # Return as is if no pattern matches
        return source_text
    
    # Check if section already contains formatted links
    def has_formatted_references(section):
        # Check for patterns like: [Title](URL) or Title - URL
        link_patterns = [
            r'\[.+?\]\(.+?\)',  # Markdown link format
            r'.+? - (?:https?://|www\.)[^\s]+',  # Title - URL format
        ]
        
        for pattern in link_patterns:
            if re.search(pattern, section):
                return True
        return False
    
    # Process sections to add sources
    output_content = []
    used_sources = set()
    available_sources = individual_sources.copy()
    
    # Flag to indicate we've reached the reference section
    in_reference_section = False
    
    for i, section in enumerate(sections):
        # Check if we're in or past the reference section
        if i >= reference_section_index and reference_section_index != -1:
            in_reference_section = True
        
        # Check if this section already has formatted references
        has_refs = has_formatted_references(section)
        
        # Clean the section of any AI markers
        for pattern in ai_marker_patterns:
            section = re.sub(pattern, '', section, flags=re.IGNORECASE)
        
        # Clean up any resulting empty lines within the section
        section = re.sub(r'\n\s*\n\s*\n+', '\n\n', section)
        # Remove trailing whitespace at end of lines
        section = re.sub(r' +\n', '\n', section)
        
        # Skip empty sections or sections with just a heading
        if not section.strip() or (section.startswith('#') and len(section.strip().split('\n')) <= 1):
            output_content.append(section)
            continue
        
        # Check if this section already has a source attached
        if "**来源:**" in section or "**来源：**" in section:
            output_content.append(section)
            continue
        
        # Skip metadata sections - they don't need sources
        if is_metadata_section(section):
            output_content.append(section)
            continue
        
        # Skip sections that are too short or likely code blocks
        if len(section.strip().split('\n')) <= 1 or section.strip().endswith('```'):
            output_content.append(section)
            continue
            
        # Don't add sources to reference sections or sections after them
        if in_reference_section or has_refs:
            output_content.append(section)
            continue
        
        # Find the best matching source
        best_source = find_best_source_for_section(section, available_sources)
        
        if best_source:
            # Format the source block differently based on whether it's in reference section
            if i < reference_section_index or reference_section_index == -1:
                # For sections before reference section, only include URL
                url = extract_url_from_source(best_source)
                source_block = f"\n\n**来源:**\n- {url}"
            else:
                # For reference section, keep the original format
                source_block = f"\n\n**来源:**\n- {best_source}"
            
            # Add section content with source
            output_content.append(section + source_block)
            
            # Mark source as used
            used_sources.add(best_source)
            available_sources.remove(best_source)
        else:
            # No source available
            output_content.append(section)
    
    # Join all sections and clean up any excessive newlines
    result_content = '\n\n'.join(output_content)
    result_content = re.sub(r'\n{3,}', '\n\n', result_content)
    
    # Write the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result_content)
    
    # Report stats
    print(f"Processing complete: Used {len(used_sources)} sources out of {len(individual_sources)} total sources")
    if available_sources:
        print(f"Unused sources: {len(available_sources)}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python format_ai_report.py input_file output_file")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)
    
    process_md_file(input_file, output_file)
    print(f"Report formatted and saved to {output_file}") 