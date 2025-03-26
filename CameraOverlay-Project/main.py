import cv2
import os
import time

# Ensure directories exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CAPTURED_DIR = os.path.join(BASE_DIR, "captured_images")

os.makedirs(CAPTURED_DIR, exist_ok=True)

# Load overlay images
overlay_images = [
    os.path.join(ASSETS_DIR, "car_left.png"),
    os.path.join(ASSETS_DIR, "car_right.png"),
    os.path.join(ASSETS_DIR, "car_front.png"),
    os.path.join(ASSETS_DIR, "car_rear.png"),
]
overlay_labels = ["left", "right", "front", "rear"]

# Overlay settings
OVERLAY_WIDTH = 400
OVERLAY_HEIGHT = 400
OVERLAY_X = 150
OVERLAY_Y = 100

# OpenCV camera setup with fallback to different indices
cap = None
for i in range(3):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera initialized on index {i}")
        break
else:
    print("No available camera detected! Exiting...")
    exit()

current_overlay_index = 0

def overlay_image(background, overlay, x, y):
    """ Blends a transparent overlay image (RGBA) onto a background (BGR). """
    if overlay is None or overlay.shape[2] < 4:
        print("Invalid overlay image")
        return background

    overlay_h, overlay_w = overlay.shape[:2]
    x = max(0, min(x, background.shape[1] - overlay_w))
    y = max(0, min(y, background.shape[0] - overlay_h))

    # Extract Alpha Channel
    alpha = overlay[:, :, 3] / 255.0
    alpha = alpha[:, :, None]  # Convert to correct shape

    # Blend overlay with the background
    background[y:y+overlay_h, x:x+overlay_w] = (alpha * overlay[:, :, :3] +
                                                (1 - alpha) * background[y:y+overlay_h, x:x+overlay_w]).astype("uint8")
    
    return background

def capture_image(label):
    """ Captures and saves the image. """
    ret, clean_frame = cap.read()
    if ret:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(CAPTURED_DIR, f"captured_{label}_{timestamp}.png")
        cv2.imwrite(filename, clean_frame)
        print(f"Image saved: {filename}")

while current_overlay_index < len(overlay_images):
    overlay_path = overlay_images[current_overlay_index]

    if not os.path.exists(overlay_path):
        print(f"Missing overlay file: {overlay_path}")
        current_overlay_index += 1
        continue

    overlay = cv2.imread(overlay_path, cv2.IMREAD_UNCHANGED)
    if overlay is None:
        print(f"Failed to load overlay: {overlay_path}")
        current_overlay_index += 1
        continue

    if overlay.shape[2] < 4:  # Convert to RGBA if needed
        overlay = cv2.cvtColor(overlay, cv2.COLOR_BGR2BGRA)

    # Resize overlay
    overlay_resized = cv2.resize(overlay, (OVERLAY_WIDTH, OVERLAY_HEIGHT))

    retry_count = 0
    max_retries = 5

    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"Camera feed error. Retrying... ({retry_count+1}/{max_retries})")
            time.sleep(2)
            retry_count += 1
            if retry_count >= max_retries:
                print("Camera feed not responding. Exiting...")
                cap.release()
                cv2.destroyAllWindows()
                exit()
            continue

        # Adjust overlay position within frame bounds dynamically
        overlay_x = max(0, min(OVERLAY_X, frame.shape[1] - OVERLAY_WIDTH))
        overlay_y = max(0, min(OVERLAY_Y, frame.shape[0] - OVERLAY_HEIGHT))

        # Show the overlay for guidance
        frame_with_overlay = overlay_image(frame.copy(), overlay_resized, x=overlay_x, y=overlay_y)

        # ---- Add User Guide ----
        instruction_text = f"Align the {overlay_labels[current_overlay_index]} side of the car with the frame"
        cv2.putText(frame_with_overlay, instruction_text, (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Car Inspection Camera", frame_with_overlay)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):  # Capture image
            capture_image(overlay_labels[current_overlay_index])
            current_overlay_index += 1
            break  # Restart loop for the next overlay

        elif key == ord('q'):  # Quit
            cap.release()
            cv2.destroyAllWindows()
            exit()

cap.release()
cv2.destroyAllWindows()
print("All images captured successfully!")
