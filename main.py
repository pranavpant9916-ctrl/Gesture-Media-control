import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from utils import calculate_distance
from gesture_classifier import classify_gesture
from collections import deque
import time 
import media_controller as media
import queue
import threading

CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17) 
]


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
        num_hands=1
    )
    detector = vision.HandLandmarker.create_from_options(options)
    
    volume_control_active = False
    start_y = 0.0
    start_volume = 50
    current_volume = 50
    smoothed_volume = 50.0 
    
    x_history = deque(maxlen=15)
    last_swipe_time = 0.0
    last_toggle_time = 0.0
    last_volume_time = 0.0 
    hud_message = ""
    hud_message_expiry = 0.0 
    cmd_queue = queue.Queue()
    worker_thread = threading.Thread(target=command_worker, args=(cmd_queue,), daemon=True)
    worker_thread.start()
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open Camera.")
        return
    
    print("Camera feed is working. Press 'q' to exit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break
        
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = detector.detect(mp_image)
        current_time = time.time()
        
        if result.hand_landmarks:
            for hand_landmarks, handedness in zip(result.hand_landmarks, result.handedness):
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
                
                x_history.append(index_tip.x)
                swipe_event = None
                
                if current_time - last_swipe_time > 1.5:
                   if len(x_history) == 15:
                       displacement = x_history[-1] - x_history[0]
                       if displacement > 0.25:
                          swipe_event = "Swipe Right"
                          last_swipe_time = current_time
                          x_history.clear()
                                                    
                          cmd_queue.put((media.next_track, ()))
                          hud_message = "⏭️ SKIP AHEAD"
                          hud_message_expiry = current_time + 2.0
                          
                          print(f"[{hand_label} Hand] Skip Ahead triggered.")
                          
                       elif displacement < -0.25:
                          swipe_event = "Swipe Left"
                          last_swipe_time = current_time 
                          x_history.clear()
                          
                          cmd_queue.put((media.previous_track, ()))
                          hud_message = "⏮️ SKIP BACK"
                          hud_message_expiry = current_time + 2.0
                          
                          print(f"[{hand_label} Hand] Skip Back triggered.")
                
                distance = calculate_distance(thumb_tip, index_tip)
                
                if distance < 0.05:
                    if not volume_control_active:
                        volume_control_active = True
                        start_y = index_tip.y
                        start_volume = current_volume
                        print(f"[{hand_label} Hand] 🔒 Volume Locked! Start Y: {start_y:.2f} | Vol: {start_volume}%")
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
                        
                        bar_length = 10
                        filled_blocks = int(current_volume / 10)
                        empty_blocks = bar_length - filled_blocks
                        volume_bar = "🁢" * filled_blocks + "🀆" * empty_blocks
                        print(f"[{hand_label} Hand] Volume Control | [{volume_bar}] {current_volume}%")
                else:
                    volume_control_active = False
                    gesture = classify_gesture(hand_landmarks, hand_label)
                    
                    if gesture == "Thumbs Up" and (current_time - last_toggle_time > 2.0):
                        cmd_queue.put((media.toggle_play_pause, ()))
                        last_toggle_time = current_time
                        hud_message = "⏯️ PLAY / PAUSE"
                        hud_message_expiry = current_time + 2.0
                        print(f"[{hand_label} Hand] Play/Pause toggled.")
            
        else:
            x_history.clear()
            volume_control_active = False
           
        if volume_control_active:
            cv2.rectangle(frame, (30, 150), (60, 350), (100, 100, 100), 2)
            filled_height = int(current_volume * 2)
            cv2.rectangle(frame, (30, 350 - filled_height), (60, 350), (255, 120, 0), -1)
            cv2.putText(frame, f"Vol: {current_volume}%", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, "[LOCKED]", (20, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        if current_time < hud_message_expiry:
            overlay = frame.copy()
            cv2.rectangle(overlay, (w // 2 - 140, h - 70), (w // 2 + 140, h - 30), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            cv2.putText(frame, hud_message, (w // 2 - 110, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
       
        cv2.imshow('Camera Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cmd_queue.put((None, ()))
    detector.close()
    cap.release() 
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()