# Version History

### Version 1.6 — May 12, 2026

Changes include:

1. Renamed `-Killharm` to `-harmonicfilter`, retaining `-Killharm` as a backward-compatible synonym.
2. Added `-fourierfilter`, a full-band Fourier-domain filter.
3. Added `-setlcname` option to override the `stdin` placeholder used as the LC name when input comes from `-i -`.
4. Added `allcols`, `changesuffix`, `gzip`, and `bzip2` keywords to `-o`, and auto-detection of compressed light-curve inputs (`.gz`, `.bz2`, `.fits.gz`, `.fits.fz`, `.fits.Z`, `.fits.bz2`) on `-i` and `-l`.
5. Added `outputcolumn` keyword to `-expr` (used with `listvar`/`scalar`/`const`) that exposes the computed value in the result table.
6. Reject duplicate statistic names in `-stats` at parse time.
7. Added aggregate functions (`mean`, `median`, `stddev`, `sum`, `vmin`, `vmax`, `MAD`, `weightedmean`, `wmedian`, `meddev`, `medmeddev`, `kurtosis`, `skewness`, `pct<n>`, `wpct<n>`) to the analytic-expression engine, plus parse-time constant folding and per-LC aggregate-call memoisation, which can speed common O(N²) patterns by orders of magnitude.
8. Fixed `parseonedelim*()` STRING corruption (regression from the r5380 combinelcs change in 1.51).
9. Fixed `-nonlinfit` `fitmask` heap overflow and missing variable resolution that caused SIGSEGV in MCMC fitting, and a `-nonlinfit omodel` token-order bug that caused `-oneline` (and any subsequent global option) to be silently swallowed.
10. Fixed `-linfit format` keyword silently swallowing the following argv token.
11. Fixed `-linfit save_model` to honour `model_nameformat`.
12. Fixed `-BLSFixPerDurTc save_phcurve` buffer overflow that triggered a glibc abort.
13. Fixed `-addnoise wavelet` last-point out-of-bounds read.
14. Fixed `-python` and `-R` undersize allocations under `-readall`.
15. Fixed `-Starspot fitstarspot_amoeba` uninitialised index.
16. Fixed multiple format-string vulnerabilities in output and Python/R callback code.
17. Fixed `vartools -help` and `vartools -example` output rendering literal `%%` instead of `%` in many help strings.
18. Added the `libvartoolspipeline.so` shared library providing an in-process embedding API for external programs.
19. Added `make install-python` and `make check-asan` build targets.
20. Updated `configure.ac` to handle NumPy 2.x include layout.
21. Initial release of `pyvartools`, a Python interface to VARTOOLS — see the [Python API documentation](python/index.md) for details.

---

### Version 1.52 — March 19, 2026

Changes include:

1. Added examples for the `-difffluxtomag`, `-restoretimes`, and `-sortlc` commands.
2. Fixed typo in `-restoretimes` description.
3. Fixed `-TFA` syntax display to correctly show `use_lc_errors` and `weight_by_template_stddev` as sub-options of `trend_coeff_priors`.
4. Added `noinitmark` sub-option of `markrestrict` to `-restricttimes` syntax display.

---

### Version 1.51 — May 27, 2025

Changes include:

1. Modified usage of semaphores to fix error preventing parallel processing on Mac OS X.
2. Sort the TFA template light curves by time for the case where FITS files are used for the templates and matching is done on time.
3. Added `markclip` option to `-clip`, and `clip`, `fitmask` and `outfitmask` options to `-TFA` and `-TFA_SR`.
4. Added `fitmask` option to `-linfit` and `maskpoints` option to `-stats`.
5. Added `-hatpiflag usercommand`.
6. Added mutexes for cspice to allow parallel processing with this library.
7. Added `maskpoints` option to the `-rms`, `-rmsbin`, `-chi2`, `-chi2bin` and `-decorr` commands, and fixed bug in `-chi2bin` and `-rmsbin` that would lead to invalid results if NaN values were included in the input light curve.
8. Added `maskpoints` option to the `-binlc`, `-changeerror`, `-ensemblerescalesig`, `-rescalesig`, `-LS` and `-BLS` commands.
9. Added `markrestrict` option to `-restricttimes` command.
10. Added `maskpoints` option to `-BLSFixPer`, `-BLSFixDurTc`, `-BLSFixPerDurTc`, and `-aov` commands, fixed bug in recent commit for `-linfit`.
11. Added `dates_Jstet` file for the `-Jstet` example.
12. Added `mask` option for the `-alarm`, `-expr`, `-aov`, `-autocorrelation`, `-dftclean`, `-Jstet` and `-wwz` commands, and added option to include additional description of light curve column in the FITS header COMMENTS in the `-o` command.
13. Added the `T0` option to `-binlc`.
14. Added bitwise OR, AND and complement operators to analytic expression evaluation.
15. Added `pointingflag` to `-hatpiflag` command.
16. Added `combinelcs` option to `-i` and `-l`, and `-addfitskeyword` command.
17. Added help and examples for the `-addfitskeyword` command.
18. Added the `append` and `update` options to `-addfitskeyword`.
19. Added `-stitch USERLIBS` command.
20. Added `-sortlc` command.
21. Fixed bug in `-expr` command affecting the `==` operator.
22. Added `namefromlist` option to `-o` command.
23. Added option to use `var` or `expr` keywords to set parameters for the `-BLS`, `-LS`, `-aov` and `-aov_harm` commands.
24. Added ability to specify `df` rather than `nfreq` for `-BLS`.
25. Added `-columnsuffix` option.
26. Added `-print` command.

---

### Version 1.41 — July 23, 2024

Changes include:

1. Modified to support compilation for older versions of Python without the `Py_SetPath` function.
2. Changes to build process for backward compatibility with Python 2.7.
3. Updated `configure.ac` to handle case where `python-config` sends usage error to stdout instead of stderr.
4. Added `skipfail` option to `-python` command.
5. Added `-splinedetrend USERLIB`.
6. Added some missing error handling to the `error2_noexit` function.
7. Fixed segfault in BLS that occurs when there are no out-of-transit points.
8. Added `expr`, `perJD expr`, and `perJD fromlc` input options for the `radec` and `input-radec` parameters of the `-converttime` command.
9. Added `expr` and `lcexpr` options to `coords` option for `-converttime`.
10. Added `isnan` function to analytic function list.
11. Added `-BLSFixPerDurTc` command.
12. Added outlier rejection to `-linfit`.
13. Added support for providing `all` as the entry for the column option to `-l`.
14. Changed `JDTOL` from global variable to member of `ProgramData` struct to avoid compile errors with new gcc.
15. Added `namecommand` option to `-o` command and `%b` option to `nameformat` option of `-o` command.

---

### Version 1.40 — April 15, 2022

Added `-match` command.

---

### October 30, 2020

Modified build tools and minor change to `runpython.c` to enable using `-python` with Python 3 under virtualenv.

---

### October 8, 2020

Removed implicit function declarations to enable compilation on Mac OS Catalina. Thanks to J. Rodriguez for the report.

---

### August 7, 2019

Changes include:

1. Catch cases where light curve is too short for `-BLS`, skip the light curve, and report a warning to stderr.
2. Fixed bug in `-restricttimes` causing incorrect behavior for the `JDlist` and `imagelist` options.

Thanks to L. Sweeney and V. Nascimbeni for the bug reports.

---

### April 17, 2019

Changes include:

1. Changed build to allow finding R library on macOS.
2. Fixed bug causing possible segfault in `-IFFT`.
3. Fixed bug causing buffer overflow in `-Starspot`.

---

### Version 1.38 — April 10, 2019

Changes include:

1. Added `-R` command.
2. Added `vars` option to `-restorelc` command.
3. Fixed bugs in the `-python` command related to specifying different `invars` and `outvars` variables, handling the `continueprocess` keyword, and transferring large amounts of data between VARTOOLS and Python.
4. Fixed bug in `-python` where the light curve header might be output multiple times.
5. Redirect stdout to stderr for output produced by the Python sub-process.

---

### Version 1.37 — April 4, 2019

Changes include:

1. Added `-FFT` and `-IFFT` commands and the `-ftuneven` extension command (thanks to J. Scargle for the code implementing the algorithm behind `-ftuneven`).
2. Modified build to allow specifying the cfitsio library path and include directory.
3. Ensured the status variable is initialized to zero in various FITS library calls.
4. Debugged thread locking problems with FITS input/output.
5. Debugged output of string variables to FITS.
6. Added `copyheader` and `logcommandline` options to `-o` command.
7. Modified `-TFA` and `-TFA_SR` to allow FITS format trend light curves.

---

### Version 1.36 — December 12, 2018

Changes include:

1. Added `reportharmonic` options to `-BLS`.
2. Modified `-converttime` to give an informative error message when performing BJD/TDB conversion without cspice.
3. Added `delimiter` option to `-inputlcformat` and fixed bug in `skipchar` option.
4. Added `bootstrap` option to `-LS`.
5. Fixed bug handling default skipping of commented lines when no `inputlcformat` was given.
6. Fixed bug in `-stats` command when multiple weighted-percentile commands are given on the stats string.
7. Fixed bug in computing output models for the `-RunBLSFixDurTc` command (thanks to X. Yao for the bug report).

---

### July 11, 2017

Fixed bug preventing compilation when Python is not detected. Thanks to K. Burdge for the bug report.

---

### Version 1.35 — July 3, 2017

Changes include:

1. Added `-python` command, `-restoretimes` command, and `expr` option to `-restricttimes`.
2. Added ability to index arrays in analytic expressions and added new `len` function analogous to the same function in Python.
3. Added `-f` option.
4. Added delimiter option to output.
5. Added new astrophysically relevant functions to the `astrofuncs` USERFUNCS library.
6. Fixed bug in `-aov` periodogram header, bug in memory allocation by `-BLS`, and bug causing NaN S/N estimates in some runs of `blsfixdurtc`.

---

### Version 1.34 — June 29, 2016

Changes include:

1. Added stellar density as an input option to `-BLS`.
2. Corrected bug in `parselc.c` preventing compilation when not using CFITSIO.
3. Fixed README to give correct output from new `-LS` command.

---

### Version 1.33 — December 9, 2015

Changes include:

1. Added `fixcolumn` option to `-BLSFixPer` and `expr` input options to `-Injecttransit` and `-BLSFixPer`.
2. Fixed bug in parsing command line for `-nonlinfit` command and added Gaussian Process Regression to output model file.
3. Fixed bug in computing log(det(Cov)) in `-nonlinfit`.
4. Fixed bug in header of GLS periodogram file.
5. Modified `-BLS` to allow searching for transits with periods up to the timebase of the observations; also added `stepP`, `steplogP`, `adjust-qmin-by-mindt` and `reduce-nbins` options to `-BLS`.
6. Added `opencommand` option to `-l`.
7. Modified calling options for `-binlc` and added `bincolumns`, `tnoshrink` and `bincolumnsonly` options to this command.
8. Fixed bug in `-Injecttransit` affecting duration of simulated transits for non-solar stars.
9. Added `bintime` option to `-addnoise` command.
10. Added line broadening profile to the `astrofuncs` library.

---

### Version 1.32 — June 6, 2015

Changes include:

1. Converted to GNU autobuild system to improve portability.
2. Changed loading of user-developed commands so that the necessary library is automatically loaded when a command is issued (the `-L` option is no longer needed).
3. Changed `-LS` to compute the Generalized Lomb-Scargle Periodogram instead of the traditional LS (the traditional version can still be called using the `noGLS` keyword).
4. Added the `modelvar`, `ophcurve` and `ojdcurve` keyword options to `-MandelAgolTransit`.
5. Added the `phasevar` and `startphase` keyword options to `-Phase`.

---

### Version 1.31 — April 29, 2015

Fixed bug in `restricttimes.c` preventing compilation. Thanks to T. Almeyda for the report.

---

### Version 1.31 — January 20, 2015

Changes include:

1. Added new commands: `-BlsFixDurTc`, `-copylc`, `-nonlinfit`, `-resample`, and `-WWZ`.
2. Significantly revised the `-addnoise` command to allow simulation of time-correlated noise via a Gaussian process model.
3. Modified routines for loading user-developed libraries (initialization function now requires more input values).
4. Auto-sort light curves on input.
5. Added `wmedian` and `wpct` statistics to `-stats` command.
6. Added `niter` and `median` options to `-clip`.
7. Added `format` option to `-linfit`.

---

### September 11, 2014

Fixed bug causing buffer overflow or segfault when outputting the model function in the `-Killharm` command. Thanks to T. Bovaird for the bug report.

---

### July 16, 2014

Corrected bugs related to compiling without libraries and to compiling on Windows.

---

### June 17, 2014

Fixed bug in `vartools_functionpointers.h` preventing compilation with the `PARALLEL` option turned off.

---

### Version 1.3 — April 22, 2014

Major update. Changes include:

1. New commands added: `-changevariable`, `-expr`, `-if -else -elif -fi`, `-linfit`, `-restricttimes`, `-stats`.
2. New options added: `-inputlcformat`, `-inlistvars`, `-showinputlistformat`, `-showinputlcformat`, `-log-command-line`, `-functionlist`, `-L` and `-F`.
3. New extension commands added: `-fastchi2`, `-jktebop`, `-macula`, `-magadd`.
4. Changed the `spec` keyword to `list` for all commands (more intuitive).
5. Changed the syntax for `-o` to allow greater control over output formatting.
6. Changed `-aov_harm` to correct for a singularity which can appear when applying the method to evenly sampled data (thanks to A. Schwarzenberg-Czerny for pointing this out).
7. Changed `-binlc` and `-clip` to handle all light curve related vectors, not just t, mag and err.
8. Allow reading in rows of arbitrary length from ASCII files.
9. Major new features include: the ability to handle analytic expressions and assign variable names to input vectors and scalars; the ability to read in many columns from a light curve as vectors and change the vectors which commands operate on using `-changevariable`; support for user-developed extensions (including adding custom commands and new functions for use with `-expr`, `-linfit`, etc.).

---

### July 18, 2013

Added Mac installation notes. Thanks to J. Pepper and his research team.

---

### May 15, 2013

Updated help for the `-Jstet` command to note a difference between the J statistic computed by VARTOOLS and that defined in Stetson's paper. Thanks to L. Macri for reporting this.

---

### Version 1.202 — April 23, 2012

Changes include:

1. Fixed bugs in `-converttime` related to the location of the observer and handling of `input-ppm`; also corrected bug in `-converttime` causing loss of timing precision from accumulated rounding errors. Time conversions are now precise to ~0.1 millisecond near JD2000.0.
2. Reworked the internal method for parsing light curve data; the old method can be restored by deleting `-D _USE_PARSELC` from the makefile.
3. Changed `-readformat` to allow reading in light curves that are missing one or more of the JD, mag, or sig columns.
4. Fixed memory leak in `-getampthresh`.
5. Added substantial code related to supporting user-developed extensions to VARTOOLS (not fully functional in this release and not compiled by default).

---

### February 8, 2012

Fixed bug in `-decorr` causing `LCColumn_?_coeff_err_?_?` to not be output correctly. Thanks to D. Flateau for the report.

---

### Version 1.201 — February 3, 2012

Fixed bug in `-BLSFixPer` causing incorrect periods to be printed to the ASCII output table when using `list`. Thanks to J. Pepper for the bug report.

---

### February 1, 2012

Changes include:

1. Fixed segfault when using `-inputlistformat` with `-SYSREM`.
2. Corrected a bug in the output table when combining `-header` and `-redirectstats`.

Thanks to D. Flateau for the bug report.

---

### November 10, 2011

Updated descriptions of some commands on the website.

---

### Version 1.2 — October 21, 2011

Significant changes including:

1. Added `-addnoise` and `-converttime` commands, and `-example`, `-inputlistformat` and `-parallel` options.
2. Significant internal revisions to allow for parallel processing of light curves (affecting many commands which had previously used global or static variables; there may be bugs introduced as a result).
3. Added options to most commands to specify the column number for parameters taken from the input list file.
4. Added `inpututc` option to `-readformat`.
5. Changed `-help` to only provide a brief synopsis of the program (`-help all` gives the previous behavior).
6. Changed `-MandelAgolTransit` and `-SoftenedTransit` to internally vary the initial and final transit epochs rather than the period and epoch, and improved the initial parameter estimates based on `-BLS`.
7. Added `dilute` option to `-Injecttransit` to simulate diluted transits.

---

### Version 1.158 — April 6, 2011

Changes include:

1. Added `fittrap` option to `-BLS` and `-BLSFixPer`, which fits a trapezoid transit at each peak period.
2. Added `nobinnedrms` option to `-BLS` (speeds up the run but suppresses the `BLS_SN` statistic; use when not relying on `BLS_SN` to select transits).
3. Added `ophcurve` and `ojdcurve` options to `-BLS`.
4. Fixed bug in `-BLS` which caused period "-1" peaks to be listed before the correct peaks when fewer than Npeaks periods were found.
5. Added `-oneline` option for easier to read output when processing a single light curve.

---

### Version 1.157 — April 5, 2011

Fixed bug in `-BLS` causing integer overflow for large frequency number searches. Thanks to B. Sipocz for pointing out the bug and the fix.

---

### Version 1.156 — March 1, 2011

Fixed bug in `-BLS` causing a memory leak. Thanks to R. Siverd for debugging this.

---

### Version 1.155 — February 25, 2011

Fixed bug in `-BLS` causing the wrong transit time center to be output. Thanks to T. Beatty for reporting the bug.

---

### Version 1.154 — February 14, 2011

Changes include:

1. Minor change to `inputoutput.c` to correct unpredictable behavior when reading FITS files (thanks to J. Rasor for reporting the bug).
2. Fixed bug related to the file names of BLS periodograms and added the version number to the help and usage functions (thanks to R. Siverd for the report/suggestion).

---

### Version 1.153 — February 10, 2011

Changes include:

1. Added the ability to read binary FITS table files.
2. Renamed the old `-fluxtomag` command as `-difffluxtomag` and added a new `-fluxtomag` command.
3. Added option to use amplitude spectra with `-dftclean`.
4. Added `replace` option to `-medianfilter` command.
5. Improvements to the `-Phase` command.
6. Fixed bug in `-starspot` which prevented the model from being output when no fitting was done.
7. Modified output of `-BLS` and `-BLSFixPer` to include the epoch of transit center for the first transit after the start of the light curve.

---

### Version 1.152 — August 13, 2009

Changes include:

1. Added the `-microlens` command.
2. Changed the DFT routine in `-dftclean` from the brute force to the FDFT algorithm.
3. Fixed a bug in the calculation of S/N for the `-LS` command.
4. Added GNU license.

---

### Version 1.151 — May 19, 2009

Added the `-findblends` command (thanks to Kris Stanek for the suggestion).

---

### Version 1.15 — March 3, 2009

Changes include:

1. Added `whiten` and `clip` options to `-aov`, `-aov_harm` and `-LS` commands. Also added SNR
   output to these commands, and the option to determine the SNR at a fixed period. Note that
   the default behavior for `-aov` now gives the AoV statistic and its SNR; previously it gave
   the SNR of the log AoV statistic, which tended to suppress detection significance for large
   amplitude variables. Use the `uselog` option to restore the previous behavior.
2. Added the `-Injecttransit` command.
3. Fixed a bug in the AoV peak finder that could cause it to miss the peak in some cases.
4. Fixed a bug in the `-MandelAgolTransit` algorithm that caused the transit to appear at the
   wrong phase for some values of omega. Changed `-MandelAgolTransit` to input/output omega in
   degrees.
5. Fixed an incompatibility between `-clip` and several other commands.
6. Added the `-savelc` and `-restorelc` commands.
7. Changed `-autocorrelation` to use the Discrete Correlation Function (binning is done on the
   ACF rather than on the light curve, which also yields error estimates for the ACF).
8. Added the ability to reference arbitrary previously computed statistics by output column name
   or number (not yet fully extended to all commands).
9. Added the option of reading in signals from a file to the `-GetLSAmpThresh` command.
10. Added the option of simultaneously fitting a Fourier series to a light curve with TFA to the
    `-TFA_SR` command.

---

### December 11, 2008

Changes include:

1. Changed `-Killharm` to allow different output formats.
2. Fixed a bug with the `phaserel` and `amprel` options to `-Injectharm`.
3. Added an example on injecting and recovering a simulated RR Lyrae signal.

---

### December 10, 2008

Substantial changes:

1. Added new commands: `-autocorrelation`, `-changeerror`, `-dftclean`, `-Injectharm`, and `-TFA_SR`.
2. Added new options: `-matchstringid`, `-quiet`, `-randseed`, `-numbercolumns`, `-listcommands`.
3. Changed the `-help` option to allow displaying help for individual commands.
4. Modified `-Killharm` to allow `injectharm` and `fix` options for inputting periods; also added the `fitonly` option and changed the output format/column headings.
5. Modified `-TFA` to allow specification of readformat of trend light curves.
6. Added `fitRV` options to `-MandelAgolTransit` (not fully debugged; not recommended for production use).

---

### September 25, 2008

Changed the `Mean_Mag` output for the `-Killharm` command to be the fitted mean rather than the statistical mean, in line with Example 2.

---

### September 22, 2008

Added `-nobuffer` option (thanks to Rob Siverd).

---

### August 18, 2008

Fixed segfault when reading long input lists (thanks to Josh Pepper).

---

### July 31, 2008

Added `-headeronly` option.

---

### July 2, 2008

Modified to allow input from stdin.

---

### May 27, 2008

Modified the `-BLS` and `-BLSFixPer` commands to output the number of points in transit, the number of transits, the number of points before and after transit, the red and white noise of the signal after removing the BLS model, and the signal-to-pink-noise ratio of the transit.

---

### May 25, 2008

Fixed segfault in `initialize_tfa` routine. Added examples. (Thanks to Rob Siverd.)

---

### March 26, 2008

Fixed memory leak in `-aov` command. (Thanks to David Nataf.)

---

### January 16, 2008

Fixed `isinf` portability problem. (Thanks to Alceste Bonanos.)

---

### November 26, 2007

Added `-SYSREM` and `-binlc` commands and the `-jdtol` option.

---

### November 19, 2007

Added `-TFA` and `-fluxtomag` commands.

---

### November 15, 2007

Added `-MandelAgolTransit`, `-GetLSAmpThresh`, and `-aov_harm` commands.
