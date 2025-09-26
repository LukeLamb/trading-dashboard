#!/usr/bin/env python3
"""
Fix model_validator methods for Pydantic v2 compatibility.
In Pydantic v2, model_validator(mode='after') receives the model instance, not a dict.
"""

import re
import os

def fix_model_validator_file(file_path):
    """Fix model validators in a single file."""
    print(f"Processing {file_path}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to find model_validators with (cls, values) signature
    pattern = r'(@model_validator\(mode=[\'"]after[\'"]\)\s+def\s+\w+\(cls,\s*values\):)'

    def replace_validator(match):
        # Replace (cls, values) with (self)
        old_signature = match.group(1)
        new_signature = old_signature.replace('(cls, values)', '(self)')
        return new_signature

    new_content = re.sub(pattern, replace_validator, content)

    # Now fix the body of these validators
    # Replace values.get('field') with self.field
    new_content = re.sub(r"values\.get\(['\"](\w+)['\"]\)", r"self.\1", new_content)

    # Replace return values with return self
    new_content = re.sub(r"return values", "return self", new_content)

    # Fix specific patterns that might not be caught
    new_content = re.sub(r"values\[(['\"])([^'\"]+)\1\]", r"self.\2", new_content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Fixed {file_path}")

def main():
    """Fix all model files."""
    model_files = [
        'src/models/market_data.py',
        'src/models/agent_status.py',
        'src/models/system_metrics.py',
        'src/models/api_responses.py'
    ]

    for file_path in model_files:
        if os.path.exists(file_path):
            fix_model_validator_file(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == '__main__':
    main()