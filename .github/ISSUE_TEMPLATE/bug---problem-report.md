---
name: Bug / problem report
about: Report a problem so we can improve the integration
title: ''
labels: 
assignees: HairingX

---

**Describe the bug or problem**
<!--
  A clear and concise description of what the bug or problem is.
-->

**Please answer the following**
- Version of integration:
- Version of Home Assistant:
- Charger brand / model:
- Relevant upstream HA integrations in use (e.g. Easee, Zaptec, OCPP, Nord Pool, solar inverter):

**REQUIRED! Provide debug log from the integration**
- Enable by adding the following to your configuration.yaml:
```
logger:
  default: info
  logs:
    custom_components.charge_smarter: debug
```
- Restart Home Assistant
- Capture all log lines (from the integration only), save it to a file and attach it here.
