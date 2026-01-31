import cv2
import math
import numpy as np
from scoring_logic import get_score_from_coords

# Global variables
center_point = None
board_radius = None
background_frame = None
last_score = ""
last_click = None
vertical_scale = 1.0
treble_scale = 0.61
double_scale = 0.953
outer_double_scale = 1.0
inner_bull_scale = 0.0374
bull_scale = 0.0935
calibration_angle = 0.0
ellipse_angle = 0.0
dragging = None  # 'CENTER' or 'RADIUS'
show_threshold = False # Debug view

def auto_detect_board(frame):
    """
    Automatically detects the dartboard using edge detection and ellipse fitting.
    Returns (center_point, radius, vertical_scale, angle) or (None, None, None, None).
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Blur to reduce noise (heavier blur helps ignore internal wire details)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    
    # Adaptive Thresholding - robust against lighting
    # Block size 11, C=2 are standard starting points
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Morphological operations to clean up noise and close gaps
    kernel = np.ones((3,3), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Find contours (RETR_LIST to get all contours, not just external)
    contours, _ = cv2.findContours(processed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    best_ellipse = None
    max_score = 0
    
    height, width = frame.shape[:2]
    center_frame_x, center_frame_y = width // 2, height // 2
    
    for cnt in contours:
        # Need at least 5 points to fit an ellipse
        if len(cnt) < 5:
            continue
            
        area = cv2.contourArea(cnt)
        # Filter small noise and massive contours (like the whole frame)
        if area < 5000 or area > (width * height * 0.95): 
            continue
            
        # Fit ellipse
        ellipse = cv2.fitEllipse(cnt)
        (x, y), (d1, d2), angle = ellipse
        
        # Aspect ratio check (dartboard shouldn't be too flattened)
        major_axis = max(d1, d2)
        minor_axis = min(d1, d2)
        
        if major_axis == 0: continue
        aspect_ratio = minor_axis / major_axis
        
        if aspect_ratio < 0.4: # Too skewed to be a board
            continue
            
        # Check shape similarity (Perimeter check)
        perimeter = cv2.arcLength(cnt, True)
        # Ramanujan approximation for ellipse perimeter
        a, b = major_axis/2, minor_axis/2
        ellipse_perimeter = math.pi * (3*(a+b) - math.sqrt((3*a + b) * (a + 3*b)))
        
        if ellipse_perimeter == 0: continue
        
        # Error metric: how close is the contour perimeter to the fitted ellipse perimeter?
        perimeter_error = abs(perimeter - ellipse_perimeter) / ellipse_perimeter
        
        # Dartboards are fairly smooth. Wires might make it jagged, but > 0.2 is likely noise.
        if perimeter_error > 0.2: 
            continue

        # Score: Prefer larger areas, but penalize if far from center
        dist_from_center = math.sqrt((x - center_frame_x)**2 + (y - center_frame_y)**2)
        score = area / (1.0 + dist_from_center * 0.1)
        
        if score > max_score:
            max_score = score
            best_ellipse = ellipse
            
    if best_ellipse:
        (x, y), (d1, d2), angle = best_ellipse
        # d1 and d2 are the axes lengths (diameters).
        # We assume the wider dimension is the true width (un-squashed diameter).
        radius = max(d1, d2) / 2
        
        # Vertical scale is the ratio of height to width
        v_scale = min(d1, d2) / max(d1, d2)
        
        return (int(x), int(y)), radius, v_scale, angle
        
    return None, None, None, None

def mouse_callback(event, x, y, flags, param):
    global center_point, board_radius, last_score, last_click, vertical_scale, dragging, treble_scale, double_scale, outer_double_scale, inner_bull_scale, bull_scale, calibration_angle, ellipse_angle, show_threshold

    if event == cv2.EVENT_LBUTTONDOWN:
        # Check for drag start if calibration is active
        if center_point is not None:
            # Check distance to center
            dist_center = np.sqrt((x - center_point[0])**2 + (y - center_point[1])**2)
            if dist_center < 20:
                dragging = 'CENTER'
                return

            if board_radius is not None:
                # Check distance to ellipse edge (using transformed coordinates)
                dx = x - center_point[0]
                dy = y - center_point[1]
                rad = math.radians(-ellipse_angle)
                rx = dx * math.cos(rad) - dy * math.sin(rad)
                ry = dx * math.sin(rad) + dy * math.cos(rad)
                dist_transformed = math.sqrt(rx**2 + (ry/vertical_scale)**2)
                
                if abs(dist_transformed - board_radius) < 20:
                    dragging = 'RADIUS'
                    return

        # If not dragging, proceed with setup steps
        if center_point is None:
            center_point = (x, y)
            print(f"Center set to: {center_point}")
        elif board_radius is None:
            # Calculate radius from center to this point (outer edge of double)
            dx = x - center_point[0]
            dy = y - center_point[1]
            rad = math.radians(-ellipse_angle)
            rx = dx * math.cos(rad) - dy * math.sin(rad)
            ry = dx * math.sin(rad) + dy * math.cos(rad)
            board_radius = math.sqrt(rx**2 + (ry/vertical_scale)**2)
            print(f"Radius set to: {board_radius:.2f}")
        else:
            # Testing mode
            score = get_score_from_coords(x, y, center_point[0], center_point[1], board_radius, 
                                        vertical_scale=vertical_scale, treble_scale=treble_scale, 
                                        double_scale=double_scale, outer_double_scale=outer_double_scale,
                                        inner_bull_scale=inner_bull_scale, bull_scale=bull_scale,
                                        calibration_angle=calibration_angle, ellipse_angle=ellipse_angle)
            last_score = score
            last_click = (x, y)
            print(f"Clicked at ({x}, {y}) -> Score: {score}")

    elif event == cv2.EVENT_MOUSEMOVE:
        if dragging == 'CENTER':
            center_point = (x, y)
        elif dragging == 'RADIUS' and center_point is not None:
            dx = x - center_point[0]
            dy = y - center_point[1]
            rad = math.radians(-ellipse_angle)
            rx = dx * math.cos(rad) - dy * math.sin(rad)
            ry = dx * math.sin(rad) + dy * math.cos(rad)
            board_radius = math.sqrt(rx**2 + (ry/vertical_scale)**2)

    elif event == cv2.EVENT_LBUTTONUP:
        dragging = None

def main():
    global center_point, board_radius, background_frame, vertical_scale, dragging, treble_scale, double_scale, outer_double_scale, inner_bull_scale, bull_scale, calibration_angle, ellipse_angle, show_threshold

    # Initialize Camera (0 is usually default, 1 might be DroidCam if 0 is integrated)
    # If DroidCam is running, it usually appears as a webcam device.
    cap = cv2.VideoCapture(0)
    
    # Request 720p
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("Error: Could not open video source. Try changing the index in cv2.VideoCapture(0).")
        return

    cv2.namedWindow("Debug Camera")
    cv2.setMouseCallback("Debug Camera", mouse_callback)

    print("--- Darts Debug Camera ---")
    print("Step 1: Click the exact CENTER of the Bullseye.")
    print("Step 2: Click the OUTER EDGE of the Double Ring (at the 3 o'clock position / Right side).")
    print("Step 3: Click anywhere on the board to verify the calculated score.")
    print("        (You can drag the Center or Ring to adjust)")
    print("Keys:")
    print("  'b': Capture Background (for dart detection testing)")
    print("  'a': Auto-detect board (Experimental)")
    print("  '[' / ']': Vertical Scale (Squish)")
    print("  '-' / '=': Treble Ring Size")
    print("  '1' / '2': Inner Bull (50)")
    print("  '3' / '4': Outer Bull (25)")
    print("  '5' / '6': Inner Double")
    print("  '7' / '8': Outer Double")
    print("  '9' / '0': Rotate Ellipse")
    print("  ',' / '.': Rotate Board")
    print("  't': Toggle Threshold View (Debug)")
    print("  'c': Clear Calibration")
    print("  'q': Quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display_frame = frame.copy()

        if show_threshold:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY_INV, 11, 2)
            cv2.imshow("Debug Camera", thresh)
        else:

            # 1. Background Subtraction Visualization
            if background_frame is not None:
                # Convert to gray for diffing
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray_bg = cv2.cvtColor(background_frame, cv2.COLOR_BGR2GRAY)
                
                # Calculate absolute difference
                diff = cv2.absdiff(gray_bg, gray_frame)
                
                # Threshold to remove noise (adjust 30 if needed)
                _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
                
                # Find contours (potential darts)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for cnt in contours:
                    if cv2.contourArea(cnt) > 50: # Filter small noise
                        # Draw the actual shape of the detected object
                        cv2.drawContours(display_frame, [cnt], -1, (0, 255, 0), 2)
                        
                        # Calculate score if calibrated
                        if center_point and board_radius:
                            # Use Centroid (Center of Mass) instead of Bounding Box center
                            M = cv2.moments(cnt)
                            if M["m00"] != 0:
                                dart_x = int(M["m10"] / M["m00"])
                                dart_y = int(M["m01"] / M["m00"])
                            else:
                                x, y, w, h = cv2.boundingRect(cnt)
                                dart_x = x + w // 2
                                dart_y = y + h // 2

                            # Draw the detection point
                            cv2.circle(display_frame, (dart_x, dart_y), 4, (0, 0, 255), -1)

                            score = get_score_from_coords(dart_x, dart_y, center_point[0], center_point[1], board_radius, 
                                                        vertical_scale=vertical_scale, treble_scale=treble_scale, 
                                                        double_scale=double_scale, outer_double_scale=outer_double_scale,
                                                        inner_bull_scale=inner_bull_scale, bull_scale=bull_scale,
                                                        calibration_angle=calibration_angle, ellipse_angle=ellipse_angle)
                            cv2.putText(display_frame, str(score), (dart_x, dart_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

                cv2.putText(display_frame, "BG Subtraction Active - Throw Dart to Test", (20, 140), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # 2. On-Screen Instructions
            if center_point is None:
                cv2.putText(display_frame, "STEP 1: Click CENTER of Bullseye", (20, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            elif board_radius is None:
                cv2.putText(display_frame, "STEP 2: Click Double Ring (Right Side)", (20, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            else:
                cv2.putText(display_frame, "Test Mode: Click to check score", (20, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(display_frame, "Drag lines | 'b': BG | 'a': Auto-detect", (20, 80), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                cv2.putText(display_frame, "Press 'c' to clear calibration", (20, 105), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            # 3. Draw Calibration Markers
            if center_point:
                color = (0, 0, 255) if dragging == 'CENTER' else (0, 255, 0)
                cv2.drawMarker(display_frame, center_point, color, cv2.MARKER_CROSS, 20, 2)
            
            if center_point and board_radius:
                color = (0, 0, 255) if dragging == 'RADIUS' else (0, 255, 0)
                # Draw Ellipse for outer double
                axes = (int(board_radius), int(board_radius * vertical_scale))
                cv2.ellipse(display_frame, center_point, axes, ellipse_angle, 0, 360, color, 2)
                
                # Draw Ellipse for treble
                axes_treble = (int(board_radius * treble_scale), int(board_radius * treble_scale * vertical_scale))
                cv2.ellipse(display_frame, center_point, axes_treble, ellipse_angle, 0, 360, (255, 255, 0), 1)
                
                # Draw Ellipse for Outer Double
                axes_od = (int(board_radius * outer_double_scale), int(board_radius * outer_double_scale * vertical_scale))
                cv2.ellipse(display_frame, center_point, axes_od, ellipse_angle, 0, 360, (0, 255, 0), 1)

                # Draw Ellipse for Inner Double
                axes_id = (int(board_radius * double_scale), int(board_radius * double_scale * vertical_scale))
                cv2.ellipse(display_frame, center_point, axes_id, ellipse_angle, 0, 360, (0, 255, 0), 1)

                # Draw Ellipse for Outer Bull (25)
                axes_bull = (int(board_radius * bull_scale), int(board_radius * bull_scale * vertical_scale))
                cv2.ellipse(display_frame, center_point, axes_bull, ellipse_angle, 0, 360, (0, 0, 255), 1)

                # Draw Ellipse for Inner Bull (50)
                axes_ibull = (int(board_radius * inner_bull_scale), int(board_radius * inner_bull_scale * vertical_scale))
                cv2.ellipse(display_frame, center_point, axes_ibull, ellipse_angle, 0, 360, (0, 0, 255), 1)
                
                # Draw 20 Segment Direction
                # Angle 0 (Up) + calibration_angle. 
                # Note: In image coords, Up is -90 deg. So we draw at -90 + calibration_angle.
                rad = math.radians(-90 + calibration_angle)
                # We must apply the ellipse rotation to this point as well
                # Point on un-rotated ellipse
                px = board_radius * math.cos(rad)
                py = board_radius * math.sin(rad) * vertical_scale
                # Rotate by ellipse_angle
                rad_e = math.radians(ellipse_angle)
                end_x = int(center_point[0] + px * math.cos(rad_e) - py * math.sin(rad_e))
                end_y = int(center_point[1] + px * math.sin(rad_e) + py * math.cos(rad_e))
                
                cv2.line(display_frame, center_point, (end_x, end_y), (0, 255, 255), 2)
                cv2.putText(display_frame, "20", (end_x, end_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # Stats
                stats = f"Scale:{vertical_scale:.2f} | Trb:{treble_scale:.2f} | Dbl:{double_scale:.2f}-{outer_double_scale:.2f} | Bull:{inner_bull_scale:.3f}-{bull_scale:.3f}"
                cv2.putText(display_frame, stats, (20, 170), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # 4. Draw Last Test Click
            if last_click:
                cv2.circle(display_frame, last_click, 5, (255, 0, 255), -1)
                cv2.putText(display_frame, f"Score: {last_score}", (last_click[0]+10, last_click[1]), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

            cv2.imshow("Debug Camera", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            center_point = None
            board_radius = None
            background_frame = None
            print("Calibration cleared.")
        elif key == ord('b'):
            background_frame = frame.copy()
            print("Background captured.")
        elif key == ord(']'):
            vertical_scale += 0.01
        elif key == ord('['):
            vertical_scale = max(0.1, vertical_scale - 0.01)
        elif key == ord('='):
            treble_scale += 0.01
        elif key == ord('-'):
            treble_scale -= 0.01
        elif key == ord('1'):
            inner_bull_scale = max(0.005, inner_bull_scale - 0.002)
        elif key == ord('2'):
            inner_bull_scale += 0.002
        elif key == ord('3'):
            bull_scale = max(inner_bull_scale, bull_scale - 0.002)
        elif key == ord('4'):
            bull_scale += 0.002
        elif key == ord('5'):
            double_scale = max(0.01, double_scale - 0.005)
        elif key == ord('6'):
            double_scale = min(outer_double_scale, double_scale + 0.005)
        elif key == ord('7'):
            outer_double_scale = max(double_scale, outer_double_scale - 0.005)
        elif key == ord('8'):
            outer_double_scale += 0.005
        elif key == ord('.'):
            calibration_angle += 1.0
        elif key == ord(','):
            calibration_angle -= 1.0
        elif key == ord('t'):
            show_threshold = not show_threshold
        elif key == ord('0'):
            ellipse_angle += 1.0
        elif key == ord('9'):
            ellipse_angle -= 1.0
        elif key == ord('a'):
            c, r, v, a = auto_detect_board(frame)
            if c is not None:
                center_point = c
                board_radius = r
                vertical_scale = v
                ellipse_angle = a
                
                # Reset ring scales to standard dartboard ratios
                treble_scale = 0.606      # 103/170 (Center of treble)
                double_scale = 0.953      # 162/170 (Inner double)
                outer_double_scale = 1.0  # 170/170 (Outer double)
                inner_bull_scale = 0.0374 # 6.35/170
                bull_scale = 0.0935       # 15.9/170
                
                print(f"Auto-detected: Center={c}, Radius={r:.1f}, Scale={v:.2f}, Angle={a:.1f}")
                print("Ring areas reset to standard dartboard dimensions.")
            else:
                print("Auto-detection failed. Try adjusting lighting or camera angle.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()