Explain v2 Contract

Purpose:
Define the immutable interface between Analysis v2 and Explain v2, ensuring that explanation is mechanism-based, human-comprehensible, and non-procedural.

1. Scope & Non-Goals
1.1 What Explain v2 Is

Explain v2 is a mechanism-level translator.

It converts structural traps identified by Analysis v2 into human-understandable explanations that answer:

Why the user is disadvantaged

How that disadvantage accumulates

Whether there is still an escape window

Explain v2 does not analyze contracts, assess legality, or generate advice.

1.2 What Explain v2 Is Not

Explain v2 must never:

Interpret contract text directly

Re-evaluate risk or legality

Generate speculative outcomes

Replace user decision-making

Explain v2 is descriptive, not prescriptive.

2. Accepted Input (from Analysis v2)

Explain v2 accepts only mechanism-level input.

If any required field is missing, Explain v2 must refuse to generate output.

2.1 Required Fields
trap_type        : Temporal Lock-in | Asymmetric Power | Exit Barrier | Ambiguity
strength         : low | medium | high
beneficiary      : provider | counterparty
cost_bearer      : user
irreversibility  : reversible | partially_reversible | irreversible
evidence         : clause references and detected signals
window           : escape window existence and conditions


Explain v2 must trust Analysis v2 and must not re-verify evidence.

3. Core Trap Types (Worldview Primitives)

Explain v2 recognizes exactly four trap primitives.

3.1 Temporal Lock-in

A structure where exit cost increases over time, while the counterparty remains flexible.

3.2 Asymmetric Power

A structure where decision rights and consequence burdens are misaligned.

3.3 Exit Barrier

A structure where exit costs are hidden, delayed, or fragmented, discouraging rational evaluation.

3.4 Interpretation / Ambiguity Trap

A structure where ambiguity + interpretation rights create unilateral discretion.

No additional trap types may be introduced without contract revision.

4. Mandatory Explanation Output Schema

Explain v2 output must conform to the following conceptual schema.

All required fields must be present.

4.1 Required Fields
mechanism            : trap_type
headline             : single-sentence structural conclusion
core_logic           : explanation of how disadvantage forms
power_map            : who benefits vs who bears cost
irreversibility      : carried over from Analysis v2
lock_in_dynamics     : required for Temporal Lock-in only
escape_window        : must exist (even if closed)
user_actions         : structural options, not legal advice
confidence_level     : high | medium | low

5. Trap-Specific Field Requirements
5.1 Temporal Lock-in

Must include:

lock_in_dynamics

escape_window

Must explicitly state time-dependent cost escalation.

5.2 Asymmetric Power

Must include:

power_map

explanation of decision vs consequence mismatch

5.3 Exit Barrier

Must include:

irreversibility

explanation of hidden or delayed cost realization

5.4 Ambiguity / Interpretation Trap

Must include:

identification of interpretation authority

explanation of how ambiguity becomes power

6. Strength Modulation Rules

Explanation intensity must scale with strength, but structure must remain unchanged.

low → awareness

medium → warning

high → structural exposure

Explain v2 must never escalate beyond structural description.

7. Failure Conditions (Fail-Fast Rules)

Explain v2 must refuse output if:

Required input fields are missing

trap_type is unrecognized

Structural explanation cannot be formed

Silent degradation is forbidden.

8. Explicit Prohibitions

Explain v2 must never:

Provide legal judgments

Suggest legal actions

Predict outcomes

Soften structural imbalance

Explain v2 exists to reveal, not to comfort.

9. Contract Stability

This contract is immutable by implementation.

Any change requires:

Explicit versioning

Downstream gateway impact review

10. Design Philosophy (Non-Executable)

Explain v2 is designed to create a moment of clarity, not reassurance.

It should leave the user with:

“I now understand the structure I am in.”

Not:

“I feel safer.”