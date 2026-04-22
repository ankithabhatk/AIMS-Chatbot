"""
AIMS Institutes — Official Knowledge Base
==========================================
SOURCE: Official AIMS brochure, placement reports, and admissions documentation
PRIORITY: 2 (highest — always beats scraped web data)
VERSION: 1.0

These chunks are structured, verified, and institution-provided.
They replace scraped approximations for all key facts.
DO NOT modify without re-verifying against official AIMS documents.
"""

from typing import List, Dict

# ─────────────────────────────────────────────────────────────────────────────
# OFFICIAL CHUNK BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _chunk(title: str, content: str, url: str, category: str) -> Dict:
    """Build a standardized official knowledge chunk."""
    return {
        "title": title,
        "content": content.strip(),
        "url": url,
        "type": "official",
        "source": "official",
        "priority": 2,
        "category": category,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PLACEMENTS (HIGHEST PRIORITY — most asked at demo)
# ─────────────────────────────────────────────────────────────────────────────

PLACEMENTS = [
    _chunk(
        title="AIMS Placement Statistics — Official Data",
        content="""
AIMS Institutes Placement Record (Official):

Key Statistics:
- Highest Package (Overall): ₹27 LPA
- Highest Package (Current Batch): ₹16.5 LPA
- Average Package: ₹8 LPA
- Placement Rate: 84% of eligible students placed
- Internship to Pre-Placement Offer (PPO) Conversion: 70%

Top Recruiting Companies:
Deloitte, EY (Ernst & Young), KPMG, Accenture, Amazon, Infosys, Wipro, TCS,
Cognizant, Capgemini, HCL, Mphasis, Synchrony Financial, Wells Fargo,
Bosch, Samsung, Honeywell, Tata Motors, Bajaj Finserv, HDFC Bank,
Axis Bank, ICICI Bank, Reliance Industries, ITC, Berger Paints.

Sector Coverage:
IT & Software, BFSI (Banking, Financial Services & Insurance),
Consulting, Manufacturing, FMCG, Healthcare, Logistics & Supply Chain,
E-Commerce, Real Estate.

Placement Support:
- Dedicated Placement Cell with industry professionals
- 300+ corporate tie-ups and 100+ annual recruiters
- Mock interviews, resume workshops, and soft skills training
- Group discussion and aptitude training
- Industry mentorship programs
- Value Added Programs (VAP) every semester
        """,
        url="https://www.theaims.ac.in/placement",
        category="placements",
    ),

    _chunk(
        title="AIMS Placement Cell and Career Support",
        content="""
AIMS Placement Cell — Career Development Services:

The AIMS Placement Cell bridges students with the corporate world through:

Pre-Placement Training:
- Aptitude and logical reasoning workshops
- Group discussion (GD) preparation
- Personal interview (PI) coaching
- Resume and LinkedIn profile building
- Business communication and email etiquette

Industry Exposure:
- Live projects with partner companies
- Industry visits and plant tours
- Guest lectures by senior industry professionals
- Case study competitions and hackathons
- Leadership summits and management conclaves

Internship Programme:
- Mandatory summer internship (8–10 weeks) for all MBA students
- 70% of internships convert to Pre-Placement Offers (PPO)
- Stipend-based internships at top companies

Alumni Network:
- 10,000+ AIMS alumni across India and globally
- Active alumni mentoring and referral programme
- Annual alumni meet connecting students with industry leaders
        """,
        url="https://www.theaims.ac.in/placement",
        category="placements",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# MBA PROGRAM
# ─────────────────────────────────────────────────────────────────────────────

MBA = [
    _chunk(
        title="MBA Program — Specializations, Eligibility, and Entrance Exams",
        content="""
MBA (Master of Business Administration) at AIMS Institutes

Duration: 2 years (4 semesters)
Affiliation: Bangalore City University (formerly Bangalore University)
Approval: AICTE Approved
Accreditation: IACBE (International), NAAC 'A' Grade

Specializations Available:
1. Marketing Management
2. Finance Management
3. Human Resource Management (HRM)
4. Business Analytics
5. Healthcare Management
6. BFSI (Banking, Financial Services & Insurance)
7. Logistics & Supply Chain Management
8. Operations Management
9. International Business

Students choose ONE major specialization and ONE minor specialization.
Final specialization selected in Semester 3 based on academic performance and industry demand.

Eligibility:
- Bachelor's degree of minimum 3 years duration from a recognized university
- Minimum 50% aggregate marks (45% for SC/ST/Category I Karnataka candidates)
- Candidates with single sitting degree NOT eligible

Entrance Exams Accepted:
- CAT: 65 percentile or above
- MAT / XAT / CMAT / ATMA: 70 percentile or above
- PGCET (Karnataka): Valid state-level score accepted
- Management Quota: Direct admission based on academic merit (limited seats)

Application Process:
1. Apply online at apply.theaims.ac.in
2. Submit entrance test scorecard and academic documents
3. Shortlisting based on percentile/score
4. Personal Interview (PI) at AIMS campus
5. Merit list announcement and offer letter
6. Fee payment and seat confirmation
        """,
        url="https://www.theaims.ac.in/business-school/master-business-administration",
        category="mba",
    ),

    _chunk(
        title="MBA Curriculum and Academic Structure",
        content="""
MBA Academic Structure at AIMS Institutes:

Semester 1 — Foundation:
Management Concepts & Organisational Behaviour, Managerial Economics,
Financial Accounting & Analysis, Marketing Management,
Business Statistics & Research Methods, Business Communication

Semester 2 — Core:
Strategic Management, Financial Management, Human Resource Management,
Operations Management, Business Law & Corporate Governance,
Entrepreneurship & Innovation

Semester 3 — Specialization Major + Minor:
Domain electives based on chosen specialization (Marketing / Finance / HR /
Business Analytics / Healthcare / BFSI / Logistics / Operations / International Business)
Industry internship (live project with corporate partner)

Semester 4 — Capstone:
Advanced specialization electives, dissertation/project report,
Industry immersion, Pre-placement activities

Pedagogy:
- Case study method (Harvard Business School style)
- Simulations, role plays, and live business problems
- Industry expert guest lectures every semester
- Mandatory summer internship (8–10 weeks, Semester 2–3 gap)
- Annual management fest and inter-college competitions
        """,
        url="https://www.theaims.ac.in/business-school/master-business-administration",
        category="mba",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# BBA PROGRAM
# ─────────────────────────────────────────────────────────────────────────────

BBA = [
    _chunk(
        title="BBA Program — Specializations and Eligibility",
        content="""
BBA (Bachelor of Business Administration) at AIMS Institutes

Duration: 3 years (6 semesters)
Affiliation: Bangalore City University
Approval: AICTE Approved

Specializations:
1. Marketing
2. Finance
3. Human Resource Management (HRM)
4. Aviation Management (specialized BBA track)

BBA in Aviation Management:
A dedicated 3-year BBA program for students pursuing careers in aviation,
airport operations, airline management, and travel & tourism.

Eligibility:
- 10+2 (PUC / Class 12) from any recognized board
- Any stream: Science, Commerce, or Arts
- Minimum 45% aggregate marks (40% for reserved categories)
- No entrance exam mandatory; admission based on merit and PI

Admission Process:
1. Apply online or visit the campus
2. Merit-based shortlisting
3. Personal Interview (optional)
4. Documents verification and fee payment

Career Outcomes:
BBA graduates placed at Deloitte, EY, Accenture, Infosys, Amazon,
HDFC Bank, ICICI Bank, Axis Bank, and leading MNCs in Bangalore.
Many BBA graduates pursue MBA at AIMS or top B-schools.
        """,
        url="https://www.theaims.ac.in/business-school/bachelor-business-administration",
        category="bba",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# OTHER PROGRAMS
# ─────────────────────────────────────────────────────────────────────────────

OTHER_PROGRAMS = [
    _chunk(
        title="All Programs Offered at AIMS Institutes",
        content="""
Programs Offered at AIMS Institutes (Complete List):

Postgraduate Programs:
- MBA (Master of Business Administration) — 2 years
- MCA (Master of Computer Applications) — 2 years

Undergraduate Programs:
- BBA (Bachelor of Business Administration) — 3 years
- BBA in Aviation Management — 3 years
- BCA (Bachelor of Computer Applications) — 3 years
- B.Com (Bachelor of Commerce) — 3 years

Doctoral Program:
- PhD in Management / Commerce — 3 to 5 years (part-time and full-time)

All programs are:
- AICTE Approved
- Affiliated to Bangalore City University (formerly Bangalore University)
- NAAC 'A' Grade accredited (institute level)
- MBA additionally holds IACBE international accreditation

AIMS is one of the few institutions in Karnataka with IACBE accreditation,
placing it alongside global business schools in academic standards.
        """,
        url="https://www.theaims.ac.in/business-school",
        category="programs",
    ),

    _chunk(
        title="MCA and BCA Programs at AIMS Institutes",
        content="""
MCA (Master of Computer Applications) at AIMS Institutes:
- Duration: 2 years (4 semesters)
- Eligibility: BCA / B.Sc (CS/IT/Maths) / BBA with Maths / B.Com with Maths
- Minimum 50% marks in bachelor's degree
- Affiliation: Bangalore City University, AICTE Approved

MCA Curriculum highlights: Python, Java, Data Structures, DBMS, Cloud Computing,
Machine Learning, Web Development, Cyber Security, Software Engineering

BCA (Bachelor of Computer Applications) at AIMS Institutes:
- Duration: 3 years (6 semesters)
- Eligibility: 10+2 with Mathematics or Computer Science
- Minimum 45% aggregate marks
- Strong focus on programming, web, mobile app development

B.Com (Bachelor of Commerce) at AIMS Institutes:
- Duration: 3 years (6 semesters)
- Eligibility: 10+2 in Commerce (Science/Arts also considered)
- Covers Accounting, Taxation, Business Law, Economics, Finance
        """,
        url="https://www.theaims.ac.in/business-school",
        category="programs",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# ADMISSIONS
# ─────────────────────────────────────────────────────────────────────────────

ADMISSIONS = [
    _chunk(
        title="AIMS Admissions — Eligibility, Entrance Exams, and Process",
        content="""
AIMS Institutes Admissions Guide:

MBA Eligibility:
- 3-year bachelor's degree from recognized university
- Minimum 50% aggregate (45% for SC/ST/Category I)
- Valid CAT score (65 percentile+) or MAT/XAT/CMAT/ATMA (70 percentile+)
- PGCET Karnataka score also accepted
- Candidates with single sitting degree NOT eligible

BBA / BCA / B.Com Eligibility:
- 10+2 from any recognized board, any stream
- Minimum 45% aggregate (40% for reserved categories)
- No mandatory entrance exam; admission by merit and PI

Application Steps:
Step 1: Visit apply.theaims.ac.in and fill online form
Step 2: Upload documents — mark sheets (10th, 12th, UG), entrance scorecard,
         ID proof (Aadhar), community certificate if applicable
Step 3: Shortlisting notification (within 5–7 working days)
Step 4: Personal Interview at AIMS campus (Bangalore)
Step 5: Merit list and offer letter
Step 6: Fee payment and enrollment confirmation

Important Dates (Approximate, verify with admissions office):
- Application opens: January–February each year
- MBA admission closes: June–July
- UG programs: May–July
- Classes begin: August

Contact:
Email: admissions@theaims.ac.in
Phone: +91-80-40789999
Address: #1, Pipeline Road, Hesaraghatta Main Road, Bangalore – 560090
        """,
        url="https://www.theaims.ac.in/student-information-zone",
        category="admissions",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# CAMPUS & FACILITIES
# ─────────────────────────────────────────────────────────────────────────────

CAMPUS = [
    _chunk(
        title="AIMS Campus Facilities — Hostel, Library, Labs, Sports",
        content="""
AIMS Institutes Campus — Bangalore:

Location: #1, Pipeline Road, Hesaraghatta Main Road, Bangalore – 560090
(Well connected by public transport; approx. 45 min from MG Road)

Academic Facilities:
- Air-conditioned smart classrooms with projectors and audio systems
- Computer labs with 200+ systems, high-speed internet
- Wi-Fi enabled campus (100 Mbps broadband)
- Central Library: 40,000+ books, 100+ national/international journals,
  digital library, DELNET access, e-books and online databases
- Seminar and conference halls (capacity 100–500)
- Open-air amphitheater for cultural events

Hostel Facilities (Separate for Boys and Girls):
- Fully furnished rooms (single, double, triple occupancy)
- 24/7 security with CCTV surveillance and biometric entry
- Wi-Fi in all hostel rooms
- Mess serving vegetarian and non-vegetarian meals (breakfast, lunch, dinner)
- Laundry facility
- Common room with TV and recreation
- Medical room and emergency support

Sports & Recreation:
- Indoor sports: Table tennis, badminton, chess, carrom
- Outdoor: Cricket ground, volleyball court, basketball court
- Annual sports meet and inter-college tournaments

Other:
- ATM on campus
- Cafeteria/canteen
- Medical room with nurse on duty
- Stationary and photocopy shop
- Wheelchair-accessible infrastructure (ramps, lifts)
        """,
        url="https://www.theaims.ac.in/campus-facilities",
        category="campus",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# SCHOLARSHIPS
# ─────────────────────────────────────────────────────────────────────────────

SCHOLARSHIPS = [
    _chunk(
        title="AIMS Scholarships and Fee Concessions",
        content="""
AIMS Institutes Scholarship Programmes:

Merit Scholarships (based on entrance test performance):
- CAT 90 percentile and above: Significant fee waiver (contact admissions)
- CAT 80–89 percentile: Partial fee concession
- MAT/XAT/CMAT 90 percentile+: Merit scholarship (limited seats)

Special Scholarships:
- Sports Scholarship: For students who represented state or national level
- NCC/NSS Scholarship: For students with NCC 'B' or 'C' certificate or NSS active service
- Defence Quota: For children of defence personnel (fee concession)
- Differently-Abled: As per Karnataka government policy

Government Scholarships (apply separately):
- Karnataka Backward Classes Welfare Department scholarships
- SC/ST Post-Matric Scholarship (Karnataka)
- OBC Merit Scholarship
- Minority Welfare Scholarship
- Students can apply via the official Karnataka scholarship portal

Fee Structure:
Exact fee amounts are shared during the admissions process to ensure
up-to-date accuracy. Contact the admissions office for current fee schedule:
Email: admissions@theaims.ac.in | Phone: +91-80-40789999

Note: Fee structure is regulated by Bangalore City University and
Karnataka Government norms. Installment payment options are available.
        """,
        url="https://www.theaims.ac.in/scholarships",
        category="scholarships",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# ACCREDITATIONS & RANKINGS
# ─────────────────────────────────────────────────────────────────────────────

ACCREDITATIONS = [
    _chunk(
        title="AIMS Accreditations, Rankings, and Recognition",
        content="""
AIMS Institutes — Accreditations and Recognition:

Accreditations:
- NAAC: 'A' Grade (National Assessment and Accreditation Council)
- IACBE: Full Accreditation (International Accreditation Council for Business Education)
  → One of only a handful of Indian B-schools with this global recognition
- AICTE: Approved by All India Council for Technical Education
- Bangalore City University: Affiliated (formerly Bangalore University)

Rankings (Approximate, verify for current year):
- Listed in NIRF (National Institutional Ranking Framework) by Ministry of Education
- Ranked among Top B-Schools in Bangalore by multiple private ranking agencies
- Featured in leading education publications for placement performance

About AIMS:
- Established: 1994
- 30+ years of excellence in management education
- Location: Bangalore, the Silicon Valley of India
- Alumni: 10,000+ across India and globally
- Founder: Part of the Acharya Institutes group

Key Differentiators:
1. IACBE international accreditation (rare in India)
2. Industry-integrated curriculum updated annually
3. 300+ corporate recruiters visiting campus
4. Strong alumni network in IT, BFSI, consulting, and manufacturing
5. Bangalore location = direct access to top MNC headquarters
        """,
        url="https://www.theaims.ac.in/naac-accreditation",
        category="accreditations",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# GENERAL / CONTACT
# ─────────────────────────────────────────────────────────────────────────────

GENERAL = [
    _chunk(
        title="AIMS Institutes — About, Contact, and Location",
        content="""
About AIMS Institutes (Acharya Institute of Management Sciences):

AIMS Institutes is a premier business and technology institution in Bangalore,
Karnataka, India. Established in 1994, AIMS has 30+ years of academic excellence.

Vision: To be a globally recognized institution producing ethical, innovative,
and industry-ready leaders.

Mission: To provide quality education through industry-integrated curriculum,
research, and strong corporate partnerships.

Programs Offered: MBA, BBA, BBA Aviation, BCA, MCA, B.Com, PhD

Contact Information:
- Address: #1, Pipeline Road, Hesaraghatta Main Road, Bangalore – 560090
- Phone: +91-80-40789999
- Admissions: admissions@theaims.ac.in
- General: info@theaims.ac.in
- Website: www.theaims.ac.in
- Online Application: apply.theaims.ac.in

How to Reach:
- By Metro: Nearest metro station — Peenya (Green Line), then auto/cab (15 min)
- By Bus: BMTC buses to Hesaraghatta Cross connect directly
- By Car: Pipeline Road off Hesaraghatta Main Road, near Jalahalli

Office Hours:
Monday–Friday: 9:00 AM – 5:00 PM
Saturday: 9:00 AM – 1:00 PM (Admissions office)
        """,
        url="https://www.theaims.ac.in/contact-us",
        category="general",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# FEES (most-searched query — answer what we can, gate exact amounts)
# ─────────────────────────────────────────────────────────────────────────────

FEES = [
    _chunk(
        title="AIMS Fee Structure — MBA, BBA, MCA, BCA Programs",
        content="""
AIMS Institutes Fee Information:

Important Note:
Exact fee amounts vary by batch and are confirmed by the admissions office
to reflect the latest government-approved rates. Contact for current figures:
Email: admissions@theaims.ac.in | Phone: +91-80-40789999

General Fee Guidance (approximate — verify with admissions):
- MBA: Regulated by Bangalore City University fee committee
  Structured as annual installments over 2 years
  Merit scholarship holders receive waiver on a portion of tuition
- BBA / BCA / B.Com: Undergraduate programs follow BCU fee norms
  More affordable than PG programs; installment options available
- MCA: Postgraduate technical program; fees aligned with MBA bracket

What is included in fees:
- Tuition and university exam fees
- Library and digital database access
- Wi-Fi and computer lab usage
- Sports and cultural activity access
- Placement cell support and pre-placement training

Additional charges (optional / separate):
- Hostel: Annual charges for accommodation + mess (separate from tuition)
- Transport: Available on select routes; charges apply
- Study materials: Recommended books purchased separately

Payment Options:
- Installment plan available (semester-wise payments)
- Education loans: Bank tie-ups with SBI, Canara Bank, HDFC Bank, Axis Bank
- Government scholarships deductible from fee if sanctioned
- Online payment via the college portal

For exact current fee structure contact: admissions@theaims.ac.in
        """,
        url="https://www.theaims.ac.in/student-information-zone",
        category="fees",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# FREQUENTLY ASKED QUESTIONS (FAQs)
# ─────────────────────────────────────────────────────────────────────────────

FAQS = [
    _chunk(
        title="AIMS FAQs — Hostel, Entrance Exam, Loan, Scholarship, Lateral Entry",
        content="""
Frequently Asked Questions about AIMS Institutes:

Q: Is hostel compulsory at AIMS?
A: No, hostel is not compulsory. It is optional. AIMS provides separate hostel
   facilities for boys and girls. Most local students commute from home.

Q: Is an entrance exam required for MBA admission?
A: Yes, for the merit quota. CAT (65 percentile+), MAT/XAT/CMAT/ATMA (70 percentile+),
   or PGCET Karnataka score is required. Management quota allows direct
   admission based on academic merit without an entrance exam.

Q: Is an entrance exam required for BBA / BCA / B.Com?
A: No. Admission to UG programs (BBA, BCA, B.Com) is based on 10+2 marks
   and a Personal Interview. No entrance exam is mandatory.

Q: Is education loan available for AIMS programs?
A: Yes. AIMS has tie-ups with SBI, Canara Bank, HDFC Bank, and Axis Bank.
   Students apply for loans with the AIMS admission offer letter.

Q: Are scholarships available at AIMS?
A: Yes. Merit scholarships for high CAT/MAT scores, sports scholarships,
   NCC/NSS, defence quota, and government Karnataka scholarships are all available.

Q: Is lateral entry available at AIMS?
A: Lateral entry into BCA/B.Com 2nd year may be available for diploma holders
   subject to university norms. Contact admissions for current eligibility.

Q: What is the medium of instruction at AIMS?
A: English is the primary medium of instruction for all programs at AIMS.

Q: Can I visit the AIMS campus before applying?
A: Yes. Campus visits are welcome on working days (Mon–Fri, 9 AM – 5 PM).
   Call +91-80-40789999 to schedule a counselling session.

Q: How is the placement record at AIMS?
A: Highest package: ₹27 LPA (overall), ₹16.5 LPA (current batch).
   Placement rate: 84% of eligible students. 300+ recruiters including
   Deloitte, EY, KPMG, Amazon, Accenture, TCS visit campus annually.

Q: Does AIMS have on-campus hostel or off-campus?
A: AIMS has on-campus hostel (separate blocks for boys and girls) with
   24/7 security, CCTV, Wi-Fi, mess facility, and medical support.
        """,
        url="https://www.theaims.ac.in/student-information-zone",
        category="faqs",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# MASTER EXPORT
# ─────────────────────────────────────────────────────────────────────────────

OFFICIAL_KNOWLEDGE_BASE: List[Dict] = (
    PLACEMENTS
    + MBA
    + BBA
    + OTHER_PROGRAMS
    + ADMISSIONS
    + CAMPUS
    + SCHOLARSHIPS
    + ACCREDITATIONS
    + FEES
    + FAQS
    + GENERAL
)


def get_official_chunks() -> List[Dict]:
    """Return all official knowledge chunks, ready for ingestion."""
    return OFFICIAL_KNOWLEDGE_BASE


if __name__ == "__main__":
    chunks = get_official_chunks()
    total_words = sum(len(c["content"].split()) for c in chunks)
    print(f"Official Knowledge Base:")
    print(f"  Total chunks : {len(chunks)}")
    print(f"  Total words  : {total_words:,}")
    print(f"  Avg words/chunk: {total_words // len(chunks)}")
    print()
    for c in chunks:
        words = len(c["content"].split())
        print(f"  [{c['category']:15s}] {words:4d}w  {c['title'][:60]}")
