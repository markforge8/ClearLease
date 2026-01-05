# Explain v2.1 · Default Language (Frozen)

This document defines the default human-facing language
used by Gateway for Explain v2.

It replaces all previous language candidates and drafts.
Only this document is considered authoritative.

Any modification requires version bump (v2.1.x).

Explain v2.1 · 默认语言（收敛版）

用途：Gateway 第一轮默认映射
原则：稳、短、不解释过头

1️⃣ headline（单句结构结论）

最终选用：

你如果错过特定的时间点，后续想要退出的话，成本会增加。

为什么选这条：

不提“合同”“设计”“机制”（避免专家感）

直接把因果关系说清楚

“成本会增加”是事实描述，不是恐吓

❌ 淘汰原因：

「时间相关的设计」——太像报告

「时间会改变你的选择成本」——抽象度偏高

2️⃣ core_logic（劣势如何形成）

最终选用：

如果你错过了某个时间窗口，合同会自动延续，到那时你再去取消，需要付出的代价就比现在高了。

为什么选这条：

时间 → 自动发生 → 后果

逻辑顺序清晰

“比现在高了”非常贴近日常思维

3️⃣ power_map（谁受益、谁承担成本）

最终选用：

对方可以在特定时间自动延续合同，而你如果错过了取消的时间，后续成本需要你来承担。

为什么选这条：

明确不对称

没有指责语气

“需要你来承担”是事实，不是价值判断

4️⃣ lock_in_dynamics.description

（仅 Temporal Lock-in 使用）

最终选用：

一旦过了可以取消的时间点，合同会自动继续，之后想要退出的话，付出的代价会比现在更高。

为什么选这条：

语言与 core_logic 呼应（一致性）

没有引入新信息

不增加焦虑

5️⃣ escape_window.conditions（逃脱窗口）

最终选用：

如果在指定的日期前取消，就不会自动延续；如果过了这个时间点，合同会自动继续。

为什么选这条：

条件非常清楚

不带操作步骤

不像“教程”，像“状态说明”

6️⃣ user_actions（用户行动建议）

最终采用组合：

👉 主用：时间提醒类（A）
👉 辅用：成本评估类（B）

默认展示顺序：

记下需要做出决定的截止日期，并设置提醒

在截止日期前考虑清楚是否要继续

先了解一下，如果错过取消窗口，后续退出的成本是多少

为什么这样配：

先行动（时间）

再思考（是否继续）

最后理性评估（成本）

❌ 不选纯“决策准备类”，因为太虚。

7️⃣ irreversibility（不可逆性）
partially_reversible（默认最常见）

最终选用：

这个选择后续可以撤销，但可能需要承担一些成本。

为什么选这条：

非常克制

不制造恐惧

与现实高度一致

8️⃣ confidence_level（置信度）
high（当前样本多为此）

最终选用：

合同条款比较明确，这个判断可信度较高。

为什么选这条：

不说“我很确定”

把确定性归因于“条款”，不是系统自信