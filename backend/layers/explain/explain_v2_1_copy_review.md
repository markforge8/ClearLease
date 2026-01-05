# Explain v2.1 Copy Review
## Self-blame and Anxiety Trigger Analysis

### Review Criteria
1. ✅ Explicit re-centering statement before analysis
2. ❌ Sentences implying user fault, urgency, or missed responsibility
3. ✅ Modal verbs softened (can / may / often) vs absolute claims
4. ✅ Clear scope boundary (when this actually matters)

---

## Issues Found

### 1. headline
**Current:**
> 你如果错过特定的时间点，后续想要退出的话，成本会增加。

**Issues:**
- ❌ "你如果错过" - implies user fault ("if you miss")
- ❌ Conditional structure suggests user responsibility for missing
- ⚠️ No re-centering statement before this

**Proposed adjustment:**
> 如果错过了特定的时间点，后续想要退出的话，成本可能会增加。

**Rationale:**
- Remove "你" (you) to depersonalize
- Add "可能" (may) to soften certainty
- Maintains same meaning with softer framing

---

### 2. core_logic
**Current:**
> 如果你错过了某个时间窗口，合同会自动延续，到那时你再去取消，需要付出的代价就比现在高了。

**Issues:**
- ❌ "如果你错过了" - direct user fault implication
- ❌ "你再去取消" - emphasizes user action as cause
- ⚠️ No re-centering statement

**Proposed adjustment:**
> 如果错过了某个时间窗口，合同会自动延续，到那时再取消的话，需要付出的代价可能会比现在高一些。

**Rationale:**
- Remove "你" (you) references
- Add "可能" (may) and "一些" (some) to soften
- Change "就比现在高了" to "可能会比现在高一些" (less absolute)

---

### 3. power_map
**Current:**
> 对方可以在特定时间自动延续合同，而你如果错过了取消的时间，后续成本需要你来承担。

**Issues:**
- ❌ "而你如果错过了" - contrasts user fault with counterparty action
- ❌ "需要你来承担" - emphasizes user burden
- ⚠️ Creates blame contrast

**Proposed adjustment:**
> 对方可以在特定时间自动延续合同，而如果错过了取消的时间，后续成本通常需要由用户承担。

**Rationale:**
- Remove "你" (you) to depersonalize
- Add "通常" (usually) to soften
- Change "需要你来承担" to "需要由用户承担" (more neutral)

---

### 4. lock_in_dynamics.description
**Current:**
> 一旦过了可以取消的时间点，合同会自动继续，之后想要退出的话，付出的代价会比现在更高。

**Issues:**
- ⚠️ "一旦过了" - absolute timing, but acceptable as structural fact
- ✅ "会" is already softened (would, not must)
- ✅ No direct user fault implication

**Proposed adjustment:**
> 一旦过了可以取消的时间点，合同会自动继续，之后想要退出的话，付出的代价可能会比现在更高。

**Rationale:**
- Add "可能" (may) to soften certainty
- Minimal change, maintains structural accuracy

---

### 5. escape_window.conditions
**Current:**
> 如果在指定的日期前取消，就不会自动延续；如果过了这个时间点，合同会自动继续。

**Issues:**
- ✅ Neutral, factual statement
- ✅ No user fault implication
- ✅ Clear scope boundary

**Status:** ✅ No changes needed

---

### 6. user_actions
**Current:**
1. 记下需要做出决定的截止日期，并设置提醒
2. 在截止日期前考虑清楚是否要继续
3. 先了解一下，如果错过取消窗口，后续退出的成本是多少

**Issues:**
- ⚠️ Item 2: "考虑清楚" - implies user should have clarity (pressure)
- ⚠️ Item 3: "如果错过" - conditional fault framing
- ⚠️ No re-centering before action items

**Proposed adjustments:**
1. 记下需要做出决定的截止日期，并设置提醒 ✅ (no change)
2. 在截止日期前考虑是否要继续
3. 先了解一下，如果错过取消窗口，后续退出的成本可能会是多少

**Rationale:**
- Item 2: Remove "清楚" (clearly) to reduce pressure
- Item 3: Add "可能" (may) to soften

---

### 7. irreversibility
**Current:**
> 这个选择后续可以撤销，但可能需要承担一些成本。

**Issues:**
- ✅ Already uses "可能" (may)
- ✅ Soft framing
- ✅ No user fault implication

**Status:** ✅ No changes needed

---

### 8. confidence_level
**Current:**
> 合同条款比较明确，这个判断可信度较高。

**Issues:**
- ✅ Neutral, factual
- ✅ No user fault implication
- ✅ Clear scope boundary

**Status:** ✅ No changes needed

---

## Summary

### Missing Re-centering Statements
- ❌ No explicit re-centering statement appears before headline or core_logic
- ⚠️ Re-centering only appears in UI layer (handoff screen), not in Explain v2 content itself

### Sentences Triggering Self-blame
1. headline: "你如果错过" → Remove "你", add "可能"
2. core_logic: "如果你错过了" + "你再去取消" → Remove "你", soften certainty
3. power_map: "而你如果错过了" → Remove "你", add "通常"
4. user_actions item 2: "考虑清楚" → Remove "清楚"
5. user_actions item 3: "如果错过" → Add "可能"

### Modal Verb Softening
- Most statements use "会" (will/would) which is acceptable
- Add "可能" (may) where certainty is implied but not guaranteed
- Add "通常" (usually) where patterns are common but not universal

### Scope Boundaries
- ✅ escape_window provides clear timing boundary
- ✅ Most statements are conditional (if/then), which provides scope
- ⚠️ Could benefit from explicit "when this matters" framing

---

## Recommended Minimal Adjustments

**Priority 1 (High impact, low change):**
1. Remove "你" (you) from headline, core_logic, power_map
2. Add "可能" (may) to headline, core_logic, lock_in_dynamics, user_actions item 3
3. Remove "清楚" from user_actions item 2

**Priority 2 (Medium impact):**
4. Add "通常" to power_map
5. Soften "就比现在高了" to "可能会比现在高一些"

**Priority 3 (Consider for future):**
6. Add explicit re-centering statement at start of Explain v2 content (not just in UI layer)

