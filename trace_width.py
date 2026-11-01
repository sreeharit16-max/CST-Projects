"""
trace_width.py
--------------
Find the microstrip trace width W that gives a target characteristic
impedance Z0, from:
    - substrate height h
    - relative permittivity er
    - required impedance Z0
    - copper (conductor) thickness t

Uses the Hammerstad synthesis equations (standard closed-form design) to get
the width ignoring thickness, then applies the Wheeler/Bahl thickness
correction: a finite copper thickness makes the trace EFFECTIVELY wider, so
the physical (etched) width must be a little NARROWER to keep the same Z0.

All lengths in mm, impedance in ohm.
"""

import sys
from math import pi, exp, log, sqrt

COPPER_OZ_MM = 0.0348           # 1 oz copper thickness in mm


def synth_width_over_h(z0: float, er: float) -> float:
    """
    Hammerstad synthesis: return W/h for a target Z0 and er.
    Uses the narrow-strip branch (W/h < 2) or the wide-strip branch
    (W/h > 2), picking whichever is self-consistent.
    """
    # --- narrow-strip branch (valid when the result W/h < 2) ---
    A = (z0 / 60.0) * sqrt((er + 1.0) / 2.0) \
        + (er - 1.0) / (er + 1.0) * (0.23 + 0.11 / er)
    woh_narrow = 8.0 * exp(A) / (exp(2.0 * A) - 2.0)
    if woh_narrow < 2.0:
        return woh_narrow

    # --- wide-strip branch (valid when the result W/h > 2) ---
    B = 377.0 * pi / (2.0 * z0 * sqrt(er))
    woh_wide = (2.0 / pi) * (
        B - 1.0 - log(2.0 * B - 1.0)
        + (er - 1.0) / (2.0 * er) * (log(B - 1.0) + 0.39 - 0.61 / er)
    )
    return woh_wide


def analyse_z0(woh: float, er: float) -> tuple:
    """
    Analysis: given W/h and er, return (Z0, eps_eff).
    Used to verify the synthesised width really gives the target Z0.
    """
    if woh >= 1.0:
        eps_eff = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 / woh) ** -0.5
        z0 = 120 * pi / (sqrt(eps_eff) *
                         (woh + 1.393 + 0.667 * log(woh + 1.444)))
    else:
        eps_eff = (er + 1) / 2 + (er - 1) / 2 * \
            ((1 + 12 / woh) ** -0.5 + 0.04 * (1 - woh) ** 2)
        z0 = (60 / sqrt(eps_eff)) * log(8 / woh + woh / 4)
    return z0, eps_eff


def thickness_correction(W0: float, h: float, t: float) -> float:
    """
    Wheeler/Bahl effective-width increase dW due to conductor thickness t.
    A thicker conductor behaves like a wider one, so the EFFECTIVE width is
    W0 = W_physical + dW.  W0 here is the thickness-free synthesised width.
    """
    if t <= 0:
        return 0.0
    if W0 / h >= 1.0 / (2.0 * pi):        # normal traces
        dW = (1.25 * t / pi) * (1.0 + log(2.0 * h / t))
    else:                                 # very narrow traces
        dW = (1.25 * t / pi) * (1.0 + log(4.0 * pi * W0 / t))
    return dW


def trace_width(z0: float, er: float, h: float,
                t: float = COPPER_OZ_MM) -> dict:
    """Full result: physical width W (thickness-corrected) plus verification."""
    if h <= 0 or er < 1 or z0 <= 0 or t < 0:
        raise ValueError("Need h>0, er>=1, Z0>0, t>=0.")

    woh = synth_width_over_h(z0, er)      # W/h ignoring thickness
    W0 = woh * h                          # effective width needed for Z0
    z0_check, eps_eff = analyse_z0(woh, er)

    dW = thickness_correction(W0, h, t)   # effective widening from thickness
    W_phys = W0 - dW                      # physical (etched) width

    return {
        "W0": W0, "W_phys": W_phys, "dW": dW, "woh": woh,
        "eps_eff": eps_eff, "t": t,
        "z0_target": z0, "z0_check": z0_check,
    }


def get_inputs():
    """Take h, er, Z0, t from the user (CLI args or prompt)."""
    if len(sys.argv) >= 5:
        return (float(sys.argv[1]), float(sys.argv[2]),
                float(sys.argv[3]), float(sys.argv[4]))
    h = float(input("Enter substrate height h (mm): ").strip())
    er = float(input("Enter relative permittivity er: ").strip())
    z0 = float(input("Enter required impedance Z0 (ohm): ").strip())
    t = float(input("Enter copper thickness t (mm, e.g. 0.035 for 1oz): ").strip())
    return h, er, z0, t


def main():
    h, er, z0, t = get_inputs()
    r = trace_width(z0, er, h, t)

    print("\n=== Microstrip trace width ===")
    print(f"  Substrate height h : {h:7.3f} mm")
    print(f"  Permittivity er    : {er:7.2f}")
    print(f"  Target impedance   : {z0:7.1f} ohm")
    print(f"  Copper thickness t : {t:7.3f} mm")
    print(f"  ---------------------------------")
    print(f"  Trace width  W     : {r['W_phys']:7.3f} mm   <- etch this")
    print(f"  (W/h               = {r['W_phys']/h:.3f})")
    print(f"  Zero-thickness W0  : {r['W0']:7.3f} mm")
    print(f"  Thickness corr. dW : {r['dW']:7.3f} mm  "
          f"(W is {r['dW']/r['W0']*100:.1f}% narrower)")
    print(f"  Effective er_eff   : {r['eps_eff']:7.3f}")
    err = abs(r['z0_check'] - z0) / z0 * 100
    print(f"  Base synthesis check: Z0 = {r['z0_check']:.2f} ohm "
          f"(target {z0:.1f}, err {err:.2f}%)\n")


if __name__ == "__main__":
    main()