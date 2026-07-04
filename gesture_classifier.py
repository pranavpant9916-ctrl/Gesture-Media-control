import joblib 

try:
    model = joblib.load('gesture_model.pkl')

except Exception as e:
    print(f"[ERROR] Could not load gesture_model.pkl: {e}")
    model = None
    
    
def classify_gesture(landmarks , hand_label = None):
    if model is None:
        return "UNKNOWN"
    
    wrist = landmarks[0]
    
    features = []
    
    for lm in landmarks:
        features.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
        
    prediction = model.predict([features])
    
    print(f"[ML Model] Predicted: {prediction[0]}")
    
    return prediction[0]
