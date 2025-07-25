import sys
import os

def in_virtual_environment():
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )

if in_virtual_environment():
    print(f"✅ In virtual environment: {sys.prefix}")
else:
    print("❌ Not in a virtual environment.")
