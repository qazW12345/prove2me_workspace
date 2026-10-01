# Survivor analysis for the seven-mod-32 Syracuse residual

## Executive conclusion

The residue sieve has exposed a clean symbolic core.

Up through every fully computed level (modulus depths 17 through 30), the hard
survivor cylinders are **exactly** the cylinders whose uniformly determined
accelerated-Syracuse valuation word has not yet crossed the coefficient
contraction barrier.

Write

[
a_i=v_2(3,mathrm{Syr}^{i-1}(n)+1),qquad
S_t=a_1+cdots+a_t,qquad
lambda=log_2 3.
]

For this branch, every survivor valuation word begins

[
(a_1,a_2,a_3)=(1,1,2)
]

and its determined prefixes satisfy

[
S_jle lfloor jlambdafloor.
]

A first coefficient contraction occurs exactly when

[
S_tge lfloor tlambdafloor+1.
]

This means the residue tree we have been generating is, to the tested depth,
not hiding an additional mysterious arithmetic obstruction: it is a concrete
realization of the classical **coefficient stopping-time** tree.

That is useful, but it also identifies the limit of blind refinement.  The
coefficient-safe symbolic tree has no dead ends, so no amount of merely asking
for "one more binary digit" can make the symbolic residual empty.

The next research target should therefore be the distinction between:

1. arbitrary infinite coefficient-safe **2-adic** paths, which definitely
   exist; and
2. paths coming from **positive integers**, whose binary expansion is
   eventually zero.

That distinction is where genuinely new information would have to enter.

---

## 1. Exact batch-count identity

Let (A_t) be the number of positive-integer words

[
(a_1,ldots,a_t)
]

such that:

- ((a_1,a_2,a_3)=(1,1,2));
- every (a_ige 1);
- for every prefix (jle t),

[
a_1+cdots+a_jle lfloor jlog_2 3floor.
]

The observed "new certificate family" at accelerated descent time (t+1)
has size **exactly (A_t)**.

| safe word length (t) | (A_t) | new descent time | first modulus depth |
|---:|---:|---:|---:|
| 10 | 194 | 11 | 19 |
| 11 | 525 | 12 | 21 |
| 12 | 1,570 | 13 | 22 |
| 13 | 3,387 | 14 | 24 |
| 14 | 9,690 | 15 | 25 |
| 15 | 20,423 | 16 | 27 |
| 16 | 58,040 | 17 | 28 |
| 17 | 121,977 | 18 | 30 |
| 18 | 346,769 | 19 | 32 |
| 19 | 1,076,930 | 20 | 33 |
| 20 | 2,427,209 | 21 | 35 |

The first depth at which a descent-time-(t) coefficient certificate can
appear is not an empirical mystery.  It is forced by

[
K_t=lfloor tlog_2 3floor+2.
]

So the depth schedule is a Beatty/mechanical schedule coming directly from
the coefficient inequality (3^t<2^{S_t}).

This corrects an earlier tempting interpretation: the gaps in appearance
depths are not by themselves evidence of a new continued-fraction phenomenon.
They are already forced by the irrational slope (log_2 3).

---

## 2. A very simple slack dynamical system

Define the nonnegative slack

[
D_t=lfloor tlambdafloor-S_t
]

for a coefficient-safe word, and write (b_i=a_i-1ge0).  Let

[
arepsilon_t=
lfloor (t+1)lambdafloor-lfloor tlambdafloor-1.
]

Since (1<lambda<2), every (arepsilon_t) is either 0 or 1.  The survivor
language then obeys

[
D_{t+1}=D_t+arepsilon_t-b_{t+1},qquad D_{t+1}ge0.
]

The driving sequence (arepsilon_t) is the mechanical/Sturmian clock of
slope (lambda-1approx0.5849625).

This turns the hard-prefix enumeration into a one-dimensional,
time-inhomogeneous lattice-path problem.  There is no need to enumerate
millions of residue classes to predict the next family counts.

---

## 3. Why the symbolic survivor tree cannot terminate

Every admissible word has at least one admissible child.

Indeed,

[
lfloor (t+1)lambdafloor-lfloor tlambdafloorge1.
]

Therefore, if (S_tlelfloor tlambdafloor), then choosing

[
a_{t+1}=1
]

gives

[
S_{t+1}=S_t+1
lelfloor tlambdafloor+1
lelfloor (t+1)lambdafloor.
]

So the coefficient-safe language has **no dead ends**.

The full residue computations through depth 30 show the same phenomenon:
every surviving residue class has either one or two surviving binary lifts;
none has zero.

This is the decisive reason that blind finite refinement cannot finish the
branch.  Even if every positive integer eventually leaves the tree, the tree
itself contains infinite 2-adic paths.

---

## 4. Repeated certificate counts are mostly 2-adic "hairs"

Once a coefficient-safe prefix (w=(a_1,ldots,a_{t-1})) exists, consider
making the next valuation (a_t) larger and larger.

At each extra modulus bit, one lift can acquire the exact finite valuation
needed for coefficient contraction, while the sibling continues with an even
larger (a_t).  In the 2-adic limit this continuing spine forces

[
3x_{t-1}+1=0,
qquad	ext{hence}qquad
x_{t-1}=-rac13
]

in (mathbb Z_2).

Pulling this point back through the affine inverse maps determined by (w)
gives one rational 2-adic boundary point.

This explains a conspicuous feature of our data:

- the (t=11) family has size 194 at depth 19;
- size 194 appears again at depth 20, 21, 22, ...;
- similarly for the later (t)-families.

Those repeated 194/525/1570/... removals are not fresh independent
discoveries at every depth.  They are successive finite approximations to the
same collection of singular 2-adic spines.

Hence "classes removed at the next modulus" overstates mathematical progress
unless we separate:

- **first appearance of a new stopping time**; from
- **one more bit shaved off an already-known singular spine**.

---

## 5. Exact agreement with the coefficient barrier through depth 30

The repository analysis code compares two classifiers for every candidate
cylinder at every depth (17le Kle30):

1. the original finite uniform certificate test:
   (3^t<2^{S_t}) and the representative iterate is below the representative;
2. the purely symbolic test:
   every uniformly determined prefix obeys
   (S_tlelfloor tlog_2 3floor).

There are **zero mismatches** through depth 30.

So in the computed range there are no "paradoxical" survivor cylinders where
the coefficient has become contracting but the additive term keeps the
representative above its start.

This is also consistent with classical stopping-time work.  Terras introduced
coefficient stopping time and proved equality with ordinary stopping time
through a substantial finite range; Garner extended the finite coefficient
stopping-time verification much further.  In the standard half-Collatz map,
one accelerated Syracuse word with total stripped exponent (S_t) represents
(S_t) ordinary half-Collatz iterations, so our current (S_tle29) range is
tiny compared with those classical verified bounds.

References:

- R. Terras, *A stopping time problem on the positive integers*,
  Acta Arith. 30 (1976), 241-252.
  DOI: 10.4064/aa-30-3-241-252
- L. E. Garner, *On the Collatz 3n+1 algorithm*,
  Proc. Amer. Math. Soc. 82 (1981), 19-22.
  DOI: 10.1090/S0002-9939-1981-0603593-2
- J. C. Lagarias, *The 3x+1 Problem: An Annotated Bibliography*,
  which summarizes Terras' and Garner's coefficient-stopping-time bounds.

This is another reason not to spend the main research effort pushing the same
sieve from depth 30 to depth 100: over such ranges it is largely rediscovering
known coefficient-stopping-time structure in residue form.

---

## 6. Concrete natural numbers can survive many modulus levels

The smallest representative still present at depth 30 is (71).

Its accelerated Syracuse orbit first drops below 71 after 32 accelerated
steps:

[
mathrm{Syr}^{32}(71)=61,
]

and the total stripped exponent at that point is

[
S_{32}=51.
]

Therefore this particular descent cannot become a uniform residue-class
certificate until modulus depth at least

[
K=52.
]

So the fact that 71 remains in every residual through (2^{30}) says nothing
mysterious about 71; the sieve simply does not yet contain enough 2-adic
precision to see its known finite descent uniformly.

For the 395 base representatives modulo (2^{16}):

- all were directly checked to have coefficient stopping time equal to actual
  stopping time;
- the most demanding base representative in this finite set is (35655);
- it descends after 85 accelerated steps with total stripped exponent 135;
- its corresponding uniform certificate needs modulus depth 136.

This is a useful warning against interpreting "survives to depth (K)" as
"looks like a counterexample."

---

## 7. The real hard core

After quotienting out the singular hairs, the genuinely interesting object is
the set of **infinite coefficient-safe valuation words**

[
S_tlelfloor tlog_2 3floor
quad	ext{for every }t.
]

There are plenty of such 2-adic paths.  For example, after the mandatory
prefix (1,1,2), continually choosing (a_i=1) stays safely below the
coefficient barrier forever.

That particular eventually periodic valuation path corresponds to a rational
2-adic orbit, not to a positive integer.  For example, choosing an all-1 tail
after the prefix leads to a 2-adic preimage of the fixed point (-1); solving
backwards through the prefix gives the rational starting point

[
-rac{35}{27}.
]

So local 2-adic admissibility alone cannot distinguish the integer problem.

A **positive integer** has an eventually-zero binary expansion.  Thus a
positive-integer counterexample in this branch would have to lie in the
intersection

[
{	ext{infinite coefficient-safe 2-adic paths}}
cap
{	ext{eventually-zero binary 2-adics}}.
]

That intersection, not the raw survivor count, is the object we should now
attack.

---

## 8. A useful external restriction on any rational survivor

Tao's Syracuse formulation writes an accelerated iterate as an affine map
determined by the valuation word and notes that, under Haar measure on odd
2-adics, the valuations behave like iid geometric-(1/2) variables.  This
explains why the coefficient-safe set has measure tending to zero even though
the symbolic tree never becomes empty.

J. López and P. Stoll (2021) prove a relevant necessary condition for rational
2-adic non-cyclic trajectories: their parity density must sit at the critical
Collatz slope.  Translated into accelerated notation, an integer/rational
non-cyclic survivor cannot remain a fixed positive distance below the
coefficient boundary forever; it must approach the critical ratio.

Reference:

- J. López and P. Stoll, *The 3x+1 Periodicity Conjecture in R*,
  arXiv:2101.12747.

For our slack variable this suggests concentrating on paths for which

[
rac{D_t}{t}
=
rac{lfloor tlog_2 3floor-S_t}{t}
]

returns arbitrarily close to zero.

That is a much thinner and more meaningful target than all residue survivors.

---

## 9. Recommended change of research direction

### Stop treating every modulus level as equally informative

In particular, a depth with no newly available descent time is mostly shaving
another bit from existing singular hairs.

For example, after the currently staged (t=18) family at depth 30:

- the next genuinely new family is descent time 19;
- its size is (A_{18}=346,769);
- it first appears only at depth 32.

Depth 31 does not add a new coefficient-stopping-time length.

### Main analysis target

Study the infinite safe language via

[
D_{t+1}=D_t+arepsilon_t-b_{t+1}
]

together with the map from valuation words to starting 2-adic integers.

The concrete question is:

> Can an infinite coefficient-safe word beginning (1,1,2) map to a positive
> integer, i.e. to a 2-adic number whose binary expansion is eventually zero?

A useful intermediate target is stronger than density but weaker than the full
statement:

> Show that any rational non-cyclic safe path must hug the critical boundary
> (D_t=o(t)) along a subsequence, then classify or obstruct those
> boundary-hugging paths.

### Prove2Me-worthy structural lemmas

Rather than thousands more residue leaves, useful formal nodes would be:

1. **Survivor-word characterization:** coefficient-safe prefixes are exactly
   the words satisfying (S_jlelfloor jlog_2 3floor).
2. **Slack recurrence:** derive the Sturmian-clock recurrence for (D_t).
3. **No-dead-end theorem:** every safe word has a safe extension.
4. **Singular-spine theorem:** the repeated same-(t) residue family converges
   to the 2-adic preimage of (-1/3).
5. **Integer-survivor reduction:** an infinite positive-integer survivor would
   give an eventually-zero 2-adic point in the infinite safe language.
6. **Critical-density reduction:** combine rationality with known parity-density
   restrictions to force any such survivor to hug the boundary.

Those statements actually expose what remains difficult instead of hiding it
behind a larger modulus.

---

## 10. Reproducibility

The companion script is:

`scripts/analyze_collatz_survivor_language.py`

It computes the symbolic dynamic program, verifies the observed family counts,
records the first-appearance schedule, checks the 395 original
representatives, and can optionally reproduce the full residue sieve and
compare the certificate classifier with the coefficient-language classifier.

For the expensive exact check through depth 30:

```bash
python scripts/analyze_collatz_survivor_language.py --bruteforce-depth 30
```

The expected result is zero classifier mismatches at every level 17 through
30 and no parent with zero surviving children.


---

## 11. Exact 2-adic cylinder map

A finite valuation word (a_1,ldots,a_t) does not merely describe a family
qualitatively: it determines one exact residue class.

Let

[
S_t=a_1+cdots+a_t
]

and define (C_0=0) by

[
C_{t+1}=3C_t+2^{S_t}.
]

Then

[
operatorname{Syr}^t(x)=rac{3^t x+C_t}{2^{S_t}}.
]

Consequently the starting value must satisfy

[
xequiv r_t:=-C_t,3^{-t}pmod{2^{S_t}}.
]

Because (3) is a 2-adic unit, this residue is unique.

For an infinite valuation word the compatible residues (r_t) converge to a
unique point of (mathbb Z_2).  A nonnegative integer (n) is much more
special: once (2^{S_t}>n), its canonical representative modulo
(2^{S_t}) is literally (n).  Therefore

> an infinite valuation word represents a nonnegative integer if and only if
> its canonical residues (r_t) are eventually constant.

Equivalently, after some stage every higher-precision lift digit is zero.

This gives us a direct arithmetic observable for the "eventually-zero binary
2-adic" condition instead of reasoning about the full residue sets.

---

## 12. Eventually periodic safe valuation words are automatically negative

There is a clean structural obstruction that removes all eventually periodic
safe words from the positive-integer problem.

Suppose a tail repeats a valuation block

[
(a_1,ldots,a_p)
]

with total valuation

[
A=a_1+cdots+a_p.
]

The map of one period is

[
xlongmapstorac{3^p x+C}{2^A}
]

for an integer (C>0).  Its unique periodic point is

[
x_*=rac{C}{2^A-3^p}.
]

If the repeated word is coefficient-safe forever, then its asymptotic average
must satisfy

[
rac{A}{p}lelog_2 3.
]

Equality is impossible because (log_2 3) is irrational while (A/p) is
rational.  Hence

[
A<plog_2 3,
qquad
2^A<3^p.
]

Therefore

[
2^A-3^p<0
]

and so (x_*<0).

A finite preperiod cannot repair the sign.  The inverse of one accelerated
step is

[
x=rac{2^a y-1}{3},
]

which is negative whenever (y<0).

Thus:

> **Every eventually periodic coefficient-safe accelerated valuation word
> represents a negative rational 2-adic integer.**

In particular, a positive integer counterexample in this survivor branch must
have an **aperiodic** valuation word.

This is stronger than merely observing that simple periodic examples such as
the all-1 tail lead to negative 2-adic cycles.

---

## 13. Critical density means sublinear slack, not bounded slack

López--Stoll work with the ordinary half-Collatz parity vector.  At the end of
(t) accelerated Syracuse blocks,

- the number of odd half-Collatz steps is (h=t);
- the total number of half-Collatz steps is (ell=S_t).

Thus their parity-density ratio is

[
rac hell=rac{t}{S_t}.
]

For coefficient-safe paths,

[
rac{S_t}{t}lelog_2 3
]

and hence

[
rac{t}{S_t}gerac1{log_2 3}.
]

Their necessary condition for a rational 2-adic integer with a noncyclic
trajectory forces the critical value to be approached.  In our slack
notation this gives, at least along a subsequence of accelerated block
endpoints,

[
rac{D_t}{t}longrightarrow0.
]

It is important not to strengthen this without justification to (D_t=O(1)).

The companion DP confirms that fixed-width slack bands become a vanishing
fraction of the long safe language.  For example, under the natural Haar /
geometric weighting, among words safe through length 100:

- (D_tle5) accounts for only about (0.52%) of safe mass;
- (D_tle10) accounts for a much larger but still non-universal portion.

By length 200 even the (D_tle10) band is only about (5.7%) of safe mass.

So the rationality restriction points us toward **sublinear boundary
excursions**, not merely a fixed finite-state strip.

---

## 14. Refined hard target

Combining the structural reductions, a positive-integer survivor in this
branch would have to satisfy all of the following:

1. its accelerated valuation word begins ((1,1,2));
2. it is coefficient-safe for every prefix;
3. it is aperiodic;
4. its canonical 2-adic residues eventually stabilize to a nonnegative
   integer;
5. its slack returns sublinearly close to the critical boundary,
   (liminf D_t/t=0).

This is a qualitatively smaller target than the raw residue tree.

The next computational experiment should therefore search the safe language
not by modulus depth but by **slack profile and lift digits**:

- rank safe prefixes by (D_t/t);
- compute their canonical-residue lift digits;
- measure long zero-lift runs (near-stabilization);
- test whether boundary-hugging paths systematically force nonzero high lift
  digits;
- isolate any symbolic condition that forbids eventual stabilization.

The companion script
`scripts/analyze_collatz_2adic_survivors.py` implements the first version of
that experiment.


---

## 15. Eventual-constant slack is formally excluded by mechanical-itinerary results

There is a stronger exact exclusion than the elementary eventually-periodic
valuation-word argument above.

Suppose a coefficient-safe accelerated valuation path has eventually constant
slack:

[
D_t=lfloor tlog_2 3floor-S_t=c
]

for all sufficiently large (t).  Then

[
S_t=lfloor tlog_2 3floor-c.
]

In the ordinary Terras (half-Collatz) parity word, the (t)-th accelerated
block begins with an odd step at ordinary time (S_t).  Hence, after a finite
prefix, the positions of the odd steps are exactly a fixed translate of the
Beatty sequence

[
{lfloor tlog_2 3floor:tge0}.
]

Equivalently, the parity tail is a mechanical/Sturmian word of slope

[
alpha=rac1{log_2 3}.
]

This is not merely an experimental observation.  The external Lean
formalization at

https://github.com/msharpe248/collatz

contains the theorem

`Collatz.eventual_mechanical_reaches_one`

in `lean/Collatz/RationalMechanical.lean`: any positive natural-number orbit
with a mechanical parity tail reaches 1.  The stronger global classification
`Collatz.mechanical_classification` states that the only positive natural
seeds with globally mechanical itineraries are 1 and 2, with slope 1/2.

Since (1/log_2 3
e1/2), and a globally coefficient-safe survivor in our
seven-mod-32 branch cannot reach 1 without first descending below its starting
value, we obtain:

> **No positive-integer survivor in this branch can have eventually constant
> slack (D_t).**

In particular, the exact zero-slack Sturmian spine is rigorously excluded,
not merely numerically non-stabilizing.

This refines the hard target again.  A hypothetical positive survivor must be:

- coefficient-safe forever;
- aperiodic in its accelerated valuation word;
- not eventually mechanical;
- not eventually constant in slack;
- critical in the López--Stoll sense, with (liminf D_t/t=0);
- yet have its canonical 2-adic residues eventually stabilize to one positive
  integer.

What remains is therefore a genuinely irregular critical path: it must return
arbitrarily close to the coefficient boundary on a linear scale while never
settling onto the mechanical boundary orbit.

Reference for the Lean theorem and accompanying paper:
Michael Sharpe, *Collatz at the Critical Line*, repository section
`Collatz.RationalMechanical`, especially
`eventual_mechanical_reaches_one` and `mechanical_classification`.


---

## 16. Machine-verified orbit summability forces the slack to infinity

A substantially stronger restriction follows from the machine-verified
`Collatz.OrbitSummability` development in the external repository

https://github.com/msharpe248/collatz

For a positive natural seed (N), the theorem

`unbounded_inverse_drift_tendsto_zero`

proves that every unbounded orbit satisfies

[
rac{2^ell}{3^{h(ell)}}longrightarrow0,
]

where (ell) is the number of ordinary Terras half-steps and (h(ell))
is the number of odd steps among them.

A positive coefficient-safe survivor in our branch cannot have a bounded
orbit: a bounded integer orbit is eventually periodic, hence eventually
cycles, whereas a globally no-descent orbit starting above 1 cannot enter the
(1leftrightarrow2) cycle and an eventual positive cycle would force a
coefficient contraction over one period.

Therefore a hypothetical positive survivor is unbounded and the theorem
applies.

At the endpoint of the (t)-th accelerated Syracuse block,

[
ell=S_t,qquad h(ell)=t.
]

Thus the inverse drift along this subsequence is

[
rac{2^{S_t}}{3^t}
=
2^{S_t-tlog_2 3}
=
2^{-D_t-{tlog_2 3}}.
]

Since the fractional part lies in ([0,1)), convergence to zero is equivalent
to

[
oxed{D_tlongrightarrow+infty.}
]

This is much stronger than the earlier exclusions of zero slack, eventually
constant slack, and eventually periodic valuation words.

Combining it with the López--Stoll critical-density restriction gives the
central asymptotic shape of any hypothetical positive survivor:

[
oxed{
D_t	oinfty
quad	ext{but}quad
liminf_{t	oinfty}rac{D_t}{t}=0.
}
]

So the path must escape arbitrarily far below the coefficient boundary in
absolute slack, while returning arbitrarily close to it on the *linear*
scale.  It cannot remain in any fixed-width band.

### A quantitative summability restriction

The same external development proves

`unbounded_orbit_reciprocal_summable`:

[
sum_{ellge0}rac1{T^ell(N)}<infty
]

for every unbounded positive natural orbit.

For accelerated block endpoints, the exact affine formula is

[
operatorname{Syr}^t(N)
=
rac{3^t}{2^{S_t}}
left(
N+sum_{j=0}^{t-1}rac{2^{S_j}}{3^{j+1}}
ight).
]

Coefficient safety gives (2^{S_j}le3^j), hence the parenthesized correction
is at most (N+t/3).  Also

[
rac{3^t}{2^{S_t}}
=
2^{D_t+{tlog_2 3}}
<2^{D_t+1}.
]

Therefore

[
operatorname{Syr}^t(N)
<
2^{D_t+1}left(N+rac t3ight)
]

and hence

[
rac1{operatorname{Syr}^t(N)}
>
rac{2^{-D_t-1}}{N+t/3}.
]

Because the accelerated orbit is a subsequence of the ordinary Terras orbit,
its reciprocal series must also converge.  Consequently any positive
survivor must satisfy the necessary condition

[
oxed{
sum_{tge1}rac{2^{-D_t}}{N+t}<infty.
}
]

This is stronger than (D_t	oinfty).  For example, a path with

[
D_tle(1-arepsilon)log_2log t
]

eventually would make the comparison series diverge.  Near-critical returns
therefore have to be sufficiently sparse/deep to preserve reciprocal
summability.

The surviving target is now not merely "sublinear slack".  It is an integer
path whose slack simultaneously satisfies:

1. (D_tge0) for every (t);
2. (D_t	oinfty);
3. (liminf D_t/t=0);
4. (sum 2^{-D_t}/(N+t)<infty);
5. the canonical 2-adic residues eventually stabilize to (N).

That is the structural regime the next search should target.

External formal references:

- `Collatz.unbounded_orbit_reciprocal_summable`
- `Collatz.unbounded_inverse_drift_tendsto_zero`

in `lean/Collatz/OrbitSummability.lean`.


---

## 17. Critical returns force exact 3-adic shadow hits

The same valuation prefix has a second arithmetic encoding.

From

[
2^{S_t}operatorname{Syr}^t(N)=3^tN+C_t
]

we obtain, modulo (3^t),

[
operatorname{Syr}^t(N)
equiv
C_t,2^{-S_t}
pmod{3^t}.
]

Define the canonical shadow residue

[
Q_t=
C_t,2^{-S_t}mod 3^t,
qquad
0le Q_t<3^t.
]

This depends only on the valuation/parity prefix, not on the starting integer.

Now take the critical subsequence forced by López--Stoll, on which

[
D_t/t	o0.
]

Coefficient safety and the affine bound from the previous section give

[
operatorname{Syr}^t(N)
<
2^{D_t+1}left(N+rac t3ight)
=
exp(o(t)).
]

But (3^t=exp(tlog3)).  Hence along this subsequence,

[
rac{operatorname{Syr}^t(N)}{3^t}	o0.
]

In particular, for all sufficiently large critical-return indices,

[
0<operatorname{Syr}^t(N)<3^t.
]

The congruence modulo (3^t) therefore has no room for a nonzero multiple of
the modulus:

[
oxed{
operatorname{Syr}^t(N)=Q_t
}
]

at those indices.

Thus a hypothetical positive survivor is squeezed simultaneously from both
adic sides:

- the **2-adic starting cylinders** must eventually stabilize to the fixed
  integer (N);
- along infinitely many critical returns, the **3-adic shadow residues** must
  equal the actual forward orbit values and satisfy
  (Q_t/3^t	o0).

This connects our survivor-language analysis directly to the machine-verified
3-adic shadow framework in `Collatz.Shadow`, where the shadow congruence and
its entropy-compression properties are formalized.

The new computational target is therefore not merely low slack.  Search for
safe prefixes satisfying all three simultaneous signatures:

1. large absolute slack (D_t) (eventually, since (D_t	oinfty));
2. small relative slack (D_t/t) on critical returns;
3. anomalously tiny normalized shadow residue (Q_t/3^t).

A positive counterexample would have to realize such shadow hits infinitely
often while its 2-adic canonical start has already frozen to one fixed
positive integer.

External formal reference:
`Collatz.Shadow.shadow_modEq` and the surrounding 3-adic shadow development
in https://github.com/msharpe248/collatz.
