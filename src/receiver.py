import cv2
import threading
import time
import os
import queue
from utils.hand_tracking import HandDetector
from utils.network import FileReceiver

# Global state for file reception
received_queue = queue.Queue()

class ReceiverThread(threading.Thread):
    def __init__(self, port=5001):
        threading.Thread.__init__(self)
        self.receiver = FileReceiver(port=port)
        self.daemon = True

    def run(self):
        while True:
            filepath = self.receiver.accept_and_receive()
            if filepath:
                received_queue.put(filepath)

def main():
    # Setup
    port = 5001
    thread = ReceiverThread(port)
    thread.start()
    
    # Vision
    cap = cv2.VideoCapture(0)
    detector = HandDetector(detectionCon=0.7, maxHands=1)

    # State
    pending_file = None
    status_msg = "Waiting for file..."
    
    # Ensure save directory exists
    if not os.path.exists("received_files"):
        os.makedirs("received_files")

    print(f"Receiver started on port {port}. Press 'q' to quit.")

    while True:
        success, img = cap.read()
        if not success:
            break

        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)

        # Check for incoming files
        try:
            if not received_queue.empty():
                pending_file = received_queue.get_nowait()
                status_msg = "File Received in Memory! Open Hand to Drop."
                print(f"File staged: {pending_file}")
        except:
            pass

        if pending_file:
            cv2.putText(img, "FILE HELD - SHOW OPEN HAND", (10, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Gesture Logic
        if len(lmList) != 0:
            is_grabbing = detector.isGrabbing()
            is_open = not is_grabbing # Simplified for "Not Grabbing" = Open

            if pending_file and is_open:
                # "Drop" gesture detected
                status_msg = "Dropping file..."
                print("Drop detected!")
                
                # In a real scenario, we might move it from temp to final
                # For now, just 'opening' it is the satisfaction
                final_path = pending_file # already saved by FileReceiver in received_files
                
                # Visual feedback
                cv2.putText(img, "DROPPED!", (50, 100), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)
                cv2.imshow("Receiver Camera", img)
                cv2.waitKey(500)
                
                # Open the file (OS dependent, using os.startfile for Windows)
                try:
                    os.startfile(final_path)
                except AttributeError:
                    # Linux/MacOS fallback (not needed for this specific user but good practice)
                    import subprocess
                    subprocess.call(['xdg-open', final_path])

                status_msg = f"Opened {os.path.basename(final_path)}"
                pending_file = None # Reset
        
        cv2.putText(img, status_msg, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.imshow("Receiver Camera", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
