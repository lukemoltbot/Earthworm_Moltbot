# LAS Curve Pane Architecture Design
## Comprehensive Improvement Plan - Part 5/6

**Date:** 2026-02-11  
**Author:** Subagent LAS-Curve-Architect-5  
**Status:** Design Document

---

## Executive Summary

This document outlines a comprehensive architectural redesign of the LAS curve pane to address 6 identified issues while maintaining performance, ensuring synchronization with EnhancedStratigraphicColumn, providing intuitive UI controls, and supporting future extensibility.

## 1. Identified Issues Analysis

Based on code review and test reports, the following issues have been identified:

### Issue 1: Dual-Axis Scaling Mismatch
- **Problem:** Configuration mismatch between `config.py` (gamma: 0-150) and `pyqtgraph_curve_plotter.py` (gamma: 0-300)
- **Root Cause:** Inconsistent range definitions across components
- **Impact:** Incorrect scaling and axis labeling

### Issue 2: Scroll Coordination Problems
- **Problem:** Independent scrolling between curve plotter and stratigraphic column
- **Root Cause:** No unified scroll coordination system
- **Impact:** User confusion, manual synchronization required

### Issue 3: Scale Synchronization Issues
- **Problem:** Depth and value scales not properly synchronized
- **Root Cause:** Separate scaling calculations in different components
- **Impact:** Misaligned visual representations

### Issue 4: Curve Alignment Problems
- **Problem:** Curves with different ranges not properly normalized
- **Root Cause:** Inconsistent normalization algorithms
- **Impact:** Difficult comparative analysis

### Issue 5: Visibility Management Complexity
- **Problem:** Curve visibility toggles lack persistence and intuitive controls
- **Root Cause:** Ad-hoc visibility management without state persistence
- **Impact:** User frustration, loss of context

### Issue 6: Event Handling Fragmentation
- **Problem:** Inconsistent signal/slot patterns across components
- **Root Cause:** Lack of unified event architecture
- **Impact:** Integration complexity, maintenance overhead

## 2. Design Requirements

### 2.1 Core Requirements
1. **Fix all 6 identified issues** - Comprehensive solution addressing each problem
2. **Maintain or improve performance** - No regression in rendering speed or responsiveness
3. **Ensure proper synchronization** - Unified behavior with EnhancedStratigraphicColumn
4. **Provide intuitive UI controls** - User-friendly curve management interface
5. **Support future extensibility** - Modular architecture for new features

### 2.2 Performance Targets
- **Rendering:** < 100ms for typical LAS data (1000-5000 depth points)
- **Memory:** < 50MB for loaded curves
- **Responsiveness:** < 50ms UI response time
- **Scalability:** Support for 10+ concurrent curves

## 3. Architecture Design

### 3.1 Plotting Technology Selection

#### Option Analysis:
1. **Matplotlib (Current Fallback)**
   - Pros: Mature, extensive features
   - Cons: Slower rendering, heavier memory footprint

2. **PyQtGraph (Current Implementation)**
   - Pros: Fast rendering, lightweight, Qt-native
   - Cons: Steeper learning curve, fewer built-in features

3. **Hybrid Approach (Recommended)**
   - **Primary:** PyQtGraph for real-time interactive plotting
   - **Secondary:** Matplotlib for static exports and complex visualizations
   - **Integration:** Unified API with technology abstraction layer

#### Decision: Hybrid Architecture
```
┌─────────────────────────────────────────────┐
│            Curve Pane Controller            │
│  (Unified API, Technology Abstraction)      │
├─────────────────────────────────────────────┤
│  PyQtGraph Renderer │  Matplotlib Renderer  │
│  (Interactive)      │  (Export/Static)      │
└─────────────────────────────────────────────┘
```

### 3.2 Scroll Coordination System

#### Design: Unified Vertical Scrolling Only
```
┌─────────────────────────────────────────────┐
│          Scroll Coordinator                 │
│  (Singleton, Event Bus Pattern)             │
├─────────────────────────────────────────────┤
│  • Depth-based synchronization              │
│  • Velocity matching                        │
│  • Inertial scrolling support               │
│  • Viewport state management                │
└─────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
┌───────────────────┬───────────────────┬───────────────────┐
│ Curve Plotter     │ Strat Column      │ Overview Panel    │
│ Viewport          │ Viewport          │ Viewport          │
└───────────────────┴───────────────────┴───────────────────┘
```

#### Implementation Strategy:
1. **Central Scroll Manager:** Singleton coordinating all viewports
2. **Depth-based Synchronization:** All components share same depth reference
3. **Velocity Matching:** Smooth synchronized scrolling
4. **Viewport State:** Persistent viewport configuration

### 3.3 Scale Synchronization Mechanism

#### Design: Hierarchical Scale Management
```
┌─────────────────────────────────────────────┐
│         Scale Synchronization Engine        │
├─────────────────────────────────────────────┤
│  • Master depth scale (pixels/unit)         │
│  • Curve value normalization                │
│  • Axis range coordination                  │
│  • Unit conversion management               │
└─────────────────────────────────────────────┘
           │              │
           ▼              ▼
┌───────────────────┬───────────────────┐
│ Depth Scale       │ Value Scale       │
│ Controller        │ Controller        │
│ • Vertical sync   │ • Horizontal sync │
│ • Zoom levels     │ • Range mapping   │
└───────────────────┴───────────────────┘
```

#### Key Features:
1. **Unified Depth Scale:** Single source of truth for vertical scaling
2. **Dynamic Value Normalization:** Automatic range adjustment
3. **Axis Label Synchronization:** Consistent labeling across components
4. **Unit Conversion:** Support for metric/imperial units

### 3.4 Curve Alignment System

#### Design: Normalized Display Pipeline
```
Raw Data → Preprocessing → Normalization → Rendering
    │           │              │              │
    ▼           ▼              ▼              ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ LAS     │ │ Filter  │ │ Range   │ │ Visual  │
│ Parser  │ │ NaN/Out │ │ Mapper  │ │ Render  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘
```

#### Normalization Strategies:
1. **Global Range:** All curves use dataset min/max
2. **Per-Curve Range:** Individual curve min/max
3. **Standardized Ranges:** Predefined ranges (0-300 API, 0-4 g/cc)
4. **Dynamic Adjustment:** Auto-adjust based on visible range

### 3.5 Visibility Management Layer

#### Design: Stateful Visibility Controller
```
┌─────────────────────────────────────────────┐
│       Visibility Management Layer           │
├─────────────────────────────────────────────┤
│  • Curve registry with metadata             │
│  • Visibility state persistence             │
│  • Group visibility controls                │
│  • Preset management                        │
└─────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│            UI Control Panel                 │
├─────────────────────────────────────────────┤
│  • Checkbox tree with hierarchy             │
│  • Color-coded indicators                   │
│  • Quick toggle shortcuts                   │
│  • Search/filter functionality              │
└─────────────────────────────────────────────┘
```

#### Features:
1. **Persistent State:** Remember visibility across sessions
2. **Group Management:** Toggle curve groups (all gamma, all density)
3. **Preset System:** Save/load visibility configurations
4. **Visual Feedback:** Immediate visual updates

### 3.6 Event Handling Architecture

#### Design: Clean Signal/Slot Patterns
```
┌─────────────────────────────────────────────┐
│          Event Bus (Central Hub)            │
├─────────────────────────────────────────────┤
│  • Standardized event types                 │
│  • Type-safe signal connections             │
│  • Event logging and debugging              │
│  • Async event processing                   │
└─────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
┌───────────────────┬───────────────────┬───────────────────┐
│ Curve Events      │ UI Events         │ Data Events       │
│ • Point clicked   │ • Control changed │ • Data loaded     │
│ • Range changed   │ • Visibility      │ • Data updated    │
│ • Zoom changed    │   toggled         │ • Scale changed   │
└───────────────────┴───────────────────┴───────────────────┘
```

#### Implementation Patterns:
1. **Observer Pattern:** Decoupled component communication
2. **Command Pattern:** Undo/redo support for actions
3. **Factory Pattern:** Event object creation
4. **Mediator Pattern:** Component coordination

## 4. Technical Design

### 4.1 Class Hierarchy

```
CurvePaneController (Main Interface)
├── RendererManager (Technology Abstraction)
│   ├── PyQtGraphRenderer
│   └── MatplotlibRenderer
├── ScrollCoordinator (View Synchronization)
│   ├── DepthSyncManager
│   └── ViewportState
├── ScaleManager (Scale Synchronization)
│   ├── DepthScaleController
│   └── ValueScaleController
├── CurveManager (Curve Management)
│   ├── CurveRegistry
│   ├── VisibilityController
│   └── AlignmentEngine
├── EventManager (Event Handling)
│   ├── EventBus
│   └── SignalRegistry
└── UIController (User Interface)
    ├── ControlPanel
    └── ToolbarManager
```

### 4.2 Data Flow and Transformation Pipelines

#### Primary Data Flow:
```
1. Data Loading
   LAS File → Parser → DataFrame → DataValidator → Clean Data

2. Curve Processing
   Clean Data → CurveExtractor → RangeCalculator → Normalizer → Render Data

3. Visualization Pipeline
   Render Data → LayoutEngine → Renderer → Display
```

#### Transformation Stages:
1. **Parsing:** LAS → pandas DataFrame
2. **Validation:** Data quality checks
3. **Extraction:** Column-based curve extraction
4. **Normalization:** Range adjustment and scaling
5. **Rendering:** Visual representation generation

### 4.3 View Coordination Patterns

#### Pattern 1: Master-Slave Synchronization
- **Master:** EnhancedStratigraphicColumn depth view
- **Slaves:** Curve plotter, overview panel
- **Sync:** Depth range, zoom level, scroll position

#### Pattern 2: Peer-to-Peer Event Broadcasting
- **Event Types:** ViewChanged, DataUpdated, ScaleAdjusted
- **Broadcast:** All interested components notified
- **Response:** Components update based on event data

#### Pattern 3: State Snapshot and Restoration
- **Snapshot:** Capture complete view state
- **Storage:** Serializable state object
- **Restoration:** Apply saved state to all components

### 4.4 Performance Optimization Strategies

#### 1. Rendering Optimization
- **Lazy Loading:** Load curves on demand
- **Progressive Rendering:** Render visible range first
- **Caching:** Cache rendered curves
- **GPU Acceleration:** Utilize PyQtGraph GPU features

#### 2. Memory Management
- **Data Streaming:** Process large files in chunks
- **Reference Counting:** Manage curve data references
- **Cleanup:** Automatic cleanup of unused curves
- **Compression:** Compress historical data

#### 3. Responsiveness Enhancement
- **Background Processing:** Offload heavy computations
- **Event Throttling:** Limit frequent UI updates
- **Predictive Loading:** Pre-load likely needed data
- **Async Operations:** Non-blocking data operations

### 4.5 Error Handling and Edge Cases

#### Error Categories:
1. **Data Errors:** Invalid LAS files, missing columns
2. **Rendering Errors:** Graphics context issues
3. **Synchronization Errors:** Component state mismatches
4. **User Error:** Invalid operations, out-of-range inputs

#### Handling Strategy:
- **Graceful Degradation:** Fallback to simpler rendering
- **User Feedback:** Clear error messages with recovery options
- **State Recovery:** Automatic rollback on failure
- **Logging:** Comprehensive error logging for debugging

## 5. Migration Strategy

### Phase 1: Foundation (Week 1-2)
1. Create new architecture classes
2. Implement core interfaces
3. Set up test infrastructure
4. Create migration utilities

### Phase 2: Integration (Week 3-4)
1. Integrate with existing UI components
2. Implement backward compatibility layer
3. Migrate existing functionality
4. Test integration points

### Phase 3: Enhancement (Week 5-6)
1. Add new features (visibility management, etc.)
2. Implement performance optimizations
3. Add comprehensive error handling
4. Create user documentation

### Phase 4: Validation (Week 7-8)
1. Comprehensive testing
2. Performance benchmarking
3. User acceptance testing
4. Bug fixing and refinement

## 6. Risk Assessment and Mitigation

### Technical Risks:
1. **Performance Regression**
   - **Mitigation:** Extensive benchmarking, optimization focus
   - **Fallback:** Maintain old implementation as backup

2. **Integration Complexity**
   - **Mitigation:** Incremental migration, compatibility layer
   - **Fallback:** Phase-by-phase rollout

3. **Memory Issues**
   - **Mitigation:** Memory profiling, efficient data structures
   - **Fallback:** Streaming data processing

### Project Risks:
1. **Scope Creep**
   - **Mitigation:** Strict requirement adherence, change control
   - **Fallback:** Minimum viable product first

2. **Timeline Slippage**
   - **Mitigation:** Agile methodology, regular milestones
   - **Fallback:** Prioritize core functionality

3. **Quality Issues**
   - **Mitigation:** Comprehensive testing, code reviews
   - **Fallback:** Extended testing phase

## 7. Deliverables

### 7.1 Architectural Design Document (This Document)
- Complete system architecture
- Class diagrams and interfaces
- Data flow diagrams
- Migration strategy

### 7.2 Implementation Plan
- Detailed task breakdown
- Timeline with milestones
- Resource allocation
- Risk management plan

### 7.3 Technical Specifications
- API documentation
- Data format specifications
- Configuration guidelines
- Integration protocols

### 7.4 Quality Assurance Plan
- Test strategy
- Performance benchmarks
- Acceptance criteria
- Deployment checklist

## 8. Success Metrics

### Technical Metrics:
- **Performance:** < 100ms rendering time
- **Memory:** < 50MB peak usage
- **Reliability:** 99.9% uptime in testing
- **Compatibility:** 100% backward compatibility

### User Experience Metrics:
- **Usability:** Intuitive controls (user testing score > 4/5)
- **Responsiveness:** < 50ms UI response time
- **Learnability:** < 5 minutes to basic proficiency
- **Satisfaction:** User feedback score > 4/5

### Project Metrics:
- **Timeline:** On schedule delivery
- **Quality:** < 1 critical bug per 1000 lines
- **Maintainability:** Code complexity score < 10
- **Documentation:** 100% API documentation coverage

## 9. Conclusion

This architectural design provides a comprehensive solution for the LAS curve pane issues while establishing a robust foundation for future enhancements. The hybrid rendering approach balances performance with flexibility, the unified scroll coordination ensures seamless user experience, and the modular architecture supports extensibility.

The implementation follows best practices in software architecture, emphasizing separation of concerns, clean interfaces, and maintainable code structure. The migration strategy minimizes disruption while delivering significant improvements in functionality and user experience.

**Next Steps:** Proceed to detailed implementation planning and begin Phase 1 foundation work.