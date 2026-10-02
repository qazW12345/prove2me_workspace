import Mathlib.Data.Nat.Choose.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

set_option autoImplicit false

theorem solution :
    (323 : ℚ) * (Nat.choose 15 4) =
      (91 : ℚ) * (Nat.choose 20 4) := by
  norm_num [Nat.choose]
