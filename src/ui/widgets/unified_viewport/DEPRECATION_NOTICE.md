# System B Deprecation Notice

**Effective Date:** 2026-03-01
**Status:** DEPRECATED
**Removal Target:** v2.0.0

## What is Deprecated

All components in this directory (src/ui/widgets/unified_viewport/) are part of System B (deprecated) and should not be used in new code.

## What to Use Instead

Use System A components from src/ui/graphic_window/:

| System B (Deprecated) | System A (Recommended) |
|----------------------|----------------------|
| UnifiedDepthScaleManager | DepthStateManager |
| PixelDepthMapper | DepthCoordinateSystem |
| ScrollingSynchronizer | ScrollSynchronizer |
| GeologicalAnalysisViewport | UnifiedGraphicWindow |
| ComponentAdapter | (Direct signal wiring) |

## Migration Path

1. Replace UnifiedDepthScaleManager instantiation with DepthStateManager
2. Inject DepthStateManager into widgets via __init__ parameter
3. Remove PixelDepthMapper (use DepthCoordinateSystem from state manager)
4. Replace GeologicalAnalysisViewport with UnifiedGraphicWindow
5. Wire signals directly instead of using ComponentAdapter

## Timeline

- **2026-03-01 to 2026-06-01:** Deprecation period (warnings issued)
- **2026-06-01:** Hard removal (System B components deleted)
- **After 2026-06-01:** Only System A components available

## Questions?

See src/ui/graphic_window/unified_graphic_window.py for System A examples.
