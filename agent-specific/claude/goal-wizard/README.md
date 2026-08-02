# Goal Sandbox Plugin - Natural Language Verification

Enhances the goal-sandbox skill with natural language verification options.

## Overview

Converts vague goals like "Refactor the billing module" into guided verification options.

## Phase 1 (MVP) - Current Status

**Implemented:**
- Plugin directory structure
- 5 core verifications (2 structural, 2 behavioral, 1 property placeholder)
- 3 core guardrails
- Template base class system
- Dispatcher script (analyze_goal.py)
- Verifier generator (generate_verifier.py)
- Guardrail enforcer (enforce_guardrails.py)

**Pending:**
- Integration with goal-sandbox skill
- End-to-end testing

## Installation

```bash
# Copy plugin to Claude plugins directory
cp -r goal-sandbox-plugin ~/.claude/plugins/

# Reload plugins in Claude Code
/reload-plugins
```

## Usage

### Manual Testing

```bash
# Test dispatcher
cd plugins/goal-sandbox-plugin
python scripts/analyze_goal.py "Refactor billing module" --files billing.py

# Test verifier generation (requires config file)
python scripts/generate_verifier.py --config sample_config.json --output test_verify.py

# Test guardrails
python scripts/enforce_guardrails.py --action edit --target billing.py --config sample_guardrails.json
```

### Via Skill

```
/goal-sandbox "Refactor billing module for multi-currency support"
```

## Architecture

```
goal-sandbox-plugin/
  .claude-plugin/plugin.json        # Plugin manifest
  resources/
    verifiers/
      structural/                   # Code structure checks
      behavioral/                   # Runtime behavior tests
      property/                     # Property-based tests (placeholder in MVP)
    guardrails/                     # Safety constraints
  scripts/
    analyze_goal.py                 # Dispatcher
    generate_verifier.py            # Suite generator
    enforce_guardrails.py           # Guardrail checker
```

## Next Steps (Phase 2)

- Metadata-driven dispatcher (YAML-based discovery)
- Full hypothesis integration for property-based testing
- Usage tracking and learning system
- Progressive disclosure UX
- Performance optimization (caching)

## Dependencies

- Python 3.8+
- PyYAML (for manifest parsing - Phase 2)
