# Control Flow and Output

Commands and options for conditional execution, saving and restoring light curve state, writing output light curves, printing variables, modifying column names, and calling external Python or R code.

---

## `-addfitskeyword`

**Syntax**
```
-addfitskeyword
    keyword
    ["combinelc" lcnumvar]
    < "TDOUBLE" | "TINT" | "TLONG" | "TSTRING" >
    < "fix" val | "var" variable >
    ["comment" commentstring]
    ["primary" | "extension"]
    ["append" | "update"]
```

**Description**

Add a keyword to the header of any subsequently output FITS-format light curves.

Python equivalent: [`addfitskeyword`](../python/commands/control-flow.md#addfitskeyword-add-a-fits-keyword).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `keyword` | The FITS header keyword to add. When `"combinelc"` is used, this should be a format string containing `%d` which is replaced by the unique values of `lcnumvar`. |
| `"combinelc" lcnumvar` | Emit one keyword per unique value of `lcnumvar`; the value of the associated variable is taken at the first occurrence of each new `lcnumvar`. |
| `"TDOUBLE" / "TINT" / "TLONG" / "TSTRING"` | Data type for the keyword value. |
| `"fix" val` | Fixed constant value for all light curves. |
| `"var" variable` | Take the value from a VARTOOLS variable. |
| `"comment" commentstring` | Optional comment string for the FITS header entry. |
| `"primary" / "extension"` | Place the keyword in the primary FITS header (`primary`, default) or in the binary-table extension header (`extension`). |
| `"append" / "update"` | If the keyword already exists: `append` adds a duplicate; `update` (default) overwrites the value. |

**Examples**

**Example 1.** Convert the ASCII light curve `EXAMPLES/1` to a FITS-format light curve at `EXAMPLES/1.tmpout.fits`, attaching a string keyword `TMPKEY` to the primary header. The value comes from the input-list variable `x` (which evaluates to `"HELLO"` here) and a comment is included.

```bash
echo EXAMPLES/1 HELLO | \
vartools -l - -inlistvars x:2:string \
    -addfitskeyword "TMPKEY" TSTRING \
        var x \
        comment "a comment" \
    -o EXAMPLES/ nameformat "%s.tmpout.fits" fits
```

---

## `-changevariable`

**Syntax**
```
-changevariable
    < "t" | "mag" | "err" | "id" > var
```

**Description**

Reassign the internal role of the time (`t`), magnitude (`mag`), magnitude uncertainty (`err`), or image-identifier (`id`) variable to a different named column. Subsequent commands will use the new assignment. The original variable still exists; to restore it, issue `-changevariable mag mag`.

Python equivalent: [`changevariable`](../python/commands/control-flow.md#changevariable-reassign-standard-column-roles).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `"t"` / `"mag"` / `"err"` / `"id"` | Which built-in role to reassign. |
| `var` | Name of the existing light-curve column to promote to that role. |

**Examples**

**Example 1.** Run an LS period search, then use `-changevariable` to store the current time in a `phase` variable, phase-fold on the LS period, then swap `t` back before writing output so the light curve is sorted by time.

```bash
vartools -l EXAMPLES/lc_list \
    -LS 0.1 100.0 0.1 1 0 \
    -expr 'phase=t' \
    -changevariable t phase \
    -Phase ls \
    -changevariable t t \
    -o EXAMPLES/OUTDIR1 nameformat "%s.phase.txt" \
        columnformat "t:%17.9f,mag:%9.5f,err:%9.5f,phase:%9.5f" \
    -header
```

Output: a table with columns `Name`, `LS_Period_1_0`, `Log10_LS_Prob_1_0`, `LS_SNR_1_0` for each light curve in the list, plus one phase-folded output file per light curve.

---
## `-if` / `-elif` / `-else` / `-fi`

**Syntax**
```
-if <expression>

    [-command1 ... -commandN]

[-elif <expression>

    [-command1 ... -commandN]
]

[-else

    [-command ... -command]
]

-fi
```

**Description**

Make execution of VARTOOLS commands conditional on the evaluation of an analytic expression. If `expression` evaluates to `0` (when cast to an integer), the commands in that branch are skipped; any non-zero integer value causes the branch to execute. `-elif <expression>` and `-else` provide alternative branches evaluated in order; the construct is terminated by `-fi`. Nested `-if`/`-elif`/`-else`/`-fi` constructs are allowed. Any conditional construct not explicitly terminated with `-fi` is assumed to be closed after the last command on the command line.

Python equivalent: [`ifcmd` / `elifcmd` / `elsecmd` / `ficmd`](../python/commands/control-flow.md#ifcmd-elifcmd-elsecmd-ficmd-conditional-execution).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `expression` | Analytic expression evaluated to decide whether to execute the branch. May reference any variable computed by a preceding command (run `-headeronly` to see variable names), light-curve vectors, or scalar constants. Branch is taken if the expression evaluates to a non-zero integer. See the [Analytic Expressions](expressions.md) reference for supported operators, functions, and constants. |

!!! caution
    Conditional constructs are **ignored** by commands that process all light curves simultaneously (e.g., `-SYSREM`, `-findblends`) and by the `-savelc` and `-restorelc` commands.

**Examples**

**Example 1.** Run an LS period search and apply a harmonic filter only to light curves with a strong periodicity.

```bash
vartools -l EXAMPLES/lc_list \
    -LS 0.5 20.0 4.0 1 0 \
    -if 'Log10_LS_Prob_1_0 < -10.0' \
        -harmonicfilter ls 2 0 1 EXAMPLES/OUTDIR1 \
    -fi
```

**Example 2.** Use nested `-if`, `-elif`, `-else`, `-fi` constructs to apply different statistics depending on the values returned by `-rms`.

```bash
vartools -l EXAMPLES/lc_list -rms \
    -if 'RMS_0>10*Expected_RMS_0' \
        -if 'RMS_0 > 0.1' \
            -stats mag stddev \
        -else \
            -stats mag pct30 \
        -fi \
    -elif 'Npoints_0>3900' \
        -stats mag kurtosis \
    -else \
        -rms \
    -fi \
    -header
```

---

## `-o`

**Syntax**
```
-o
    <outdir | outname>
    ["nameformat" formatstring | "namecommand" command |
     "namefromlist" ["column" col]]
    ["columnformat" formatstring | "allcols"]
    ["delimiter" delimchar]
    ["fits"] ["copyheader"] ["logcommandline"] ["noclobber"]
```

**Description**

Output the current light curve(s) to files or to stdout. When processing a list of light curves, provide an output directory (`outdir`); when processing a single light curve, provide a filename (`outname`). Use `"-"` for `outname` to write to stdout (combine with `-quiet` or `-redirectstats` to avoid mixing the statistics table with the light curve data). By default, output files are named `$outdir/$inname` where `$inname` is the base filename of the input light curve, and contain three whitespace-separated columns: `t`, `mag`, `err`.

Python equivalent: [`o`](../python/commands/control-flow.md#o-output-light-curve).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `outdir` / `outname` | Directory (when processing a list) or filename (when processing a single LC). Use `"-"` for stdout. |
| `"nameformat" formatstring` | Override the naming convention. Tokens: `%s` = input basename; `%b` = basename stripped of its last extension; `%d` = light-curve number (from 1); `%0nd` = zero-padded; `%%` = literal `%`. |
| `"namecommand" command` | Execute a shell command to determine the output name. The string `echo $fulllcname $outdir $lcnum` is piped into `command`; its stdout is the output filename. |
| `"namefromlist" ["column" col]` | Read the output filename from the input list file. `outdir` is prepended. By default the next unused column is used. |
| `"columnformat" formatstring` | Comma-separated list of `varname[:printf_format]` entries (e.g. `t:%.17g,mag:%.5f,err:%.5f,xpos:%.3f`). For FITS output the text after the first `:` is the column unit, a second `:` introduces a description, and a third `:` an alternative units string. |
| `"allcols"` | Write every light-curve-vector variable defined by commands *before* this `-o`, with a type-appropriate default `printf` format and a `# name1 name2 …` header line for ASCII. Mutually exclusive with `"columnformat"`. |
| `"delimiter" delimchar` | Column separator character (default: single space). |
| `"fits"` | Write FITS binary table. The `.fits` extension is appended if not already present. |
| `"copyheader"` | Copy the primary FITS header from the input light curve to the output (FITS input only). |
| `"logcommandline"` | Log the full VARTOOLS command line to the output file header. |
| `"noclobber"` | Do not overwrite existing files; VARTOOLS terminates if a file already exists. |

**Examples**

**Example 1.** Use `nameformat` and `columnformat` to write phase-folded light curves with custom filenames and a custom column layout. The `-LS` command finds the period; `-expr` defines a new vector `phase` initialized to the times in the light curves; `-changevariable` causes subsequent commands to use `phase` where time would normally be used. Together with `-Phase`, this stores the light curve phase for the LS period in `phase`. The first light curve (`EXAMPLES/1`) yields output to `EXAMPLES/OUTDIR1/file_1_00001_simout.txt`, the second to `EXAMPLES/OUTDIR1/file_2_00002_simout.txt`, and so on. Without `columnformat`, only `t`, `mag`, and `err` would be output, formatted as `%17.9f`, `%9.5f`, and `%9.5f` respectively.

```bash
vartools -l EXAMPLES/lc_list -header \
    -LS 0.1 100.0 0.1 1 0 \
    -expr phase=t \
    -changevariable t phase \
    -Phase ls \
    -o EXAMPLES/OUTDIR1 \
        nameformat "file_%s_%05d_simout.txt" \
        columnformat "t:%11.5f,phase:%8.5f,mag:%7.4f,err:%7.4f"
```

Output table:
```
#Name LS_Period_1_0 Log10_LS_Prob_1_0 LS_SNR_1_0
EXAMPLES/1     0.97821072 -452.25157   41.33409
EXAMPLES/2     1.23440877 -704.49194   58.45119
EXAMPLES/3     1.14786351  -30.00548   15.74701
EXAMPLES/4    14.81290524  -59.52748   13.11947
EXAMPLES/5     7.40645262  -53.86771   10.01489
EXAMPLES/6     0.96306814  -42.42348   10.53479
EXAMPLES/7     0.32704113  -11.84669    4.77871
EXAMPLES/8     3.07991099  -88.30735   15.34709
EXAMPLES/9     7.23420953  -37.93155   14.15476
EXAMPLES/10     0.96906857  -40.55309   11.32727
```

Sample output (`head -3 EXAMPLES/OUTDIR1/file_1_00001_simout.txt`):
```
53725.17392  0.00000 10.0850  0.0012
53726.15280  0.00068 10.0886  0.0009
53726.15378  0.00169 10.0918  0.0009
```

---

## `-print`

**Syntax**
```
-print
    var1[,var2,var3...]
    ["columnnames" col1[,col2,col3...]]
    ["format" fmt1[,fmt2,fmt3...]]
```

**Description**

Print the value of one or more variables to the output statistics table. This is the primary way to include user-computed scalars, list-input columns, or values copied from prior commands in the output. If a variable is a light-curve vector (length equal to the number of points in the light curve), only the value at the **first** point is output.

Python equivalent: [`print_cols`](../python/commands/control-flow.md#print_cols-emit-user-computed-variables-to-the-output-table).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `var1[,var2,...]` | Comma-separated list of previously defined variable names to print. |
| `"columnnames" col1[,col2,...]` | Override the default output column names. By default columns are named `Print_${varname}_${varnum}_${commandnum}`. The command-number suffix `_${commandnum}` is still appended unless `-columnsuffix` is used. |
| `"format" fmt1[,fmt2,...]` | Printf-style format codes for each value (e.g., `%.6f`). |

**Examples**

**Example 1.** Print five variables to the output ASCII table — the light-curve file name (read in as the first column in the list), the `x` and `y` coordinates (read in as the second and third columns), the `RMS_0` output column from `-rms`, and the first term in the `mag` vector read from each light curve. Since `mag` is a light-curve column vector, this command prints only its first value.

```bash
cat EXAMPLES/lc_list_tfa_sr_* | \
vartools -l - \
    -inlistvars name:1:string,x:2,y:3 -rms \
    -print name,x,y,RMS_0,mag format %20s,%.2f,%.2f,%.3f,%.3f \
    -header
```

---

## `-savelc` / `-restorelc`

Checkpoint and restore the in-memory light-curve state. Useful for running several analysis branches from the same starting point without re-reading files, and for restoring the original light curve after a destructive transformation.

Python equivalent: [`savelc` / `restorelc`](../python/commands/control-flow.md#savelc-restorelc-light-curve-state-snapshots).

**Quick reference**

```
-savelc
```

Save the current light curve state.

```
-restorelc
    savenumber ["vars" var1,var2,...]
```

Restore the light curve to the state saved at the `savenumber`-th call to `-savelc`.

**Examples**

**Example 1.** Running a battery of variability selection algorithms on a list of light curves in parallel, using `-savelc` and `-restorelc` to branch from different saved states.

```bash
vartools -l EXAMPLES/lc_list -header -numbercolumns \
    -nobuffer -parallel 4 \
    -savelc \
    -clip 5.0 1 \
    -savelc \
    -LS 0.1 100. 0.1 3 0 clip 5. 1 \
    -aov 0.1 100. 0.1 0.01 1 0 clip 5. 1 \
    -restorelc 1 \
    -clip 10.0 1 \
    -BLS q 0.01 0.1 0.1 20. 10000 200 7 2 0 0 0 \
    -restorelc 2 \
    -changeerror \
    -autocorrelation 0. 30. 0.1 EXAMPLES/OUTDIR1/ \
  > EXAMPLES/OUTDIR1/vartools.out
```

---

