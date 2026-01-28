from typing import TypedDict, Annotated, List, Optional
import operator

class OnboardingState(TypedDict):
    # 1. Employee Context 
    user_info: dict  
    
    # 2. Sentiment & AI Feature Data
    audio_path: Optional[str]
    transcript: Optional[str]
    sentiment_score: Optional[float] 
    sentiment_label: Optional[str]  # "High Confidence" / "Low Confidence"
    personality_summary: Optional[str] 
    final_assigned_email: Optional[str]
    final_remark: Optional[str]
    
    # 3. Process & Quiz Tracking
    current_node: str
    quiz_score: int
    quiz_attempts: int 
    hr_assessment: Optional[str] # "POSITIVE", "NEUTRAL", "NEGATIVE"
    final_remark: Optional[str]   # <--- NEW: To store the dynamic HR comment
    
    # 4. Email Identity
    final_assigned_email: Optional[str] # <--- NEW: To trigger the Admin Dashboard in UI
    email_prefix: Optional[str]
    
    # 5. The Log History
    orchestrator_history: Annotated[List[str], operator.add]