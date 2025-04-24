import re
import requests
from bs4 import BeautifulSoup
import argparse
from urllib.parse import urlparse
import os

def extract_links_from_content(content):
    """Extract all links from the markdown content before the references section."""
    # Pattern to find markdown links [text](url)
    md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    # Find the reference section
    ref_section_pattern = r'(参考资料|References|参考文献)'
    ref_match = re.search(ref_section_pattern, content, re.IGNORECASE)
    
    if ref_match:
        # Only consider content before the reference section
        content_before_refs = content[:ref_match.start()]
        # Extract all links from content before references
        links = re.findall(md_link_pattern, content_before_refs)
        return links
    else:
        # If no reference section found, extract from entire content
        links = re.findall(md_link_pattern, content)
        return links

def extract_reference_section(content):
    """Extract the reference section from the markdown content."""
    ref_section_pattern = r'(参考资料|References|参考文献).*?($|\Z)'
    ref_match = re.search(ref_section_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if ref_match:
        return ref_match.group(0)
    return ""

def extract_existing_references(ref_section):
    """Extract existing references and their numbers from the reference section."""
    if not ref_section:
        return [], 0
    
    # Pattern to match numbered references: 1. [text](url)
    ref_pattern = r'(\d+)\.\s+\[([^\]]+)\]\(([^)]+)\)'
    references = re.findall(ref_pattern, ref_section)
    
    max_ref_num = 0
    if references:
        max_ref_num = max(int(num) for num, _, _ in references)
    
    return references, max_ref_num

def get_article_info(url):
    """Get article title and author from URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to get the title
        title = soup.title.string if soup.title else ""
        title = title.strip()
        
        # Try to find author
        # This is tricky as different sites use different formats
        author = ""
        # Common patterns for author elements
        author_patterns = [
            "author", "byline", "meta[name*=author]", "meta[property*=author]",
            ".author", "#author", "[rel=author]", "[itemprop=author]"
        ]
        
        for pattern in author_patterns:
            author_elem = soup.select_one(pattern)
            if author_elem:
                if author_elem.name == "meta":
                    author = author_elem.get("content", "")
                else:
                    author = author_elem.text
                author = author.strip()
                if author:
                    break
        
        return title, author
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return url, ""

def create_new_reference(num, title, url, author=""):
    """Create a new reference with the given number, title, URL, and author."""
    if author:
        return f"{num}. [{title}]({url}) - {author}"
    else:
        return f"{num}. [{title}]({url})"

def process_markdown_file(file_path):
    """Process a markdown file to update its references."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract links from content
    content_links = extract_links_from_content(content)
    
    # Extract reference section
    ref_section = extract_reference_section(content)
    
    # Extract existing references
    existing_refs, max_ref_num = extract_existing_references(ref_section)
    
    # Extract URLs from existing references
    existing_urls = [url for _, _, url in existing_refs]
    
    # Process content links and add missing ones
    new_refs = []
    for link_text, link_url in content_links:
        # Skip if the URL is already in references
        if link_url in existing_urls:
            continue
        
        # Get article info
        title, author = get_article_info(link_url)
        if not title:
            title = link_text  # Use link text if title not found
        
        # Create new reference
        max_ref_num += 1
        new_ref = create_new_reference(max_ref_num, title, link_url, author)
        new_refs.append(new_ref)
    
    # Update content with new references
    if new_refs:
        if ref_section:
            # Find where the reference section starts in the content
            ref_start = content.find(ref_section)
            if ref_start != -1:
                # Remove the old reference section and add a completely new one with all references
                content_without_refs = content[:ref_start]
                
                # Rebuild reference section with existing and new references
                all_refs = []
                # Add existing references
                for i, (_, title, url) in enumerate(existing_refs):
                    author = ""  # Extract author if available in the existing reference
                    ref_text = f"{i+1}. [{title}]({url})"
                    if " - " in ref_text:
                        ref_parts = ref_text.split(" - ", 1)
                        ref_text = ref_parts[0]
                        author = ref_parts[1]
                    all_refs.append(create_new_reference(i+1, title, url, author))
                
                # Add new references
                for i, new_ref in enumerate(new_refs):
                    ref_num = len(existing_refs) + i + 1
                    # Extract reference info to standardize format
                    ref_match = re.match(r'\d+\.\s+\[([^\]]+)\]\(([^)]+)\)(.*)', new_ref)
                    if ref_match:
                        title, url, author_part = ref_match.groups()
                        all_refs.append(create_new_reference(ref_num, title, url, author_part.strip(" -")))
                
                # Create updated content with new reference section
                ref_header = "参考资料" if "参考资料" in ref_section else "References" if "References" in ref_section else "参考文献"
                updated_ref_section = f"\n\n{ref_header}\n" + "\n".join(all_refs)
                updated_content = content_without_refs + updated_ref_section
            else:
                # Fallback if reference section can't be found for some reason
                updated_content = content + "\n\n参考资料\n" + "\n".join(new_refs)
        else:
            # Create new reference section
            new_ref_section = "\n\n参考资料\n" + "\n".join(new_refs)
            updated_content = content + new_ref_section
    else:
        # No new references to add
        updated_content = content
    
    # Write updated content to file
    output_path = os.path.splitext(file_path)[0] + "_updated.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"Updated file saved to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Process markdown files to update references.')
    parser.add_argument('file', help='Path to the markdown file to process')
    args = parser.parse_args()
    
    process_markdown_file(args.file)

if __name__ == "__main__":
    main()
