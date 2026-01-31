import math
import random

# Standard Dartboard Segments starting from Top (12 o'clock) and moving clockwise
SEGMENTS = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]

def get_score_from_coords(x, y, center_x, center_y, board_radius, vertical_scale=1.0, treble_scale=0.61, double_scale=0.953, outer_double_scale=1.0, inner_bull_scale=0.0374, bull_scale=0.0935, calibration_angle=0.0, ellipse_angle=0.0):
    """
    Calculates the dart score based on pixel coordinates.
    
    Args:
        x, y: Pixel coordinates of the dart.
        center_x, center_y: Pixel coordinates of the board center (bullseye).
        board_radius: Pixel radius of the board (from center to outside edge of double ring).
        vertical_scale: Aspect ratio correction (height/width). < 1.0 for angled views.
        treble_scale: Normalized radius of the treble ring center (default ~0.61).
        double_scale: Normalized radius of the inner double ring edge (default ~0.953).
        outer_double_scale: Normalized radius of the outer double ring edge (default ~1.0).
        inner_bull_scale: Normalized radius of the inner bull edge (default ~0.0374).
        bull_scale: Normalized radius of the outer bull edge (default ~0.0935).
        calibration_angle: Rotation of the board in degrees (counter-clockwise).
        ellipse_angle: Rotation of the board shape (ellipse) in degrees (clockwise).
    """
    # 1. Translate to center
    dx = x - center_x
    dy = y - center_y
    
    # 2. Rotate to align ellipse axes with X/Y (remove camera roll/ellipse rotation)
    rad_ellipse = math.radians(-ellipse_angle)
    rx = dx * math.cos(rad_ellipse) - dy * math.sin(rad_ellipse)
    ry = dx * math.sin(rad_ellipse) + dy * math.cos(rad_ellipse)
    
    # 3. Apply vertical scale (un-squash) & Calculate distance
    ry = ry / vertical_scale
    distance = math.sqrt(rx**2 + ry**2)
    
    # Normalize distance (0.0 to 1.0 relative to board radius)
    # If distance is greater than radius, it's a miss (or outside scoring area)
    norm_dist = distance / board_radius
    
    # 2. Determine Ring (based on standard dartboard measurements)
    # Ratios relative to the outer edge of the double ring (170mm):
    # Double Bull: 6.35mm / 170mm = 0.0374
    # Single Bull: 15.9mm / 170mm = 0.0935
    # Treble Ring: Width is approx 10mm/170mm = 0.059.
    # Double Ring: 162mm to 170mm -> 0.953 to 1.0
    
    if norm_dist <= inner_bull_scale:
        return "50"
    if norm_dist <= bull_scale:
        return "25"
    
    multiplier = "S" # Default Single
    
    # Treble range based on adjustable scale +/- half width (~0.03)
    treble_half_width = 0.03
    if (treble_scale - treble_half_width) <= norm_dist <= (treble_scale + treble_half_width):
        multiplier = "T"
    elif double_scale <= norm_dist <= outer_double_scale:
        multiplier = "D"
    elif norm_dist > outer_double_scale:
        return "MISS"
        
    # 3. Determine Angle and Segment
    # atan2 returns angle in radians (-pi to pi). 
    # In image coords (y down), 0 is right, pi/2 is down, -pi/2 is up.
    angle_rad = math.atan2(ry, rx)
    angle_deg = math.degrees(angle_rad)
    
    # Adjust angle so 0 is at the top (12 o'clock) and increases clockwise
    # Current: Right=0, Down=90, Left=180, Up=-90
    # Target: Up=0, Right=90, Down=180, Left=270
    corrected_angle = (angle_deg + 90 - calibration_angle) % 360
    
    # Each segment is 18 degrees (360 / 20)
    # The 20 segment is centered at 0, so it spans -9 to +9 degrees.
    segment_index = int(((corrected_angle + 9) % 360) / 18)
    score_val = SEGMENTS[segment_index]
    
    if multiplier == "S":
        return str(score_val)
    else:
        return f"{multiplier}{score_val}"

def get_coords_from_score(score_str):
    """Generates normalized (x, y) coordinates for a given score string."""
    s = str(score_str).upper().strip()
    if s in ["MISS", "0"]:
        return None
    
    if s == "50":
        return 0.0, 0.0
    if s == "25":
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(0.04, 0.09)
        return r * math.cos(angle), r * math.sin(angle)
        
    multiplier = 1
    if s.startswith("D"):
        multiplier = 2
        s = s[1:]
    elif s.startswith("T"):
        multiplier = 3
        s = s[1:]
        
    if not s.isdigit():
        return None
    
    val = int(s)
    if val not in SEGMENTS:
        return None
        
    # Calculate angle (0 is Top/20, increasing Clockwise)
    idx = SEGMENTS.index(val)
    base_angle_deg = (idx * 18) - 90 # Convert to standard math (0=Right)
    
    angle_deg = base_angle_deg + random.uniform(-8, 8)
    rad = math.radians(angle_deg)
    
    if multiplier == 3:
        r = random.uniform(0.59, 0.63)
    elif multiplier == 2:
        r = random.uniform(0.96, 0.99)
    else:
        r = random.uniform(0.15, 0.55) if random.random() < 0.5 else random.uniform(0.66, 0.93)
            
    return r * math.cos(rad), r * math.sin(rad)