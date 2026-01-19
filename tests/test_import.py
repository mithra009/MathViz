import sys
sys.path.insert(0, r'C:\Users\mithr\Desktop\Manim\manim-image')

# Import the actual function from main.py
from main import extract_scene_name

code = """from manim import *

class RotatingSphere3D(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes()
        sphere = Sphere(radius=1, color=BLUE, checkerboard_colors=[BLUE_D, BLUE_E], resolution=(20, 20))
        self.set_camera_orientation(phi=75*DEGREES, theta=30*DEGREES)
        self.add(axes)
        self.play(Create(sphere))
        self.begin_ambient_camera_rotation(rate=0.5)
        self.wait(3)
"""

print("Testing extract_scene_name function from main.py:")
print("="*60)
result = extract_scene_name(code)
print(f"Result: {result}")
print("="*60)

if result:
    print(f" SUCCESS! Detected: {result}")
else:
    print(" FAILED! Could not detect ThreeDScene class")
