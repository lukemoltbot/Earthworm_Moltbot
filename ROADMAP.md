# Earthworm Roadmap to Sale‑Ready

**Target Platform:** Windows (primary). Development/testing on macOS via VSCode.

**Audience:** Geologists.

**Pricing Model:** Upfront cost + monthly/yearly subscription option.

**Licensing:** Single‑computer license (prevents sharing). Subscription‑based activation.

---

## Phase 1: Stabilization & Bug Fixes

### 1.1 Dependency Audit & Environment
- [x] Convert `requirements.txt` from UTF‑16 to UTF‑8
- [ ] Install all dependencies in a clean virtual environment
- [ ] Verify the app launches and loads sample data
- [ ] Document setup steps for new developers

### 1.2 Known Bugs (to be identified)
- Run the app, test core workflows, log any crashes or unexpected behavior.
- Check error handling in data loading, processing, and export.
- Validate UI responsiveness and memory usage.

### 1.3 Code Quality
- Remove debug prints (replace with proper logging).
- Add exception handling for file I/O, missing columns, invalid user input.
- Ensure all PyQt6 signals/slots are properly disconnected to avoid memory leaks.

---

## Phase 2: Feature Completion

### 2.1 Missing Features (from user feedback)
- **Licensing System**
  - Generate and validate license keys tied to a machine fingerprint.
  - Subscription management (expiry, renewal).
  - Grace period and offline usage.
- **Export Enhancements**
  - Support additional output formats (CSV, PDF reports).
  - Customizable template fields.
- **Data Import**
  - Support for more well‑log formats (DLIS, LIS, etc.).
  - Drag‑and‑drop file loading.
- **Analysis Improvements**
  - Additional lithology classification algorithms.
  - User‑defined curve ranges and rules.
  - **Smart Interbedding** – improved algorithm (allows up to 3 lithologies, coarse interbedding detection).
  - **Row selection sync** – implemented.
  - **Click lithology unit to select table row** – implemented.

### 2.2 UI/UX Polish
- Modernize icons and color scheme.
- Improve layout responsiveness (resizable panels).
- Tooltips and inline help.
- Keyboard shortcuts.
- Progress indicators for long‑running operations.

---

## Phase 3: Packaging & Distribution

### 3.1 Packaging Decision
Evaluate options:
- **Standalone executable** (PyInstaller) – single `.exe`, easy for users.
- **Installer** (InnoSetup, NSIS) – professional installation flow.
- **Portable version** – no installation required.

**Recommendation:** PyInstaller + InnoSetup for Windows. Create a macOS `.app` bundle for testing.

### 3.2 Licensing Integration
- Embed license check at startup.
- Online activation/deactivation.
- Trial period (e.g., 14 days) with feature limitations.

### 3.3 Documentation
- User manual (PDF + in‑app help).
- Video tutorials (loading data, interpreting results).
- Developer guide (if open‑sourcing parts).

---

## Phase 4: Testing & Validation

### 4.1 Cross‑Platform Testing
- Windows (primary) – virtual machine or CI.
- macOS – Luke’s development environment.
- Linux – optional.

### 4.2 User Acceptance Testing (UAT)
- Recruit geologists to test real workflows.
- Collect feedback on usability, performance, and accuracy.

### 4.3 Performance & Scalability
- Profile memory usage with large LAS files.
- Optimize pandas operations and plotting.

---

## Phase 5: Launch Preparation

### 5.1 Pricing & Subscription Setup
- Decide on price points (upfront vs subscription).
- Set up payment gateway (Stripe, PayPal).
- Create license‑key generation backend.

### 5.2 Marketing Materials
- Website landing page.
- Feature highlights, screenshots.
- Download/ purchase flow.

### 5.3 Support & Maintenance
- Error‑reporting system (auto‑collect logs).
- Version‑update mechanism.
- Community forum or support email.

---

## Immediate Next Steps

1. **Finish dependency installation** and verify the app runs.
2. **Run the app** and document any bugs or missing features.
3. **Research licensing libraries** for Python (e.g., `license‑lib`, custom solution).
4. **Evaluate packaging tools** and create a proof‑of‑concept `.exe`.

---

*This roadmap is a living document. Update as we uncover more details.*