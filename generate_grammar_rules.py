import sys
sys.path.append("/Users/Ryan/src/Thesis/NLTK")
import generate_local
from nltk import *

conditionGramString="""New (nw) : S[N] −→ I[N1] S[N2]
Repeat (rp) : S/I[N] −→ I[N] I[0]
Neighbour (nb) : S/I[0] −→ I[N1] I[N2]
with N1 = −N2, |N1| ≤ n1
Passing (ps) : S/I[N] −→ I[N1] I[N2]
with N1 + N2 = N, N1N2 > 0
and |N| ≤ n2
Escape (es) : S/I[N] −→ I[N1] I[N2]
with N1 + N2 = N, N1N2 < 0
and |N1| ≤ n3
Replace by a terminal : S/I[N] −→ N"""

conditionGramString="""NW -> I NW
RP -> ANY N0 where N0 = 0
I −> RP
NB −> N1 N2 where N1 = −N2, |N1| ≤ 2
PS −> I[N1] I[N2]
with N1 + N2 = N, N1N2 > 0
and |N| ≤ n2
Escape (es) : S/I[N] −→ I[N1] I[N2]
with N1 + N2 = N, N1N2 < 0
and |N1| ≤ n3
Replace by a terminal : S/I[N] −→ N"""