import Mathlib
import Definitions.Def_CookPvsNP_defs

namespace CookPvsNP

set_option autoImplicit false

inductive CompQ (Q₁ Q₂ : Type)
  | f : Q₁ → CompQ Q₁ Q₂
  | mark : CompQ Q₁ Q₂
  | scan : CompQ Q₁ Q₂
  | back : CompQ Q₁ Q₂
  | g : Q₂ → CompQ Q₁ Q₂
  | extend : Q₂ → CompQ Q₁ Q₂
  | finish : Bool → CompQ Q₁ Q₂
  | accept : CompQ Q₁ Q₂
  | reject : CompQ Q₁ Q₂
  deriving DecidableEq, Fintype

abbrev CompΓ (Γ₁ Γ₂ : Type) := Γ₁ ⊕ Γ₂ ⊕ Unit

def marker {Γ₁ Γ₂ : Type} : Option (CompΓ Γ₁ Γ₂) :=
  some (Sum.inr (Sum.inr ()))

def liftF {Γ₁ Γ₂ : Type} : Option Γ₁ → Option (CompΓ Γ₁ Γ₂)
  | none => none
  | some a => some (Sum.inl a)

def liftG {Γ₁ Γ₂ : Type} : Option Γ₂ → Option (CompΓ Γ₁ Γ₂)
  | none => none
  | some a => some (Sum.inr (Sum.inl a))

def embF {α Γ₁ Γ₂ : Type} (e : α ↪ Γ₁) : α ↪ CompΓ Γ₁ Γ₂ where
  toFun a := Sum.inl (e a)
  inj' := by
    intro a b h
    apply e.injective
    exact Sum.inl.inj h

def embG {α Γ₁ Γ₂ : Type} (e : α ↪ Γ₂) : α ↪ CompΓ Γ₁ Γ₂ where
  toFun a := Sum.inr (Sum.inl (e a))
  inj' := by
    intro a b h
    apply e.injective
    exact Sum.inl.inj (Sum.inr.inj h)

noncomputable def compTM
    {Sym₁ Sym₂ Sym₃ Γ₁ Γ₂ : Type}
    (ι₂f : Sym₂ ↪ Γ₁) (ι₁g : Sym₂ ↪ Γ₂)
    (Mf : TM Γ₁) (Mg : TM Γ₂) :
    TM (CompΓ Γ₁ Γ₂) := by
  classical
  let δc : CompQ Mf.Q Mg.Q → Option (CompΓ Γ₁ Γ₂) →
      CompQ Mf.Q Mg.Q × Option (CompΓ Γ₁ Γ₂) × Move :=
    fun q a =>
      match q with
      | .f qf =>
          if hfhalt : qf = Mf.qaccept ∨ qf = Mf.qreject then
            (.mark, a, .left)
          else
            let af : Option Γ₁ :=
              match a with
              | none => none
              | some (Sum.inl z) => some z
              | _ => none
            let d := Mf.δ qf af
            (.f d.1, liftF d.2.1, d.2.2)
      | .mark => (.scan, marker, .right)
      | .scan =>
          match a with
          | none => (.back, none, .left)
          | some (Sum.inl z) =>
              match Function.partialInv (fun s => ι₂f s) z with
              | some s => (.scan, some (Sum.inr (Sum.inl (ι₁g s))), .right)
              | none => (.scan, none, .right)
          | _ => (.scan, a, .right)
      | .back =>
          match a with
          | some (Sum.inr (Sum.inr ())) => (.g Mg.q₀, marker, .right)
          | _ => (.back, a, .left)
      | .g qg =>
          match a with
          | some (Sum.inr (Sum.inr ())) => (.extend qg, none, .left)
          | _ =>
              if ha : qg = Mg.qaccept then
                (.finish true, a, .right)
              else if hr : qg = Mg.qreject then
                (.finish false, a, .right)
              else
                let ag : Option Γ₂ :=
                  match a with
                  | none => none
                  | some (Sum.inr (Sum.inl z)) => some z
                  | _ => none
                let d := Mg.δ qg ag
                (.g d.1, liftG d.2.1, d.2.2)
      | .extend qg => (.g qg, marker, .right)
      | .finish b => (if b then .accept else .reject, a, .left)
      | .accept => (.accept, a, .right)
      | .reject => (.reject, a, .right)
  exact {
    Q := CompQ Mf.Q Mg.Q
    q₀ := .f Mf.q₀
    qaccept := .accept
    qreject := .reject
    accept_ne_reject := by simp
    δ := δc
  }

example
    {Sym₁ Sym₂ Sym₃ : Type}
    (f : List Sym₁ → List Sym₂) (g : List Sym₂ → List Sym₃)
    (hf : PolyTimeComputable f) (hg : PolyTimeComputable g) :
    PolyTimeComputable (g ∘ f) := by
  sorry

end CookPvsNP
