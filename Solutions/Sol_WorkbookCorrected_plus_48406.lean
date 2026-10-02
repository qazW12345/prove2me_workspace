import Mathlib.Data.Nat.Factorial.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

set_option autoImplicit false

theorem solution :
    (15 : ℚ) * ((Nat.factorial 4) * (Nat.factorial 2)) =
      (1 : ℚ) * (Nat.factorial 6) := by
  norm_num [Nat.factorial]
