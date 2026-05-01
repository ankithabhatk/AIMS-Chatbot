# Knowledge Audit Report: AIMS Academic Programs

## 🟢 Summary
The institutional knowledge base for AIMS Institutes is incomplete regarding several key academic programs. While the system correctly identifies core management and commerce courses (MBA, BBA, B.Com, BCA), it lacks structured data for Doctoral (PhD) programs and several specialized Undergraduate and Postgraduate offerings.

## 🚩 Missing / Incomplete Programs

### 1. Doctoral (PhD) Programs
- **Status:** Incomplete
- **Found in Index:** Faculty profiles and testimonials only.
- **Official Data:** AIMS is a recognized research centre affiliated with the University of Mysore (UoM).
- **Programs:** PhD in Management, PhD in Commerce.
- **Gaps:** Admission criteria, coursework structure (1 semester/20 weeks), and research methodology details are missing from retrieval chunks.

### 2. School of Arts & Humanities (Missing)
- **Programs:** BA (Journalism, Psychology, Optional English, Sociology, Economics).
- **Status:** Not found in current index.

### 3. School of Science (Missing)
- **Programs:** B.Sc (Microbiology, Genetics, Biochemistry, Mathematics, Statistics, Computer Science).
- **Status:** Not found in current index.

### 4. Specialized Postgraduate (Incomplete)
- **Programs:** PGDM, MSW (Master of Social Work), MFA (Master of Fine Arts), M.Sc (Mathematics).
- **Status:** Mentions found in 'News' and 'Events' chunks, but no canonical program pages indexed.

### 5. Certifications & Diplomas (Incomplete)
- **Programs:** VET by EHL (Swiss Hospitality), Diploma in Culinary Arts.
- **Status:** Incomplete details on partnership and curriculum.

## 📂 Canonical Inventory (Verified vs Official Site)

| Category | Program | Status in Index |
|----------|---------|-----------------|
| UG | BBA / BBA Aviation | ✅ Complete |
| UG | BCA | ✅ Complete |
| UG | B.Com | ✅ Complete |
| UG | BHM | ✅ Complete |
| UG | BA (Multiple Specializations) | ❌ Missing |
| UG | B.Sc (Multiple Specializations) | ❌ Missing |
| PG | MBA | ✅ Complete |
| PG | MCA | ✅ Complete |
| PG | M.Com | ✅ Complete |
| PG | PGDM | ⚠️ Incomplete |
| PG | MSW | ❌ Missing |
| PG | MFA | ❌ Missing |
| PG | M.Sc | ❌ Missing |
| PhD | Management / Commerce | ⚠️ Testimonials Only |

## 🛠️ Retrieval Audit Details
- **Total Chunks in Index:** 2092
- **PhD Search Similarity:** 0.74 (Testimonials only)
- **BA Search Similarity:** 0.71 (No relevant match)
- **B.Sc Search Similarity:** 0.69 (No relevant match)

## 🎯 Next Steps
1. Scrape canonical URLs for missing programs.
2. Enrich `course_guidance.json` with entry criteria for all discovered programs.
3. Rebuild FAISS index to include high-priority program descriptions.
4. Add regression test for "PhD programs" and "BA Journalism" response accuracy.
