import Mathlib

set_option autoImplicit false

namespace OddPerfectNumber.Kernel

theorem solution (p : Nat) (hp4 : p % 4 = 1) :
    Nat.gcd ((p + 1) / 2) (p ^ 2 - p + 1) ∣ 3 := by
  by_cases hp1 : p = 1
  · subst p
    norm_num
  have hp5 : 5 ≤ p := by
    omega
  let d := Nat.gcd ((p + 1) / 2) (p ^ 2 - p + 1)
  change d ∣ 3
  have hdA : d ∣ (p + 1) / 2 := by
    dsimp [d]
    exact Nat.gcd_dvd_left _ _
  have hdB : d ∣ p ^ 2 - p + 1 := by
    dsimp [d]
    exact Nat.gcd_dvd_right _ _
  have hA2 : 2 * ((p + 1) / 2) = p + 1 := by
    omega
  have hdp1 : d ∣ p + 1 := by
    rcases hdA with ⟨k, hk⟩
    refine ⟨2 * k, ?_⟩
    rw [← hA2, hk]
    ring
  have hprod : d ∣ (p - 2) * (p + 1) := by
    rcases hdp1 with ⟨k, hk⟩
    refine ⟨(p - 2) * k, ?_⟩
    rw [hk]
    ring
  have hp_decomp : p = (p - 2) + 2 := by
    omega
  have hring :
      p ^ 2 = ((p - 2) * (p + 1) + 2) + p := by
    nlinarith [hp_decomp]
  have hsub :
      p ^ 2 - p = (p - 2) * (p + 1) + 2 := by
    omega
  have hdiff :
      (p ^ 2 - p + 1) - ((p - 2) * (p + 1)) = 3 := by
    omega
  have hdivdiff : d ∣ (p ^ 2 - p + 1) - ((p - 2) * (p + 1)) := by
    exact Nat.dvd_sub hdB hprod
  rw [hdiff] at hdivdiff
  exact hdivdiff

end OddPerfectNumber.Kernel
