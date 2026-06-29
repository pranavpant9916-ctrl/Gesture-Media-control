import cv2 
import mediapipe as mp
from mediapipe.tasks import python 
from mediapipe.tasks.python import vision
import csv
import os

CONNECTIONS = [
    (0,1) , (1,2) , (2,3) , (3,4) , 
    (0,5) , (5,6) , (6,7) , (7,8) ,
    (5,9) , (9,10) , (10,11) , (11 , 12) ,
    (9,13) , (13,14) , (14,15) , (15,16) ,
    (13,17) , (17,18) , (18,19) , (19,20) ,
    (0,17)    
]

GESTURES = {
    ord('0') : "Fist" ,
    ord('1') : "Open Palm" , 
    ord('2') : "Thumbs Up"
}

def save_to_csv(label , landmarks) :
    file_path = "gesture_data.csv"
    
    wrist = landmarks[0]
    
    row  = [label]
    
    for lm in landmarks :
        row.extend(lm.x - wrist.x , lm.y - wrist.y , lm.z - wrist.z )
    
    file_exist = os.path.isfile(file_path)
    
    
    with open(file_path , 'a' , newline= "") as f:
        writer= csv.writer(f)
        
    
    if not file_exist:
        header = ["Label"]
        
        for i in range (21) :
            header.extend([f"x{i}",f"y{i}",f"z{i}"])
            
        writer.writerow(header)
        
    
    writer.writerow(row)
    


def main():
    
    base_options = python.baseOptions(model_asset_path = 'hand_landmarker.task')
    
    options = vision.HandLandmarkerOptions(
        base_options= base_options ,
        running_mode = vision.RunningMode.IMAGE,
        num_hands = 1
    )
    
    detector = vision.HandLandmarker.create_from_options(options)
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error , cannot open camera.")
        return
    
    
    print("--------------------------------------------------")
    print("DATA COLLECTOR ACTIVE.")
    print("Hold your hand in position and press:")
    print("  '0' to record FIST")
    print("  '1' to record OPEN PALM")
    print("  '2' to record THUMBS UP")
    print("Press 'q' to exit.")
    print("--------------------------------------------------")
    
    
    while True:
        
        ret, frame = cap.read()
        
        if not ret:
            break
        
        
        frame = cv2.flip(frame,1)
        
        h,w, _ = frame.shape
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame) 
        
        result = detector.detect(mp_image)
        
        if result.hand_landmarks:
            hand_found = True
            current_landmarks = result.hand_landmarks[0]
            
            
            for start_idx , end_idx in CONNECTIONS:
                
                start_pt = current_landmarks[start_idx]
                end_pt = current_landmarks[end_idx]
                
                start_pixel = (int(start_pt.x *w), int(start_pt.y*h))
                
                end_pixel = (int(end_pt.x*w), int(end_pt.y*h))
                
                cv2.line(frame , start_pixel , end_pixel , (255,255,0) ,2)
                
                
            for idx, landmark in enumerate (current_landmarks):
                pixel = (int(landmark.x*w), int(landmark.y*h))
                
                if idx == 8:
                    cv2.circle = (frame, pixel , 8 , (0, 0, 255), -1 )
                    
                else:
                    cv2.circle = (frame, pixel , 8 , (0, 255,0 ), -1 )
        
        
        cv2.putText(frame, "Record: [0] Fist | [1] Palm | [2] Thumbs Up" , (10 ,30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2) 
        
        cv2.imshow("Data Collector Feed" , frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key in GESTURES:
            if hand_found:
                label = GESTURES[key]
               
                save_to_csv(label, current_landmarks)
                print(f"[SAVED] recorded 1 sample of: {label}")
            else:
                print("[WARNING] No hand in frame! Cannot record.")
                
   
    detector.close()
    cap.release()
    cv2.destroyAllWindows()
if __name__ == "__main__":
    main()
                