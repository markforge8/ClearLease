import uuid
from typing import List
from backend.models.data_models import Trap, RiskChain


class RiskChainBuilder:
    def build_chains(self, traps: List[Trap]) -> List[RiskChain]:
        """
        Builds risk chains for each trap.
        
        For Temporal Lock-in Trap, constructs a fixed 3-step chain:
        1. 用户错过操作窗口（低风险）
        2. 自动续约生效（中风险）
        3. 退出成本上升/合同锁死（高风险）
        
        Args:
            traps: List of detected traps
            
        Returns:
            List of RiskChain objects
        """
        chains = []
        
        for trap in traps:
            if trap.trap_type == "temporal_lock":
                chain = self._build_temporal_lock_chain(trap)
                chains.append(chain)
            elif trap.trap_type == "asymmetric_power":
                chain = self._build_asymmetric_power_chain(trap)
                chains.append(chain)
            elif trap.trap_type == "exit_barrier":
                chain = self._build_exit_barrier_chain(trap)
                chains.append(chain)
            elif trap.trap_type == "interpretation_ambiguity":
                chain = self._build_interpretation_ambiguity_chain(trap)
                chains.append(chain)
        
        return chains
    
    def _build_temporal_lock_chain(self, trap: Trap) -> RiskChain:
        """
        Builds a fixed 3-step risk chain for Temporal Lock-in Trap.
        """
        steps = [
            {
                "step_id": "step_1",
                "description": "用户错过操作窗口",
                "severity": "low",
                "order": 1
            },
            {
                "step_id": "step_2",
                "description": "自动续约生效",
                "severity": "medium",
                "order": 2
            },
            {
                "step_id": "step_3",
                "description": "退出成本上升/合同锁死",
                "severity": "high",
                "order": 3
            }
        ]
        
        chain = RiskChain(
            chain_id=f"chain_{uuid.uuid4().hex[:8]}",
            trap_id=trap.trap_id,
            steps=steps,
            final_outcome="用户失去低成本退出路径"
        )
        
        return chain
    
    def _build_asymmetric_power_chain(self, trap: Trap) -> RiskChain:
        """
        Builds a fixed 3-step risk chain for Asymmetric Power Trap.
        """
        steps = [
            {
                "step_id": "step_1",
                "description": "合同初始状态看似安全",
                "severity": "low",
                "order": 1
            },
            {
                "step_id": "step_2",
                "description": "对方单方面调整条款",
                "severity": "medium",
                "order": 2
            },
            {
                "step_id": "step_3",
                "description": "争议发生时用户处于劣势",
                "severity": "high",
                "order": 3
            }
        ]
        
        chain = RiskChain(
            chain_id=f"chain_{uuid.uuid4().hex[:8]}",
            trap_id=trap.trap_id,
            steps=steps,
            final_outcome="用户在未来争议中处于系统性劣势地位"
        )
        
        return chain
    
    def _build_exit_barrier_chain(self, trap: Trap) -> RiskChain:
        """
        Builds a fixed 3-step risk chain for Exit Barrier Trap.
        """
        steps = [
            {
                "step_id": "step_1",
                "description": "合同初始阶段看似可自由退出",
                "severity": "low",
                "order": 1
            },
            {
                "step_id": "step_2",
                "description": "用户尝试退出时触发高额限制或费用",
                "severity": "medium",
                "order": 2
            },
            {
                "step_id": "step_3",
                "description": "用户被迫继续履约或承担显著损失",
                "severity": "high",
                "order": 3
            }
        ]
        
        chain = RiskChain(
            chain_id=f"chain_{uuid.uuid4().hex[:8]}",
            trap_id=trap.trap_id,
            steps=steps,
            final_outcome="用户在尝试退出合同时遭遇系统性退出障碍，导致被迫承担显著经济损失"
        )
        
        return chain
    
    def _build_interpretation_ambiguity_chain(self, trap: Trap) -> RiskChain:
        """
        Builds a fixed 3-step risk chain for Interpretation / Ambiguity Trap.
        """
        steps = [
            {
                "step_id": "step_1",
                "description": "合同条款在签署时看似灵活或无明显风险",
                "severity": "low",
                "order": 1
            },
            {
                "step_id": "step_2",
                "description": "实际执行中条款含义被单方面解释",
                "severity": "medium",
                "order": 2
            },
            {
                "step_id": "step_3",
                "description": "争议发生时用户因解释权劣势承担不利后果",
                "severity": "high",
                "order": 3
            }
        ]
        
        chain = RiskChain(
            chain_id=f"chain_{uuid.uuid4().hex[:8]}",
            trap_id=trap.trap_id,
            steps=steps,
            final_outcome="用户因合同条款解释权不对等，在实际执行或争议中处于系统性不利地位"
        )
        
        return chain

