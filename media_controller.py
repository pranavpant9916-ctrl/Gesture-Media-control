import subprocess
import platform

os_name = platform.system()

if os_name == "Windows":
    import ctypes
    vk_media_play_pause = 0xB3
    vk_media_next_track = 0xB0
    vk_media_prev_track = 0xB1
    def win_key(code):
        ctypes.windll.user32.keybd_event(code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(code, 0, 2, 0)

def set_system_volume(volume_level):
    if os_name != "Darwin":
        return
    volume = max(0, min(100, int(volume_level)))
    script = f"set volume output volume {volume}"
    subprocess.run(["osascript", "-e", script])

def toggle_play_pause():
    if os_name == "Windows":
        win_key(vk_media_play_pause)
        return
    elif os_name == "Linux":
        subprocess.run(["playerctl", "play-pause"])
        return

    applescript = '''
    -- Get active application name without using System Events (Permission-Free)
    set frontAppPath to (path to frontmost application as text)
    set AppleScript's text item delimiters to ":"
    set frontAppName to text item -2 of frontAppPath
    set AppleScript's text item delimiters to ""

    if frontAppName contains "Spotify" then
        tell application "Spotify" to playpause
        return
    else if frontAppName contains "Music" then
        tell application "Music" to playpause
        return
    else if frontAppName contains "VLC" then
        tell application "VLC" to play
        return
    else if frontAppName contains "IINA" then
        tell application "System Events" to keystroke " "
        return
    else if frontAppName contains "Chrome" then
        tell application "Google Chrome"
            if (count of windows) > 0 then
                set activeTabURL to URL of active tab of front window
                if activeTabURL contains "youtube.com" or activeTabURL contains "netflix.com" then
                    tell active tab of front window to execute javascript "
                        if (window.location.host.includes('youtube.com')) {
                            const playBtn = document.querySelector('.ytp-play-button');
                            if (playBtn) playBtn.click();
                        } else {
                            const v = document.querySelector('video');
                            if (v) { if (v.paused) v.play(); else v.pause(); }
                        }
                    "
                    return
                end if
            end if
        end tell
    else if frontAppName contains "Safari" then
        tell application "Safari"
            if (count of windows) > 0 then
                set activeTabURL to URL of document 1
                if activeTabURL contains "youtube.com" or activeTabURL contains "netflix.com" then
                    tell document 1 to do JavaScript "
                        if (window.location.host.includes('youtube.com')) {
                            const playBtn = document.querySelector('.ytp-play-button');
                            if (playBtn) playBtn.click();
                        } else {
                            const v = document.querySelector('video');
                            if (v) { if (v.paused) v.play(); else v.pause(); }
                        }
                    "
                    return
                end if
            end if
        end tell
    end if

    -- Background Players Fallback (If browser/music app is in background)
    tell application "System Events"
        if (exists process "Spotify") then
            tell application "Spotify" to playpause
            return
        else if (exists process "VLC") then
            tell application "VLC" to play
            return
        else if (exists process "Music") then
            tell application "Music" to playpause
            return
        end if
    end tell

    if application "Google Chrome" is running then
        tell application "Google Chrome"
            repeat with w in windows
                repeat with t in tabs of w
                    if URL of t contains "youtube.com" or URL of t contains "netflix.com" then
                        tell t to execute javascript "
                            if (window.location.host.includes('youtube.com')) {
                                const playBtn = document.querySelector('.ytp-play-button');
                                if (playBtn) playBtn.click();
                            } else {
                                const v = document.querySelector('video');
                                if (v) { if (v.paused) v.play(); else v.pause(); }
                            }
                        "
                        return
                    end if
                end repeat
            end repeat
        end tell
    end if

    if application "Safari" is running then
        tell application "Safari"
            repeat with w in windows
                repeat with t in tabs of w
                    if URL of t contains "youtube.com" or URL of t contains "netflix.com" then
                        tell t to do JavaScript "
                            if (window.location.host.includes('youtube.com')) {
                                const playBtn = document.querySelector('.ytp-play-button');
                                if (playBtn) playBtn.click();
                            } else {
                                const v = document.querySelector('video');
                                if (v) { if (v.paused) v.play(); else v.pause(); }
                            }
                        "
                        return
                    end if
                end repeat
            end repeat
        end tell
    end if
    '''
    subprocess.run(["osascript", "-e", applescript])

def next_track():
    if os_name == "Windows":
        win_key(vk_media_next_track)
        return
    elif os_name == "Linux":
        subprocess.run(["playerctl", "next"])
        return
    applescript = '''
    set frontAppPath to (path to frontmost application as text)
    set AppleScript's text item delimiters to ":"
    set frontAppName to text item -2 of frontAppPath
    set AppleScript's text item delimiters to ""

    if frontAppName contains "Spotify" then
        tell application "Spotify" to next track
        return
    else if frontAppName contains "VLC" then
        tell application "VLC" to next
        return
    else if frontAppName contains "Music" then
        tell application "Music" to next track
        return
    else if frontAppName contains "IINA" then
        tell application "System Events" to key code 124 using command down
        return
    else if frontAppName contains "Chrome" then
        tell application "Google Chrome"
            if (count of windows) > 0 then
                set activeTabURL to URL of active tab of front window
                if activeTabURL contains "youtube.com" or activeTabURL contains "netflix.com" then
                    tell active tab of front window to execute javascript "
                        if (window.location.host.includes('youtube.com')) {
                            const nextBtn = document.querySelector('.ytp-next-button');
                            if (nextBtn) nextBtn.click();
                        } else {
                            const v = document.querySelector('video');
                            if (v) v.currentTime += 10;
                        }
                    "
                    return
                end if
            end if
        end tell
    else if frontAppName contains "Safari" then
        tell application "Safari"
            if (count of windows) > 0 then
                set activeTabURL to URL of document 1
                if activeTabURL contains "youtube.com" or activeTabURL contains "netflix.com" then
                    tell document 1 to do JavaScript "
                        if (window.location.host.includes('youtube.com')) {
                            const nextBtn = document.querySelector('.ytp-next-button');
                            if (nextBtn) nextBtn.click();
                        } else {
                            const v = document.querySelector('video');
                            if (v) v.currentTime += 10;
                        }
                    "
                    return
                end if
            end if
        end tell
    end if

    tell application "System Events"
        if (exists process "Spotify") then
            tell application "Spotify" to next track
            return
        else if (exists process "Music") then
            tell application "Music" to next track
            return
        else if (exists process "VLC") then
            tell application "VLC" to next
            return
        end if
    end tell
    '''
    subprocess.run(["osascript", "-e", applescript])

def previous_track():
    if os_name == "Windows":
        win_key(vk_media_prev_track)
        return
    elif os_name == "Linux":
        subprocess.run(["playerctl", "previous"])
        return
    applescript = '''
    set frontAppPath to (path to frontmost application as text)
    set AppleScript's text item delimiters to ":"
    set frontAppName to text item -2 of frontAppPath
    set AppleScript's text item delimiters to ""

    if frontAppName contains "Spotify" then
        tell application "Spotify" to previous track
        return
    else if frontAppName contains "VLC" then
        tell application "VLC" to previous
        return
    else if frontAppName contains "Music" then
        tell application "Music" to previous track
        return
    else if frontAppName contains "IINA" then
        tell application "System Events" to key code 123 using command down
        return
    else if frontAppName contains "Chrome" then
        tell application "Google Chrome"
            if (count of windows) > 0 then
                set activeTabURL to URL of active tab of front window
                if activeTabURL contains "youtube.com" or activeTabURL contains "netflix.com" then
                    tell active tab of front window to execute javascript "
                        if (window.location.host.includes('youtube.com')) {
                            const prev = document.querySelector('.ytp-prev-button');
                            if (prev) { prev.click(); } else { window.history.back(); }
                        } else {
                            const v = document.querySelector('video');
                            if (v) v.currentTime -= 10;
                        }
                    "
                    return
                end if
            end if
        end tell
    else if frontAppName contains "Safari" then
        tell application "Safari"
            if (count of windows) > 0 then
                set activeTabURL to URL of document 1
                if activeTabURL contains "youtube.com" or activeTabURL contains "netflix.com" then
                    tell document 1 to do JavaScript "
                        if (window.location.host.includes('youtube.com')) {
                            const prev = document.querySelector('.ytp-prev-button');
                            if (prev) { prev.click(); } else { window.history.back(); }
                        } else {
                            const v = document.querySelector('video');
                            if (v) v.currentTime -= 10;
                        }
                    "
                    return
                end if
            end if
        end tell
    end if

    tell application "System Events"
        if (exists process "Spotify") then
            tell application "Spotify" to previous track
            return
        else if (exists process "Music") then
            tell application "Music" to previous track
            return
        else if (exists process "VLC") then
            tell application "VLC" to previous
            return
        end if
    end tell
    '''
    subprocess.run(["osascript", "-e", applescript])

def quit_active_app():
    if os_name == "Windows":

        win_key(0x12) # Alt
        win_key(0x73) # F4
        return
    elif os_name == "Linux":
        subprocess.run(["xdotool", "getactivewindow", "windowkill"])
        return

    applescript = '''
    set frontAppPath to (path to frontmost application as text)
    set AppleScript's text item delimiters to ":"
    set frontAppName to text item -2 of frontAppPath
    set AppleScript's text item delimiters to ""

    -- If a media app is in the foreground, quit it
    if frontAppName contains "Spotify" then
        tell application "Spotify" to quit
    else if frontAppName contains "VLC" then
        tell application "VLC" to quit
    else if frontAppName contains "Music" then
        tell application "Music" to quit
    else if frontAppName contains "IINA" then
        tell application "IINA" to quit
    else
        -- If you are working in another app (like VS Code), hunt down the background media player and kill it
        tell application "System Events"
            if (exists process "Spotify") then
                tell application "Spotify" to quit
            else if (exists process "VLC") then
                tell application "VLC" to quit
            else if (exists process "Music") then
                tell application "Music" to quit
            end if
        end tell
    end if
    '''
    subprocess.run(["osascript", "-e", applescript])