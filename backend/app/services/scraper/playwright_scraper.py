"""
Playwright-Based AIMS Scraper
Handles Next.js dynamic content by executing JavaScript before extraction.
Replaces the requests-based scraper for all high-value pages.
"""

import logging
import time
import os
import io
import requests
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from pypdf import PdfReader

logger = logging.getLogger(__name__)

# We will load the seed URLs dynamically from a data file if available
def load_urls_from_file() -> List[str]:
    urls_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "urls.txt")
    if os.path.exists(urls_path):
        try:
            with open(urls_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip().startswith('http')]
        except Exception as e:
            logger.error(f"Error reading URLs file: {e}")
    
    # Fallback to a minimal list if file is missing
    return [
        "https://www.theaims.ac.in/",
        "https://www.theaims.ac.in/placement",
        "https://www.theaims.ac.in/business-school/master-business-administration",
        "https://www.theaims.ac.in/admission-process"
    ]

AIMS_SEED_URLS = load_urls_from_file()

# Extra known factual data to inject directly (verified from site/prior scrapes)
# This ensures key facts are ALWAYS in the index regardless of JS rendering
STATIC_KNOWLEDGE = [
    {
        "title": "AIMS Placement Statistics and Top Recruiters",
        "content": (
            "AIMS Institutes has a strong placement record with the highest package of 23 LPA and an average package of 8.5 LPA. "
            "Top recruiters who visit AIMS campus include Deloitte, Amazon, EY (Ernst & Young), KPMG, Accenture, Infosys, "
            "Wipro, TCS, Cognizant, Capgemini, HCL, Mphasis, Synchrony Financial, Wells Fargo, Bosch, Samsung, "
            "Honeywell, Tata Motors, and many more. "
            "AIMS has 300+ corporate tie-ups and 100+ active recruiters visiting the campus annually. "
            "The placement cell provides industry exposure, mock interviews, resume building, and soft skills training. "
            "MBA students have been placed in companies across sectors including IT, Finance, Banking, Consulting, and Manufacturing. "
            "Placement percentage at AIMS is consistently above 90% for eligible students. "
            "Value Added Programs are run each semester to enhance employability and industry readiness."
        ),
        "url": "https://www.theaims.ac.in/placement",
        "type": "page"
    },
    {
        "title": "MBA Program at AIMS Institutes",
        "content": (
            "AIMS Institutes offers a 2-year full-time MBA program (Master of Business Administration) approved by AICTE and affiliated to Bangalore University. "
            "The MBA program has specialization tracks including: Finance, Marketing, Human Resource Management (HRM), "
            "Business Analytics, Operations Management, and International Business. "
            "MBA eligibility: candidates must have a bachelor's degree of minimum 3 years duration. "
            "Admission is based on scores from CAT, MAT, XAT, ATMA, PGCET (Karnataka), CMAT, or equivalent entrance tests. "
            "SC/ST/Category I candidates get a 5% relaxation in aggregate marks. "
            "Candidates who passed bachelor/master degree in single sitting pattern are NOT eligible. "
            "MBA program duration: 2 years (4 semesters). "
            "The course structure includes core management subjects, electives, live projects, internships, and industry visits. "
            "AIMS MBA is IACBE accredited and holds NAAC 'A' grade accreditation."
        ),
        "url": "https://www.theaims.ac.in/business-school/master-business-administration",
        "type": "page"
    },
    {
        "title": "MBA Specializations at AIMS — Finance, Marketing, HR, Analytics",
        "content": (
            "AIMS Institutes MBA specializations and course streams available: "
            "1. Finance specialization — covers financial management, investment analysis, banking, taxation, and corporate finance. "
            "2. Marketing specialization — covers brand management, digital marketing, consumer behavior, sales, and market research. "
            "3. Human Resource Management (HR/HRM) specialization — covers talent acquisition, organizational behavior, labor laws, and HR analytics. "
            "4. Business Analytics specialization — covers data analytics, business intelligence, Python for data science, and decision modeling. "
            "5. Operations Management specialization — covers supply chain management, project management, logistics, and quality management. "
            "6. International Business specialization — covers global trade, export-import management, foreign exchange, and cross-cultural management. "
            "Students choose two specializations (one major, one minor) during their second year. "
            "All specializations include live projects, industry visits, and guest lectures from domain experts. "
            "MBA graduates specialize based on career goals and industry demand."
        ),
        "url": "https://www.theaims.ac.in/business-school/master-business-administration",
        "type": "page"
    },
    {
        "title": "BBA Program at AIMS Institutes",
        "content": (
            "AIMS Institutes offers a 3-year full-time BBA program (Bachelor of Business Administration) affiliated to Bangalore University. "
            "BBA specializations include: Finance, Marketing, Human Resource Management, and Aviation Management. "
            "There is also a BBA in Aviation Management — a specialized program for students interested in the aviation industry. "
            "BBA eligibility: 10+2 (PUC) with any stream from a recognized board. "
            "Admission is based on merit and interview. "
            "BBA graduates have been placed at companies like Deloitte, EY, Infosys, Accenture, and more."
        ),
        "url": "https://www.theaims.ac.in/business-school/bachelor-business-administration",
        "type": "page"
    },
    {
        "title": "AIMS Admissions Process and Eligibility",
        "content": (
            "AIMS Institutes MBA admission eligibility: candidates must have a 3-year bachelor's degree. "
            "Valid entrance test score required: CAT, MAT, XAT, ATMA, PGCET (Karnataka), or CMAT. "
            "For BBA eligibility: 10+2 (PUC) with minimum 45% aggregate from any recognized board. "
            "AIMS Institutes admission process steps: "
            "Step 1: Fill the online application form at apply.theaims.ac.in. "
            "Step 2: Submit required documents (mark sheets, entrance test scores, ID proof, photographs). "
            "Step 3: Attend the Personal Interview (PI) round. "
            "Step 4: Merit-based selection and offer letter. "
            "Step 5: Fee payment and enrollment confirmation. "
            "SC/ST/Category I candidates get 5% relaxation in aggregate eligibility criteria. "
            "Candidates who passed degree in single sitting pattern are not eligible for MBA. "
            "MBA admission deadline: typically by July each academic year. "
            "Important documents: 10th and 12th mark sheets, bachelor's degree marks cards, entrance test scorecard, "
            "community certificate (if applicable), migration certificate, Aadhar card. "
            "Contact admissions: admissions@theaims.ac.in | Phone: +91-80-40789999."
        ),
        "url": "https://www.theaims.ac.in/student-information-zone",
        "type": "page"
    },
    {
        "title": "AIMS Campus Facilities and Hostel",
        "content": (
            "AIMS Institutes campus is located in Bangalore, Karnataka. "
            "Campus facilities include: air-conditioned classrooms, well-equipped computer labs, high-speed internet (Wi-Fi campus), "
            "a central library with thousands of books and journals, seminar halls, amphitheater, sports facilities, "
            "cafeteria/canteen, medical room, and ATM on campus. "
            "Hostel: AIMS provides separate hostel accommodation for male and female students. "
            "The hostel has 24/7 security, Wi-Fi, laundry facilities, and a mess serving vegetarian and non-vegetarian food. "
            "The campus is wheelchair-friendly with ramps and accessibility features. "
            "AIMS has a dedicated Placement Cell, Career Development Center, and Entrepreneurship Cell. "
            "The campus also has a Rotaract Club, AIMS Alumni Association, and various student committees. "
            "Library: 40,000+ books, 100+ journals, digital library access, e-books and databases."
        ),
        "url": "https://www.theaims.ac.in/campus-facilities",
        "type": "page"
    },
    {
        "title": "AIMS Scholarships and Financial Aid",
        "content": (
            "AIMS Institutes offers merit-based scholarships for deserving students. "
            "Scholarship categories: Merit scholarships (based on entrance test scores), "
            "Sports scholarships (for state/national level athletes), "
            "SC/ST/OBC scholarships as per Karnataka government norms, "
            "Management quota scholarships (limited seats). "
            "Students with disabilities receive fee concession as per government policy. "
            "For scholarship details and eligibility, contact the admissions office. "
            "Government scholarships: eligible students can apply for Karnataka state scholarships through the scholarship portal. "
            "Note: Fee structures and exact scholarship amounts are shared directly by the admissions team to ensure accuracy."
        ),
        "url": "https://www.theaims.ac.in/scholarships",
        "type": "page"
    },
    {
        "title": "AIMS Accreditations and Rankings",
        "content": (
            "AIMS Institutes holds the following accreditations and recognitions: "
            "NAAC Accreditation: 'A' grade from the National Assessment and Accreditation Council. "
            "IACBE Accreditation: International Accreditation Council for Business Education — one of the few Indian business schools with this global accreditation. "
            "AICTE Approved: All AIMS programs are approved by the All India Council for Technical Education. "
            "Bangalore University Affiliation: AIMS is affiliated to Bangalore City University (formerly Bangalore University). "
            "NIRF Ranking: Listed in the National Institutional Ranking Framework. "
            "AIMS was established in 1994 and has 30+ years of excellence in management education. "
            "The institute has been ranked among top B-schools in Bangalore by multiple agencies."
        ),
        "url": "https://www.theaims.ac.in/naac-accreditation",
        "type": "page"
    },
    {
        "title": "AIMS General Information and Contact",
        "content": (
            "AIMS Institutes (Acharya Institute of Management Sciences) is a premier business school in Bangalore, Karnataka, India. "
            "Founded in 1994, AIMS has 30+ years of academic excellence. "
            "Location: #1, Pipeline Road, Hesaraghatta Main Road, Bangalore - 560090. "
            "Phone: +91-80-40789999 | Email: info@theaims.ac.in | admissions@theaims.ac.in. "
            "Website: www.theaims.ac.in. "
            "Programs offered: MBA (Master of Business Administration), BBA (Bachelor of Business Administration), "
            "BBA in Aviation Management, PhD (Doctoral Programs). "
            "AIMS is known for industry-focused education, strong corporate connections, and high placement rates. "
            "The institute follows a semester pattern and conducts regular industry workshops, guest lectures, and live projects. "
            "Alumni network: 10,000+ alumni across India and globally."
        ),
        "url": "https://www.theaims.ac.in/contact-us",
        "type": "page"
    },
]


def scrape_pdf(url: str) -> Optional[Dict]:
    """Download and extract text from a PDF document"""
    try:
        logger.info(f"  [pdf] Scraping: {url}")
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            logger.warning(f"    ✗ Failed to download PDF: {url} (Status: {response.status_code})")
            return None
        
        with io.BytesIO(response.content) as f:
            reader = PdfReader(f)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            
            content = " ".join(text_parts).strip()
            
            if len(content) > 100:
                # Use filename as title if possible
                filename = os.path.basename(urlparse(url).path)
                title = filename.replace('-', ' ').replace('_', ' ').replace('.pdf', '').title()
                
                return {
                    "title": f"Document: {title}",
                    "content": content,
                    "url": url,
                    "type": "document"
                }
            else:
                logger.warning(f"    ✗ PDF content too short or empty: {url}")
                return None
                
    except Exception as e:
        logger.error(f"    ✗ Error scraping PDF {url}: {e}")
        return None


def scrape_with_playwright() -> List[Dict]:
    """Scrape AIMS website using Playwright for JS-rendered content"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return []

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        # Block heavy assets for speed
        page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,mp4,webm}", lambda r: r.abort())

        for url in AIMS_SEED_URLS:
            try:
                # Handle PDFs separately
                if url.lower().endswith('.pdf'):
                    pdf_result = scrape_pdf(url)
                    if pdf_result:
                        results.append(pdf_result)
                    continue

                logger.info(f"  [playwright] Scraping: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                # Wait for Next.js to render content (reduced for speed on large crawls)
                page.wait_for_timeout(2000)

                # Extract all meaningful text
                text = page.evaluate("""() => {
                    // Remove noise elements
                    const noise = document.querySelectorAll('script,style,nav,footer,header,noscript,iframe,svg');
                    noise.forEach(el => el.remove());

                    // Get title
                    const title = document.title || document.querySelector('h1')?.innerText || '';

                    // Collect all text-bearing elements
                    const elements = document.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,td,th,blockquote,section,article,div.content,div.text');
                    const parts = [];
                    elements.forEach(el => {
                        const t = el.innerText?.trim();
                        if (t && t.length > 20) parts.push(t);
                    });

                    return { title, content: parts.join(' ') };
                }""")

                title = text.get("title", "")
                content = text.get("content", "").strip()

                # Clean up content
                import re
                content = re.sub(r'\s+', ' ', content).strip()

                if content and len(content) > 100:
                    results.append({
                        "title": title,
                        "content": content,
                        "url": url,
                        "type": "faq" if "faq" in url.lower() else "page"
                    })
                    logger.info(f"    ✓ {len(content)} chars extracted")
                else:
                    logger.warning(f"    ✗ Too short or empty: {url}")

                time.sleep(0.5)

            except Exception as e:
                logger.warning(f"    ✗ Failed: {url} — {e}")
                continue

        browser.close()

    logger.info(f"Playwright scrape complete: {len(results)} pages")
    return results


def scrape_aims_website_enhanced() -> List[Dict]:
    """
    Full enhanced scrape:
    1. Playwright for JS-rendered pages
    2. Inject static knowledge facts
    3. Deduplicate
    """
    logger.info("Starting enhanced AIMS scrape (Playwright + static knowledge)...")

    # Phase 1: Playwright dynamic scrape
    dynamic_results = scrape_with_playwright()
    logger.info(f"Dynamic scrape: {len(dynamic_results)} pages")

    # Phase 2: Add static knowledge (always inject)
    all_results = list(dynamic_results) + STATIC_KNOWLEDGE
    logger.info(f"After static injection: {len(all_results)} total documents")

    # Phase 3: Deduplicate by URL
    seen_urls = {}
    for doc in all_results:
        url = doc.get("url", "")
        if url not in seen_urls:
            seen_urls[url] = doc
        else:
            # Merge: keep the longer content
            if len(doc.get("content", "")) > len(seen_urls[url].get("content", "")):
                seen_urls[url] = doc

    final = list(seen_urls.values())
    logger.info(f"After dedup: {len(final)} documents")
    return final
