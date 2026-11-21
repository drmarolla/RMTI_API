"""How robust is each Tier-4 classification, and what does a $50M package buy under uncertainty?"""
from rmti import UncertainParam as U, simulate_rmti, boundary_margins, woe_sensitivity
from rmti.domains import urban

for city in ("Bamako", "Lagos", "Lilongwe"):
    c = urban.COHORT[city]
    m = boundary_margins(c["L"], c["E_sel"], c["V"], c["rho_now"])
    print(f"{city}: R={m['R']:.3f}; any one of L/E/V must be {m['rel_change_LEV_to_lower']:+.1%} to drop a tier; "
          f"rho must rise by {m['delta_rho_to_lower']:+.3f}")
    print("   P(Tier 4) by assumed evidence grade:", {g: round(p, 2) for g, p in
          woe_sensitivity(c["L"], c["E_sel"], c["V"], c["rho_now"]).items()})

c = urban.COHORT["Lagos"]
res = simulate_rmti(U(c["L"], "w_ic"), U(c["E_sel"], "w_ic"), U(c["V"], "w_ic"), U(c["rho_now"], "w_ic"),
                    rho_after=U(c["rho_after"], "w_ic"), n_sims=50_000)
print("\nLagos, all inputs at WoE grade w_ic (ASSUMED concentration=35):")
for k, v in res.summary().items():
    print(f"  {k}: {v}")
