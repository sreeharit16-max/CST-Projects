"""
inset_feed.py
-------------
Given the resonant frequency and the patch width W and length L, compute the
inset-feed depth x0 that matches the patch to the feed line.

Inset-feed model (cos^2 law):
        R(x0) = R_edge * cos^2( pi * x0 / L )
    =>  x0    = (L / pi) * arccos( sqrt( R / R_edge ) )

Assumptions (as requested):
    R_edge = 200 ohm    (typical patch edge resistance -- a starting value)
    R      = 50  ohm    (feed line / system impedance -> match target)

About the frequency:
    x0 itself depends only on L, R and R_edge -- NOT directly on frequency.
    But frequency is useful: it gives the wavelength, and lets us check that
    the L you entered is roughly right to resonate at that frequency (the
    length is what actually encodes the frequency).

All lengths in mm, frequency in GHz.
"""

import sys
from math import pi, acos, sqrt

C0_MM_GHZ = 299.792458          # c in mm*GHz  (lambda0[mm] = C0 / f[GHz])


def compute_x0(L: float, r_target: float = 50.0,
               r_edge: float = 200.0) -> float:
    """Inset depth x0 (mm) for a target input resistance."""
    if L <= 0:
        raise ValueError("Patch length L must be positive.")
    if not (0 < r_target <= r_edge):
        raise ValueError(f"Need 0 < R ({r_target}) <= R_edge ({r_edge}).")
    return (L / pi) * acos(sqrt(r_target / r_edge))


def expected_length(f0_ghz: float, W: float,
                    er: float = 2.0, h: float = 1.53) -> float:
    """
    Accurate expected patch length for resonance at f0, using the
    transmission-line model (effective permittivity + fringing).
    Defaults: er = 2, h = 1.53 mm (the dielectric of the 1.6 mm board).
    Returns L in mm.  Used as a sanity reference for the user's entered L.
    """
    lambda0 = C0_MM_GHZ / f0_ghz
    eps_eff = (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 12.0 * h / W) ** -0.5
    delta_L = 0.412 * h * ((eps_eff + 0.3) * (W / h + 0.264)) / \
        ((eps_eff - 0.258) * (W / h + 0.8))
    return lambda0 / (2.0 * sqrt(eps_eff)) - 2.0 * delta_L


def get_inputs():
    """Take frequency, W and L from the user (CLI args or prompt)."""
    if len(sys.argv) >= 4:
        return float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    f0 = float(input("Enter resonant frequency f0 (GHz): ").strip())
    W = float(input("Enter patch width  W (mm): ").strip())
    L = float(input("Enter patch length L (mm): ").strip())
    return f0, W, L


def main():
    f0, W, L = get_inputs()
    r_edge = 200.0
    r_target = 50.0
    er = 2.0

    x0 = compute_x0(L, r_target, r_edge)
    lambda0 = C0_MM_GHZ / f0
    L_ref = expected_length(f0, W, er)      # accurate expected L (er=2 board)

    print("\n=== Inset-feed depth ===")
    print(f"  Frequency f0   : {f0:7.3f} GHz")
    print(f"  Wavelength l0  : {lambda0:7.2f} mm")
    print(f"  Patch width  W : {W:7.3f} mm")
    print(f"  Patch length L : {L:7.3f} mm")
    print(f"  R_edge         : {r_edge:7.1f} ohm")
    print(f"  Target R       : {r_target:7.1f} ohm")
    print(f"  ---------------------------------")
    print(f"  Inset depth x0 : {x0:7.3f} mm")
    print(f"  (x0 / L        = {x0/L:.3f}, must be < 0.5 = centre)")

    # sanity checks
    print()
    rel = abs(L - L_ref) / L_ref
    print(f"  Expected L for {f0:.2f} GHz on er={er} board ~ {L_ref:.2f} mm")
    if rel > 0.15:
        print(f"  WARNING: your L ({L:.2f}) differs from the expected "
              f"{L_ref:.2f} mm by {rel*100:.0f}% -- on an er={er} board this L "
              f"would NOT resonate at {f0:.2f} GHz (check L, er, or frequency).")
    else:
        print(f"  ok: your L matches ~{f0:.2f} GHz on an er={er} board.")

    if W / L < 1.0:
        print(f"  note: W/L = {W/L:.2f} (<1) -> narrow patch, lower directivity")
    elif W / L > 2.0:
        print(f"  note: W/L = {W/L:.2f} (>2) -> wide patch, watch higher modes")

    print("  x0 is a STARTING value -- sweep it in CST to land the match.\n")


if __name__ == "__main__":
    main()