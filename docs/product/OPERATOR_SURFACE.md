# Operator Surface (P2)

The primary operator surface now follows one clean enterprise demo path:

1. Risk Board
2. Case Detail
3. Pending Approval
4. Simulation before execution
5. Audit Timeline + governed writeback receipt

Highlights:

- richer board filters for assignee, approval state, SLA state, and minimum risk
- SLA and aging badges to show urgency directly on the board
- plain-language approval narrative for non-technical walkthroughs
- simulation endpoint that previews governed writeback without mutating state
- governed writeback adapter that issues receipt-style evidence after execution

## Executive mode

Executive mode is a polished summary lens layered on top of the same operator workflow. It highlights:
- headline business risk
- revenue / cost / gap exposure
- top risk cards
- governed connector mix
- simple talking points for non-technical demos

## Scenario comparison

Each case now includes a scenario comparison payload with:
- row-level comparison data
- a recommended scenario
- normalized chart bars for risk, cost, and service impact

## Connector packs

Governed writeback now routes to one of three stub connector packs:
- ERP
- supplier portal
- ticketing

## P4 buyer-confidence upgrades

- Executive persona and customer theme selectors now drive the executive headline and one-page brief export.
- Governed writeback now emits richer receipt payloads with change ticket, approval checkpoint, business owner, and connector evidence.
- Connector-specific approval policies distinguish ERP, supplier portal, and ticketing behavior.
- The live-demo board/card styling is cleaned up for easier walkthroughs on customer calls.



## P5 buyer-tailored packaging

- Vertical seed packs: portfolio, data_center, ev_launch, industrial_edge
- Brand/theme swap layer driven by `contracts/demo_experience_pack.yaml`
- Exportable screenshot stills from `/operator/screenshot_manifest` and the web demo export button
- Scripted guided walkthrough from `/operator/demo_script` and the web demo guide rail
