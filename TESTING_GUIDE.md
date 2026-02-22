# Earthworm Testing Guide - Unified Geological Analysis Viewport

**Latest Release:** `v1.0.0-unified-viewport` (2026-02-22)

## Quick Start

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/lukemoltbot/Earthworm_Moltbot.git
cd Earthworm_Moltbot

# Checkout the unified viewport release
git checkout v1.0.0-unified-viewport
```

### 2. Install Dependencies
```bash
# Create virtual environment (Python 3.8+ required)
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```

## What to Test - Unified Viewport Features

### Core Features
1. **Unified Geological Analysis Viewport**
   - Side-by-side layout (68% LAS curves, 32% stratigraphic column)
   - Pixel-perfect synchronization (≤1 pixel drift)
   - Professional geological color palette

2. **Navigation & Synchronization**
   - Mouse wheel scrolling (both displays sync)
   - Zoom controls (affect both displays)
   - Depth selection clicks

3. **Performance**
   - Smooth scrolling (target: 60+ FPS)
   - Fast zoom response (<100ms)
   - Efficient memory usage

### Test Workflows

#### Workflow 1: Basic Application Launch
1. Run `python main.py`
2. Verify main window opens with unified viewport
3. Check window title: "Earthworm Borehole Logger - Unified Geological Analysis Viewport"
4. Verify no errors in console or `earthworm.log`

#### Workflow 2: Load Sample Data
1. Click **File → Load LAS File**
2. Use sample data if available (check `tests/test_data/` directory)
3. Verify curves load in right pane (68% width)
4. Verify stratigraphic column appears in left pane (32% width)
5. Check synchronization - scroll one display, both should move

#### Workflow 3: Navigation Testing
1. **Mouse Wheel**: Scroll through depth - both displays should sync
2. **Zoom**: Use +/- keys or zoom controls - both displays should zoom together
3. **Click**: Click on curve point - should highlight corresponding depth in column
4. **Drag**: Try dragging stratigraphic boundaries (if data loaded)

#### Workflow 4: Curve Visibility
1. Toggle curve visibility (gamma, density, etc.)
2. Verify curves show/hide in real-time
3. Check performance during visibility changes

## Known Issues & Workarounds

### Issue 1: Scrolling with No Data
- **Symptom**: Programmatic scrolling may not work when no geological data loaded
- **Root Cause**: Scene height < viewport height when empty
- **Workaround**: Load data before testing scrolling functionality
- **Status**: Pre-existing, doesn't affect production usage with data

### Issue 2: Single Test Failure
- **Test**: `test_clear_column` in enhanced stratigraphic column tests
- **Impact**: Unit test only, component appears functional
- **Status**: Being investigated separately

### Issue 3: macOS Permissions
- **Symptom**: "Python quit unexpectedly" dialog
- **Solution**: Click "Ignore" or grant Accessibility permissions
- **Note**: Test wrapper handles this automatically

## Advanced Testing

### Headless Testing (CI/CD)
```bash
# Run pilot wrapper (crash-resistant)
QT_QPA_PLATFORM=offscreen python tests/test_pilot_wrapper.py

# Run specific test suites
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_phase5_workflow_validation.py
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_unified_viewport_integration.py
```

### Performance Validation
```bash
# Run performance tests
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_phase3_performance.py -v

# Expected results:
# - 322.9 FPS during smooth scrolling (target: 60 FPS)
# - <100ms response time for zoom changes (achieved: 3-6ms)
# - ≤1 pixel maximum drift between components
```

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'PyQt6'"
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

#### Application crashes on startup
1. Check `earthworm.log` for error details
2. Verify Python version (3.8+ required)
3. Check Qt installation: `python -c "from PyQt6.QtWidgets import QApplication; print('Qt OK')"`

#### Displays not synchronized
1. Check pixel drift is ≤1 pixel (design target)
2. Verify both components are connected to UnifiedDepthScaleManager
3. Check console for synchronization warnings

#### Slow performance
1. Reduce dataset size if testing with large files
2. Check system resources (RAM, CPU)
3. Verify graphics drivers are up to date

## Manual Test Checklist

### [ ] Application Launch
- [ ] Main window opens without errors
- [ ] Unified viewport displays correctly
- [ ] No console errors or warnings

### [ ] Layout Verification
- [ ] Side-by-side layout (68%/32% ratio)
- [ ] Professional geological styling
- [ ] Clear axis labels and grid lines

### [ ] Synchronization Testing
- [ ] Mouse wheel scrolls both displays
- [ ] Zoom controls affect both displays
- [ ] Click events propagate correctly
- [ ] Pixel drift ≤1 pixel (visual check)

### [ ] Performance Testing
- [ ] Smooth scrolling (no stuttering)
- [ ] Fast zoom response
- [ ] Efficient memory usage (check Activity Monitor/Task Manager)

### [ ] Workflow Testing
- [ ] Load LAS/CSV/Excel files
- [ ] Curve visibility toggles work
- [ ] Stratigraphic column updates with data
- [ ] Editor table interactions work

## Documentation

### Key Documentation Files
1. `Unified_Viewport_API.md` - Developer API documentation
2. `Migration_Guide.md` - Guide for existing users
3. `User_Guide.md` - Updated user guide with unified viewport section
4. `Phase_6_Completion_Summary.md` - Deployment readiness report

### Architecture
- **Main Component**: `GeologicalAnalysisViewport` (`src/ui/widgets/unified_viewport/`)
- **Synchronization**: `UnifiedDepthScaleManager`, `PixelDepthMapper`
- **Performance**: `ScrollingSynchronizer`
- **Integration**: `ComponentAdapter`

## Reporting Issues

When reporting issues, include:
1. Earthworm version: `v1.0.0-unified-viewport`
2. Operating system and version
3. Python version: `python --version`
4. Steps to reproduce
5. Console output or `earthworm.log`
6. Screenshots if visual issue

## Support

- **GitHub Issues**: https://github.com/lukemoltbot/Earthworm_Moltbot/issues
- **Documentation**: Check `docs/` directory
- **Testing Tools**: Use `tests/test_pilot_wrapper.py` for crash-resistant testing

---

*Last Updated: 2026-02-22*  
*Phase: 6 - Deployment Complete*