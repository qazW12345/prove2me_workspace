import Definitions.Def_BirkhoffGlobalSection_AmbientRotation

namespace BirkhoffGlobalSection

theorem variational_cocycle_angle_defect_symplectic
    (F : Phase → ℝ) (x : ℝ → Phase) (T : ℝ)
    (hper : ∀ t : ℝ, x (t + T) = x t)
    (Y : ℝ → (Phase →L[ℝ] Phase))
    (hY : IsHamiltonianVariationalSolution F x Y)
    (hcocycle : ∀ t : ℝ, Y (t + T) = (Y t).comp (Y T))
    (hsymp : ∀ t : ℝ, ∀ u v : Phase,
      (Y t) u ⬝ᵥ TangentialHessian.qI.mulVec ((Y t) v) =
        u ⬝ᵥ TangentialHessian.qI.mulVec v)
    (α : ℝ → ℝ) (hα : IsAmbientRotationAngle Y α) :
    ∀ a : ℝ, α (a + T) - α a ≤ α T - α 0 + 2 * Real.pi := by sorry

end BirkhoffGlobalSection
