"""
Agent 1: JobLinkVerifier
Part of the Promora AI-powered hiring platform

This agent validates job posting links and extracts structured data.
"""

import json
import logging
from typing import Dict, Any, Optional
import sys
import os

# Import utils from parent src directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.scraper import fetch_html_cleaned, fetch_html_raw
from utils.prompt_loader import load_prompt_with_placeholder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_agent_1(url: str) -> Dict[str, Any]:
    """
    Run Agent 1: JobLinkVerifier to validate a job posting link.
    
    This function:
    1. Fetches and cleans HTML content from the URL
    2. Loads the validation prompt template
    3. Replaces the {{html_content}} placeholder with actual content
    4. Returns a mocked JSON response (ready for GPT-4 integration)
    
    Args:
        url (str): The job posting URL to validate
        
    Returns:
        Dict[str, Any]: JSON response containing validation result and extracted data
        
    Example:
        >>> result = run_agent_1("https://company.com/careers/engineer")
        >>> print(result)
        {
            "isValidJobPage": true,
            "jobTitle": "AI Engineer",
            "company": "Promora Inc.",
            "jobDescription": "You will build AI agents for hiring evaluations."
        }
    """
    try:
        logger.info(f"Starting Agent 1 validation for URL: {url}")
        
        # Step 1: Fetch raw HTML content for analysis
        logger.info("Step 1: Fetching HTML content...")
        html_content = fetch_html_raw(url)
        
        if html_content is None:
            logger.error("Failed to fetch HTML content")
            return {
                "isValidJobPage": False,
                "error": "Failed to fetch content from URL"
            }
        
        logger.info(f"Successfully fetched {len(html_content)} characters of content")
        
        # Step 2: Load the prompt template
        logger.info("Step 2: Loading prompt template...")
        try:
            prompt = load_prompt_with_placeholder(
                filename="validate_job_link.txt",
                placeholder="{{html_content}}",
                replacement=html_content
            )
            logger.info("Successfully loaded and populated prompt template")
        except Exception as e:
            logger.error(f"Failed to load prompt template: {str(e)}")
            return {
                "isValidJobPage": False,
                "error": f"Failed to load prompt template: {str(e)}"
            }
        
        # Step 3: Analyze the scraped content
        logger.info("Step 3: Analyzing scraped content...")
        
        # Use real analysis instead of mocked responses
        analysis_result = _analyze_scraped_content(html_content, url)
        
        logger.info(f"Agent 1 completed successfully. Result: {analysis_result['isValidJobPage']}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Unexpected error in Agent 1: {str(e)}")
        return {
            "isValidJobPage": False,
            "error": f"Unexpected error: {str(e)}"
        }


def run_agent_1_with_real_analysis(url: str) -> Dict[str, Any]:
    """
    Run Agent 1 with real analysis (placeholder for GPT-4 integration).
    
    This function demonstrates how the agent would work with actual AI analysis.
    Currently returns a mock response, but can be extended to call GPT-4 API.
    
    Args:
        url (str): The job posting URL to validate
        
    Returns:
        Dict[str, Any]: JSON response with real analysis results
    """
    try:
        logger.info(f"Running Agent 1 with real analysis for URL: {url}")
        
        # Fetch HTML content
        html_content = fetch_html_cleaned(url)
        if html_content is None:
            return {"isValidJobPage": False, "error": "Failed to fetch content"}
        
        # Load prompt template
        prompt = load_prompt_with_placeholder(
            filename="validate_job_link.txt",
            placeholder="{{html_content}}",
            replacement=html_content
        )
        
        # TODO: Replace this with actual GPT-4 API call
        # For now, return a mock response
        logger.info("TODO: Integrate with GPT-4 API for real analysis")
        
        return {
            "isValidJobPage": True,
            "jobTitle": "Senior AI Engineer",
            "company": "FutureTech Corp",
            "jobDescription": "This is a placeholder for real AI analysis results. The actual implementation would call GPT-4 API with the prompt to get real validation and extraction results.",
            "note": "This is a mock response. Real implementation would use GPT-4 API."
        }
        
    except Exception as e:
        logger.error(f"Error in real analysis mode: {str(e)}")
        return {"isValidJobPage": False, "error": str(e)}


def _analyze_scraped_content(html_content: str, url: str) -> Dict[str, Any]:
    """
    Analyze scraped HTML content to determine if it's a valid job posting.
    
    Args:
        html_content (str): Scraped HTML content
        url (str): Original URL
        
    Returns:
        Dict[str, Any]: Analysis result with job data or validation failure
    """
    try:
        # Simple content analysis using keyword matching
        content_lower = html_content.lower()
        
        # Check if it's likely a job posting
        job_indicators = [
            'job', 'position', 'career', 'hiring', 'employment', 'vacancy',
            'title', 'description', 'requirements', 'responsibilities',
            'apply', 'application', 'resume', 'cv'
        ]
        
        job_score = sum(1 for indicator in job_indicators if indicator in content_lower)
        
        # Check if it's a job board or search results (should reject)
        job_board_indicators = [
            'search results', 'browse jobs', 'job listings', 'find jobs',
            'multiple positions', 'open positions', 'career opportunities'
        ]
        
        job_board_score = sum(1 for indicator in job_board_indicators if indicator in content_lower)
        
        # Determine if it's a valid single job posting
        is_valid = job_score >= 3 and job_board_score < 2
        
        if not is_valid:
            return {"isValidJobPage": False}
        
        # Extract job information using simple patterns
        job_title = _extract_job_title(html_content)
        company_name = _extract_company_name(html_content, url)
        job_description = _extract_job_description(html_content)
        
        return {
            "isValidJobPage": True,
            "jobTitle": job_title,
            "company": company_name,
            "jobDescription": job_description
        }
        
    except Exception as e:
        logger.error(f"Error analyzing content: {str(e)}")
        return {"isValidJobPage": False, "error": f"Analysis error: {str(e)}"}


def _extract_job_title(html_content: str) -> str:
    """Extract job title from HTML content."""
    import re
    
    # Look for common title patterns
    title_patterns = [
        r'<h1[^>]*>(.*?)</h1>',
        r'<title[^>]*>(.*?)</title>',
        r'class="[^"]*title[^"]*"[^>]*>(.*?)<',
        r'class="[^"]*job-title[^"]*"[^>]*>(.*?)<'
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            title = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if title and len(title) > 3:
                return title
    
    # Fallback: look for text that looks like a job title
    lines = html_content.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        line = re.sub(r'<[^>]+>', '', line).strip()
        if line and len(line) > 5 and len(line) < 100:
            if any(word in line.lower() for word in ['developer', 'engineer', 'manager', 'analyst', 'specialist']):
                return line
    
    return "Position Not Specified"


def _extract_company_name(html_content: str, url: str) -> str:
    """Extract company name from HTML content."""
    import re
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Priority 1: Look for "Hiring Company" field (common in job boards like iCIMS)
    # Try BeautifulSoup first for structured extraction
    hiring_company_elements = soup.find_all(string=re.compile(r'Hiring\s+Company', re.I))
    for elem in hiring_company_elements:
        # Get parent and find the next text or element
        parent = elem.parent
        if parent:
            # Look for the company name in the same element or nearby
            parent_text = parent.get_text()
            match = re.search(r'Hiring\s+Company[:\s]+([^<\n]+?)(?:\n|$|</)', parent_text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Clean up common suffixes but keep them if it's part of the name
                # Only remove trailing ", Inc." if it's clearly separate
                if company.endswith(', Inc.') or company.endswith(', LLC'):
                    company = company.rsplit(',', 1)[0].strip()
                if 5 <= len(company) <= 100:
                    return company
            # Also check sibling elements
            next_sibling = parent.find_next_sibling()
            if next_sibling:
                company = next_sibling.get_text().strip()
                if 5 <= len(company) <= 100:
                    return company
    
    # Also try regex patterns on HTML
    hiring_company_patterns = [
        r'<[^>]*>Hiring\s+Company[:\s]*</[^>]*>([^<]+)',
        r'Hiring\s+Company[:\s]+([A-Z][^<\n,]{5,80})',  # Match company names starting with capital
        r'Hiring\s+Company[:\s]+([^<\n]+)',
    ]
    for pattern in hiring_company_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            company = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            # Remove trailing ", Inc." or ", LLC" if present
            company = re.sub(r',\s*(Inc|LLC|Corp|Corporation)\.?$', '', company, flags=re.IGNORECASE).strip()
            # Remove any trailing commas
            company = company.rstrip(',').strip()
            if 5 <= len(company) <= 100:
                return company
    
    # Priority 2: Look for company name in structured data or meta tags
    # Check for JSON-LD or other structured data
    script_tags = soup.find_all('script', type=re.compile(r'application/(ld\+json|json)'))
    for script in script_tags:
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, dict):
                # Check various fields that might contain company name
                for field in ['hiringOrganization', 'employer', 'company', 'organization']:
                    if field in data:
                        org = data[field]
                        if isinstance(org, dict) and 'name' in org:
                            return org['name']
                        elif isinstance(org, str):
                            return org
        except:
            pass
    
    # Priority 3: Look for company name patterns in text
    company_patterns = [
        r'Hiring\s+Company[:\s]+([A-Z][^<\n]{5,80})',
        r'Company[:\s]+([A-Z][^<\n]{5,80})',
        r'Employer[:\s]+([A-Z][^<\n]{5,80})',
        r'at\s+([A-Z][a-zA-Z\s&,\-\.]{5,80})\s+(Inc|LLC|Corp|Systems|Technologies)',
        r'<title[^>]*>.*?at\s+([A-Z][a-zA-Z\s&]+)',  # Job title at Company
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            company = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            # Remove common job board suffixes
            company = re.sub(r'\s*\|\s*.*$', '', company)  # Remove | job board name
            if company and 5 <= len(company) <= 100:
                return company
    
    # Priority 4: Look for company name in specific HTML structures
    company_selectors = [
        {'class': re.compile(r'company', re.I)},
        {'class': re.compile(r'employer', re.I)},
        {'class': re.compile(r'hiring-company', re.I)},
        {'id': re.compile(r'company', re.I)},
    ]
    
    for selector in company_selectors:
        elements = soup.find_all(attrs=selector)
        for elem in elements:
            text = elem.get_text().strip()
            if text and 5 <= len(text) <= 100 and not any(word in text.lower() for word in ['search', 'apply', 'job', 'login']):
                return text
    
    # Fallback: Extract from URL domain (last resort)
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if domain:
            # Handle subdomains like careers-gdms.icims.com -> General Dynamics Mission Systems
            # This is imperfect, so it's a last resort
            domain_part = domain.replace('www.', '').split('.')[0]
            # If it looks like an abbreviation (short, all caps), don't use it
            if len(domain_part) > 5:
                return domain_part.replace('-', ' ').title()
    except:
        pass
    
    return "Company Not Specified"


def _extract_text_with_paragraphs(element) -> str:
    """Extract text while preserving paragraph structure."""
    import html
    
    paragraphs = []
    
    # Find all paragraph-like elements
    for tag in element.find_all(['p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        if tag.name in ['p', 'div']:
            text = tag.get_text().strip()
            if text and len(text) > 10:  # Only add substantial text
                # Decode HTML entities and Unicode escapes
                text = html.unescape(text)
                paragraphs.append(text)
        elif tag.name == 'br':
            paragraphs.append('')  # Add empty line for breaks
        elif tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            text = tag.get_text().strip()
            if text:
                # Decode HTML entities and Unicode escapes
                text = html.unescape(text)
                paragraphs.append(f"\n{text}\n")  # Add headers with spacing
    
    # If no paragraphs found, fall back to regular text extraction
    if not paragraphs:
        text = element.get_text().strip()
        return html.unescape(text)
    
    # Join paragraphs with double newlines to preserve structure
    return '\n\n'.join(paragraphs)

def _extract_job_description(html_content: str) -> str:
    """Extract job description from HTML content."""
    import re
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove only specific navigation elements, not all containers
    for element in soup.find_all(['nav', 'header', 'footer', 'aside']):
        element.decompose()
    
    # Remove only specific UI elements, not entire containers
    for element in soup.find_all(['button', 'a']):
        text = element.get_text().strip()
        if text in ['Apply', 'Back to jobs', 'New', 'Create alert']:
            element.decompose()
    
    # Don't remove text elements as they might be part of the job description
    
    # Look for the main content area
    # Try to find the job description container
    main_content = None
    
    # Look for containers with job description content
    potential_containers = soup.find_all(['div', 'section', 'article', 'main'])
    
    # Find the container with the most complete job content
    best_container = None
    best_score = 0
    
    for container in potential_containers:
        text = container.get_text().strip()
        if len(text) > 500:  # Substantial content
            # Score based on job-related content
            score = 0
            if 'about the role' in text.lower():
                score += 10
            if 'bonus points' in text.lower():
                score += 10
            if 'this role is eligible for equity' in text.lower():
                score += 10
            if 'salary range' in text.lower():
                score += 10
            if 'responsibilities' in text.lower() or 'you will' in text.lower():
                score += 5
            if 'requirements' in text.lower() or 'you\'ll be a great addition' in text.lower():
                score += 5
            if 'company' in text.lower() or 'amplitude' in text.lower():
                score += 3
            
            # Prefer longer content (more complete)
            score += min(len(text) // 1000, 10)  # Up to 10 points for length
            
            if score > best_score:
                best_score = score
                best_container = container
    
    if best_container:
        main_content = best_container
    
    if main_content:
        # Extract text while preserving paragraph structure
        desc_text = _extract_text_with_paragraphs(main_content)
        
        # Decode Unicode escape sequences first
        import html
        import codecs
        try:
            # Decode Unicode escapes like \u00a0
            desc_text = codecs.decode(desc_text, 'unicode_escape')
        except:
            pass
        desc_text = html.unescape(desc_text)
        
        # Remove repetitive navigation patterns at the start
        navigation_patterns = [
            r'^(Search Again\s*)+',
            r'^(Returning Candidate\?[\s\n]*Log back in![\s\n]*)+',
            r'^Please Enable Cookies to Continue.*?Returning Candidate\?[\s\n]*',
            r'Please enable cookies.*?Log back in![\s\n]*',
        ]
        for pattern in navigation_patterns:
            desc_text = re.sub(pattern, '', desc_text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
        
        # Find the start of actual job content (skip navigation)
        job_start_indicators = [
            r'Job Location',
            r'Posted Date',
            r'Required Clearance',
            r'Basic Qualifications',
            r'Responsibilities',
            r'Job Description',
            r'About.*Role',
            r'What you\'ll',
        ]
        
        for indicator in job_start_indicators:
            match = re.search(indicator, desc_text, re.IGNORECASE)
            if match:
                # Start from a bit before the indicator to include title
                start_pos = max(0, match.start() - 200)
                # But try to find a better boundary (start of line or paragraph)
                better_start = desc_text.rfind('\n\n', 0, match.start())
                if better_start != -1:
                    start_pos = better_start + 2
                desc_text = desc_text[start_pos:]
                break
        
        # Remove common UI artifacts and navigation elements (but preserve salary info)
        desc_text = re.sub(r'Back to jobs.*?Apply', '', desc_text, flags=re.DOTALL | re.IGNORECASE)
        desc_text = re.sub(r'Search Again\s*', '', desc_text, flags=re.IGNORECASE)
        desc_text = re.sub(r'Returning Candidate\?[\s\n]*Log back in![\s\n]*', '', desc_text, flags=re.IGNORECASE)
        desc_text = re.sub(r'Create a Job Alert.*?Create alert', '', desc_text, flags=re.DOTALL | re.IGNORECASE)
        desc_text = re.sub(r'New\s*$', '', desc_text, flags=re.MULTILINE)
        
        # Remove application form content markers
        application_markers = [
            r'Apply\s*Apply for this job.*',
            r'Autofill with.*',
            r'First Name\*.*',
            r'Demographic Questions.*',
            r'Need help finding.*',
            r'Application FAQs.*',
            r'Software Powered by.*',
            r'Equal Opportunity.*?Veteran.*',  # Usually at the very end
        ]
        
        earliest_form_start = len(desc_text)
        for marker in application_markers:
            # Extract the literal text to search for (before regex operators)
            search_text = marker.split('.*')[0].replace('\\', '').replace('(', '').replace(')', '').replace('[', '').replace(']', '')
            marker_pos = desc_text.lower().find(search_text.lower())
            if marker_pos != -1 and marker_pos < earliest_form_start:
                earliest_form_start = marker_pos
        
        # Also look for common end markers
        end_markers = [
            'Equal Opportunity Employer',
            'Application FAQs',
            'Software Powered by',
            'Apply for this job online',
            'Need help finding the right job?',
        ]
        
        for marker in end_markers:
            marker_pos = desc_text.find(marker)
            if marker_pos != -1 and marker_pos < earliest_form_start:
                earliest_form_start = marker_pos
        
        if earliest_form_start < len(desc_text):
            desc_text = desc_text[:earliest_form_start].strip()
        
        # Remove any remaining repetitive patterns
        desc_text = re.sub(r'(Search Again\s*)+', '', desc_text, flags=re.IGNORECASE)
        desc_text = re.sub(r'(Returning Candidate\?[\s\n]*Log back in![\s\n]*)+', '', desc_text, flags=re.IGNORECASE)
        
        # Clean up whitespace but preserve paragraph breaks
        desc_text = re.sub(r'[ \t]+', ' ', desc_text)  # Replace multiple spaces/tabs with single space
        desc_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', desc_text)  # Replace multiple newlines with double newline
        desc_text = re.sub(r'^\s+', '', desc_text, flags=re.MULTILINE)  # Remove leading whitespace from lines
        
        # Remove any standalone "Search Again" or similar leftover text
        lines = desc_text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not re.match(r'^(Search Again|Returning Candidate|Log back in|Please enable cookies)', line, re.IGNORECASE):
                cleaned_lines.append(line)
        desc_text = '\n'.join(cleaned_lines)
        
        # Final cleanup
        desc_text = re.sub(r'\n{3,}', '\n\n', desc_text)  # Max 2 consecutive newlines
        desc_text = desc_text.strip()
        
        if len(desc_text) > 200:  # Ensure it's substantial content
            return desc_text
    
    # Fallback: look for description patterns
    desc_patterns = [
        r'class="[^"]*description[^"]*"[^>]*>(.*?)</[^>]*>',
        r'class="[^"]*job-content[^"]*"[^>]*>(.*?)</[^>]*>',
        r'class="[^"]*content[^"]*"[^>]*>(.*?)</[^>]*>'
    ]
    
    for pattern in desc_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            desc = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if desc and len(desc) > 50:
                return desc
    
    return "Description Not Available"


def validate_response_format(response: Dict[str, Any]) -> bool:
    """
    Validate that the response has the correct format.
    
    Args:
        response (Dict[str, Any]): The response to validate
        
    Returns:
        bool: True if format is valid, False otherwise
    """
    if not isinstance(response, dict):
        return False
    
    if "isValidJobPage" not in response:
        return False
    
    if not isinstance(response["isValidJobPage"], bool):
        return False
    
    if response["isValidJobPage"]:
        required_fields = ["jobTitle", "company", "jobDescription"]
        return all(field in response for field in required_fields)
    
    return True
