---
name: provider-selection
description: Choose market, account, and execution providers without coupling data source and broker.
---

# Provider Selection Skill

Use this skill when the user asks which data source or broker should be used.

Provider rules:
1. Market data and execution are separate capabilities.
2. A workflow may use one provider for data and another for execution.
3. Longbridge is suitable for market, account, and execution capabilities once the CLI is installed and authenticated.
4. Futu requires OpenD availability before runtime use.
5. Eastmoney should be treated as market-data only until an execution connector is explicitly implemented.
6. IBKR can support market, account, and execution later, but must pass health checks before live use.

Runtime behavior:
- Check provider health before relying on a non-mock provider.
- Record provider names in run artifacts.
- Fall back only when the workflow mode allows it.
- For live execution, require explicit approval and a healthy broker connector.
