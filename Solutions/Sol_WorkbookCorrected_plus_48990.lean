import Mathlib.Data.Nat.Choose.Basic
import Mathlib.Tactic.NormNum

set_option autoImplicit false

theorem solution :
    ¬ ((Nat.choose (16 + 3) 3) - (Nat.choose (11 + 3) 3) -
      (Nat.choose (10 + 3) 3) - 2 * (Nat.choose (9 + 3) 3) +
      (Nat.choose (5 + 3) 3) + 2 * (Nat.choose (4 + 3) 3) +
      2 * (Nat.choose (3 + 3) 3) + (Nat.choose (2 + 3) 3) = 55) := by
  norm_num [Nat.choose]
