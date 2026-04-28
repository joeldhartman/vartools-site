# Miscellaneous

Commands that don't fit cleanly into any of the other command categories.

---

## `-findblends`

**Syntax**
```
-findblends
    matchrad ["radec"] ["xycol" xcol ycol]
    < "fix" period | "list" ["column" col] | "fixcolumn" <colname | colnum> >
    ["starlist" starlistfile] ["zeromag" zeromagval] ["nofluxconvert"]
    ["Nharm" Nharm] ["omatches" outputmatchfile]
```

**Description**

Determine whether a detected periodic signal is likely due to contamination (blending) from a nearby variable star. For each potential variable, the routine measures the flux amplitude of all nearby light curves and reports the one with the highest amplitude. A light-curve list (`-l`) is required with x and y coordinates as additional columns.

Python equivalent: [`findblends`](../python/commands/misc.md#findblends-search-for-blended-transits).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `matchrad` | Matching radius (arcseconds if `"radec"`, pixels otherwise). |
| `"radec"` | Treat the x/y columns as RA and Dec in degrees; `matchrad` is then arcseconds. |
| `"xycol" xcol ycol` | Columns in the input list for x and y (default: next two available). |
| Period source | One of `"fix" period`, `"list" ["column" col]`, or `"fixcolumn" <col>`. |
| `"starlist" starlistfile` | Match against an external catalogue instead of the input list. Format: `lcname x y`. |
| `"zeromag" zeromagval` | Zero-point magnitude for the mag→flux conversion (default 25.0). |
| `"nofluxconvert"` | Skip the magnitude-to-flux conversion (input already in flux units). |
| `"Nharm" Nharm` | Harmonics for the Fourier amplitude measurement (default 2; 0 = sinusoid). |
| `"omatches" outputmatchfile` | Write per-target lists of matching stars and their flux amplitudes to this file. |

**Output columns**: `Findblends_VarName_N` (name of the brightest blended variable in flux), `Findblends_FluxAmp_N` (its flux amplitude).

**Examples**

**Example 1.** The list `EXAMPLES/lc_list_testblend` contains two LCs along with their x/y coordinates. We search both for a sinusoidal signal with `-LS` and then check for blending — any stars within 2 pixels of each other are potential blends, and the period from `-LS` is used for the amplitude measurement (read from the output column with `fixcolumn`). Running this gives `EXAMPLES/2` as the source of the variability for both LCs since it has the higher flux amplitude.

```bash
vartools -l EXAMPLES/lc_list_testblend -header \
    -LS 0.1 10. 0.1 1 0 \
    -findblends 2.0 fixcolumn LS_Period_1_0
```

---

