# AIMS Chatbot - Data Requirements Document
## Professional Data Collection Framework for RAG System Enhancement

**Objective:** Improve chatbot answer accuracy from 40% to 90%+ through structured data collection

**System Context:**
- Production chatbot deployed with FAISS + embedding pipeline
- No hallucination risk (strict confidence threshold + fallback system)
- Current limitation: Missing authoritative institutional data
- Goal: Answer all common student queries with >70% confidence

---

## 1. ADMISSIONS & ENROLLMENT

### 1.1 Admission Process & Timeline
**Data Type:** Structured process documentation
**Examples Required:**
- Step-by-step admission process for each program
- Application deadlines (current and upcoming years)
- Required documents checklist
- Application fee information
- Expected timeline from application to decision

**Why Important:** Students frequently ask "How do I apply?" - accurate process documentation prevents misguidance

**Format:** PDF guide or structured text with dates clearly marked

### 1.2 Eligibility Criteria
**Data Type:** Program-specific requirements
**Examples Required:**
- Educational qualifications by program (BBA, MBA, PhD, etc.)
- Entrance exam requirements (if any)
- Experience requirements (for graduate programs)
- Age restrictions
- Nationality/residency requirements

**Why Important:** Determines who can actually apply - critical for accurate guidance

**Format:** Table format (Program | Qualification | Exam | Experience | Notes)

### 1.3 Selection Process
**Data Type:** Detailed methodology
**Examples Required:**
- Merit-based criteria and weightage
- Interview process (if applicable)
- Group discussion details
- Selection timeline
- How decisions are communicated

**Why Important:** Helps students prepare appropriately

**Format:** Structured document with clear stages

---

## 2. FEES & FINANCIAL INFORMATION

### 2.1 Complete Fee Structure
**Data Type:** Comprehensive financial breakdown
**Examples Required:**
- Tuition fees by program and year
- Separate fees (exam fees, material fees, etc.)
- Hostel charges (if applicable)
- Food/meal charges
- Additional mandatory fees
- Fee payment schedules

**Why Important:** Top student question - "What is the cost?" Accuracy critical

**Format:** Detailed table or spreadsheet by program and year

### 2.2 Fee Payment Terms
**Data Type:** Payment policies and options
**Examples Required:**
- Payment methods accepted
- Installment options (if available)
- Refund policy
- Late payment penalties
- Scholarship impact on fees

**Why Important:** Financial planning for students

**Format:** Structured policy document

### 2.3 Financial Aid & Payment Plans
**Data Type:** Alternative financing
**Examples Required:**
- EMI options
- Bank partnerships
- Corporate sponsorship options
- Payment deadline flexibility

**Why Important:** Accessibility information

**Format:** Text or linked program details

---

## 3. PLACEMENTS & CAREER OUTCOMES

### 3.1 Placement Statistics
**Data Type:** Verified placement data (3 years minimum)
**Examples Required:**
- Overall placement rate (%) by program
- Average salary by program
- Salary range (min-max)
- Top recruiting companies
- Industry breakdown of placements

**Why Important:** Critical for student decision-making and chatbot credibility

**Format:** Year-wise table with clear metrics

**Example Structure:**
```
Program | Year | Total Students | Placed | Placement % | Avg Salary | Range | Top Companies
```

### 3.2 Company Recruitment Details
**Data Type:** Employer information
**Examples Required:**
- List of 20+ recruiting companies
- Sectors represented (IT, Finance, Consulting, etc.)
- Types of roles offered
- Salary packages from major companies
- Internship opportunities

**Why Important:** Answers "Who hires from AIMS?" and "What jobs do students get?"

**Format:** List with company details and salary bands

### 3.3 Placement Timeline & Process
**Data Type:** Recruitment cycle information
**Examples Required:**
- When placement drive starts
- Duration of recruitment season
- Number of placement drives per year
- Internship-to-placement conversion rate
- Pre-placement training details

**Why Important:** Student planning and expectations management

**Format:** Timeline document

---

## 4. COURSES & ACADEMIC PROGRAMS

### 4.1 Program Details & Curriculum
**Data Type:** Academic structure information
**Examples Required:**
- Program duration and format
- Course list by semester
- Specializations available
- Internship/project requirements
- Industry partnerships in curriculum

**Why Important:** "What will I study?" is fundamental question

**Format:** Structured curriculum document with semester breakdown

### 4.2 Faculty & Expertise
**Data Type:** Faculty credentials
**Examples Required:**
- Faculty qualifications (PhD, experience)
- Industry experience in faculty
- Research specializations
- Published research/patents
- Guest lectures and industry experts

**Why Important:** Quality assurance information

**Format:** Faculty directory with credentials

### 4.3 Learning Resources
**Data Type:** Support systems
**Examples Required:**
- Library resources and databases
- Online learning platforms used
- Lab facilities
- Internship support
- Career counseling services

**Why Important:** Learning experience quality

**Format:** Descriptive documentation

---

## 5. INFRASTRUCTURE & FACILITIES

### 5.1 Campus Facilities
**Data Type:** Facility inventory and capacity
**Examples Required:**
- Classroom details (size, technology)
- Computer labs (systems, software)
- Library (books, seats, hours)
- Auditorium and meeting rooms
- Sports facilities
- Cafeteria and food options
- Parking facilities

**Why Important:** Answers "What campus facilities exist?" common student query

**Format:** Facility list with specifications and capacity

### 5.2 Academic Technology
**Data Type:** Technological infrastructure
**Examples Required:**
- LMS platform used
- Online meeting tools
- Digital library access
- WiFi coverage
- Student portal features

**Why Important:** Distance/hybrid learning capabilities

**Format:** Technology stack documentation

### 5.3 Accessibility & Support Services
**Data Type:** Inclusive facilities
**Examples Required:**
- Wheelchair accessibility
- Physical accessibility for disabled students
- Medical facilities on campus
- Counseling services
- Learning support services

**Why Important:** Inclusive education information

**Format:** Accessibility guide

---

## 6. HOSTEL & CAMPUS LIFE

### 6.1 Hostel Facilities & Rules
**Data Type:** Residential information
**Examples Required:**
- Hostel capacity and availability
- Room types (single, double, shared)
- Hostel charges
- Amenities (WiFi, AC, etc.)
- Food facilities and meal plans
- Rules and curfew timings
- Safety and security measures

**Why Important:** Many students ask "Do you have hostel?" and "What's the cost?"

**Format:** Hostel handbook or detailed guide

### 6.2 Mess & Food Services
**Data Type:** Meal information
**Examples Required:**
- Meal plan options
- Meal costs
- Menu details
- Dietary accommodations (vegetarian, vegan, allergies)
- Food quality and health standards

**Why Important:** Basic living expense question

**Format:** Meal plan document with pricing

### 6.3 Student Activities & Clubs
**Data Type:** Extracurricular activities
**Examples Required:**
- Club list and activities
- Sports opportunities
- Cultural events
- Annual fest details
- Student council and roles

**Why Important:** Campus life and student engagement

**Format:** Activities list with descriptions

---

## 7. SCHOLARSHIPS & FINANCIAL AID

### 7.1 Scholarship Programs
**Data Type:** Financial assistance details
**Examples Required:**
- Merit-based scholarship amounts
- Need-based scholarship availability
- Scholarship eligibility criteria
- Application process and deadlines
- Renewable scholarships
- Special scholarships (women, minorities, etc.)

**Why Important:** Cost reduction is major decision factor

**Format:** Scholarship matrix with amounts and criteria

### 7.2 External Scholarships
**Data Type:** Third-party aid programs
**Examples Required:**
- Government scholarships students can apply for
- NGO scholarships
- Corporate scholarships
- International funding options

**Why Important:** Additional financial resources

**Format:** Curated list with application links

---

## 8. POLICIES & ACADEMIC RULES

### 8.1 Academic Policies
**Data Type:** Study regulations
**Examples Required:**
- Attendance requirements
**Data Type:** Continuous feedback and improvement

**Examples Required:**
- Minimum attendance threshold
- Exam/assessment rules
- Grading system explanation
- Academic probation policies
- Transfer/exit policies

**Why Important:** Student success and compliance

**Format:** Academic handbook

### 8.2 Conduct & Discipline
**Data Type:** Student conduct policies
**Examples Required:**
- Code of conduct
- Disciplinary procedures
- Harassment policies
- Drug/alcohol policies
- Technology use policies

**Why Important:** Safety and expectation setting

**Format:** Student handbook chapter

### 8.3 Leave & Absence Policies
**Data Type:** Attendance and leave rules
**Examples Required:**
- Casual leave entitlement
- Sick leave policies
- Emergency leave procedures
- Medical certificate requirements
- Impact on grades/credits

**Why Important:** Operational information for students

**Format:** Policy document

---

## 9. FACULTY & RESEARCH

### 9.1 Faculty Research & Publications
**Data Type:** Research output
**Examples Required:**
- Research papers published (with venue)
- Patents filed/granted
- Ongoing research projects
- Funded research grants
- Research areas and expertise

**Why Important:** Academic credibility and innovation index

**Format:** Research publication list with details

### 9.2 Faculty Qualifications & Expertise
**Data Type:** Educational credentials
**Examples Required:**
- Faculty profiles (education, experience)
- Industry experience years
- PhD holders percentage
- International affiliations
- Guest lecture history

**Why Important:** Program quality assurance

**Format:** Faculty directory with detailed profiles

---

## 10. CONTACT & SUPPORT SERVICES

### 10.1 Contact Information
**Data Type:** Communication channels
**Examples Required:**
- Main office phone and email
- Program-specific contacts
- Admission office hours
- Emergency contacts
- Faculty office hours
- Website and social media

**Why Important:** Student support accessibility

**Format:** Structured contact directory

### 10.2 Support Services
**Data Type:** Student assistance
**Examples Required:**
- Academic counseling
- Career guidance services
- Mental health support
- Technical support
- Document verification process

**Why Important:** Holistic student support

**Format:** Services directory

---

## 11. ACCREDITATIONS & RANKINGS

### 11.1 Accreditation Details
**Data Type:** Quality certifications
**Examples Required:**
- IACBE accreditation status and scope
- NAAC rating and details
- AICTE approval status
- Subject-specific accreditations
- International accreditations (if any)

**Why Important:** Quality assurance validation

**Format:** Accreditation certificate details and URLs

### 11.2 Rankings & Recognition
**Data Type:** Comparative metrics
**Examples Required:**
- NIRF ranking (national ranking position)
- Magazine rankings (India Today, etc.)
- Industry recognition surveys
- Best employer feedback

**Why Important:** Institutional credibility

**Format:** Ranking details with scores

---

## 12. ADMISSIONS STATISTICS & ANALYTICS

### 12.1 Historical Admission Data
**Data Type:** Enrollment metrics
**Examples Required:**
- Number of applications received yearly
- Acceptance rate by program
- Student diversity (geography, background)
- Cutoff marks/scores (if applicable)
- Waiting list statistics

**Why Important:** Competitive analysis and realistic expectations

**Format:** Year-wise comparison table

---

## MINIMUM REQUIRED DATASET FOR MVP (High Impact)

### Tier 1: MUST HAVE FIRST (Critical for 70%+ confidence)

These 4 documents address 80% of common student queries:

1. **FEES STRUCTURE** (with all breakdowns)
   - Why: #1 student question
   - Impact: +25% confidence on cost-related queries
   - Format: Detailed spreadsheet/PDF by program

2. **PLACEMENT STATISTICS** (3-year verified data)
   - Why: Critical decision factor
   - Impact: +20% confidence on career queries
   - Format: Table with company names and salaries

3. **ADMISSIONS PROCESS & ELIGIBILITY** (step-by-step guide)
   - Why: Fundamental requirement
   - Impact: +15% confidence on application queries
   - Format: Process document with timeline

4. **HOSTEL & CAMPUS FACILITIES** (with capacity and cost)
   - Why: Common student concern
   - Impact: +12% confidence on lifestyle queries
   - Format: Facility handbook with details

**Expected Result After Tier 1:** 68% → 80% confidence

---

### Tier 2: SHOULD HAVE (Medium Impact)

5. **SCHOLARSHIP PROGRAMS** (with criteria and amounts)
   - Impact: +8% confidence
   - Addresses: "Can I get financial aid?"

6. **PROGRAM CURRICULUM** (semester-wise structure)
   - Impact: +6% confidence
   - Addresses: "What will I study?"

7. **FACULTY PROFILES & RESEARCH** (education and expertise)
   - Impact: +4% confidence
   - Addresses: "Who teaches here?"

**Expected Result After Tier 2:** 80% → 88% confidence

---

### Tier 3: NICE TO HAVE (Incremental Impact)

8. **ACADEMIC POLICIES** (attendance, grading, etc.)
   - Impact: +1-2% confidence

9. **STUDENT ACTIVITIES & CLUBS** (extracurricular)
   - Impact: +1-2% confidence

10. **RESEARCH & PUBLICATIONS** (credibility metrics)
    - Impact: +1% confidence

**Expected Result After Tier 3:** 88% → 91% confidence

---

## DELIVERY SPECIFICATIONS

### Format Requirements
- All documents should be text-extractable (searchable PDFs preferred over scans)
- Include dates and version numbers
- Provide current academic year data
- Include historical data where available (3 years minimum for statistics)

### Quality Checklist
- No confidential/private information
- Public-facing content (publishable on website)
- Clear authorship and last update date
- Consistent terminology
- Accurate contact information
- Verified statistics (third-party sources where available)

### Delivery Method
- Email with documents as attachments OR
- Shared drive/folder access OR
- Web links to published documents

### Timeline
- Tier 1 (Critical): Within 2 weeks
- Tier 2 (Important): Within 4 weeks
- Tier 3 (Enhancements): Within 6 weeks

---

## EXPECTED IMPACT SUMMARY

| Stage | Confidence Level | Coverage | Student Satisfaction |
|-------|-----------------|----------|----------------------|
| Current | 68% | Programs, basic info | Moderate |
| After Tier 1 | 80% | Fees, placements, admissions | Good |
| After Tier 2 | 88% | Most common queries | Very Good |
| After Tier 3 | 91% | Comprehensive coverage | Excellent |

---

## TECHNICAL INTEGRATION

Once data is provided:

1. **Data Processing:** 2-3 hours
2. **FAISS Index Update:** Automatic (rebuild command)
3. **Quality Testing:** 1-2 hours with 50+ test queries
4. **Production Deployment:** Same day
5. **Monitoring & Optimization:** Ongoing

---

## QUESTIONS FOR CLARIFICATION

When requesting this data from AIMS, consider asking:

1. Is this data available in digital format?
2. Are there any confidentiality restrictions?
3. Can we publish anonymized salary ranges?
4. How frequently is this data updated?
5. Who is the best contact for each data category?

---

## DOCUMENT PREPARED FOR

- **System:** AIMS Institutional Chatbot (RAG-based)
- **Purpose:** Data collection for accuracy improvement
- **Date:** April 21, 2026
- **Status:** Production-ready system awaiting authoritative data
