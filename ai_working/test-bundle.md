---
bundle:
  name: test-skills-bundle
  version: 1.0.0
  description: Test bundle for validating skills integration

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: git+https://github.com/robotdad/amplifier-module-tool-skills@bundle-integration#subdirectory=behaviors/skills.yaml

tools:
  - module: tool-skills
    config:
      skills_dirs:
        - .amplifier/skills
---

# Test Skills Bundle

This is a test bundle to validate the skills integration pattern.

It includes:
- Foundation bundle (base capabilities)
- Skills behavior (from our fork for testing)

## Testing

```bash
# Test with this bundle
amplifier run --bundle ai_working/test-bundle.md "List available skills"
```

---

@foundation:context/shared/common-system-base.md
