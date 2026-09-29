import Mathlib.Data.Nat.Choose.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

set_option autoImplicit false

theorem solution :
    (286 : ℚ) * (Nat.choose 9 6) =
      (3 : ℚ) * (Nat.choose 16 6) := by
  norm_num [Nat.choose]
