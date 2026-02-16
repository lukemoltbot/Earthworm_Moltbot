# Earthworm GUI Testing Setup Guide

## 🎯 Overview
This guide explains how to set up automated GUI testing for Earthworm using PyAutoGUI.

## 📋 Prerequisites

### 1. Earthworm Application
- Earthworm must be installed and runnable
- Test files available:
  - `Testing Docs/24162R_GN.las`
  - `Testing Docs/earthworm settings.json`

### 2. Python Environment
- Python 3.8+ with virtual environment
- Required packages: `pyautogui`, `opencv-python`, `numpy`

### 3. macOS Permissions
- **Screen Recording**: Required for PyAutoGUI screenshots
- **Accessibility**: Required for keyboard/mouse simulation

## 🚀 Setup Steps

### Step 1: Start Earthworm Manually
```bash
cd Earthworm_Moltbot
.venv/bin/python main.py
```

### Step 2: Position the Window
- Move Earthworm window to a consistent position
- Recommended: Top-left corner, 1200x800 pixels
- Make sure window is not maximized (for consistent positioning)

### Step 3: Take Reference Screenshots
Take screenshots of these UI elements:

1. **Main Window** (full window)
2. **File Menu** (click File → take screenshot)
3. **Open Dialog** (File → Open → screenshot)
4. **Hole Editor Window** (after loading LAS file)
5. **Curve Dropdowns** (Gamma, Density, Caliper dropdowns)
6. **Run Analysis Button**
7. **Toolbar Buttons** (zoom in/out, scaling)

Save screenshots to: `Earthworm_Moltbot/logs/gui_references/`

### Step 4: Create Configuration File
Create `gui_config.json` based on your screen setup:

```json
{
  "screen_width": 2560,
  "screen_height": 1600,
  "earthworm_window": {
    "x": 100,
    "y": 100,
    "width": 1200,
    "height": 800
  },
  "reference_images": {
    "main_window": "logs/gui_references/main_window.png",
    "file_menu": "logs/gui_references/file_menu.png",
    "hole_editor": "logs/gui_references/hole_editor.png"
  },
  "curve_mappings": {
    "Gamma": "GRDE",
    "Short Space Density": "DENB",
    "Long Space Density": "DENL",
    "Caliper": "CADE",
    "Resistivity": ""
  }
}
```

### Step 5: Run Automation Test
```bash
cd Earthworm_Moltbot
.venv/bin/python gui_automation_framework.py --config gui_config.json --las "../Testing Docs/24162R_GN.las" --settings "../Testing Docs/earthworm settings.json"
```

## 🧪 Test Workflow

The automation will attempt to:

1. **Start Earthworm** (manual - you need to start it first)
2. **Load Settings File** via File → Settings
3. **Load LAS File** via File → Open
4. **Map Curves** in Hole Editor:
   - Gamma = GRDE
   - Short Space Density = DENB
   - Long Space Density = DENL
   - Caliper = CADE
   - Resistivity = (leave blank)
5. **Click Run Analysis**
6. **Test UI Components**:
   - Check if window defaults to maximized
   - Adjust splitters without crashing
   - Test scaling buttons
   - Verify scroll synchronization
   - Check depth alignment

## ⚠️ Important Notes

### Safety Features
- **FAILSAFE**: Move mouse to top-left corner to abort automation
- **PAUSE**: 0.5-second delay between actions
- **Screenshots**: Taken before/after each major step

### Manual Intervention Points
1. Start Earthworm application
2. Grant macOS permissions if prompted
3. Monitor for error dialogs
4. Stop automation if something goes wrong

### Error Handling
- Automation will continue if an element is not found
- Screenshots help debug issues
- Test results are saved to JSON files

## 📊 Expected Results

### Successful Test Indicators
- LAS file loads without errors
- Curves are mapped correctly
- Analysis completes
- No application crashes
- Scroll synchronization works

### Common Issues to Watch For
1. **Permission dialogs** (macOS security)
2. **File not found** errors
3. **UI element not found** (window moved/resized)
4. **Analysis errors** (curve data issues)
5. **Memory issues** with large LAS files

## 🔧 Troubleshooting

### PyAutoGUI Can't Find Elements
1. Check screenshot quality and size
2. Verify window position hasn't changed
3. Update reference images if UI changed
4. Adjust confidence threshold (default: 0.8)

### macOS Permission Issues
1. System Settings → Privacy & Security
2. Screen Recording: Allow Python/terminal app
3. Accessibility: Allow Python/terminal app
4. Restart application after granting permissions

### Earthworm-Specific Issues
1. Check terminal for Python errors
2. Verify LAS file is valid (can be opened in other software)
3. Check settings file format
4. Look for error dialogs in Earthworm

## 📈 Advanced Configuration

### Customizing Test Flow
Edit `gui_automation_framework.py` to:
- Add new test cases
- Change timing/delays
- Modify image recognition settings
- Add custom validation logic

### Integrating with CI/CD
1. Run tests on schedule (cron job)
2. Save results to database
3. Generate HTML reports
4. Send notifications on failure

## 🆘 Getting Help

If automation fails:
1. Check `logs/gui_screenshots/` for visual evidence
2. Review `logs/test_report_*.json` for detailed results
3. Check terminal output for Python errors
4. Take new reference screenshots if UI changed

## 📚 Additional Resources

- [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/)
- [OpenCV Template Matching](https://docs.opencv.org/)
- [Earthworm Documentation](https://github.com/lukemoltbot/Earthworm_openclaw)
- [macOS Automation Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)

---

**Note**: This is a framework for automated GUI testing. The first run will likely require manual adjustments to get the image recognition working correctly. Once configured, it can run autonomously.