#!/usr/bin/env python3
"""
Script to fix Pydantic v1 to v2 validator syntax.
"""

import os
import re
import glob

def fix_validators_in_file(filepath):
    """Fix validators in a single file."""
    print(f"Processing {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Fix imports
    content = re.sub(
        r'from pydantic import.*validator.*root_validator.*',
        'from pydantic import BaseModel, Field, field_validator, model_validator',
        content
    )

    content = re.sub(
        r'from pydantic import (.*), validator, root_validator',
        r'from pydantic import \1, field_validator, model_validator',
        content
    )

    content = re.sub(
        r'from pydantic import (.*), validator(.*)',
        r'from pydantic import \1, field_validator\2',
        content
    )

    content = re.sub(
        r'from pydantic import (.*), root_validator(.*)',
        r'from pydantic import \1, model_validator\2',
        content
    )

    # Fix @validator to @field_validator
    content = re.sub(
        r'@validator\((.*?)\)\s*\n\s*def (\w+)\(cls, v\):',
        r'@field_validator(\1)\n    @classmethod\n    def \2(cls, v):',
        content,
        flags=re.MULTILINE
    )

    # Fix @root_validator to @model_validator
    content = re.sub(
        r'@root_validator\s*\n\s*def (\w+)\(cls, values\):',
        r'@model_validator(mode=\'after\')\n    def \1(self):',
        content,
        flags=re.MULTILINE
    )

    # Fix the function body for model_validator
    # This is more complex, so let's do a simple replacement for common patterns
    content = re.sub(
        r'values\.get\((.*?)\)',
        r'self.\1',
        content
    )

    content = re.sub(
        r'values\[(.*?)\] = (.*?)\n',
        r'self.\1 = \2\n',
        content
    )

    content = re.sub(
        r'return values',
        r'return self',
        content
    )

    # Fix Config class to ConfigDict
    content = re.sub(
        r'class Config:\s*\n\s*use_enum_values = True\s*\n\s*json_encoders = \{[^}]*\}',
        'model_config = ConfigDict(use_enum_values=True)',
        content,
        flags=re.MULTILINE | re.DOTALL
    )

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
        return True
    else:
        print(f"No changes needed for {filepath}")
        return False

def main():
    """Main function."""
    model_files = glob.glob('src/models/*.py')

    for filepath in model_files:
        if os.path.basename(filepath) != '__init__.py':
            fix_validators_in_file(filepath)

if __name__ == "__main__":
    main()