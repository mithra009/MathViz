import re

code = """from manim import *

class RotatingSphere3D(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes()
"""

print("Testing each pattern individually:")
print("="*60)
print(f"Code to match:\n{code}")
print("="*60)

patterns = [
    r'class\s+(\w+)\s*\(\s*Scene\s*\):',
    r'class\s+(\w+)\s*\(\s*ThreeDScene\s*\):',
    r'class\s+(\w+)\s*\(\s*manim\.Scene\s*\):',
    r'class\s+(\w+)\s*\(\s*manim\.ThreeDScene\s*\):',
]

for i, pattern in enumerate(patterns):
    print(f"\nPattern {i}: {pattern}")
    match = re.search(pattern, code, re.MULTILINE)
    if match:
        print(f"   MATCHED! Class name: {match.group(1)}")
        print(f"  Matched text: '{match.group(0)}'")
    else:
        print(f"   No match")

# Try without MULTILINE flag
print("\n" + "="*60)
print("Trying WITHOUT re.MULTILINE flag:")
for i, pattern in enumerate(patterns):
    match = re.search(pattern, code)
    if match:
        print(f"Pattern {i} MATCHED: {match.group(1)}")
        break
