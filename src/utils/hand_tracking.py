import cv2
import mediapipe as mp
import math

class HandDetector:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        self.lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
        return self.lmList

    def fingersUp(self):
        fingers = []
        if len(self.lmList) == 0:
            return fingers

        # Determine if hand is Left or Right
        # Default to Right Hand behavior if unknown
        # Note: MediaPipe mirrors input by default for selfies, so "Left" hand appears on Right side
        # But we need to check Handedness if available. 
        # For simplicity, we'll use a heuristic based on x-coordinates for the thumb.
        
        # Thumbs up logic
        # For Right Hand: Thumb x < Index Finger x means open (if palm facing camera)
        # But this depends heavily on rotation.
        # Let's use a simpler "folded" check: Is tip closer to pinky base (MCP) than IP joint?
        
        # Better Thumb Check: Compare Tip x with IP x
        # We need to know which hand it is to know direction.
        # Assuming typical "Stop" gesture (palm to camera).
        
        # Simple heuristic:
        # If Tip x > IP x (Right side of screen), and it's a Right Hand, it's open? No.
        # Let's rely on 4 fingers + distance for grab.
        
        # 4 Fingers (Index, Middle, Ring, Pinky)
        # If Tip y < Pip y (Tip is higher), it is Open (1)
        # Else Closed (0)
        # Note: Considers y increases downward.
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return fingers

    def isGrabbing(self):
        if len(self.lmList) == 0:
            return False
            
        # Robust Grab Detection
        # 1. Check if 4 fingers (Index-Pinky) are closed
        fingers_4 = self.fingersUp() # Only returns 4 values now based on my change above? 
        # Wait, previous implementation returned 5. Better to return 5 for consistency?
        # Let's stick to the 4 fingers check for the "Fist" part, and check thumb distance.
        
        # Re-implementing simplified fingersUp inside or fixing logic?
        # Let's maintain API compatibility but fix internal logic.
        
        # Check 4 fingers (Index to Pinky)
        fingers_closed = 0
        for id in range(1, 5):
            # If Tip Y > PIP Y (Tip is lower than knuckle), it's closed
            if self.lmList[self.tipIds[id]][2] > self.lmList[self.tipIds[id] - 2][2]:
                fingers_closed += 1
        
        # Check Thumb
        # Thumb is closed if Tip is close to the base of Pinky or just generally "in"
        # Distance based heuristic is best for grabbing
        
        # Distance between Thumb Tip (4) and Index Base (5) or Pinky Base (17)
        x1, y1 = self.lmList[4][1], self.lmList[4][2]
        x2, y2 = self.lmList[17][1], self.lmList[17][2] # Pinky Base
        # x3, y3 = self.lmList[5][1], self.lmList[5][2] # Index Base
        
        length = math.hypot(x2 - x1, y2 - y1)
        
        # Normalized length check?
        # Improve reliability: If 4 fingers are down AND thumb is somewhat close
        if fingers_closed >= 4: # All 4 fingers closed
            return True
            
        return False
