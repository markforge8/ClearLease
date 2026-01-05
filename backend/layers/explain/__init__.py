"""
Explanation Layer Package
=========================
This package contains the explanation layer implementation.

Exports:
    ExplainService: Main service class for data explanation v0
    ExplainV1Service: Service class for data explanation v1
    ExplainGateway: Gateway for aggregating explanations from v0, v1, v2
    ExplanationOutput: Output model from explanation v0
    ExplanationOutputV1: Output model from explanation v1
    ExplanationBlock: Model representing a single explanation block
"""

from .explain_service import ExplainService
from .explain_v1_service import ExplainV1Service
from .explain_v2_service import ExplainV2Service
from .explain_gateway import ExplainGateway
from backend.models.data_models import (
    ExplanationOutput,
    ExplanationOutputV1,
    ExplanationBlock,
    ExplainV2Input,
    ExplainV2Output,
    GatewayOutput
)

__all__ = [
    "ExplainService",
    "ExplainV1Service",
    "ExplainV2Service",
    "ExplainGateway",
    "ExplanationOutput",
    "ExplanationOutputV1",
    "ExplanationBlock",
    "ExplainV2Input",
    "ExplainV2Output",
    "GatewayOutput"
]

