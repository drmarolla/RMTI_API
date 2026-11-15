# Elasticity in the RMTI

**Research prototype. Not validated against outcomes. Synthetic examples only. Not a medical device.**

`rmti_elasticity.py` evaluates properties that follow from the RMTI residual-risk expression, `R = L · E · V · (1 − ρ)`, by taking logarithms and differentiating. It adds no new model equation.

## Definition

The elasticity of R with respect to a term X is the proportional change in R per proportional change in X, with the other terms held fixed:

    ε_X = (∂R/∂X) · (X/R) = ∂ln R / ∂ln X

It is unit-free, so terms measured on different scales can be compared.

## Elasticities of RMTI quantities

| Quantity (with respect to) | Elasticity | Meaning in RMTI applications |
|---|---|---|
| R (L), R (E), R (V) | +1 | A proportional change passes one-to-one into residual risk |
| R (ρ) | −ρ/(1 − ρ) | Leverage of resilience grows with baseline ρ: −0.25 at 0.2, −1 at 0.5, −4 at 0.8 |
| R (ρ_care), ρ_bio fixed | −ρ_care/(1 − ρ_care) | Leverage of care-system capacity (for example delivery of surveillance or of a program) |
| R (ρ_bio), ρ_care fixed | −ρ_bio/(1 − ρ_bio) | Leverage of biological capacity |
| EAL (L), EAL (C) | +1 | Consequence weighting passes one-to-one into the severity index |
| EAL (ρ) | −ρ/(1 − ρ) | As for R |
| R(t) (filtered drive d) | k·d/(v_lo + k·d) < 1 | See below |

`ρ_bio` and `ρ_care` are combined as `ρ = 1 − (1 − ρ_bio)(1 − ρ_care)` (see `rmti_resilience_components.py`), so R is proportional to `(1 − ρ_care)` when `ρ_bio` is fixed.

## Logarithm and trajectory attribution

    ln R = ln L + ln E + ln V + ln(1 − ρ)

The change in ln R between two states is the sum of the changes in the four logs, which attributes a changing R to its terms (`log_decomposition`). With L, E and ρ fixed, R changes by exactly the same percentage as V (for example, V* 0.769 → 0.647 gives −15.9% in both).

## Relation to the time-indexed layer

In `rmti_dynamic.py` (Marolla 2026d), V*(t) = v_lo + (v_hi − v_lo)·clip(d, 0, y_max)/y_max, where d = level + look_ahead·slope with the filter on, or the observed indicator with the filter off. At each cycle R(t) has the same elasticities as above (`trajectory_decomposition` takes the rows returned by `run_trajectory`). With k = (v_hi − v_lo)/y_max and the clip inactive, the elasticity of R with respect to the filtered drive is

    ε_d = k·d / (v_lo + k·d)

which is below 1 because V* has a floor v_lo. For v_lo = 0.35, v_hi = 0.85, y_max = 10 and d = 8, ε_d ≈ 0.53: a 10% change in the filtered indicator changes R by about 5.3%.

## Usage

```python
import rmti_elasticity as el

el.elasticity_rho(0.5)                          # -1.0
el.relative_R_error_from_rho_error(0.8, 0.05)   # -0.25: an absolute error of 0.05 in rho at 0.8 gives -25% in R
el.elasticity_wrt_drive(8, 0.35, 0.85, 10)      # 0.533...
el.log_decomposition({"L": .25, "E": .6, "V": .769, "rho": .3},
                     {"L": .25, "E": .6, "V": .647, "rho": .3})["pct_change_R"]   # -15.9
```

Run the tests from this folder (the integration test is skipped if the reference implementation is not found):

```
RMTI_PY_PATH=/path/to/rmti-python python -m unittest -v test_rmti_elasticity
```

## Caveats

Elasticities are local; they assume the other terms are fixed and independent; they say nothing about cost or whether a term can be changed; and R is a relative index, not a probability. In a model where V and ρ are correlated (for example fibrosis lowering reserve), "others fixed" does not hold.

## Where this is cited

Section 1, Section 3, Equations S1, S2, S9 and S10 and Supplementary Table 4 of the Supplementary Material to *Toward a Multidimensional Framework for Predicting Disease Trajectories in MASLD* (Baffy and Marolla). Add the release DOI here once archived.

## License

Code: Apache License 2.0 (see the `LICENSE` file at the repository root).
