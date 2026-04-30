"""
100 Real Student Questions - Comprehensive Test Dataset

Categories:
1. Admission Process & Requirements (20)
2. Fees & Financial Aid (15)
3. Courses & Programs (15)
4. Placements & Career (15)
5. Campus & Facilities (10)
6. Hostel & Accommodation (10)
7. Exploratory/Counselor Queries (15)
"""

STUDENT_QUESTIONS = {
    "admission_process": [
        # Application basics
        "What is the university's current acceptance rate?",
        "Are there any application fee waivers available?",
        "What are the key deadlines for regular and early decision applications?",
        "Does the college require specific standardized tests (SAT, ACT, JEE, NEET)?",
        "What are the minimum required scores for my program of interest?",
        
        # Requirements
        "Are there supplemental requirements like a portfolio, interview, or audition?",
        "What key aspects do you look for in a successful application?",
        "How does the university view extracurricular activities in the selection process?",
        "Is there an advantage to submitting an application early?",
        "Can I apply for a major and later change it if I change my mind?",
        
        # Documents & eligibility
        "What documents are required for admission?",
        "What is the eligibility criteria for MBA?",
        "Do I need entrance exam scores for BCA?",
        "Can I get admission with 45% in 12th?",
        "Is there direct admission or entrance test?",
        
        # Process details
        "How long does the admission process take?",
        "When do admissions open for 2024?",
        "Is there a personal interview round?",
        "Can I apply online or do I need to visit campus?",
        "What happens after I submit my application?",
    ],
    
    "fees_financial": [
        # Fee structure
        "What are the fees for BCA?",
        "How much does MBA cost per year?",
        "Are there any hidden charges apart from tuition?",
        "Can I pay fees in installments?",
        "What is included in the fee structure?",
        
        # Scholarships & aid
        "Are scholarships available for merit students?",
        "What is the scholarship criteria?",
        "Is there financial aid for economically weaker sections?",
        "Do you offer education loans assistance?",
        "Are there any fee concessions for SC/ST students?",
        
        # Comparisons
        "How do your fees compare to other colleges?",
        "Is the fee worth the placement opportunities?",
        "What is the total cost including hostel?",
        "Are there any additional charges for labs or library?",
        "Do international students pay different fees?",
    ],
    
    "courses_programs": [
        # Course offerings
        "What courses are offered at AIMS?",
        "Tell me about the BCA program",
        "What specializations are available in MBA?",
        "Is MCA available at your college?",
        "Do you offer part-time or distance learning programs?",
        
        # Course details
        "What is the duration of BBA?",
        "What subjects are taught in BCA?",
        "Is the curriculum industry-relevant?",
        "Are there any practical training or internships?",
        "What is the difference between BBA and MBA?",
        
        # Comparisons
        "Should I choose BCA or B.Sc Computer Science?",
        "Which is better - BBA or B.Com?",
        "What are the career options after MCA?",
        "Is MBA worth it after BBA?",
        "Can I do MBA after B.Com?",
    ],
    
    "placements_career": [
        # Placement stats
        "What is the placement record?",
        "What is the average package offered?",
        "What is the highest package in recent years?",
        "What percentage of students get placed?",
        "Which companies come for campus recruitment?",
        
        # Career support
        "Is there a dedicated placement cell?",
        "Do you provide internship opportunities?",
        "What kind of career counseling is available?",
        "Are there industry tie-ups for placements?",
        "Do you help with resume building and interview prep?",
        
        # Specific queries
        "What are the placement opportunities for BCA students?",
        "Which companies hire MBA graduates from AIMS?",
        "Is there placement assistance for all courses?",
        "What roles do students typically get?",
        "Are there opportunities for higher studies abroad?",
    ],
    
    "campus_facilities": [
        # Infrastructure
        "What facilities are available on campus?",
        "Is there a library with digital resources?",
        "Are classrooms air-conditioned?",
        "Is Wi-Fi available throughout campus?",
        "What sports facilities do you have?",
        
        # Campus life
        "What is campus life like at AIMS?",
        "Are there student clubs and societies?",
        "Do you organize cultural events and fests?",
        "Is there a cafeteria or food court?",
        "How is the overall campus environment?",
    ],
    
    "hostel_accommodation": [
        # Hostel basics
        "Is hostel facility available?",
        "What are the hostel fees?",
        "Are hostels separate for boys and girls?",
        "What type of rooms are available - single, double, triple?",
        "Is hostel accommodation mandatory for first year?",
        
        # Hostel facilities
        "What facilities are provided in the hostel?",
        "Is the hostel food good?",
        "Is there 24/7 security in hostels?",
        "Are there laundry facilities?",
        "Can parents visit the hostel?",
    ],
    
    "exploratory_counselor": [
        # Career confusion
        "I like coding, what should I choose?",
        "I'm interested in business, which course is best?",
        "I'm not sure what to study, can you help?",
        "What should I do after 12th?",
        "I'm confused between BCA and MCA",
        
        # Vague queries
        "Tell me everything about your college",
        "Is AIMS a good college?",
        "Why should I join AIMS?",
        "What makes AIMS different from other colleges?",
        "I want to study computers, what options do I have?",
        
        # Preference-based
        "I want a job quickly, which course?",
        "I'm interested in technology and management both",
        "Which course has better scope?",
        "I like both coding and business, what to choose?",
        "What course will give me the highest salary?",
    ],
}

# Flatten all questions into a single list
ALL_QUESTIONS = []
for category, questions in STUDENT_QUESTIONS.items():
    ALL_QUESTIONS.extend(questions)

# Verify we have 100 questions
assert len(ALL_QUESTIONS) == 100, f"Expected 100 questions, got {len(ALL_QUESTIONS)}"

# Category mapping for analysis
CATEGORY_MAP = {}
for category, questions in STUDENT_QUESTIONS.items():
    for question in questions:
        CATEGORY_MAP[question] = category

if __name__ == "__main__":
    print("=" * 80)
    print("100 STUDENT QUESTIONS - DATASET")
    print("=" * 80)
    
    for category, questions in STUDENT_QUESTIONS.items():
        print(f"\n{category.upper().replace('_', ' ')} ({len(questions)} questions)")
        print("-" * 80)
        for i, q in enumerate(questions, 1):
            print(f"{i:2d}. {q}")
    
    print("\n" + "=" * 80)
    print(f"TOTAL: {len(ALL_QUESTIONS)} questions")
    print("=" * 80)
