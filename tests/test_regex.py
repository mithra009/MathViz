import re

code = """from manim import *

class ThreeDSphereVisualization(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes()
        sphere = Sphere(radius=1, color=BLUE)
        self.set_camera_orientation(phi=75*DEGREES, theta=30*DEGREES)
        self.add(axes)
        self.play(Create(sphere))
        self.wait(2)
"""

patterns = [
    r'class\s+(\w+)\s*\(\s*Scene\s*\):',
    r'class\s+(\w+)\s*\(\s*ThreeDScene\s*\):',
    r'class\s+(\w+)\s*\(\s*manim\.Scene\s*\):',
    r'class\s+(\w+)\s*\(\s*manim\.ThreeDScene\s*\):',
]

print("Testing ThreeDScene detection:")
print("="*50)
print("Code to test:")
print(code)
print("="*50)

for i, pattern in enumerate(patterns):
    match = re.search(pattern, code, re.MULTILINE)
    if match:
        print(f" Pattern {i} MATCHED: {pattern}")
        print(f"  Scene name: {match.group(1)}")
        break
    else:
        print(f" Pattern {i} failed: {pattern}")
else:
    print("\n NO PATTERNS MATCHED!")
