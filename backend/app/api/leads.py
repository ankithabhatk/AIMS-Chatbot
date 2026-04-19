"""Lead Capture Endpoint - Supabase Integration"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
import logging
import re

from app.services.database.supabase_client import get_lead_store, get_chat_log_store

router = APIRouter(prefix="/api/v1", tags=["leads"])
logger = logging.getLogger(__name__)


class LeadData(BaseModel):
    """Lead capture request"""
    session_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    interested_programs: List[str] = []
    qualification: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    consent_marketing: bool = False
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            # Remove non-digits
            digits = re.sub(r'\D', '', v)
            if len(digits) < 10:
                raise ValueError('Phone must have at least 10 digits')
        return v


class LeadResponse(BaseModel):
    """Lead capture response"""
    status: str
    lead_id: Optional[str] = None
    message: str
    lead_score: Optional[float] = None


async def calculate_lead_score(
    session_id: str,
    qualification: Optional[str],
    conversation_quality: Optional[float] = None
) -> float:
    """
    Calculate lead score based on:
    - Chat engagement (number of questions)
    - Qualification level
    - Intent signals
    """
    score = 0.5  # Base score
    
    try:
        # Get chat history for this session
        log_store = get_chat_log_store()
        logs = await log_store.get_chat_logs(session_id=session_id)
        
        # Score based on engagement
        if logs:
            query_count = len(logs)
            if query_count >= 5:
                score += 0.2
            elif query_count >= 3:
                score += 0.1
            
            # Score based on confidence
            avg_confidence = sum(log.get("confidence_score", 0) for log in logs) / len(logs)
            score += (avg_confidence * 0.1)
        
        # Score based on qualification
        if qualification and qualification.lower() in ['12th pass', '12th pass', 'graduated']:
            score += 0.1
        
        # Cap score at 1.0
        return min(score, 1.0)
    
    except Exception as e:
        logger.error(f"Failed to calculate lead score: {e}")
        return score


@router.post("/leads", response_model=LeadResponse)
async def capture_lead(lead: LeadData):
    """
    Capture student information and store in Supabase
    
    Flow:
    1. Validate input
    2. Check for duplicates (deduplication)
    3. Get chat transcript for context
    4. Calculate lead score
    5. Insert into Supabase
    6. Return response with lead ID
    """
    try:
        full_name = f"{lead.first_name} {lead.last_name}".strip()
        logger.info(f"Lead capture: {full_name} ({lead.email})")
        
        # 1. Validate input (already done by Pydantic)
        if not lead.email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # 2. Check for duplicates (deduplication)
        lead_store = get_lead_store()
        existing_leads = await lead_store.get_leads_by_email(lead.email)
        
        if existing_leads:
            logger.info(f"Lead already exists: {lead.email}")
            existing = existing_leads[0]
            
            # Update last contact
            await lead_store.update_lead(
                existing["id"],
                {"last_contact": None}  # Will use DB default
            )
            
            return LeadResponse(
                status="existing",
                lead_id=existing["id"],
                message=f"Lead already exists for {lead.email}",
                lead_score=existing.get("lead_score")
            )
        
        # 3. Calculate lead score
        interest_str = ", ".join(lead.interested_programs) if lead.interested_programs else None
        lead_score = await calculate_lead_score(
            session_id=lead.session_id,
            qualification=lead.qualification
        )
        
        # 4. Insert into Supabase
        new_lead = await lead_store.create_lead(
            name=full_name,
            email=lead.email,
            phone=lead.phone,
            interest=interest_str,
            source="chatbot"
        )
        
        # Update with calculated score
        await lead_store.update_lead(
            new_lead["id"],
            {
                "lead_score": lead_score,
                "status": "new"
                # TODO: Add qualification, state, city fields to schema
            }
        )
        
        logger.info(f"Lead created: {new_lead['id']} with score {lead_score:.2f}")
        
        return LeadResponse(
            status="created",
            lead_id=new_lead["id"],
            message=f"Lead captured successfully for {full_name}",
            lead_score=lead_score
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lead capture error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to capture lead: {str(e)}"
        )


@router.get("/leads/{lead_id}", response_model=dict)
async def get_lead(lead_id: str):
    """Retrieve lead information"""
    try:
        lead_store = get_lead_store()
        lead = await lead_store.get_lead(lead_id)
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return lead
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve lead")


@router.put("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: str, updates: dict):
    """Update lead information"""
    try:
        lead_store = get_lead_store()
        updated_lead = await lead_store.update_lead(lead_id, updates)
        
        if not updated_lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return LeadResponse(
            status="updated",
            lead_id=lead_id,
            message="Lead updated successfully",
            lead_score=updated_lead.get("lead_score")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update lead: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update lead")
        # - Deduplication check
        # - Calculate lead score
        # - Save to database
        # - Queue CRM sync
        
        return LeadResponse(
            status="pending",
            lead_id=None,
            message="Lead capture integration in progress"
        )
    
    except Exception as e:
        logger.error(f"Lead capture error: {str(e)}")
        raise HTTPException(status_code=500, detail="Lead capture failed")
