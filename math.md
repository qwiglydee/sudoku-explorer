#### Notation

- AND: $A \wedge B$
- NAND: $A \barwedge B$
- OR: $A \vee B$
- XOR: $A \veebar B$
- serial NAND: $\bar\bigwedge A_i$
- serial XOR: $\underline\bigvee A_i$

# The Core

Rules

- each unit must contain different digits
- each digit should appear once in each unit

A draft: $l*d \equiv d*l$ is an assumption of placing digit $d$ into location $l$

Logic:

- different digits in each unit: $\forall d,l_i,l_j: l_i*d \barwedge l_j*d$
- appearing once in a unit: $\forall d: \underline\bigvee d*l_i$

# Basics

- hidden single: if in some unit only one cell remains for a draft is possible, the draft is valid
- open single: if a digit is placed (the draft is valid), all other matching drafts in peer cells are invalid

$\begin{equation}
\exists U \ni l: \forall l' \in (U \setminus l): d*l' = \mathcal{F}
\implies 
\bold{d*l} = \mathcal{T}
\implies
\forall U \ni l: \forall l' \in (U \setminus l): d*l' = \mathcal{F} 
\tag{basic reduction}
\end{equation}$

The $U \setminus l$ means all the peers of $l$ in unit $U$

# Triplets

Set of drafts at intercections of boxes with rows/cols, which are sections of 3 cells.
There are always 3 cells on the intersections, there could be 2 or 3 actual drafts combined, but that doesn't matter

$d*l^n\mid^{U_{box}}_{U_{line}} \equiv \underline\bigvee (d*l_i), l_i \in U_{box} \wedge l_i \in U_{line}$ — assumption that a digit is placed in one of the cells and that some of the cells contain the digit.

When a triplet is locked within their box, all matching drafts in adjacent line can be removed.

$\begin{equation}
\forall l' \in (U_{box} \setminus l^n) : d*l' = \mathcal{F}
\implies
\bold{d*l^n\mid^{U_{box}}_{U_{line}} = \mathcal{T}}
\implies 
\forall l' \in (U_{line} \setminus l) : d*l' = \mathcal{F}
\tag{pointing triplet}
\end{equation}$

When a triplet is locked within their line, all mathing drafts in adjacent box can be removed.

$\begin{equation}
\forall l' \in (U_{line} \setminus l^n) : d*l' = \mathcal{F}
\implies
\bold{d*l^n\mid^{U_{box}}_{U_{line}}} = \mathcal{T}
\implies
\forall l' \in (U_{box} \setminus l^n) : d*l' = \mathcal{F}
\tag{line reduction}
\end{equation}$

## Multiples

The doubles/triples/quads/etc are set of drafts of a combo of digits, within a unit.

$d^m*l^m|_U \equiv \underline\bigvee P^m_{i,j}d_i*l_j$ — assumption that the $m$ digits are placed in the $m$ cells in one of possible peremutations, and that the cells only contain the digits.

Th $P^m_{i,j}$ is all possible combinations in totally vague notation

It is proven when no other cells in the unit contain the digits.

\begin{equation}
\forall l' \in (U \setminus l^m), d \in d^m : d*l' = \mathcal{F}
\implies
\bold{d^m*l^m|\_U} = \mathcal{T}
\tag{multiples evaluation}
\end{equation}

\begin{equation}
\bold{d^m*l^m|\_U^{U_a}} = \mathcal{T}
\implies
\forall l' \in (U_a \setminus l^m), d \in d^m : d * l' = \mathcal{F}
\tag{open multiples}
\end{equation}

It only makes sense when the group has adjacent unit. The main unit that is used to evaluate the multiple, and the other to use for elimination.

\begin{equation}
\bold{d^m*l^m|\_U} = \mathcal{T}
\implies
\forall d' \notin d^m, l \in l^m : l*d' = \mathcal{F}
\tag{hidden multiples}
\end{equation}

This works for a group within a single unit

# Links

Links are relations beween drafts.

### Weak/Soft links

Represent NAND relation of drafts: $A \barwedge B$

Crtiteria:

- bilocation link: the drafts are of the same digit and within the same unit
    - $d*l_a \barwedge d*l_b \mid_U \Longleftarrow l_a \ne l_b \wedge \exists U: l_a \in U, l_b \in U$
- bivalue link: the drafts are in the same cell of different digits:
    - $l*d_a \barwedge l*d_b \mid_l \Longleftarrow d_a \ne d_b$

Totally vague creiteria linking basically all the drafts within any unit or cell.

### Strong/Hard links

Represent XOR relation of drafts: $A \veebar B$

Criteria:

- all the weak link +
- bilocation link: the drafts are of the same digit, and there's some unit where it's only 2 locations for the digit:
    - $d*l_a \veebar d*l_b \mid_U \Longleftarrow l_a \ne l_b \wedge  \exists U: \forall l' \in (U \setminus l_a, l_b) : d*l' = \mathcal{F}$
- bivalue link: the drafts are in the same cell, and there're only 2 digts in the sell possible:
    - $l*d_a \veebar l*d_b \mid_l \Longleftarrow d_a \ne d_b \wedge \forall d' \notin \{d_1, d_b\}: l*d' = \mathcal{F}$

## Chains (AIC)

Alternating chains connect drafts in sequence:

$(C_1 \veebar C_2) \cdot (C_2 \barwedge C_3) \cdot (C_3 \veebar C_4) \cdot ...$

A hard-ended chain starts and ends with hard-links:

$(C_1 \veebar C_2) \cdot ... \cdot (C_{n-1} \veebar C_{n}) \equiv (C_1 \veebar ... \veebar C_n)$

A hard-ended chain edges are xor-related:

$\begin{equation}
(C_1 \veebar ... \veebar C_n) \implies (C_1 \veebar C_n)
\tag{edge equation}
\end{equation}$

The chain can be extended by $\barwedge \veebar$ segmeins and remain hard-ended:

$(C_1 \veebar ... \veebar C_n) \cdot (C_n \barwedge X_1) \cdot (X_1 \veebar X_2) \Rightarrow  (C_1 \veebar ... \veebar X_2)$

### Open chain

Elimination rule: when some draft is _visible_ from both ends of a hard-ended edge, it is invalid

$\begin{equation}
(X \barwedge C_1) \cdot (C_1 \veebar ... \veebar C_n) \cdot (C_n \barwedge X) \implies X = \mathcal{F}
\tag{edge elimination}
\end{equation}$

### Closed chain

Loop rule: when a chain is cycled, all it's soft links are also hard links

$\begin{equation}
(C_1 \veebar ... \veebar C_n) \cdot (C_n \barwedge C_1) \implies (C_1 \veebar C_n) 
\tag{loop enforement}
\end{equation}$

# Generalization

The links/chain logic works totally the same for any logically evaluated assumptions that can form $\veebar$ and $\barwedge$ relations between each other.
The inference chains can mix all the types of links.

#### Soft links:

- $l*d_a \barwedge l*d_b \mid_l \Longleftarrow d_a \ne d_b$ ­— bivalue
- $d*l_a \barwedge d*l_b \mid_U \Longleftarrow l_a \ne l_b \wedge \exists U: l_a \in U, l_b \in U$ — between singular drafts
- $d*l_a \barwedge d*l_b^n  \mid_U \Longleftarrow l_a \not\in l_b^n \wedge \exists U: l_a \in U, l^n_b \subset U$ — between singular and triplet
- $d*l_a^n \barwedge d*l_b^n  \mid_U \Longleftarrow l_a^n \cap l_b^n = \emptyset \wedge \exists U: l_a^n \subset U, l^n_b \subset U$ — between triplets

#### Hard links:

- $l*d_a \veebar l*d_b \mid_l \Longleftarrow d_a \ne d_b \wedge \forall d' \notin \{d_1, d_b\}: l*d' = \mathcal{F}$ — bivalue
- $d*l_a \veebar d*l_b \mid_U \Longleftarrow l_a \ne l_b \wedge \exists U: \forall l' \in (U \setminus l_a, l_b) : d*l' = \mathcal{F}$ — ­between singular drafts
- $d*l_a \veebar d*l_b^n \mid_U \Longleftarrow l_a \notin l_b^n \wedge \exists U: \forall l' \in (U \setminus l_a, l_b^n) : d*l' = \mathcal{F}$ — ­between singular and triplet
- $d*l_a^n \veebar d*l_b^n \mid_U \Longleftarrow l_a^n \cap l_b^n = \emptyset \wedge \exists U: \forall l' \in (U \setminus l_a^n, l_b^n) : d*l' = \mathcal{F}$ — ­between triplets

#### Multivalue links

Doesn't seem to make sence...
