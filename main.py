import queue
import threading
import time
from collections import deque
import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import media_controller as media
from gesture_classifier import classify_gesture
from utils import calculate_distance
import ui_renderer
import gesture_maths

CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17) 
]

class WebcamStream:
    """Runs the webcam on a separate thread to achieve 60fps without lag."""
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            try:
                self.grabbed, self.frame = self.stream.read()

                if not self.grabbed:
                    time.sleep(0.01)
            except Exception as e:
                print(f"[FATAL ERROR] Camera thread crashed: {e}")
                self.stopped = True
                break

    def read(self):
        return self.grabbed, self.frame

    def isOpened(self):
        return self.stream.isOpened()

    def release(self):
        self.stopped = True
        self.stream.release()

def command_worker(cmd_queue):
    while True:
        func, args = cmd_queue.get()
        if func is None:
            break
        func(*args)
        cmd_queue.task_done()

def main():
    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_hands=2
    )
    detector = vision.HandLandmarker.create_from_options(options)
    
    volume_control_active = False
    start_y = 0.0
    start_volume = 50
    current_volume = 50
    smoothed_volume = 50.0 
    
    x_history = deque(maxlen=15)
    last_gesture_time = 0.0
    last_volume_time = 0.0 
    hud_message = ""
    hud_message_expiry = 0.0 
    palm_counter = 0

    vol_alpha = 0.0
    hud_alpha = 0.0
    hud_y_offset = 20.0
    
    cmd_queue = queue.Queue()
    worker_thread = threading.Thread(target=command_worker, args=(cmd_queue,), daemon=True)
    worker_thread.start()
    
    print("Starting 60fps Camera Thread...")
    cap = WebcamStream(0).start()
    time.sleep(1.0)

    if not cap.isOpened():
        print("Error: Could not open Camera.")
        return
    
    print("Camera feed is working. Press 'q' to exit.")
    
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Error: Could not read frame from Camera.")
            break
        
        frame = cv2.flip(frame, 1)

        # Auto-Contrast & Brightness Correction (CLAHE) for low-light environments
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[:, :, 0])
        frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = detector.detect(mp_image)
        current_time = time.time()
        
        if result.hand_landmarks:

            if len(result.hand_landmarks) == 2:
                h1 = result.hand_landmarks[0]
                h2 = result.hand_landmarks[1]
                detected_gesture = gesture_maths.two_hand_gesture(h1, h2)

                if detected_gesture == "X_SHAPE":
                    h, w = frame.shape[:2]
                    cv2.putText(frame, "SHUTTING DOWN...", (w//2 - 150, h//2),
                                cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 255), 3)
                    cv2.imshow('Camera Feed', frame)
                    cv2.waitKey(1000)
                    break
                elif detected_gesture == "T_SHAPE":
                    if current_time - last_gesture_time > 2.0:
                        h, w = frame.shape[:2]
                        cv2.putText(frame, "APP CLOSED", (w//2 - 250, h//2),
                                    cv2.FONT_HERSHEY_DUPLEX, 1.2, (150, 200, 255), 3)
                        cv2.imshow('Camera Feed', frame)
                        cv2.waitKey(1000)
                        cmd_queue.put((media.quit_active_app, ()))
                        last_gesture_time = current_time
                        continue

            for hand_landmarks,handedness in zip(result.hand_landmarks, result.handedness):

                for start_idx, end_idx in CONNECTIONS:
                    start_pt = hand_landmarks[start_idx]
                    end_pt = hand_landmarks[end_idx]
                    start_pixel = (int(start_pt.x * w), int(start_pt.y * h))
                    end_pixel = (int(end_pt.x * w), int(end_pt.y * h))
                    cv2.line(frame, start_pixel, end_pixel, (255, 255, 0), 2)
                
                for idx, landmark in enumerate(hand_landmarks):
                    pixel = (int(landmark.x * w), int(landmark.y * h))
                    if idx == 8:
                        cv2.circle(frame, pixel, 8, (0, 0, 255), -1)
                    else:
                        cv2.circle(frame, pixel, 5, (0, 255, 0), -1)
                
                hand_label = handedness[0].category_name
                thumb_tip = hand_landmarks[4]
                index_tip = hand_landmarks[8]


                if hand_label == "Right":
                    distance = calculate_distance(thumb_tip, index_tip)
                    gesture = classify_gesture(hand_landmarks, hand_label)
                    
                    if distance < 0.05 and gesture != "Closed":
                        if not volume_control_active:
                            volume_control_active = True
                            start_y = index_tip.y
                            start_volume = current_volume
                        else:
                            delta_y = start_y - index_tip.y
                            volume_change = (delta_y / 0.3) * 50
                            target_volume = max(0, min(100, int(start_volume + volume_change)))
                            
                            alpha = 0.25
                            smoothed_volume = (alpha * target_volume) + ((1 - alpha) * smoothed_volume)
                            current_volume = round(smoothed_volume)
                            if current_time - last_volume_time > 0.10:
                                cmd_queue.put((media.set_system_volume, (current_volume,)))
                                last_volume_time = current_time
                    else:
                        volume_control_active = False


                elif hand_label == "Left":
                    volume_control_active = False
                    x_history.append(index_tip.x)
                    
                    if current_time - last_gesture_time > 1.5:
                        if len(x_history) == 15:
                            displacement = x_history[-1] - x_history[0]
                            if displacement > 0.25:
                                last_gesture_time = current_time
                                x_history.clear()
                                cmd_queue.put((media.next_track, ()))
                                hud_message = "SKIP AHEAD"
                                hud_message_expiry = current_time + 2.0
                               
                            elif displacement < -0.25:
                                last_gesture_time = current_time 
                                x_history.clear()
                                cmd_queue.put((media.previous_track, ()))
                                hud_message = "SKIP BACK"
                                hud_message_expiry = current_time + 2.0
                    
                    gesture = classify_gesture(hand_landmarks, hand_label)
                    if current_time - last_gesture_time > 1.5:
                        if gesture == "Open Palm":
                            palm_counter += 1
                            if palm_counter >= 5:
                                cmd_queue.put((media.toggle_play_pause, ()))
                                last_gesture_time = current_time
                                palm_counter = 0
                                hud_message = "PLAY / PAUSE"
                                hud_message_expiry = current_time + 2.0
                        else:
                            palm_counter = 0
            
        else:
            x_history.clear()
            volume_control_active = False
            palm_counter = 0

        target_vol_alpha = 1.0 if volume_control_active else 0.0
        vol_alpha += (target_vol_alpha - vol_alpha) * 0.15

        hud_active = (current_time < hud_message_expiry and hud_message != "")
        target_hud_alpha = 1.0 if hud_active else 0.0
        target_hud_y = 0.0 if hud_active else 20.0

        hud_alpha += (target_hud_alpha - hud_alpha) * 0.15
        hud_y_offset += (target_hud_y - hud_y_offset) * 0.15

        temp_frame = frame.copy()

                # --- MODULAR UI RENDERING ---
        frame = ui_renderer.draw_volume_bar(frame, current_volume, vol_alpha)
        frame = ui_renderer.draw_hud(frame, hud_message, hud_alpha, hud_y_offset)
        frame = ui_renderer.draw_dashboard(frame, result, volume_control_active, palm_counter)

        cv2.imshow('Camera Feed', frame)


        cv2.imshow('Camera Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cmd_queue.put((None, ()))
    detector.close()
    cap.release() 
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()