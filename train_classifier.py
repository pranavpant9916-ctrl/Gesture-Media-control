import pandas as pd 
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
import joblib

print("Loading Dataset 'gesture_data.csv'...")

# Load the CSV normally
df = pd.read_csv("gesture_data.csv")

# Smart check: if the column 'label' is missing, treat the CSV as having no headers
if "label" in df.columns:
    x = df.drop(columns=["label"])
    y = df["label"]
else:
    # Reload with header=None so we use column positions instead of names
    df = pd.read_csv("gesture_data.csv", header=None)
    x = df.drop(columns=[0])
    y = df[0]

x_train , x_test , y_train , y_test = train_test_split(x,y, test_size = 0.2 , random_state = 42 )

print("Training the K-Nearest Neighbours model")
model = KNeighborsClassifier(n_neighbors=5)
model.fit(x_train , y_train)

y_pred = model.predict(x_test)
accuracy = accuracy_score(y_test, y_pred)
print("--------------------------------------------------")
print("Model Training Complete!")
print(f"Validation Accuracy: {accuracy * 100:.2f}%")
print("--------------------------------------------------")

joblib.dump(model, "gesture_model.pkl")
print("Saved trained model to 'gesture_model.pkl'!")