# Real-Time Gesture Media Controller (macOS)
 
---

It is a real-time computer vision system that lets you control Spotify, Apple Music, Netflix, YouTube, and IINA Player using only your webcam and hand gestures.
Instead of installing heavy packages that trigger macOS security alerts, the system talks directly to your apps using native macOS scripting.

---

## Supported Apps & Commands

| Media App | Play / Pause (Palm) | Skip Ahead (Right Swipe) | Skip Back (Left Swipe) | Volume Control (Pinch & Drag) |
| :--- | :--- | :--- | :--- | :--- |
| **Spotify** | Toggle Play/Pause | Next Song | Previous Song | System Volume |
| **Apple Music** | Toggle Play/Pause | Next Song | Previous Song | System Volume |
| **YouTube (Chrome/Safari)** | Toggle Video | Skip Forward 10s | Skip Backward 10s | System Volume |
| **Netflix (Chrome/Safari)** | Toggle Video | Skip Forward 10s | Skip Backward 10s | System Volume |
| **IINA Player** | Toggle Video | Skip Forward (Arrow R) | Skip Backward (Arrow L) | System Volume |

---

## Engineering Challenges & How I Solved Them

### 1. Eliminating Volume Jitter (Signal Smoothing)
Webcam coordinates are naturally noisy due to light changes and camera resolution. If you map raw finger coordinates directly to your system volume, the audio level fluctuates rapidly (jitter). 
*   **The Math**: I implemented an **Exponential Moving Average (EMA)** filter to smooth out coordinates:
    V_{smoothed} = (alpha * V_{target}) + ((1 - alpha) * V_{previous})
*   **The Result**: Setting the smoothing factor alpha = 0.25 blends 25% of the current frame's position with 75% of the historical average, creating a fluid, lag-free slide.

### 2. Preventing "Return-Swipe" Double Triggers
A common issue in swipe-detection algorithms is that when you swipe your hand and pull it back to the center of the camera screen, the return motion triggers a second swipe in the opposite direction.
*   **The Solution**: I designed a rolling 15-frame coordinate history buffer (`deque`) combined with a **1.5-second lockout cooldown**. Once a swipe is triggered, the queue is cleared, and the system ignores any swipe inputs for 1.5 seconds, giving you plenty of time to reset your hand position safely.

### 3. Context-Aware Targeting (Focus Priority)
If you have both Spotify playing in the background and a YouTube video open in the foreground, standard media key presses can be unpredictable.
*   **The Solution**: The automation script queries macOS for the frontmost application. If you are actively looking at Chrome, Safari, or IINA, it targets the active video. If no media player is focused, it falls back to controlling your background music player.

---

## Quick Installation

### 1. Run the Setup Script
Clone the repository and run the setup script. It will automatically create your virtual environment and install dependencies:
```bash
git clone https://github.com/your-username/gesture-media-control.git
cd gesture-media-control
chmod +x setup.sh
./setup.sh