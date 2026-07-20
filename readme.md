# Gesture Media Controller
 
---

It is a real-time computer vision system that lets you control Spotify, Apple Music, Netflix, YouTube, and IINA Player using only your webcam and hand gestures.
Built with cross-platform support in mind, the system uses native OS scripting (`ctypes` for Windows, `osascript` for macOS, and `playerctl` for Linux) to bypass heavy third-party dependencies and security alerts.

---

## Supported Apps & Commands

### Single-Hand Controls
| Media App | Play / Pause (Palm) | Skip Ahead (Right Swipe) | Skip Back (Left Swipe) | Volume Control (Pinch & Drag) |
| :--- | :--- | :--- | :--- | :--- |
| **Spotify** | Toggle Play/Pause | Next Song | Previous Song | System Volume |
| **Apple Music** | Toggle Play/Pause | Next Song | Previous Song | System Volume |
| **YouTube (Web)** | Toggle Video | Skip Forward 10s | Skip Backward 10s | System Volume |
| **Netflix (Web)** | Toggle Video | Skip Forward 10s | Skip Backward 10s | System Volume |
| **IINA Player** | Toggle Video | Skip Forward (Arrow R) | Skip Backward (Arrow L) | System Volume |
| **VLC Media** | Toggle Video | Skip Forward (Arrow R) | Skip Backward (Arrow L) | System Volume |

### Two-Handed Advanced Macros
| Global Action | X-Shape (Crossed Wrists) | T-Shape (Perpendicular Hands) |
| :--- | :--- | :--- |
| **All Systems** | Graceful App Shutdown | Terminate Target Media Process |

---

## Engineering Challenges & Solutions

### 1. Eliminating Volume Jitter (Signal Smoothing)
Webcam coordinates are naturally noisy due to light changes and camera resolution. If you map raw finger coordinates directly to your system volume, the audio level fluctuates rapidly (jitter). 
*   **The Math**: I implemented an Exponential Moving Average (EMA) filter to smooth out coordinates: `V_smoothed = (alpha * V_target) + ((1 - alpha) * V_previous)`
*   **The Result**: Setting the smoothing factor alpha to 0.25 blends 25% of the current frame's position with 75% of the historical average, creating a fluid, lag-free slide.

### 2. Preventing "Return-Swipe" Double Triggers
A common issue in swipe-detection algorithms is that when you swipe your hand and pull it back to the center of the camera screen, the return motion triggers a second swipe in the opposite direction.
*   **The Solution**: I designed a rolling 15-frame coordinate history buffer (`deque`) combined with a 1.5-second lockout cooldown. Once a swipe is triggered, the queue is cleared, and the system ignores any swipe inputs for 1.5 seconds, providing time to reset hand position safely.

### 3. Context-Aware Targeting (Focus Priority)
If you have both Spotify playing in the background and a YouTube video open in the foreground, standard media key presses can be unpredictable.
*   **The Solution**: The automation script queries the OS for the frontmost application. If you are actively looking at Chrome, Safari, VLC, or IINA, it targets the active video. If no media player is focused, it falls back to controlling your background music player.

### 4. Bypassing Hardware Bottlenecks (Camera Multithreading)
Standard OpenCV webcam loops are synchronous; the AI processing pipeline must wait for the camera hardware to physically capture the next frame, dropping the frame rate to roughly 15fps.
*   **The Solution**: I implemented a dedicated background `threading` class (`WebcamStream`) that continuously pulls frames from the camera buffer in the background. The main AI thread simply reads the most recently grabbed frame from memory, unlocking a flawless 60fps pipeline.

### 5. Multi-Hand Intersect Math (Two-Handed Macros)
Relying on a single hand for all controls limits the user experience, but tracking two hands introduces geometric complexity.
*   **The Math**: By upgrading the detector to support two hands, I built collision algorithms for complex multi-hand interactions:
    *   **T-Shape (Time Out):** Tracks the 3D distance between Hand 1's fingertips and Hand 2's palm. If the Euclidean distance drops below a threshold while the wrists are far apart, it safely terminates the background media player using a smart OS-detection routing layer.
    *   **X-Shape (Crossed Wrists):** Prevents false triggers (like resting hands side-by-side) by verifying that the wrists are close but the index fingers are pointing far away from each other. This guarantees a true X shape has been formed before safely shutting down the application.

### 6. Low-Light Environmental Fragility (CLAHE)
Standard computer vision models fail when deployed in dimly lit rooms or against harsh backlighting.
*   **The Solution**: Integrated Contrast Limited Adaptive Histogram Equalization (CLAHE). The pipeline transforms the BGR color space to LAB space, isolates the Luminance channel, and automatically balances extreme lighting variances before passing the frame to the AI, ensuring robust tracking in any lighting environment.

---

## Quick Installation

### 1. Run the Setup Script
Clone the repository and run the setup script. It will automatically create your virtual environment and install dependencies:
```bash
git clone https://github.com/your-username/gesture-media-control.git
cd gesture-media-control
chmod +x setup.sh
./setup.sh