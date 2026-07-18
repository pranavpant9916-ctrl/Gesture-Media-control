from utils import calculate_distance

def two_hand_gesture(h1,h2):
    h1_palm ,h1_wrist = h1[9],h1[0]
    h2_palm ,h2_wrist = h2[9],h2[0]
    
    wrist_distance = calculate_distance(h1_wrist,h2_wrist)
    index_distance = calculate_distance(h1[8],h2[8])
    
    if wrist_distance < 0.25 and index_distance > 0.35:
        return "X_SHAPE"
    
    h1_tips = [h1[8], h1[12], h1[16]]
    h2_tips = [h2[8], h2[12], h2[16]]
    dist_h1_to_h2 = min([calculate_distance(tip, h2_palm) for tip in h1_tips])
    dist_h2_to_h1 = min([calculate_distance(tip, h1_palm) for tip in h2_tips])
    if (dist_h1_to_h2 < 0.20 or dist_h2_to_h1 < 0.20) and wrist_distance > 0.15:
        return "T_SHAPE"
    return None
