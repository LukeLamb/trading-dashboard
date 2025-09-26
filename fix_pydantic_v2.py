#!/usr/bin/env python3
"""
Fix Pydantic v2 compatibility issues in model files.
This script corrects @validator and @root_validator decorators to use
the new field_validator and model_validator syntax.
"""

import os
import re
from pathlib import Path

def fix_pydantic_validators(file_path):
    """Fix Pydantic validator decorators in a single file."""
    print(f"Processing {file_path}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match @validator decorators with their methods
    validator_pattern = r'@field_validator\s*\(\s*([^)]+)\s*\)\s*\n\s*def\s+(\w+)\s*\(\s*cls\s*,\s*([^)]+)\s*\):'

    # Find all field_validator methods that are missing @classmethod
    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for @field_validator decorators
        if '@field_validator(' in line:
            # Check if the next non-empty line contains the method definition
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1

            if j < len(lines) and 'def ' in lines[j] and 'cls' in lines[j]:
                # Check if @classmethod is already present
                has_classmethod = False
                k = i - 1
                while k >= 0 and lines[k].strip() == '':
                    k -= 1
                if k >= 0 and '@classmethod' in lines[k]:
                    has_classmethod = True

                if not has_classmethod:
                    # Add @classmethod decorator before @field_validator
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * indent + '@classmethod')

                new_lines.append(line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

        i += 1

    new_content = '\n'.join(new_lines)

    # Remove any duplicate @classmethod decorators that might exist
    new_content = re.sub(r'@classmethod\s*\n\s*@classmethod', '@classmethod', new_content)

    # Write the fixed content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Fixed {file_path}")

def main():
    """Fix all model files."""
    model_dir = Path('src/models')

    if not model_dir.exists():
        print("Models directory not found!")
        return

    # Fix all Python files in the models directory
    for file_path in model_dir.glob('*.py'):
        if file_path.name != '__init__.py':
            fix_pydantic_validators(file_path)

    print("All model files have been processed!")

if __name__ == '__main__':
    main()