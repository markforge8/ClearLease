"""
Explanation Service V2
======================
This service handles the explanation layer responsibilities for v2:
- Converting structural traps from Analysis v2 into human-understandable explanations
- Focusing on mechanism-level translation (trap → explanation)
- Answering: why user is disadvantaged, how disadvantage accumulates, escape window

This service implements the explanation v2 contract as defined in explain_v2_contract.md.
Currently only implements Temporal Lock-in trap type (MVP constraint).
"""

from typing import Optional
from backend.models.data_models import (
    ExplainV2Input,
    ExplainV2Output,
    TrapType,
    Strength,
    Beneficiary,
    Irreversibility,
    ConfidenceLevel,
    LockInDynamics
)


class ExplainV2Service:
    """
    Service class for handling structural trap explanations v2.
    
    This service converts mechanism-level trap inputs into human-understandable explanations.
    Currently only supports Temporal Lock-in trap type (MVP constraint).
    """
    
    def explain(self, input_data: ExplainV2Input) -> ExplainV2Output:
        """
        Convert trap input into human-understandable explanation.
        
        This method:
        1. Validates that trap_type is supported (currently only Temporal Lock-in)
        2. Generates explanation fields based on trap input
        3. Refuses output if required fields are missing or trap_type is unsupported
        
        Args:
            input_data: ExplainV2Input containing trap mechanism information
            
        Returns:
            ExplainV2Output containing explanation fields
            
        Raises:
            ValueError: If trap_type is unsupported or required fields are missing
        """
        # Fail-fast: only support Temporal Lock-in in MVP
        if input_data.trap_type != TrapType.TEMPORAL_LOCK_IN:
            raise ValueError(
                f"Explain v2 currently only supports Temporal Lock-in. "
                f"Received: {input_data.trap_type.value}"
            )
        
        # Generate explanation for Temporal Lock-in
        return self._explain_temporal_lock_in(input_data)
    
    def _explain_temporal_lock_in(self, input_data: ExplainV2Input) -> ExplainV2Output:
        """
        Generate explanation for Temporal Lock-in trap.
        
        Args:
            input_data: ExplainV2Input with trap_type=Temporal Lock-in
            
        Returns:
            ExplainV2Output with all required fields for Temporal Lock-in
        """
        # Map strength to explanation intensity
        strength = input_data.strength
        
        # Generate headline based on strength
        if strength == Strength.HIGH:
            headline = "如果错过了特定的时间点，后续想要退出的话，成本可能会增加。"
        elif strength == Strength.MEDIUM:
            headline = "如果错过了特定的时间点，后续想要退出的话，成本可能会增加。"
        else:  # LOW
            headline = "如果错过了特定的时间点，后续想要退出的话，成本可能会增加。"
        
        # Generate core_logic based on strength
        if strength == Strength.HIGH:
            core_logic = "如果错过了某个时间窗口，合同会自动延续，到那时再取消的话，需要付出的代价可能会比现在高一些。"
        elif strength == Strength.MEDIUM:
            core_logic = "如果错过了某个时间窗口，合同会自动延续，到那时再取消的话，需要付出的代价可能会比现在高一些。"
        else:  # LOW
            core_logic = "如果错过了某个时间窗口，合同会自动延续，到那时再取消的话，需要付出的代价可能会比现在高一些。"
        
        # Generate power_map (who benefits vs who bears cost)
        if input_data.beneficiary == Beneficiary.PROVIDER:
            power_map = "服务提供方可以在特定时间自动延续合同，而如果错过了取消的时间，后续成本通常需要由用户承担。"
        else:  # COUNTERPARTY
            power_map = "对方可以在特定时间自动延续合同，而如果错过了取消的时间，后续成本通常需要由用户承担。"
        
        # Generate lock_in_dynamics (required for Temporal Lock-in)
        if strength == Strength.HIGH:
            lock_in_dynamics_desc = "一旦过了可以取消的时间点，合同会自动继续，之后想要退出的话，付出的代价可能会比现在更高。"
        elif strength == Strength.MEDIUM:
            lock_in_dynamics_desc = "一旦过了可以取消的时间点，合同会自动继续，之后想要退出的话，付出的代价可能会比现在更高。"
        else:  # LOW
            lock_in_dynamics_desc = "一旦过了可以取消的时间点，合同会自动继续，之后想要退出的话，付出的代价可能会比现在更高。"
        
        lock_in_dynamics = LockInDynamics(description=lock_in_dynamics_desc)
        
        # Use escape_window from input (trust Analysis v2)
        escape_window = input_data.window
        
        # Generate user_actions based on strength
        if strength == Strength.HIGH:
            user_actions = [
                "记下需要做出决定的截止日期，并设置提醒",
                "在截止日期前考虑是否要继续",
                "先了解一下，如果错过取消窗口，后续退出的成本可能会是多少"
            ]
        elif strength == Strength.MEDIUM:
            user_actions = [
                "记下需要做出决定的截止日期，并设置提醒",
                "在截止日期前考虑是否要继续"
            ]
        else:  # LOW
            user_actions = [
                "记下需要做出决定的截止日期，并设置提醒"
            ]
        
        # Map strength to confidence_level
        # Higher strength → higher confidence (more signals detected)
        if strength == Strength.HIGH:
            confidence_level = ConfidenceLevel.HIGH
        elif strength == Strength.MEDIUM:
            confidence_level = ConfidenceLevel.MEDIUM
        else:  # LOW
            confidence_level = ConfidenceLevel.LOW
        
        # Build and return ExplainV2Output
        return ExplainV2Output(
            mechanism=input_data.trap_type,
            headline=headline,
            core_logic=core_logic,
            power_map=power_map,
            irreversibility=input_data.irreversibility,
            lock_in_dynamics=lock_in_dynamics,
            escape_window=escape_window,
            user_actions=user_actions,
            confidence_level=confidence_level
        )


