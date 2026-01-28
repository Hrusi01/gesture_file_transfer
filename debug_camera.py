import cv2
import time

def test_camera(index):
    print(f"Testing camera index {index}...")
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"[-] Camera {index} failed to open.")
        return False
    
    ret, frame = cap.read()
    if ret:
        print(f"[+] Camera {index} working. Frame size: {frame.shape}")
        cv2.imshow(f"Test Camera {index}", frame)
        cv2.waitKey(2000)
        cv2.destroyAllWindows()
        return True
    else:
        print(f"[-] Camera {index} opened but failed to read frame.")
        return False
    cap.release()

print("OpenCV Version:", cv2.__version__)

# Test indices 0, 1, 2
found = False
for i in range(3):
    if test_camera(i):
        found = True
        break

if not found:
    print("\nERROR: No working camera found on indices 0-2.")
    print("Troubleshooting:")
    print("1. Check if camera is connected.")
    print("2. Check privacy settings (Windows Settings > Privacy > Camera).")
    print("3. Check if another app is using the camera.")
else:
    print("\nSUCCESS: Camera found and working.")
