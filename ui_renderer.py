import cv2
import numpy as np

def draw_volume_bar(frame, current_volume, vol_alpha):
    if vol_alpha < 0.01:
        return frame
    
    h, w = frame.shape[:2]
    temp_frame = frame.copy()
    
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
        vol_text = f"{current_volume}%"
        ts_vol, _ = cv2.getTextSize(vol_text, font, 0.5, 2)
        t_x = vx1 + (vw - ts_vol[0]) // 2
        t_y = vy1 + 30
        cv2.putText(temp_frame, vol_text, (t_x, t_y), font, 0.5, (0, 0, 0), 4)
        cv2.putText(temp_frame, vol_text, (t_x, t_y), font, 0.5, (255, 255, 255), 2)

        f_roi = frame[vy1:vy2, vx1:vx2]
        t_roi = temp_frame[vy1:vy2, vx1:vx2]
        frame[vy1:vy2, vx1:vx2] = cv2.addWeighted(t_roi, vol_alpha, f_roi, 1.0 - vol_alpha, 0)
        
    return frame


def draw_hud(frame, hud_message, hud_alpha, hud_y_offset):
    if hud_alpha < 0.01:
        return frame
        
    h, w = frame.shape[:2]
    temp_frame = frame.copy()
    
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
        
    return frame


def draw_dashboard(frame, result, volume_control_active, palm_counter):
    h, w = frame.shape[:2]
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
        
    return frame