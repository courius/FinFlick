"""Direct AppleScript integration for Microsoft PowerPoint and Apple Keynote.

Controls presentations directly via Apple Events, allowing slide transitions to work:
1. Even if macOS Accessibility permission has not yet been granted for synthetic keystrokes.
2. In full-screen presentation mode AND in normal editing mode (for PowerPoint).
"""

import logging
import platform
import subprocess

logger = logging.getLogger("FinFlick.AppleScript")


def dispatch_powerpoint(action: str) -> bool:
    """Dispatches action directly to Microsoft PowerPoint via AppleScript."""
    if platform.system() != "Darwin":
        return False

    if action == "NEXT_SLIDE":
        script = """
        tell application "Microsoft PowerPoint"
            if (count of slide show windows) > 0 then
                go to next slide (slide show view of slide show window 1)
                return "ok"
            else if (count of presentations) > 0 then
                try
                    set curIdx to slide index of slide 1 of slide range of selection of document window 1
                    set totalSlides to count of slides of active presentation
                    if curIdx < totalSlides then
                        select (slide (curIdx + 1) of active presentation)
                        return "ok"
                    end if
                end try
            end if
        end tell
        """
    elif action == "PREV_SLIDE":
        script = """
        tell application "Microsoft PowerPoint"
            if (count of slide show windows) > 0 then
                go to previous slide (slide show view of slide show window 1)
                return "ok"
            else if (count of presentations) > 0 then
                try
                    set curIdx to slide index of slide 1 of slide range of selection of document window 1
                    if curIdx > 1 then
                        select (slide (curIdx - 1) of active presentation)
                        return "ok"
                    end if
                end try
            end if
        end tell
        """
    elif action == "START_PRESENTATION":
        script = """
        tell application "Microsoft PowerPoint"
            if (count of presentations) > 0 then
                run slide show of slide show settings of active presentation
                return "ok"
            end if
        end tell
        """
    elif action == "BLACKOUT":
        script = """
        tell application "Microsoft PowerPoint"
            if (count of slide show windows) > 0 then
                tell slide show view of slide show window 1
                    if slide state is slide show state black screen then
                        set slide state to slide show state running
                    else
                        set slide state to slide show state black screen
                    end if
                end tell
                return "ok"
            else if (count of presentations) > 0 then
                run slide show of slide show settings of active presentation
                delay 0.4
                if (count of slide show windows) > 0 then
                    set slide state of (slide show view of slide show window 1) to slide show state black screen
                end if
                return "ok"
            end if
        end tell
        """
    elif action == "FIRST_SLIDE":
        script = """
        tell application "Microsoft PowerPoint"
            if (count of slide show windows) > 0 then
                go to first slide (slide show view of slide show window 1)
                return "ok"
            else if (count of presentations) > 0 then
                try
                    select slide 1 of active presentation
                    return "ok"
                end try
            end if
        end tell
        """
    elif action == "LAST_SLIDE":
        script = """
        tell application "Microsoft PowerPoint"
            if (count of slide show windows) > 0 then
                go to last slide (slide show view of slide show window 1)
                return "ok"
            else if (count of presentations) > 0 then
                try
                    set totalSlides to count of slides of active presentation
                    select (slide totalSlides of active presentation)
                    return "ok"
                end try
            end if
        end tell
        """
    elif action == "ZOOM_IN":
        script = """
        tell application "Microsoft PowerPoint"
            if (count of presentations) > 0 and (count of slide show windows) = 0 then
                try
                    set curZoom to zoom of view of document window 1
                    if curZoom < 400 then
                        set zoom of view of document window 1 to (curZoom + 15)
                        return "ok"
                    end if
                end try
            end if
        end tell
        """
    elif action == "ZOOM_OUT":
        script = """
        tell application "Microsoft PowerPoint"
            if (count of presentations) > 0 and (count of slide show windows) = 0 then
                try
                    set curZoom to zoom of view of document window 1
                    if curZoom > 25 then
                        set zoom of view of document window 1 to (curZoom - 15)
                        return "ok"
                    end if
                end try
            end if
        end tell
        """
    else:
        return False

    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=1.5)
        return "ok" in res.stdout
    except Exception as e:
        logger.debug(f"PowerPoint AppleScript error: {e}")
        return False


def dispatch_keynote(action: str) -> bool:
    """Dispatches action directly to Apple Keynote via AppleScript."""
    if platform.system() != "Darwin":
        return False

    if action == "NEXT_SLIDE":
        script = 'tell application "Keynote" to show next'
    elif action == "PREV_SLIDE":
        script = 'tell application "Keynote" to show previous'
    elif action == "START_PRESENTATION":
        script = 'tell application "Keynote" to start from current slide'
    elif action == "FIRST_SLIDE":
        script = 'tell application "Keynote" to show first'
    elif action == "LAST_SLIDE":
        script = 'tell application "Keynote" to show last'
    elif action == "BLACKOUT":
        script = """
        tell application "Keynote"
            if playing then
                tell application "System Events" to keystroke "b"
                return "ok"
            end if
        end tell
        """
    else:
        return False

    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=1.5)
        return res.returncode == 0
    except Exception as e:
        logger.debug(f"Keynote AppleScript error: {e}")
        return False
