"""Test setup: ensure a (dummy) provider key exists so agents construct.

The model is always overridden with a mock in tests, so this key is never used
for a real request — it just satisfies the Anthropic provider's constructor.
"""

import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
