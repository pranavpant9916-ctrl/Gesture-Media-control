def checkFingersExtension(hand_landmarks):
    #checks if the fingers are extended or not based on the landmarks
    #returns a list of booleans indicating the extension status of each finger (thumb,
    
    finger_tips=[8,12,16,20]
    
    finger_pips=[6,10,14,18]
    
    extended_fingers=[] #initialize an empty list to store the extension status of each finger
    
    # Loop through each finger's tip and pip landmarks to determine if the finger is extended
    for tip_idx,pip_idx in zip(finger_tips,finger_pips):
        tip= hand_landmarks[tip_idx]
        pip= hand_landmarks[pip_idx]
       
    # Y decreseS as we move up the screen
    
        is_open = tip.y < pip.y 
        #if the tip's y is higher than pip's y, the finger is considered extended (open)
        extended_fingers.append(is_open)
    
    
    return extended_fingers
    
    
    
def classify_gesture(hand_landmarks , hand_label):
    # Classifies the hand posture into a semantic gesture: "Open Palm", "Fist", "Thumbs Up", or "None"
    #hand_label is either "Left" or "Right"
    
    fingers = checkFingersExtension(hand_landmarks)
    
    thumb_tip = hand_landmarks[4]
    thumb_base = hand_landmarks[2]
    
    if hand_label == "Right":
        thumb_open = thumb_tip.x > thumb_base.x
    else:
        thumb_open = thumb_tip.x < thumb_base.x
        
    if thumb_open and fingers == [True, True, True, True]:
        return "Open Palm"
    
    elif not thumb_open and fingers == [False, False, False, False]: 
        return "Fist"
    
    elif thumb_open and fingers == [False, False, False, False]:
        return "Thumbs Up"
    
    return "None"

