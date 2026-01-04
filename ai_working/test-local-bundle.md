---
bundle:
  name: test-local-skills
  version: 1.0.0
  description: Test bundle using local development version with hooks.py

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

tools:
  - module: tool-skills
    source: file://$PWD
    config:
      # Uses default: .amplifier/skills, ~/.amplifier/skills
      visibility:
        enabled: true  # Test visibility feature
---

# Test Local Skills Bundle

This bundle loads the LOCAL development version of tool-skills (with hooks.py).

**IMPORTANT**: The $PWD variable will be resolved by the shell, so run commands from the amplifier-module-tool-skills directory.

---

@foundation:context/shared/common-system-base.md
