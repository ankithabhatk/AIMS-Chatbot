"""
Soft Fallback Messages - Guide users instead of blocking them

Instead of "I don't understand", provide helpful guidance that keeps
the conversation alive and shows what the system CAN do.
"""

def get_soft_fallback_message(query: str = None, context: dict = None) -> str:
    """
    Return a helpful fallback message that guides users.
    
    This is used when the system can't understand a query, but instead of
    blocking the user, we show them what we CAN help with.
    """
    
    # Default soft fallback - always helpful
    return """I'm not sure I understood that correctly. 

I can help you with:
• **Course Information** - Details about BCA, MBA, MCA, B.Com, BBA, BHM
• **Fees & Costs** - Fee structure and payment options
• **Admission Process** - How to apply and eligibility criteria
• **Campus & Facilities** - Hostel, labs, library, sports
• **Placements** - Career outcomes and job opportunities

What would you like to know? 😊"""


def get_soft_fallback_with_context(detected_intents: list = None, query: str = None) -> str:
    """
    Return a soft fallback that's aware of what we DID detect.
    
    If we partially understood, show related topics instead of generic fallback.
    """
    
    if detected_intents and len(detected_intents) > 0:
        # We detected something, but maybe not what user wanted
        intent = detected_intents[0]
        
        if intent == "courses":
            return f"""I think you're asking about courses. 

I can tell you about:
• Available programs (BCA, MBA, MCA, etc.)
• Course duration and structure
• Specializations and electives
• Career paths after each course

What specific program interests you? 📚"""
        
        elif intent == "fees":
            return f"""I think you're asking about fees.

I can help with:
• Annual fee structure
• Payment options and installments
• Scholarships and financial aid
• Fee breakdown by course

Which program's fees would you like to know? 💰"""
        
        elif intent == "admission":
            return f"""I think you're asking about admission.

I can help with:
• Eligibility criteria
• Application process
• Required documents
• Important dates and deadlines

What would you like to know about admission? 📝"""
    
    # Default fallback if no intent detected
    return get_soft_fallback_message(query)


def get_quick_help_suggestions() -> list:
    """
    Return quick help suggestions for the UI.
    
    These can be shown as buttons or quick replies.
    """
    return [
        {"text": "📚 Tell me about courses", "action": "courses"},
        {"text": "💰 What are the fees?", "action": "fees"},
        {"text": "📝 How to apply?", "action": "admission"},
        {"text": "🏠 Campus facilities", "action": "campus"},
    ]
