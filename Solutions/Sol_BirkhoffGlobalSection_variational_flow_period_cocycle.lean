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


lemma variational_period_cocycle_of_periodic_for_period_cocycle
    (F : Phase → ℝ) (x : ℝ → Phase) (T : ℝ)
    (hper : ∀ t : ℝ, x (t + T) = x t)
    (hxder : ∀ t : ℝ, HasDerivAt x (hamiltonianVectorField F (x t)) t)
    (hF : ∀ t : ℝ, ContDiffAt ℝ ∞ F (x t))
    (Y : ℝ → (Phase →L[ℝ] Phase))
    (hY : IsHamiltonianVariationalSolution F x Y) :
    ∀ t : ℝ, Y (t + T) = (Y t).comp (Y T) := by
  let B : ℝ → (Phase →L[ℝ] Phase) :=
    fun t => fderiv ℝ (hamiltonianVectorField F) (x t)
  have hxcont : Continuous x :=
    continuous_iff_continuousAt.mpr fun t => (hxder t).continuousAt
  have hYcont : Continuous Y :=
    continuous_iff_continuousAt.mpr fun t => (hY.2 t).continuousAt
  have hBcontAt : ∀ t : ℝ, ContinuousAt B t := by
    intro t
    exact ((hvf_contDiffAt_for_period_cocycle F (x t) (hF t)).continuousAt_fderiv
      (by norm_num)).comp t (hxder t).continuousAt
  have hzcont : Continuous (fun t : ℝ => Y (t + T)) := by
    fun_prop
  have hwcont : Continuous (fun t : ℝ => (Y t).comp (Y T)) := by
    fun_prop
  have hzder : ∀ u : ℝ,
      HasDerivAt (fun r : ℝ => Y (r + T))
        ((B u).comp (Y (u + T))) u := by
    intro u
    simpa [B, hper u] using (hY.2 (u + T)).comp_add_const u T
  have hwder : ∀ u : ℝ,
      HasDerivAt (fun r : ℝ => (Y r).comp (Y T))
        ((B u).comp ((Y u).comp (Y T))) u := by
    intro u
    simpa [B, ContinuousLinearMap.comp_assoc] using
      (hY.2 u).clm_comp (hasDerivAt_const u (Y T))
  let C : Set ℝ := {t | Y (t + T) = (Y t).comp (Y T)}
  have hCclosed : IsClosed C := by
    dsimp [C]
    exact isClosed_eq hzcont hwcont
  have hCopen : IsOpen C := by
    rw [isOpen_iff_eventually]
    intro t ht
    change Y (t + T) = (Y t).comp (Y T) at ht
    let K : ℝ≥0 := ⟨‖B t‖ + 1, by positivity⟩
    have hnorm : ∀ᶠ u in 𝓝 t, ‖B u‖ < (K : ℝ) := by
      have hnhd : {M : Phase →L[ℝ] Phase | ‖M‖ < (K : ℝ)} ∈ 𝓝 (B t) := by
        apply (isOpen_lt continuous_norm continuous_const).mem_nhds
        dsimp [K]
        linarith
      exact hBcontAt t hnhd
    have hLip : ∀ᶠ u in 𝓝 t,
        LipschitzOnWith K
          (fun M : Phase →L[ℝ] Phase => (B u).comp M) Set.univ := by
      filter_upwards [hnorm] with u hu
      have hop : ‖(B u).postcomp Phase‖ ≤ (K : ℝ) := by
        exact (ContinuousLinearMap.norm_postcomp_le (B u)).trans hu.le
      simpa using
        (ContinuousLinearMap.lipschitzWith_of_opNorm_le hop).lipschitzOnWith
    have heq :
        (fun u : ℝ => Y (u + T)) =ᶠ[𝓝 t]
          (fun u : ℝ => (Y u).comp (Y T)) := by
      apply ODE_solution_unique_of_eventually
        (v := fun u (M : Phase →L[ℝ] Phase) => (B u).comp M)
        (s := fun _ : ℝ => Set.univ) (K := K) (t₀ := t)
      · exact hLip
      · exact Filter.Eventually.of_forall fun u => ⟨hzder u, Set.mem_univ _⟩
      · exact Filter.Eventually.of_forall fun u => ⟨hwder u, Set.mem_univ _⟩
      · exact ht
    filter_upwards [heq] with u hu
    exact hu
  have hC0 : (0 : ℝ) ∈ C := by
    change Y (0 + T) = (Y 0).comp (Y T)
    simp [hY.1]
  have hCuniv : C = Set.univ :=
    (show IsClopen C from ⟨hCclosed, hCopen⟩).eq_univ ⟨0, hC0⟩
  intro t
  have ht : t ∈ C := by simpa [hCuniv]
  exact ht

theorem solution
    (F : Phase → ℝ) (S : Set Phase) (x : ℝ → Phase) (T : ℝ)
    (hx : IsPeriodicHamiltonianSolutionIn F S x T)
    (hF : ∀ t : ℝ, ContDiffAt ℝ ∞ F (x t))
    (Y : ℝ → (Phase →L[ℝ] Phase))
    (hY : IsHamiltonianVariationalSolution F x Y) :
    (∀ t : ℝ, x (t + T) = x t) ∧
      ∀ t : ℝ, Y (t + T) = (Y t).comp (Y T) := by
  have hper : ∀ t : ℝ, x (t + T) = x t :=
    periodic_of_closed_hamiltonian_for_period_cocycle
      F x T hx.2.2.1 hx.2.2.2 hF
  refine ⟨hper, ?_⟩
  exact variational_period_cocycle_of_periodic_for_period_cocycle
    F x T hper hx.2.2.1 hF Y hY

example
    (F : Phase → ℝ) (S : Set Phase) (x : ℝ → Phase) (T : ℝ)
    (hx : IsPeriodicHamiltonianSolutionIn F S x T)
    (hF : ∀ t : ℝ, ContDiffAt ℝ ∞ F (x t)) :
    ∀ t : ℝ, x (t + T) = x t := by
  exact periodic_of_closed_hamiltonian_for_period_cocycle
    F x T hx.2.2.1 hx.2.2.2 hF

end BirkhoffGlobalSection
