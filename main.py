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

# Connection lines for rendering the hand skeleton overlay
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
            self.grabbed, self.frame = self.stream.read()

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
        num_hands=1
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
        if not ret:
            continue
        
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


        # --- DRAW GLASSMORPHISM VOLUME BAR ---
        if vol_alpha > 0.01:
            vx1, vy1 = 15, 100
            vx2, vy2 = 75, 400
            vw = vx2 - vx1
            vh = vy2 - vy1
            vr = vw // 2

            if vx1 >= 0 and vy1 >= 0 and vx2 <= w and vy2 <= h:

                v_roi = temp_frame[vy1:vy2, vx1:vx2]
                v_blurred = cv2.GaussianBlur(v_roi, (45, 45), 0)
                v_milky = np.full(v_roi.shape, (255, 255, 255), dtype=np.uint8)
                v_glass = cv2.addWeighted(v_blurred, 0.65, v_milky, 0.35, 0)

                v_mask = np.zeros((vh, vw), dtype=np.uint8)
                cv2.circle(v_mask, (vr, vr), vr, 255, -1)
                cv2.circle(v_mask, (vr, vh - vr), vr, 255, -1)
                cv2.rectangle(v_mask, (0, vr), (vw, vh - vr), 255, -1)

                v_mask_3d = cv2.cvtColor(v_mask, cv2.COLOR_GRAY2BGR) / 255.0
                temp_frame[vy1:vy2, vx1:vx2] = (v_glass * v_mask_3d + v_roi * (1 - v_mask_3d)).astype(np.uint8)

                cv2.circle(temp_frame, (vx1 + vr, vy1 + vr), vr, (220, 220, 220), 1)
                cv2.circle(temp_frame, (vx1 + vr, vy2 - vr), vr, (220, 220, 220), 1)
                cv2.line(temp_frame, (vx1, vy1 + vr), (vx1, vy2 - vr), (220, 220, 220), 1)
                cv2.line(temp_frame, (vx2, vy1 + vr), (vx2, vy2 - vr), (220, 220, 220), 1)

                bar_x1, bar_y1 = vx1 + 15, vy1 + 50
                bar_x2, bar_y2 = vx2 - 15, vy2 - 50
                bar_h = bar_y2 - bar_y1

                cv2.rectangle(temp_frame, (bar_x1, bar_y1), (bar_x2, bar_y2), (180, 180, 180), 2)
                fill_height = int((current_volume / 100.0) * bar_h)

                if fill_height > 0:
                    y_start = bar_y2 - fill_height
                    y_end = bar_y2
                    overlay = temp_frame[y_start:y_end, bar_x1:bar_x2].copy()
                    cv2.rectangle(overlay, (0, 0), (bar_x2 - bar_x1, fill_height), (255, 150, 50), -1)
                    cv2.addWeighted(overlay, 0.6, temp_frame[y_start:y_end, bar_x1:bar_x2], 0.4, 0, temp_frame[y_start:y_end, bar_x1:bar_x2])

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                thickness = 2

                vol_text = f"{current_volume}%"
                ts_vol, _ = cv2.getTextSize(vol_text, font, font_scale, thickness)
                t_x = vx1 + (vw - ts_vol[0]) // 2
                t_y = vy1 + 30
                cv2.putText(temp_frame, vol_text, (t_x, t_y), font, font_scale, (0, 0, 0), thickness + 2)
                cv2.putText(temp_frame, vol_text, (t_x, t_y), font, font_scale, (255, 255, 255), thickness)

                f_roi = frame[vy1:vy2, vx1:vx2]
                t_roi = temp_frame[vy1:vy2, vx1:vx2]
                frame[vy1:vy2, vx1:vx2] = cv2.addWeighted(t_roi, vol_alpha, f_roi, 1.0 - vol_alpha, 0)


        # --- GLASSMORPHISM HUD ---
        if hud_alpha > 0.01:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            thickness = 2

            text_size, _ = cv2.getTextSize(hud_message, font, font_scale, thickness)
            padding_x, padding_y = 30, 15
            pill_w = text_size[0] + padding_x * 2
            pill_h = text_size[1] + padding_y * 2


            cx, cy = w // 2, h - 70 + int(hud_y_offset)
            x1 = cx - pill_w // 2
            y1 = cy - pill_h // 2
            x2 = x1 + pill_w
            y2 = y1 + pill_h

            if x1 >= 0 and y1 >= 0 and x2 <= w and y2 <= h:

                roi = temp_frame[y1:y2, x1:x2].copy()
                blurred_roi = cv2.GaussianBlur(roi, (45, 45), 0)
                milky = np.full(roi.shape, (255, 255, 255), dtype=np.uint8)
                glass = cv2.addWeighted(blurred_roi, 0.65, milky, 0.35, 0)

                mask = np.zeros((pill_h, pill_w), dtype=np.uint8)
                r = pill_h // 2
                cv2.circle(mask, (r, r), r, 255, -1)
                cv2.circle(mask, (pill_w - r, r), r, 255, -1)
                cv2.rectangle(mask, (r, 0), (pill_w - r, pill_h), 255, -1)

                mask_3d = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
                temp_frame[y1:y2, x1:x2] = (glass * mask_3d + roi * (1 - mask_3d)).astype(np.uint8)

                cv2.circle(temp_frame, (x1 + r, y1 + r), r, (220, 220, 220), 1)
                cv2.circle(temp_frame, (x2 - r, y1 + r), r, (220, 220, 220), 1)
                cv2.line(temp_frame, (x1 + r, y1), (x2 - r, y1), (220, 220, 220), 1)
                cv2.line(temp_frame, (x1 + r, y2), (x2 - r, y2), (220, 220, 220), 1)

                text_x, text_y = cx - text_size[0] // 2, cy + text_size[1] // 2
                cv2.putText(temp_frame, hud_message, (text_x, text_y), font, font_scale, (0, 0, 0), thickness + 2)
                cv2.putText(temp_frame, hud_message, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)

                f_roi = frame[y1:y2, x1:x2]
                t_roi = temp_frame[y1:y2, x1:x2]
                frame[y1:y2, x1:x2] = cv2.addWeighted(t_roi, hud_alpha, f_roi, 1.0 - hud_alpha, 0)

       
        # --- STATUS DASHBOARD ---
        dx1, dy1 = w - 245, 15
        dx2, dy2 = w - 15, 115
        dw = dx2 - dx1
        dh = dy2 - dy1
        dr = 10
        if dx1 >= 0 and dy1 >= 0 and dx2 <= w and dy2 <= h:
            d_roi = frame[dy1:dy2, dx1:dx2].copy()
            d_blurred = cv2.GaussianBlur(d_roi, (35, 35), 0)
            d_milky = np.full(d_roi.shape, (255, 255, 255), dtype=np.uint8)
            d_glass = cv2.addWeighted(d_blurred, 0.70, d_milky, 0.30, 0)

            d_mask = np.zeros((dh, dw), dtype=np.uint8)
            cv2.rectangle(d_mask, (0, dr), (dw, dh - dr), 255, -1)
            cv2.rectangle(d_mask, (dr, 0), (dw - dr, dh), 255, -1)
            cv2.circle(d_mask, (dr, dr), dr, 255, -1)
            cv2.circle(d_mask, (dw - dr, dr), dr, 255, -1)
            cv2.circle(d_mask, (dr, dh - dr), dr, 255, -1)
            cv2.circle(d_mask, (dw - dr, dh - dr), dr, 255, -1)

            d_mask_3d = cv2.cvtColor(d_mask, cv2.COLOR_GRAY2BGR) / 255.0
            frame[dy1:dy2, dx1:dx2] = (d_glass * d_mask_3d + d_roi * (1 - d_mask_3d)).astype(np.uint8)

            d_font = cv2.FONT_HERSHEY_SIMPLEX

            cv2.putText(frame, "SYSTEM STATUS", (dx1 + 15, dy1 + 25), d_font, 0.45, (0, 0, 0), 2)
            cv2.putText(frame, "SYSTEM STATUS", (dx1 + 15, dy1 + 25), d_font, 0.45, (255, 255, 255), 1)
            cv2.line(frame, (dx1 + 15, dy1 + 32), (dx2 - 15, dy1 + 32), (200, 200, 200), 1)

            if result.hand_landmarks:
                t_txt, t_col = "ACTIVE", (0, 255, 0)
            else:
                t_txt, t_col = "SEARCHING", (50, 50, 255)

            cv2.putText(frame, "Tracking:", (dx1 + 15, dy1 + 55), d_font, 0.4, (0, 0, 0), 2)
            cv2.putText(frame, "Tracking:", (dx1 + 15, dy1 + 55), d_font, 0.4, (220, 220, 220), 1)
            cv2.putText(frame, t_txt, (dx1 + 85, dy1 + 55), d_font, 0.4, (0, 0, 0), 2)
            cv2.putText(frame, t_txt, (dx1 + 85, dy1 + 55), d_font, 0.4, t_col, 1)

            v_txt, v_col = ("ACTIVE", (0, 255, 255)) if volume_control_active else ("IDLE", (200, 200, 200))
            cv2.putText(frame, "L-Hand:", (dx1 + 15, dy1 + 75), d_font, 0.4, (0, 0, 0), 2)
            cv2.putText(frame, "L-Hand:", (dx1 + 15, dy1 + 75), d_font, 0.4, (220, 220, 220), 1)
            cv2.putText(frame, v_txt, (dx1 + 85, dy1 + 75), d_font, 0.4, (0, 0, 0), 2)
            cv2.putText(frame, v_txt, (dx1 + 85, dy1 + 75), d_font, 0.4, v_col, 1)

            if palm_counter > 0:
                m_txt, m_col = f"PALM ({palm_counter}/5)", (0, 165, 255)
            else:
                m_txt, m_col = "IDLE", (200, 200, 200)

            cv2.putText(frame, "R-Hand:", (dx1 + 15, dy1 + 95), d_font, 0.4, (0, 0, 0), 2)
            cv2.putText(frame, "R-Hand:", (dx1 + 15, dy1 + 95), d_font, 0.4, (220, 220, 220), 1)
            cv2.putText(frame, m_txt, (dx1 + 85, dy1 + 95), d_font, 0.4, (0, 0, 0), 2)
            cv2.putText(frame, m_txt, (dx1 + 85, dy1 + 95), d_font, 0.4, m_col, 1)

        cv2.imshow('Camera Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cmd_queue.put((None, ()))
    detector.close()
    cap.release() 
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()