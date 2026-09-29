import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Real

noncomputable section

open scoped BigOperators

namespace DAREx

/-- A true bit denotes a dropped coordinate. -/
abbrev Mask (n : ℕ) := Fin n → Bool

/-- Product law of independent Bernoulli drop indicators. -/
def maskMass {n : ℕ} (p : ℝ) (ω : Mask n) : ℝ :=
  ∏ j, if ω j then p else 1 - p

def mean {n : ℕ} (p : ℝ) (f : Mask n → ℝ) : ℝ :=
  ∑ ω, maskMass p ω * f ω

def probability {n : ℕ} (p : ℝ) (event : Mask n → Prop) : ℝ := by
  classical
  exact ∑ ω, if event ω then maskMass p ω else 0

def coefficientSum {n : ℕ} (c : Fin n → ℝ) : ℝ := ∑ j, c j

def energy {n : ℕ} (c : Fin n → ℝ) : ℝ := ∑ j, c j ^ 2

def empiricalMean {n : ℕ} (c : Fin n → ℝ) : ℝ := coefficientSum c / n

def empiricalVariance {n : ℕ} (c : Fin n → ℝ) : ℝ :=
  (∑ j, (c j - empiricalMean c) ^ 2) / n

/-- Original output minus pruned output, with surviving weights rescaled by `1/q`. -/
def outputError {n : ℕ} (q : ℝ) (c : Fin n → ℝ) (ω : Mask n) : ℝ :=
  ∑ j, (c j - (if ω j then 0 else c j / q))

def dareError {n : ℕ} (p : ℝ) (c : Fin n → ℝ) : Mask n → ℝ :=
  outputError (1 - p) c

def outputBias {n : ℕ} (p q : ℝ) (c : Fin n → ℝ) : ℝ :=
  (1 - (1 - p) / q) * coefficientSum c

/-- Continuous value at one half; analytic claims use `0 < p < 1`. -/
def phi (p : ℝ) : ℝ :=
  if p = 1 / 2 then 1 / 2 else (1 - 2 * p) / Real.log ((1 - p) / p)

lemma maskMass_nonneg {n : ℕ} {p : ℝ} (hp : 0 ≤ p) (hp' : p ≤ 1) (ω : Mask n) :
    0 ≤ maskMass p ω := by
  apply Finset.prod_nonneg
  intro j _
  split
  · exact hp
  · exact sub_nonneg.mpr hp'

lemma maskMass_sum {n : ℕ} (p : ℝ) : ∑ ω : Mask n, maskMass p ω = 1 := by
  unfold maskMass
  simpa using (Fintype.prod_sum (fun (_ : Fin n) (b : Bool) ↦
    if b then p else 1 - p)).symm

end DAREx
