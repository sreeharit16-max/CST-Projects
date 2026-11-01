"""
patch_design.py
---------------
Compute the dimensions of a rectangular microstrip patch antenna from:
    - resonant frequency f0
    - relative permittivity er
    - substrate height h

Uses the standard transmission-line model (Balanis), computed in order:
    1. width W        2. effective permittivity eps_eff
    3. fringing dL    4. length L

All lengths in mm, frequency in GHz.
"""

import sys
from math import sqrt

C0_MM_GHZ = 299.792458          # c in mm*GHz  (lambda0[mm] = C0 / f[GHz])


def patch_width(f0: float, er: float) -> float:
    """W = c/(2 f0) * sqrt(2/(er+1))."""
    return (C0_MM_GHZ / (2.0 * f0)) * sqrt(2.0 / (er + 1.0))


def eps_eff(er: float, W: float, h: float) -> float:
    """Effective permittivity (valid for W/h > 1)."""
    return (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 12.0 * h / W) ** -0.5


def delta_L(ee: float, W: float, h: float) -> float:
    """Fringing length extension at one radiating edge."""
    return 0.412 * h * ((ee + 0.3) * (W / h + 0.264)) / \
        ((ee - 0.258) * (W / h + 0.8))


def patch_length(f0: float, ee: float, dL: float) -> float:
    """L = c/(2 f0 sqrt(eps_eff)) - 2*dL."""
    return (C0_MM_GHZ / (2.0 * f0 * sqrt(ee))) - 2.0 * dL


def design_patch(f0: float, er: float, h: float) -> dict:
    """Return all patch dimensions for the given specs."""
    if f0 <= 0 or er < 1 or h <= 0:
        raise ValueError("Need f0>0, er>=1, h>0.")
    W = patch_width(f0, er)
    ee = eps_eff(er, W, h)
    dL = delta_L(ee, W, h)
    L = patch_length(f0, ee, dL)
    margin = 6.0 * h                      # ground/substrate margin each side
    return {
        "W": W, "L": L, "eps_eff": ee, "delta_L": dL,
        "sub_W": W + 2.0 * margin, "sub_L": L + 2.0 * margin,
    }


def get_inputs():
    """Take f0, er, h from the user (CLI args or prompt)."""
    if len(sys.argv) >= 4:
        return float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    f0 = float(input("Enter resonant frequency f0 (GHz): ").strip())
    er = float(input("Enter relative permittivity er: ").strip())
    h = float(input("Enter substrate height h (mm): ").strip())
    return f0, er, h


def main():
    f0, er, h = get_inputs()
    d = design_patch(f0, er, h)

    print("\n=== Microstrip patch dimensions ===")
    print(f"  Frequency f0     : {f0:7.3f} GHz")
    print(f"  Permittivity er  : {er:7.2f}")
    print(f"  Substrate h      : {h:7.3f} mm")
    print(f"  ---------------------------------")
    print(f"  Patch width  W   : {d['W']:7.3f} mm   (impedance / bandwidth)")
    print(f"  Patch length L   : {d['L']:7.3f} mm   (sets the resonance)")
    print(f"  eps_eff          : {d['eps_eff']:7.3f}")
    print(f"  Fringing dL      : {d['delta_L']:7.3f} mm")
    print(f"  Ground/substrate : {d['sub_W']:.2f} x {d['sub_L']:.2f} mm "
          f"(patch + 6h each side)")
    print(f"  W/L ratio        : {d['W']/d['L']:.2f}")
    print("  (L is a STARTING value -- fine-tune in CST to centre f0.)\n")


if __name__ == "__main__":
    main()