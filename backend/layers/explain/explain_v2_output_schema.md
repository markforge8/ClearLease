# Explain v2 Output Schema

本文档定义了 Explain v2 对外暴露的字段 schema（字段名 + 含义），并标注字段类型。

## 字段分类说明

- **必须字段 (Required)**: 所有 Explain v2 输出必须包含的字段
- **条件必须字段 (Conditional Required)**: 特定 trap 类型必须包含的字段
- **可选字段 (Optional)**: 当前未使用但已定义的字段（为未来扩展预留）

---

## 字段 Schema

### 1. mechanism (必须字段)

**字段名**: `mechanism`

**类型**: `TrapType` (Enum)

**取值**: 
- `"Temporal Lock-in"`
- `"Asymmetric Power"`
- `"Exit Barrier"`
- `"Ambiguity"`

**含义**: Trap 类型（从输入继承）

**Gateway 使用**: 
- 用于 `details.v2.mechanism`
- 用于 `key_findings[].mechanism`

**参考**: explain_v2_contract.md section 4.1

---

### 2. headline (必须字段)

**字段名**: `headline`

**类型**: `str`

**含义**: 一句话结构性结论（single-sentence structural conclusion）

**Gateway 使用**: 
- 用于 `overview.summary`（v2 优先）
- 用于 `details.v2.headline`
- 用于 `key_findings[].headline`

**参考**: explain_v2_contract.md section 4.1

---

### 3. core_logic (必须字段)

**字段名**: `core_logic`

**类型**: `str`

**含义**: 劣势如何形成的解释（explanation of how disadvantage forms）

**Gateway 使用**: 
- 用于 `details.v2.core_logic`
- 用于 `key_findings[].core_logic`

**参考**: explain_v2_contract.md section 4.1

---

### 4. power_map (必须字段)

**字段名**: `power_map`

**类型**: `str`

**含义**: 谁受益 vs 谁承担成本（who benefits vs who bears cost）

**Gateway 使用**: 
- 用于 `details.v2.power_map`
- 用于 `key_findings[].power_map`

**参考**: explain_v2_contract.md section 4.1, section 5.2

---

### 5. irreversibility (必须字段)

**字段名**: `irreversibility`

**类型**: `Irreversibility` (Enum)

**取值**: 
- `"reversible"`
- `"partially_reversible"`
- `"irreversible"`

**含义**: 可逆性级别（从 Analysis v2 输入继承）

**Gateway 使用**: 
- 用于 `details.v2.irreversibility`

**参考**: explain_v2_contract.md section 4.1, section 5.3

---

### 6. escape_window (必须字段)

**字段名**: `escape_window`

**类型**: `Dict[str, Any]`

**含义**: 逃脱窗口信息（必须存在，即使窗口已关闭）

**典型结构**:
```json
{
  "exists": true,
  "conditions": "在续约窗口关闭前提供书面终止通知",
  "deadline": "合同到期前90天"
}
```

**Gateway 使用**: 
- 用于 `details.v2.escape_window`（完整传递）

**参考**: explain_v2_contract.md section 4.1, section 5.1

---

### 7. user_actions (必须字段)

**字段名**: `user_actions`

**类型**: `List[str]`

**含义**: 结构性选项（structural options），非法律建议

**Gateway 使用**: 
- 用于 `next_actions[]`（v2 优先，最多 2 个）
- 用于 `details.v2.user_actions`（完整列表）

**参考**: explain_v2_contract.md section 4.1

---

### 8. confidence_level (必须字段)

**字段名**: `confidence_level`

**类型**: `ConfidenceLevel` (Enum)

**取值**: 
- `"high"`
- `"medium"`
- `"low"`

**含义**: 置信度级别

**Gateway 使用**: 
- 用于 `overview.attention_level`（映射：high→high, medium→medium, low→low）
- 用于 `details.v2.confidence_level`

**参考**: explain_v2_contract.md section 4.1

---

### 9. lock_in_dynamics (条件必须字段)

**字段名**: `lock_in_dynamics`

**类型**: `Optional[LockInDynamics]`

**LockInDynamics 结构**:
```python
class LockInDynamics(BaseModel):
    description: str  # 时间相关的成本递增解释
```

**含义**: 锁定动态描述（仅 Temporal Lock-in 需要）

**条件**: 
- **Temporal Lock-in**: 必须字段
- **其他 trap 类型**: 可选（通常为 None）

**Gateway 使用**: 
- 仅当 `lock_in_dynamics` 存在时，用于 `details.v2.lock_in_dynamics.description`

**参考**: explain_v2_contract.md section 5.1

---

## 字段分类总结

### 必须字段 (8 个)

1. `mechanism` - Trap 类型
2. `headline` - 一句话结论
3. `core_logic` - 劣势形成逻辑
4. `power_map` - 权力映射
5. `irreversibility` - 可逆性
6. `escape_window` - 逃脱窗口
7. `user_actions` - 用户行动建议
8. `confidence_level` - 置信度

### 条件必须字段 (1 个)

9. `lock_in_dynamics` - 锁定动态（仅 Temporal Lock-in 必须）

### 可选字段

当前无可选字段（所有字段要么必须，要么条件必须）

### 未来扩展字段

当前无预留字段。如需扩展，需遵循 explain_v2_contract.md section 9 的合同稳定性要求。

---

## Gateway 输出映射

### Overview 使用
- `overview.attention_level`: 从 `confidence_level` 映射
- `overview.summary`: 直接使用 `headline`

### Key Findings 使用
- `key_findings[].source`: "v2"
- `key_findings[].headline`: 直接使用
- `key_findings[].core_logic`: 直接使用
- `key_findings[].power_map`: 直接使用
- `key_findings[].mechanism`: 直接使用

### Next Actions 使用
- `next_actions[].source`: "v2"
- `next_actions[].action`: 来自 `user_actions` 列表
- `next_actions[].mechanism`: 直接使用

### Details 使用
- `details.v2.*`: 所有字段完整传递（pass-through）
- `details.v2.lock_in_dynamics`: 仅当存在时包含

---

## 注意事项

1. **Gateway 原则**: Gateway 不修改、不解释、不推断 Explain v2 字段（treat as black box）
2. **字段完整性**: 所有必须字段必须在 Explain v2 输出中存在，否则会触发验证错误
3. **条件字段**: `lock_in_dynamics` 对于 Temporal Lock-in 是必须的，对于其他类型为 None
4. **扩展性**: 如需添加新字段，需要修改 ExplainV2Output 模型和 explain_v2_contract.md

---

## 参考文档

- `backend/models/data_models.py`: ExplainV2Output 模型定义
- `backend/layers/explain/explain_v2_contract.md`: Explain v2 合约规范
- `backend/layers/explain/explain_gateway.py`: Gateway 聚合逻辑

