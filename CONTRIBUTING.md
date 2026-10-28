# Contributing to FinFlick

Thank you for your interest in contributing to **FinFlick**! Whether you are fixing a bug, adding support for a new presentation app, or proposing a new hand gesture, contributions are welcome.

---

## 🛠️ Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/courius/FinFlick.git
   cd FinFlick
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the automated test suite:**
   ```bash
   .venv/bin/python -m unittest discover -s tests -v
   ```

---

## 🧩 Project Structure Guide

- **Adding a New Presentation Application Profile**:
  - Edit `core/app_profiles.py` to add bundle identifiers or window title rules and map actions (`NEXT_SLIDE`, `PREV_SLIDE`, `PLAY_PAUSE`, `START_PRESENTATION`, etc.) to native shortcuts.
  - Add corresponding unit tests in `tests/test_controller.py`.
- **Tuning or Adding a Hand Gesture**:
  - Pose classification and trajectory state machines live in `core/gesture_engine.py`, with thresholds persisted in `core/config.py`.
  - Add synthetic landmark tests in `tests/test_gestures.py` to verify both positive triggers and false-positive rejection (such as conversational hand movements or return strokes).
- **Updating the Desktop Studio UI**:
  - The native macOS `WKWebView` bridge lives in `ui/app_window.py`, and the self-contained HTML5/CSS3/SVG frontend bundle lives in `ui/web_assets.py`.
  - Verify SVG XML validity and RPC bridge behavior in `tests/test_web_ui.py`.

---

## ✅ Pull Request Checklist

- [ ] All existing and new unit tests pass (`python -m unittest discover -s tests -v`).
- [ ] New gestures or app profiles include unit test coverage.
- [ ] `README.md` is updated if user-facing gestures, CLI flags, or app profiles changed.
