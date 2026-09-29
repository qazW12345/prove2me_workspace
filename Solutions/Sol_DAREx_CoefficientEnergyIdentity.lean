import Definitions.Def_DAREx_Model

open scoped BigOperators

namespace DAREx

theorem solution :
  ∀ (n : ℕ) (c : Fin n → ℝ), 0 < n →
    energy c = (n : ℝ) * (empiricalMean c ^ 2 + empiricalVariance c) := by
  intro n c hn
  have hn0 : (n : ℝ) ≠ 0 := by
    exact_mod_cast (Nat.ne_of_gt hn)

  let m : ℝ := empiricalMean c

  have hsum : coefficientSum c = (n : ℝ) * m := by
    dsimp [m]
    unfold empiricalMean
    field_simp [hn0]

  have hcenter :
      (∑ j : Fin n, (c j - m) ^ 2) =
        energy c - 2 * m * coefficientSum c + (n : ℝ) * m ^ 2 := by
    calc
      (∑ j : Fin n, (c j - m) ^ 2)
          = ∑ j : Fin n, (c j ^ 2 - 2 * m * c j + m ^ 2) := by
              apply Finset.sum_congr rfl
              intro j _
              ring
      _ = (∑ j : Fin n, c j ^ 2) -
            2 * m * (∑ j : Fin n, c j) +
            (n : ℝ) * m ^ 2 := by
              simp only [Finset.sum_add_distrib, Finset.sum_sub_distrib]
              rw [← Finset.mul_sum]
              simp
      _ = energy c - 2 * m * coefficientSum c + (n : ℝ) * m ^ 2 := by
              rfl

  have hcenter' :
      (∑ j : Fin n, (c j - m) ^ 2) = energy c - (n : ℝ) * m ^ 2 := by
    rw [hcenter, hsum]
    ring

  change energy c =
    (n : ℝ) * (m ^ 2 + (∑ j : Fin n, (c j - m) ^ 2) / (n : ℝ))
  rw [hcenter']
  field_simp [hn0]
  ring

end DAREx
