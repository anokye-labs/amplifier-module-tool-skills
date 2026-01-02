---
bundle:
  name: test-behavior-inclusion
  version: 1.0.0
  description: Test that skills behavior can be included in other bundles

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/robotdad/amplifier-module-tool-skills@bundle-integration#subdirectory=behaviors/skills.yaml
---

# Test Behavior Inclusion

This bundle tests that the skills behavior can be included by other bundles.

---

@foundation:context/shared/common-system-base.md
