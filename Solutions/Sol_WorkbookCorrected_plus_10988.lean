import Mathlib.Data.Nat.Factorial.Basic
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Ring
import Mathlib.Tactic.NormNum

set_option autoImplicit false

theorem solution :
    ((2 : ℚ) / (6 ^ 5)) * (Nat.factorial 5) = (5 : ℚ) / 162 := by
  norm_num [Nat.factorial]
