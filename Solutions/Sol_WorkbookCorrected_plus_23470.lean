import Mathlib.Data.Nat.Choose.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

set_option autoImplicit false

theorem solution :
    (9 : ℚ) * (Nat.choose 35 20) =
      (4 : ℚ) * ((Nat.choose 35 20) + (Nat.choose 35 16)) := by
  norm_num [Nat.choose]
