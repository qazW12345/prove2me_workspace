import Definitions.Def_BirkhoffGlobalSection_AmbientRotation
import Mathlib.Analysis.ODE.ExistUnique
import Mathlib.Analysis.Calculus.ContDiff.RCLike
import Mathlib.Analysis.Calculus.Deriv.Shift
import Mathlib.Topology.Connected.Clopen
import Mathlib.Tactic

open scoped ContDiff Topology

namespace BirkhoffGlobalSection

lemma hvf_contDiffAt_for_period_cocycle
    (F : Phase → ℝ) (s : Phase) (h : ContDiffAt ℝ ∞ F s) :
    ContDiffAt ℝ 1 (hamiltonianVectorField F) s := by
  have hd : ContDiffAt ℝ 1 (fderiv ℝ F) s := h.fderiv_right (by norm_cast)
  have hp : ∀ i : Fin 4, ContDiffAt ℝ 1 (fun x => partialDerivative F x i) s := fun i =>
    hd.clm_apply contDiffAt_const
  apply contDiffAt_pi'
  intro i
  fin_cases i
  · simpa [hamiltonianVectorField] using hp 2
  · simpa [hamiltonianVectorField] using hp 3
  · simpa [hamiltonianVectorField] using (hp 0).neg
  · simpa [hamiltonianVectorField] using (hp 1).neg

lemma periodic_of_closed_hamiltonian_for_period_cocycle
    (F : Phase → ℝ) (x : ℝ → Phase) (T : ℝ)
    (hxder : ∀ t : ℝ, HasDerivAt x (hamiltonianVectorField F (x t)) t)
    (hclose : x T = x 0)
    (hF : ∀ t : ℝ, ContDiffAt ℝ ∞ F (x t)) :
    ∀ t : ℝ, x (t + T) = x t := by
  have hxcont : Continuous x := continuous_iff_continuousAt.mpr fun t => (hxder t).continuousAt
  have hzcont : Continuous (fun t : ℝ => x (t + T)) := by
    fun_prop
  let A : Set ℝ := {t | x (t + T) = x t}
  have hAclosed : IsClosed A := by
    dsimp [A]
    exact isClosed_eq hzcont hxcont
  have hAopen : IsOpen A := by
    rw [isOpen_iff_eventually]
    intro t ht
    change x (t + T) = x t at ht
    obtain ⟨K, U, hU, hLip⟩ :=
      (hvf_contDiffAt_for_period_cocycle F (x t) (hF t)).exists_lipschitzOnWith
    have hxU : ∀ᶠ u in 𝓝 t, x u ∈ U :=
      (hxder t).continuousAt hU
    have hzU : ∀ᶠ u in 𝓝 t, x (u + T) ∈ U := by
      have hU' : U ∈ 𝓝 (x (t + T)) := by simpa [ht] using hU
      exact hzcont.continuousAt hU'
    have hzder : ∀ u : ℝ,
        HasDerivAt (fun r : ℝ => x (r + T))
          (hamiltonianVectorField F (x (u + T))) u := by
      intro u
      exact (hxder (u + T)).comp_add_const u T
    have heq : (fun u : ℝ => x (u + T)) =ᶠ[𝓝 t] x := by
      apply ODE_solution_unique_of_eventually
        (v := fun _ : ℝ => hamiltonianVectorField F)
        (s := fun _ : ℝ => U) (K := K) (t₀ := t)
      · exact Filter.Eventually.of_forall fun _ => hLip
      · filter_upwards [hzU] with u hu
        exact ⟨hzder u, hu⟩
      · filter_upwards [hxU] with u hu
        exact ⟨hxder u, hu⟩
      · exact ht
    filter_upwards [heq] with u hu
    exact hu
  have hA0 : (0 : ℝ) ∈ A := by
    change x (0 + T) = x 0
    simpa using hclose
  have hAuniv : A = Set.univ :=
    (show IsClopen A from ⟨hAclosed, hAopen⟩).eq_univ ⟨0, hA0⟩
  intro t
  have ht : t ∈ A := by simpa [hAuniv]
  exact ht

example
    (F : Phase → ℝ) (S : Set Phase) (x : ℝ → Phase) (T : ℝ)
    (hx : IsPeriodicHamiltonianSolutionIn F S x T)
    (hF : ∀ t : ℝ, ContDiffAt ℝ ∞ F (x t)) :
    ∀ t : ℝ, x (t + T) = x t := by
  exact periodic_of_closed_hamiltonian_for_period_cocycle
    F x T hx.2.2.1 hx.2.2.2 hF

end BirkhoffGlobalSection
