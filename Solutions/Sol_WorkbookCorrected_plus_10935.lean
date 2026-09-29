import Mathlib.Data.Nat.Choose.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

set_option autoImplicit false

theorem solution :
    ((2 : ℚ) * (Nat.choose 12 2) + 6 * (Nat.choose 6 2)) /
      (Nat.choose 60 2) = (37 : ℚ) / 295 := by
  norm_num [Nat.choose]
