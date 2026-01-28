from typing import List
from backend.models.data_models import RiskField, RiskAxis, AnalysisOutput, ExtractedSignal


class RiskBuilderV1:
    def build(self, analysis_output: AnalysisOutput, extracted_signals: List[ExtractedSignal]) -> List[RiskField]:
        """
        v1：从 v0 analysis_output 和 extracted_signals 中，生成结构性 RiskField
        
        Args:
            analysis_output: AnalysisOutput from v0 analysis
            extracted_signals: List of extracted signals used in analysis
            
        Returns:
            List of RiskField objects
        """
        risk_fields = []

        # RESPONSIBILITY: 责任转移风险（维护责任转嫁给租客）
        if self._has_responsibility_transfer(extracted_signals, analysis_output):
            risk_fields.append(
                RiskField(
                    axis=RiskAxis.RESPONSIBILITY,
                    affected_party="tenant",
                    intensity="high",
                    compounding=True,
                    description="房东将维护责任转嫁给租客。",
                    source_blocks=self._get_source_blocks_for_responsibility(extracted_signals)
                )
            )

        # LIABILITY: 免责风险（房东免责条款）
        if self._has_liability_risk(extracted_signals, analysis_output):
            risk_fields.append(
                RiskField(
                    axis=RiskAxis.LIABILITY,
                    affected_party="tenant",
                    intensity="high",
                    compounding=True,
                    description="房东设置免责条款，限制其责任。",
                    source_blocks=self._get_source_blocks_for_liability(extracted_signals)
                )
            )

        # TEMPORAL: 时间风险（自动续约或提前解约惩罚）
        if self._has_temporal_risk(extracted_signals, analysis_output):
            risk_fields.append(
                RiskField(
                    axis=RiskAxis.TEMPORAL,
                    affected_party="tenant",
                    intensity="medium",
                    compounding=False,
                    description="合同包含自动续约或提前解约惩罚条款。",
                    source_blocks=self._get_source_blocks_for_temporal(extracted_signals)
                )
            )

        return risk_fields

    def _has_responsibility_transfer(self, signals: List[ExtractedSignal], analysis_output: AnalysisOutput) -> bool:
        """
        判断是否有责任转移风险（RESPONSIBILITY）
        触发条件：提取的文本中包含维护责任相关的关键词
        """
        responsibility_keywords = [
            "responsible for",
            "maintenance",
            "repair",
            "hvac",
            "plumbing",
            "electrical"
        ]
        
        for signal in signals:
            hit_text_lower = signal.hit_text.lower()
            # Negation guard: exclude negative responsibility phrases
            if "not be responsible for" in hit_text_lower or "not responsible for" in hit_text_lower:
                continue
            for keyword in responsibility_keywords:
                if keyword in hit_text_lower:
                    return True
        return False

    def _has_liability_risk(self, signals: List[ExtractedSignal], analysis_output: AnalysisOutput) -> bool:
        """
        判断是否有免责风险（LIABILITY）
        统一触发入口：
        1. risk_code 为 LIABILITY_LIMITATION
        2. 或 hit_text 包含 "not be liable" 或 "not be responsible for"
        """
        # Check risk_code
        risk_codes = [item.risk_code for item in analysis_output.risk_items]
        if "LIABILITY_LIMITATION" in risk_codes:
            return True
        
        # Check hit_text
        for signal in signals:
            hit_text_lower = signal.hit_text.lower()
            if "not be liable" in hit_text_lower or "not be responsible for" in hit_text_lower:
                return True
        return False

    def _has_temporal_risk(self, signals: List[ExtractedSignal], analysis_output: AnalysisOutput) -> bool:
        """
        判断是否有时间相关风险（TEMPORAL）
        触发条件：
        1. 提取的文本中包含明确的自动续约关键词，或
        2. 存在 EARLY_TERMINATION_PENALTY 风险代码
        """
        # 检查是否有提前解约惩罚
        risk_codes = [item.risk_code for item in analysis_output.risk_items]
        if "EARLY_TERMINATION_PENALTY" in risk_codes:
            return True
        
        # 检查是否包含明确的自动续约关键词
        temporal_keywords = [
            "automatically renew",
            "automatic renewal",
            "auto renew",
            "shall automatically renew"
        ]
        
        for signal in signals:
            hit_text_lower = signal.hit_text.lower()
            for keyword in temporal_keywords:
                if keyword in hit_text_lower:
                    return True
        return False

    def _get_source_blocks_for_responsibility(self, signals: List[ExtractedSignal]) -> List[str]:
        """获取责任转移相关的 block_id"""
        responsibility_keywords = [
            "responsible for",
            "maintenance",
            "repair",
            "hvac",
            "plumbing",
            "electrical"
        ]
        
        block_ids = set()
        for signal in signals:
            hit_text_lower = signal.hit_text.lower()
            for keyword in responsibility_keywords:
                if keyword in hit_text_lower:
                    block_ids.add(signal.block_id)
                    break
        return list(block_ids)

    def _get_source_blocks_for_liability(self, signals: List[ExtractedSignal]) -> List[str]:
        """获取免责相关的 block_id"""
        liability_keywords = [
            "not liable",
            "not be held liable",
            "not be responsible",
            "disclaimer",
            "as-is",
            "as is"
        ]
        
        block_ids = set()
        for signal in signals:
            hit_text_lower = signal.hit_text.lower()
            for keyword in liability_keywords:
                if keyword in hit_text_lower:
                    block_ids.add(signal.block_id)
                    break
        return list(block_ids)

    def _get_source_blocks_for_temporal(self, signals: List[ExtractedSignal]) -> List[str]:
        """获取时间风险相关的 block_id"""
        temporal_keywords = [
            "automatically renew",
            "automatic renewal",
            "auto renew",
            "shall automatically renew",
            "early termination",
            "penalty"
        ]
        
        block_ids = set()
        for signal in signals:
            hit_text_lower = signal.hit_text.lower()
            for keyword in temporal_keywords:
                if keyword in hit_text_lower:
                    block_ids.add(signal.block_id)
                    break
        return list(block_ids)

    def _get_source_blocks(self, signals: List[ExtractedSignal]) -> List[str]:
        """
        从 signals 中提取唯一的 block_id 列表（保留用于兼容性）
        """
        block_ids = list(set([signal.block_id for signal in signals]))
        return block_ids if block_ids else []
