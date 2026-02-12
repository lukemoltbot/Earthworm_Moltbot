# CoalLog v3.1 Lithology Geophysical Signature Reference

## Research Summary

This document provides characteristic geophysical signatures for all lithology types defined in the CoalLog v3.1 standard. The information is based on standard geological well logging principles and interpretation guidelines.

## Complete Lithology Geophysical Signature Table

| Lithology Code | Lithology Type | Short-space Density (g/cc) | Long-space Density (g/cc) | Gamma Ray (API) | Resistivity (ohm-m) | Key Distinguishing Features |
|----------------|----------------|----------------------------|---------------------------|-----------------|---------------------|-----------------------------|
| **CO** | Coal | 1.2-1.8 | 1.2-1.8 | 10-50 | 100-1000+ | Very low density, low gamma, high resistivity |
| **ZS** | Coaly Sandstone | 2.0-2.4 | 2.0-2.4 | 50-100 | 10-100 | Moderate density, elevated gamma from coal content |
| **XS** | Carbonaceous Sandstone | 2.2-2.5 | 2.2-2.5 | 60-120 | 20-150 | Similar to sandstone but with organic carbon |
| **CL** | Clay | 2.4-2.8 | 2.4-2.8 | 100-200 | 1-10 | High gamma, low resistivity, high density |
| **SI** | Silt | 2.5-2.7 | 2.5-2.7 | 80-150 | 5-20 | Moderate gamma, intermediate properties |
| **SA** | Sand | 2.6-2.8 | 2.6-2.8 | 20-80 | 50-500 | Low gamma, high resistivity, clean sand |
| **GV** | Gravel | 2.6-2.8 | 2.6-2.8 | 20-60 | 50-300 | Low gamma, variable depending on composition |
| **OB** | Cobbles | 2.6-2.8 | 2.6-2.8 | 20-60 | 50-300 | Similar to gravel, coarse-grained |
| **BO** | Boulders | 2.6-2.8 | 2.6-2.8 | 20-60 | 50-300 | Large-scale gravel deposits |
| **SS** | Sandstone | 2.3-2.7 | 2.3-2.7 | 20-100 | 20-200 | Variable based on clay content |
| **CG** | Conglomerate | 2.4-2.8 | 2.4-2.8 | 30-100 | 30-200 | Mixed grain sizes, variable signatures |
| **M1** | Conglomerate (>65% matrix) | 2.5-2.8 | 2.5-2.8 | 50-150 | 10-100 | Matrix-dominated, higher gamma |
| **M2** | Conglomerate (35-65% matrix) | 2.4-2.7 | 2.4-2.7 | 40-120 | 20-150 | Balanced matrix and clasts |
| **M3** | Conglomerate (<35% matrix) | 2.3-2.6 | 2.3-2.6 | 30-80 | 50-250 | Clast-dominated, cleaner |
| **AL** | Alluvium | 2.2-2.6 | 2.2-2.6 | 40-120 | 20-150 | Mixed sediments, variable |
| **BR** | Breccia | 2.4-2.8 | 2.4-2.8 | 40-120 | 20-150 | Angular clasts, variable matrix |
| **FB** | Fault Breccia | 2.4-2.8 | 2.4-2.8 | 40-150 | 10-100 | Often clay-rich from fault gouge |
| **TF** | Tuff | 2.0-2.5 | 2.0-2.5 | 100-200 | 10-50 | Volcanic ash, high gamma |
| **TT** | Tuffite | 2.2-2.6 | 2.2-2.6 | 80-180 | 15-80 | Mixed volcanic/sedimentary |

## Geophysical Log Interpretation Principles

### 1. Density Logs
- **Short-space density**: Measures electron density in the borehole wall region
- **Long-space density**: Measures deeper formation density, less affected by borehole conditions
- **Coal**: Distinctively low (1.2-1.8 g/cc) due to organic composition
- **Sandstones**: Moderate (2.3-2.7 g/cc) depending on mineralogy
- **Clays/Shales**: Higher (2.4-2.8 g/cc) due to compaction

### 2. Gamma Ray Log
- Measures natural radioactivity from potassium, uranium, thorium
- **Clays/Shales**: High (100-200 API) - potassium in clay minerals
- **Clean Sands**: Low (20-80 API) - quartz is non-radioactive
- **Coal**: Very low (10-50 API) - organic matter lacks radioactive elements
- **Carbonaceous rocks**: Elevated gamma due to uranium association with organic matter

### 3. Resistivity Log
- Measures electrical resistance of formation
- **Coal**: Very high (100-1000+ ohm-m) - poor electrical conductor
- **Clays**: Very low (1-10 ohm-m) - conductive due to clay minerals and bound water
- **Clean Sands**: High (50-500 ohm-m) - depends on fluid content
- **Water saturation**: Reduces resistivity significantly

## Geological Context & Application

### Coal Measures Stratigraphy
- **Coal seams (CO)**: Primary target, distinctive low density/low gamma
- **Roof/floor strata**: Often claystones (CL) or siltstones (SI)
- **Sandstone channels (SS)**: Potential aquifers, reservoir rocks
- **Carbonaceous zones (ZS, XS)**: Transitional facies

### Depositional Environments
- **Fluvial systems**: Sandstones (SS), conglomerates (CG), alluvium (AL)
- **Lacustrine**: Clays (CL), silts (SI), carbonaceous muds
- **Volcanic**: Tuffs (TF), tuffites (TT)
- **Tectonic**: Fault breccias (FB), breccias (BR)

### Practical Interpretation Guidelines

1. **Coal Identification**:
   - Density < 1.8 g/cc
   - Gamma Ray < 50 API
   - Resistivity > 100 ohm-m
   - Sharp boundaries with surrounding rocks

2. **Clay/Shale Identification**:
   - Density > 2.4 g/cc
   - Gamma Ray > 100 API
   - Resistivity < 20 ohm-m
   - Often form seals/cap rocks

3. **Sandstone Identification**:
   - Density 2.3-2.7 g/cc
   - Gamma Ray < 100 API (cleaner = lower)
   - Resistivity variable (20-500 ohm-m)
   - Potential reservoir/aquifer

4. **Mixed Lithologies**:
   - Intermediate values indicate mixtures
   - Carbonaceous sandstones (ZS, XS): Elevated gamma
   - Silty clays: Moderate gamma, intermediate density

## Data Sources & References

1. **CoalLog v3.1 Standard** - AusIMM (Australasian Institute of Mining and Metallurgy)
2. **Lithology Dictionary**: `src/assets/litho_lithoQuals.json` from Earthworm project
3. **Standard Well Log Interpretation** - Schlumberger, Baker Hughes guidelines
4. **Coal Geology References**:
   - Thomas, L. (1992). Handbook of Practical Coal Geology
   - Rider, M.H. (1996). The Geological Interpretation of Well Logs
5. **Geophysical Logging Principles**:
   - Serra, O. (1984). Fundamentals of Well-Log Interpretation
   - Ellis, D.V. (1987). Well Logging for Earth Scientists

## Limitations & Considerations

1. **Local Variations**: Actual values depend on specific basin geology
2. **Fluid Effects**: Water/hydrocarbon content affects resistivity
3. **Borehole Conditions**: Washouts, mud invasion affect log quality
4. **Tool Calibration**: Different logging tools may give slightly different readings
5. **Depth of Investigation**: Each tool measures different volumes

## Recommended Workflow for Earthworm Application

1. **Load lithology dictionary** from `litho_lithoQuals.json`
2. **Import geophysical logs** (LAS, DLIS formats)
3. **Apply characteristic ranges** from this reference table
4. **Implement automated lithology identification** based on log responses
5. **Provide uncertainty estimates** for mixed/transitional zones
6. **Allow manual override** for expert interpretation

This reference table enables automated lithology identification from geophysical logs within the Earthworm Borehole Logger application, supporting geological interpretation and coal resource estimation.