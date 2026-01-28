import cv2
import time
import os
import numpy as np
from utils.hand_tracking import HandDetector
from utils.network import FileSender

def create_dummy_image(path):
    # Create a nice gradient image if it doesn't exist
    height, width = 480, 640
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height):
        img[i, :, 0] = int(i / height * 255) # Blue gradient
        img[i, :, 1] = 100
        img[i, :, 2] = 255 - int(i / height * 255) # Red gradient
    
    cv2.putText(img, "Sample Image to Transfer", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.imwrite(path, img)

def main():
    # Setup
    host_ip = input("Enter Receiver IP (e.g., 192.168.1.X or localhost): ")
    sender = FileSender(host_ip)

    # Assets
    file_to_send = "image_to_share.png"
    if not os.path.exists(file_to_send):
        print("Creating sample image...")
        create_dummy_image(file_to_send)
    
    # Vision
    cap = cv2.VideoCapture(0)
    detector = HandDetector(detectionCon=0.7, maxHands=1)
    
    # State
    sent_flag = False
    status_msg = "Show Open Hand -> Fist to Grab"
    last_gesture_time = time.time()

    # Load the image to show in a separate window
    img_display = cv2.imread(file_to_send)
    cv2.imshow("File to Share", img_display)

    print("Sender started. Press 'q' to quit.")

    while True:
        success, img = cap.read()
        if not success:
            break

        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)
        
        is_grabbing = False
        if len(lmList) != 0:
            is_grabbing = detector.isGrabbing()
            
            # Logic: If grabbing and not sent yet
            if is_grabbing and not sent_flag:
                # Add a small delay/confirmation to avoid accidental triggers
                if time.time() - last_gesture_time > 1.0:
                    status_msg = "GRAB DETECTED! Sending file..."
                    print(status_msg)
                    
                    # Visual feedback
                    cv2.putText(img, "GRABBED!", (50, 100), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)
                    cv2.imshow("Sender Camera", img)
                    cv2.waitKey(100) # Force update

                    # Send
                    if sender.send_file(file_to_send):
                        sent_flag = True
                        status_msg = "File Sent! Release to reset."
                    else:
                        status_msg = "Send Failed. Try again."
                        last_gesture_time = time.time() # Reset debounce
            
            elif not is_grabbing and sent_flag:
                # Reset if hand opens
                sent_flag = False
                status_msg = "Ready. Grab to send again."
                last_gesture_time = time.time()

        # UI Overlay
        cv2.putText(img, status_msg, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        cv2.imshow("Sender Camera", img)
        
        # Keep the file window open
        if cv2.getWindowProperty("File to Share", cv2.WND_PROP_VISIBLE) < 1:
            cv2.imshow("File to Share", img_display)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    sender.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
