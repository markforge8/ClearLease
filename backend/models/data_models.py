"""
Data Models
===========
Defines data structures and schemas used throughout the application.
These are structural definitions only - no business logic is implemented.
"""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from sqlalchemy import Column, String, Boolean, DateTime


class IngestionInput(BaseModel):
    """
    Input model for the ingestion layer v0.
    Defines the contract for data entering the ingestion service.
    """
    text: str = Field(
        ...,
        description="Raw text content to be ingested"
    )
    source_id: Optional[str] = Field(
        default=None,
        description="Optional unique identifier for this ingestion source"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the source (e.g., filename, source name)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Sample document text content...",
                "source_id": "ingest_001",
                "metadata": {"filename": "document.txt"}
            }
        }


class TextBlock(BaseModel):
    """
    Represents a normalized block of text with basic statistics.
    Used to structure ingested text content.
    """
    block_id: str = Field(
        ...,
        description="Unique identifier for this text block"
    )
    order: int = Field(
        ...,
        description="Order/position of this block within the ingested content"
    )
    normalized_text: str = Field(
        ...,
        description="Normalized text content (whitespace normalized, trimmed)"
    )
    original_length: int = Field(
        ...,
        description="Original text length in characters"
    )
    normalized_length: int = Field(
        ...,
        description="Normalized text length in characters"
    )
    line_count: int = Field(
        ...,
        description="Number of lines in the text"
    )
    word_count: int = Field(
        ...,
        description="Approximate word count (space-separated)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "block_id": "block_0",
                "order": 0,
                "normalized_text": "Sample document text content...",
                "original_length": 150,
                "normalized_length": 145,
                "line_count": 3,
                "word_count": 25
            }
        }


class IngestionResult(BaseModel):
    """
    Output model for the ingestion layer v0.
    Defines the contract for data leaving the ingestion service.
    """
    text_blocks: List[TextBlock] = Field(
        ...,
        description="List of normalized text blocks from the ingested content"
    )
    source_id: Optional[str] = Field(
        default=None,
        description="Source identifier if provided in input"
    )
    ingestion_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when ingestion occurred"
    )
    total_characters: int = Field(
        ...,
        description="Total character count across all text blocks"
    )
    total_words: int = Field(
        ...,
        description="Total word count across all text blocks"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the ingestion process"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text_blocks": [
                    {
                        "block_id": "block_0",
                        "order": 0,
                        "normalized_text": "Sample text...",
                        "original_length": 50,
                        "normalized_length": 48,
                        "line_count": 1,
                        "word_count": 8
                    }
                ],
                "source_id": "ingest_001",
                "ingestion_timestamp": "2024-01-01T12:00:00Z",
                "total_characters": 48,
                "total_words": 8,
                "metadata": {"processing_time_ms": 5}
            }
        }


class ExtractionCandidate(BaseModel):
    """
    Represents a candidate extraction result from the extraction layer v0.
    Contains the extracted content and metadata about the extraction.
    """
    rule_id: str = Field(
        ...,
        description="Identifier of the rule that matched this extraction"
    )
    rule_type: str = Field(
        ...,
        description="Type of rule that matched (keyword, phrase, structural)"
    )
    extracted_text: str = Field(
        ...,
        description="The text that was extracted"
    )
    block_id: str = Field(
        ...,
        description="Identifier of the text block where extraction occurred"
    )
    match_position: int = Field(
        ...,
        description="Character position where the match was found"
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score for the extraction (0.0 to 1.0)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the extraction"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "rule_001",
                "rule_type": "keyword",
                "extracted_text": "lease term",
                "block_id": "block_0",
                "match_position": 45,
                "confidence": 1.0,
                "metadata": {"context": "surrounding text"}
            }
        }


class ExtractedSignal(BaseModel):
    """
    Represents an extracted signal for analysis v0.
    Input format for the analysis layer.
    """
    rule_id: str = Field(
        ...,
        description="Identifier of the rule that matched"
    )
    type: str = Field(
        ...,
        description="Type of signal (keyword, phrase, structural)"
    )
    hit_text: str = Field(
        ...,
        description="The text that was hit/matched"
    )
    block_id: str = Field(
        ...,
        description="Identifier of the text block where signal was found"
    )
    order: int = Field(
        ...,
        description="Order/position of the signal"
    )


class AnalysisInput(BaseModel):
    """
    Input model for the analysis layer v0.
    Defines the contract for data entering the analysis service.
    """
    doc_id: str = Field(
        ...,
        description="Document identifier"
    )
    extracted_signals: List[ExtractedSignal] = Field(
        ...,
        description="List of extracted signals to analyze"
    )


class RiskItem(BaseModel):
    """
    Represents a risk item identified during analysis v0.
    """
    risk_code: str = Field(
        ...,
        description="Unique code identifying the risk"
    )
    severity: str = Field(
        ...,
        description="Severity level (low, medium, high)"
    )
    evidence_rules: List[str] = Field(
        ...,
        description="List of rule_ids that contributed to this risk"
    )
    description: str = Field(
        ...,
        description="Description of the risk"
    )


class AnalysisSummary(BaseModel):
    """
    Summary of the analysis results v0.
    """
    risk_level: str = Field(
        ...,
        description="Overall risk level (low, medium, high)"
    )
    risk_flags: List[str] = Field(
        ...,
        description="List of risk codes that were flagged"
    )
    confidence: float = Field(
        ...,
        description="Confidence score for the analysis (0.0 to 1.0)"
    )


class AnalysisOutput(BaseModel):
    """
    Output model for the analysis layer v0.
    Defines the contract for data leaving the analysis service.
    """
    analysis_summary: AnalysisSummary = Field(
        ...,
        description="Summary of the analysis results"
    )
    risk_items: List[RiskItem] = Field(
        ...,
        description="List of identified risk items"
    )
    risk_fields: List['RiskField'] = Field(
        default_factory=list,
        description="List of structured risk fields (v1)"
    )


class ExplanationBlock(BaseModel):
    """
    Represents a single explanation block for a risk item v0.
    Contains user-facing explanation and action guidance.
    """
    title: str = Field(
        ...,
        description="Title of the explanation block"
    )
    message: str = Field(
        ...,
        description="Explanation message for the user"
    )
    user_action: str = Field(
        ...,
        description="Recommended action for the user"
    )
    severity: str = Field(
        ...,
        description="Severity level (low, medium, high)"
    )
    risk_code: str = Field(
        ...,
        description="Risk code identifier"
    )


class ExplanationOutput(BaseModel):
    """
    Output model for the explanation layer v0.
    Defines the contract for data leaving the explanation service.
    """
    overall_message: str = Field(
        ...,
        description="Overall message based on risk level"
    )
    explanation_blocks: List[ExplanationBlock] = Field(
        ...,
        description="List of explanation blocks, one per risk item"
    )

class RiskAxis(Enum):
    TEMPORAL = "temporal"
    RESPONSIBILITY = "responsibility"
    LIABILITY = "liability"


@dataclass
class RiskField:
    axis: RiskAxis
    affected_party: str        # "tenant" | "landlord"
    intensity: str             # "low" | "medium" | "high"
    compounding: bool
    description: str           # 给 explain 用的人话
    source_blocks: List[str]   # block_id 列表


class RiskFieldExplanation(BaseModel):
    """
    Represents a structural risk field explanation for v1.
    Focuses on "why it's unfair" rather than restating contract terms.
    """
    axis: RiskAxis = Field(
        ...,
        description="Risk axis (temporal, responsibility, liability)"
    )
    intensity: str = Field(
        ...,
        description="Risk intensity (low, medium, high)"
    )
    affected_party: str = Field(
        ...,
        description="Party affected by the risk (tenant, landlord)"
    )
    title: str = Field(
        ...,
        description="Title explaining the unfairness"
    )
    message: str = Field(
        ...,
        description="Explanation message focusing on why it's unfair"
    )
    user_action: str = Field(
        ...,
        description="Recommended action for the user"
    )
    compounding: bool = Field(
        ...,
        description="Whether this risk compounds with others"
    )
    source_blocks: List[str] = Field(
        ...,
        description="Source block IDs where this risk was detected"
    )


class ExplanationOutputV1(BaseModel):
    """
    Output model for the explanation layer v1.
    Defines the contract for structural risk field explanations.
    """
    risk_field_explanations: List[RiskFieldExplanation] = Field(
        ...,
        description="List of structural risk field explanations"
    )
    
@dataclass
class Trap:
    trap_id: str
    trap_type: str  # temporal_lock / asymmetric_power / etc
    related_signals: list
    severity: str   # low / medium / high / critical

@dataclass
class RiskChain:
    chain_id: str
    trap_id: str
    steps: list     # ordered risk steps
    final_outcome: str


# ============================================================================
# Explain v2 Schema Definitions (per explain_v2_contract.md)
# ============================================================================

class TrapType(str, Enum):
    """Trap types as defined in Explain v2 Contract section 3."""
    TEMPORAL_LOCK_IN = "Temporal Lock-in"
    ASYMMETRIC_POWER = "Asymmetric Power"
    EXIT_BARRIER = "Exit Barrier"
    AMBIGUITY = "Ambiguity"


class Strength(str, Enum):
    """Strength levels as defined in Explain v2 Contract section 2.1."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Beneficiary(str, Enum):
    """Beneficiary as defined in Explain v2 Contract section 2.1."""
    PROVIDER = "provider"
    COUNTERPARTY = "counterparty"


class Irreversibility(str, Enum):
    """Irreversibility levels as defined in Explain v2 Contract section 2.1."""
    REVERSIBLE = "reversible"
    PARTIALLY_REVERSIBLE = "partially_reversible"
    IRREVERSIBLE = "irreversible"


class ConfidenceLevel(str, Enum):
    """Confidence levels as defined in Explain v2 Contract section 4.1."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExplainV2Input(BaseModel):
    """
    Input model for Explain v2 as defined in explain_v2_contract.md section 2.
    
    Explain v2 accepts only mechanism-level input.
    If any required field is missing, Explain v2 must refuse to generate output.
    """
    trap_type: TrapType = Field(
        ...,
        description="Trap type: Temporal Lock-in | Asymmetric Power | Exit Barrier | Ambiguity"
    )
    strength: Strength = Field(
        ...,
        description="Strength level: low | medium | high"
    )
    beneficiary: Beneficiary = Field(
        ...,
        description="Beneficiary: provider | counterparty"
    )
    cost_bearer: Literal["user"] = Field(
        ...,
        description="Cost bearer: user"
    )
    irreversibility: Irreversibility = Field(
        ...,
        description="Irreversibility: reversible | partially_reversible | irreversible"
    )
    evidence: Dict[str, Any] = Field(
        ...,
        description="Clause references and detected signals"
    )
    window: Dict[str, Any] = Field(
        ...,
        description="Escape window existence and conditions"
    )


class LockInDynamics(BaseModel):
    """
    Lock-in dynamics field required for Temporal Lock-in trap type only.
    Defined in Explain v2 Contract section 5.1.
    """
    description: str = Field(
        ...,
        description="Time-dependent cost escalation explanation"
    )


class ExplainV2Output(BaseModel):
    """
    Output model for Explain v2 as defined in explain_v2_contract.md section 4.
    
    All required fields must be present.
    """
    mechanism: TrapType = Field(
        ...,
        description="Trap type (carried from input)"
    )
    headline: str = Field(
        ...,
        description="Single-sentence structural conclusion"
    )
    core_logic: str = Field(
        ...,
        description="Explanation of how disadvantage forms"
    )
    power_map: str = Field(
        ...,
        description="Who benefits vs who bears cost"
    )
    irreversibility: Irreversibility = Field(
        ...,
        description="Carried over from Analysis v2 input"
    )
    lock_in_dynamics: Optional[LockInDynamics] = Field(
        default=None,
        description="Required for Temporal Lock-in only (section 5.1)"
    )
    escape_window: Dict[str, Any] = Field(
        ...,
        description="Must exist (even if closed)"
    )
    user_actions: List[str] = Field(
        ...,
        description="Structural options, not legal advice"
    )
    confidence_level: ConfidenceLevel = Field(
        ...,
        description="Confidence level: high | medium | low"
    )


class GatewayOutput(BaseModel):
    """
    Gateway output structure as defined in requirements.
    Gateway only does aggregation, sorting, filtering, and encapsulation.
    """
    overview: Dict[str, Any] = Field(
        ...,
        description="Overview information"
    )
    key_findings: List[Dict[str, Any]] = Field(
        ...,
        description="List of key findings"
    )
    next_actions: List[Dict[str, Any]] = Field(
        ...,
        description="List of next actions"
    )
    details: Dict[str, Any] = Field(
        ...,
        description="Detailed information"
    )


# ============================================================================
# User Profile Models
# ============================================================================

from backend.config.database import Base


class UserProfile(Base):
    """
    User profile model for database storage.
    Corresponds to the user_profiles table.
    """
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    paid = Column(Boolean, default=False, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    gumroad_order_id = Column(String, nullable=True)


class UserProfileResponse(BaseModel):
    """
    User profile response model for API output.
    Used for the /api/me endpoint.
    """
    email: str
    paid: bool

    class Config:
        from_attributes = True


class GumroadWebhookPayload(BaseModel):
    """
    Gumroad webhook payload model.
    Used to parse incoming webhook requests.
    """
    buyer_email: str
    order_id: str
    product_id: Optional[str] = None
    event: Optional[str] = None