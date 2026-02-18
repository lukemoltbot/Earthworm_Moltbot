# Curve and Strat Unification Development Plan

## Project Overview
**Goal:** Replace Earthworm's separated LAS curves and Enhanced Stratigraphic Column displays with a unified, professional geological analysis viewport as the default view.

**Success Criteria:**
- LAS curves and Enhanced Stratigraphic Column displayed side-by-side in single viewport
- Pixel-perfect depth synchronization (1-pixel accuracy)
- Professional geological software aesthetics matching 1 Point Desktop
- All existing functionality preserved (editor table, overview, curve visibility, etc.)
- Equal or better performance than current implementation

## User Requirements (From Discussion)
1. **Default view** - Unified display replaces current separated layout
2. **Feature preservation** - No simplification or removal of existing functionality
3. **Multi-agent implementation** - Specialized sub-agents with coordination
4. **Pixel-perfect synchronization** - 1-pixel accuracy target
5. **Rigorous testing** - Full visual regression between phases, 3-attempt bug fix limit
6. **Complete replacement** - Deploy to GitHub once stable

## Multi-Agent Orchestration
```
ORCHESTRATOR (Main Agent)
    ↓
ARCHITECT AGENT (DeepSeek Reasoner)
    ├── UI/UX DESIGN AGENT (DeepSeek Chat)
    ├── CORE IMPLEMENTATION AGENT (DeepSeek Chat)  
    ├── SYNCHRONIZATION AGENT (DeepSeek Reasoner)
    ├── TESTING AGENT (DeepSeek Chat)
    └── VALIDATION AGENT (DeepSeek Reasoner)
```

## Phase 0: Preparation & Setup (1-2 days)
### Objectives
- Establish development environment
- Capture baseline metrics
- Set up testing infrastructure

### Tasks
1. **Baseline Performance Metrics**
   - Capture current FPS, memory usage, load times
   - Create visual baseline screenshots for regression testing
   - Document current synchronization accuracy

2. **Development Environment**
   - Create test branch: `feature/unified-viewport`
   - Configure visual regression testing framework
   - Establish bug tracking system (GitHub Issues)

3. **Agent Coordination Protocol**
   - Define handoff procedures between agents
   - Establish communication channels
   - Create shared documentation workspace

### Test Gate 0
- [ ] All baseline metrics captured
- [ ] Testing framework operational
- [ ] Development environment ready

## Phase 1: Architectural Foundation (3-4 days)
### Objectives
- Design and implement core `GeologicalAnalysisViewport` class
- Create unified depth scale manager
- Establish component interfaces

### Key Components
1. **`GeologicalAnalysisViewport` Class** - Main container widget
2. **`UnifiedDepthScaleManager`** - Pixel-perfect synchronization
3. **Component Interfaces** - Standardized component API

### Technical Specifications
```python
# Layout constants (pixel-perfect)
CURVE_WIDTH_RATIO = 0.68  # 68% curves (matches 1 Point Desktop)
COLUMN_WIDTH_RATIO = 0.32  # 32% column
MIN_CURVE_WIDTH = 350  # pixels
MIN_COLUMN_WIDTH = 220  # pixels
VERTICAL_PADDING = 2  # pixels between components
PIXEL_TOLERANCE = 1  # Maximum allowed pixel drift
```

### Test Gate 1
- [ ] `GeologicalAnalysisViewport` class compiles without errors
- [ ] Basic layout renders (empty components)
- [ ] No regression in existing test suite
- **Bug Fix Limit:** 3 attempts per issue before escalation

## Phase 2: Visual Integration & Professional Polish (4-5 days)
### Objectives
- Implement side-by-side layout
- Apply geological professional styling
- Ensure visual continuity

### Tasks
1. **Pixel-Perfect Split Layout**
   - QHBoxLayout with stretch factors for ratio control
   - Visual separator (1 pixel line, geological style)
   - Minimum width constraints

2. **Geological Professional Styling**
   - Color Palette: Standard geological colors
     - Gamma: #8b008b
     - Density: #0066cc  
     - Caliper: #ffa500
     - Resistivity: #ff0000
   - Typography: Consistent font family, 9pt axis labels
   - Axis Styling: Professional tick marks, clear unit labels

3. **Component Integration Wrappers**
   - Configure existing components for unified view
   - Remove individual scroll bars
   - Apply consistent styling

### Test Gate 2
- [ ] Side-by-side layout renders correctly
- [ ] Professional geological styling applied
- [ ] Visual regression passes (matches design mockups)
- [ ] No pixel gaps or misalignment visible
- **Bug Fix Limit:** 3 attempts per visual issue

## Phase 3: Synchronization Engine (5-6 days)
### Objectives
- Implement pixel-perfect depth synchronization (1-pixel accuracy)
- Unified event handling
- Performance-optimized rendering

### Key Components
1. **`PixelDepthMapper`** - Map depth values to pixel positions with integer rounding
2. **Unified Event Handling** - Single mouse wheel, keyboard navigation, click propagation
3. **Performance Optimization** - Viewport caching, lazy updates, memory management

### Synchronization Requirements
- 60+ FPS during smooth scrolling with 10,000 data points
- < 100ms response to zoom changes
- < 50MB additional memory usage
- < 500ms additional initialization time

### Test Gate 3
- [ ] Pixel alignment validation passes (≤1 pixel drift)
- [ ] Synchronized scrolling at 60+ FPS with 10,000 data points
- [ ] All interaction events properly synchronized
- [ ] Performance benchmarks meet or exceed current implementation
- **Bug Fix Limit:** 3 attempts per synchronization issue

## Phase 4: Main Window Integration (3-4 days)
### Objectives
- Replace current separated components with unified viewport
- Maintain all existing feature integrations
- Ensure backward compatibility

### Integration Points
1. **Main Window Layout** - Replace curve plotter and strat column with unified viewport
2. **Feature Preservation**
   - Curve Visibility Toolbar → `unified_viewport.curveVisibilityChanged`
   - Zoom Controls → Control unified viewport
   - Boundary Lines → Sync with unified display
   - Anomaly Detection → Highlight in both views
   - Editor Table Sync → Maintain row selection highlighting

3. **Backward Compatibility Layer**
   - Legacy access to individual components via adapter
   - Deprecation warnings for old access patterns
   - Migration path documentation

### Test Gate 4
- [ ] Main window loads with unified viewport as default
- [ ] All existing features work (toolbar, zoom, boundaries, anomalies)
- [ ] Editor table synchronization maintained
- [ ] No console errors or warnings
- [ ] Legacy code compatibility verified
- **Bug Fix Limit:** 3 attempts per integration issue

## Phase 5: Comprehensive Testing & Validation (6-7 days)
### Objectives
- Rigorous testing with full visual regression
- Geological workflow validation
- Structured bug fixing protocol

### Test Categories
1. **Automated Test Suite**
   - Pixel-perfect synchronization tests
   - Performance benchmarks
   - Visual regression comparisons

2. **Visual Regression Pipeline**
   - Baseline capture of all UI states
   - Automated pixel-by-pixel diff after each change
   - 1-pixel tolerance for anti-aliasing differences
   - Automatic bug report generation with diff images

3. **Geological Workflow Validation**
   - Load LAS → Run analysis → Interpret results
   - Toggle curves → Correlate with lithology
   - Zoom to interval → Edit boundaries → See updates
   - Export interpretation → Verify data integrity

### Bug Fix Protocol (3-Attempt Limit)
1. **Attempt 1:** Identify root cause, implement fix
2. **Attempt 2:** Alternative approach, additional debugging
3. **Attempt 3:** Simplified workaround, comprehensive logging
4. **Escalation:** Report to human with detailed analysis after 3 failed attempts

### Test Gate 5
- [ ] All automated tests pass
- [ ] Visual regression suite passes (≤1 pixel differences)
- [ ] Geological workflow validation successful
- [ ] Performance benchmarks met
- [ ] No critical or blocking bugs remaining
- **Bug Fix Limit:** Strict 3-attempt enforcement with escalation

## Phase 6: Documentation & Deployment (2-3 days)
### Objectives
- Complete user and developer documentation
- Final validation and approval
- Deployment to GitHub

### Documentation Requirements
1. **User Documentation**
   - New unified viewport explanation
   - Comparison with old separated view
   - Tips for professional geological analysis
   - Troubleshooting synchronization issues

2. **Developer Documentation**
   - Architectural overview
   - API documentation for `GeologicalAnalysisViewport`
   - Extension guide for adding new visualization components
   - Performance tuning guide

3. **Migration Guide**
   - Steps for existing users
   - Configuration changes required
   - Known issues and workarounds

### Deployment Strategy
1. **Final Validation**
   - Complete end-to-end testing
   - Performance verification
   - User acceptance testing simulation

2. **GitHub Deployment**
   - Merge to `main` branch
   - Create release tag (e.g., `v1.0.0-unified-viewport`)
   - Update changelog with all changes

3. **Post-Deployment Monitoring**
   - Issue tracking for first 48 hours
   - Performance monitoring in production use
   - User feedback collection

### Final Acceptance Criteria
- [ ] Unified viewport functions as default view
- [ ] All existing features preserved and functional
- [ ] Pixel-perfect synchronization (1-pixel accuracy)
- [ ] Professional geological aesthetics achieved
- [ ] Performance equal or better than previous version
- [ ] Comprehensive documentation complete
- [ ] All tests passing
- [ ] No critical bugs outstanding

## Risk Mitigation Strategies
### High Risk: Synchronization Drift
- **Mitigation:** Integer pixel math, validation checks, visual debug mode
- **Fallback:** Automatic re-sync if drift detected

### Medium Risk: Performance Degradation
- **Mitigation:** Performance profiling throughout development
- **Fallback:** Performance optimization phase, caching strategies

### Low Risk: UI Regression
- **Mitigation:** Comprehensive visual regression testing
- **Fallback:** Quick rollback capability preserved

## Success Metrics
### Quantitative Metrics
1. **Synchronization Accuracy:** 100% pixel alignment (≤1 pixel drift)
2. **Performance:** ≥60 FPS scrolling, <100ms zoom response
3. **Memory:** <10% increase in memory usage
4. **Test Coverage:** ≥90% code coverage for new components

### Qualitative Metrics
1. **User Experience:** Professional geological software feel
2. **Visual Quality:** Matches 1 Point Desktop aesthetic standards
3. **Workflow Efficiency:** Reduced cognitive load in analysis tasks
4. **Professional Credibility:** Suitable for commercial geological work

## Timeline & Resource Estimates
**Total Estimated Duration:** 21-29 days

**Weekly Breakdown:**
- **Week 1-2:** Phases 0-2 (Preparation, Architecture, Visual Integration)
- **Week 3:** Phases 3-4 (Synchronization, Main Window Integration)
- **Week 4:** Phase 5 (Comprehensive Testing)
- **Week 5:** Phase 6 (Documentation & Deployment)

**Critical Path:** Phase 3 (Synchronization Engine) → Phase 5 (Testing)

## File Structure Changes
```
src/ui/widgets/
├── geological_analysis_viewport.py      # NEW - Main unified viewport
├── unified_depth_scale_manager.py       # NEW - Synchronization engine
├── pixel_depth_mapper.py                # NEW - Pixel accuracy utilities
├── pyqtgraph_curve_plotter.py           # MODIFIED - Unified integration
├── enhanced_stratigraphic_column.py     # MODIFIED - Unified integration
└── legacy_compatibility_adapter.py      # NEW - Backward compatibility

src/ui/main_window.py                    # MODIFIED - Layout restructuring

tests/
├── test_unified_viewport.py             # NEW - Core functionality tests
├── test_pixel_synchronization.py        # NEW - Accuracy tests
├── test_visual_regression.py            # NEW - Visual comparison tests
└── test_performance_benchmarks.py       # NEW - Performance tests
```

## Agent Responsibilities & Handoffs
### Architect Agent (DeepSeek Reasoner)
- Overall system design
- Dependency mapping
- Integration planning
- **Handoff to:** Core Implementation Agent

### UI/UX Design Agent (DeepSeek Chat)
- Visual layout design
- Styling implementation
- Professional polish
- **Handoff to:** Testing Agent (visual validation)

### Core Implementation Agent (DeepSeek Chat)
- `GeologicalAnalysisViewport` implementation
- Main window integration
- Component wrapping
- **Handoff to:** Synchronization Agent

### Synchronization Agent (DeepSeek Reasoner)
- Pixel-perfect depth alignment
- Performance optimization
- Event handling coordination
- **Handoff to:** Testing Agent (performance validation)

### Testing Agent (DeepSeek Chat)
- Test suite development
- Visual regression testing
- Bug tracking and reporting
- **Handoff to:** Validation Agent

### Validation Agent (DeepSeek Reasoner)
- Geological correctness validation
- Workflow verification
- Final approval for deployment
- **Handoff to:** Orchestrator (deployment)

## Communication Protocol
1. **Daily Status Updates:** Each agent reports progress via session spawning
2. **Issue Escalation:** 3-attempt limit with detailed failure analysis
3. **Handoff Documentation:** Clear requirements and acceptance criteria
4. **Version Control:** Regular commits with descriptive messages

## Contingency Plans
### Plan A: Successful Implementation
- Deploy as complete replacement
- Monitor for issues
- Collect user feedback

### Plan B: Minor Issues Found
- Deploy with known issues documented
- Schedule follow-up fixes
- Provide workarounds

### Plan C: Major Issues Found
- Revert to previous version
- Analyze root causes
- Re-plan implementation

---

*This plan will be updated as implementation progresses. Last updated: 2026-02-18*