---
name: risk-execution
description: Apply execution safety rules before paper or live orders.
---

# Risk Execution Skill

Use this skill when a workflow may create an order or rebalance proposal.

Safety rules:
1. Research output is not an order.
2. Strategy signal, backtest validation, risk check, and human policy must align before execution.
3. HOLD signals must block automatic execution.
4. Failed provider health checks must block live execution.
5. Paper execution must be labeled clearly as paper or mock.
6. Live execution requires explicit mode, configured account, broker health, and approval policy.

Output:
- State whether execution is blocked, paper-only, or allowed.
- Include the blocking reason when execution is not allowed.
- Include broker, account, environment, and external order id when available.
