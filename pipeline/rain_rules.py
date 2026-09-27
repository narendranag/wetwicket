"""Rain rules for a chase that is ended early, after `k` completed overs.

Each rule returns the par score: the chasing side wins if it has more, ties if equal, loses if fewer.
All rules here assume Team 1 batted its full allocation uninterrupted.

  ARR        Average Run Rate (used until 1991): par = S * k / N.
  MPO        Most Productive Overs (1992 World Cup): par = Team 1's best k overs.
  DL-SE      Duckworth-Lewis Standard Edition (2002 table; still the official ICC/ECB fallback):
             par = S * R2 / R1, rounded down, where R = resources remaining from the published table.
  DL-refit   The same D/L model, Z(u, w) = Z0(w) * (1 - exp(-b(w) * u)), refitted to modern
             Cricsheet first innings. Stern's DLS changes are unpublished; this is an open stand-in.
"""
import math
import os

import numpy as np
import pandas as pd
from scipy.optimize import brentq, least_squares

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SE = pd.read_csv(os.path.join(ROOT, "data", "reference", "dl_standard_edition_2002.csv"),
                 index_col="balls_left").to_numpy()  # SE[balls_left, wickets_lost], percent


def se_resource(balls_left, wkts):
    return 0.0 if wkts >= 10 else float(SE[min(balls_left, 300), wkts])


def se_innings_resource(start_balls, stoppages=()):
    """Resources available to an innings under the Standard Edition.

    start_balls: balls allocated when the innings began. stoppages: (balls_left_at_suspension,
    wickets_lost, balls_left_at_resumption); a termination resumes with 0 balls left.
    """
    return se_resource(start_balls, 0) - sum(se_resource(s, w) - se_resource(r, w) for s, w, r in stoppages)


def se_target(S, R1, R2, G50=245):
    """Standard Edition revised target (ICC playing conditions, clause 5.6)."""
    if R2 < R1:
        return math.floor(S * R2 / R1) + 1
    if R2 == R1:
        return S + 1
    return math.floor(S + (R2 - R1) * G50 / 100) + 1


def par_arr(S, k, N, **_):
    return S * k / N


def par_mpo(over_runs1, k, **_):
    return sum(sorted(over_runs1, reverse=True)[:k])


def par_dl_se(S, k, N, wkts2, **_):
    r1 = se_resource(N * 6, 0)
    r2 = r1 - se_resource((N - k) * 6, wkts2)
    return math.floor(S * r2 / r1)


class ProEdition:
    """D/L Professional Edition (2004), reconstructed from public sources.

    Duckworth & Lewis (2004) add a match parameter lambda, set by Team 1's total S:
        Z(u, w; lam) = Z0 F(w) lam^(n(w)+1) (1 - exp(-b u / (F(w) lam^n(w))))
    The ICC never published F(w), b or n(w). We use C. Baker's reconstruction ("Duckworth-Lewis
    analysis", 2011): F(w) and b = 0.03 fitted to the 2002 table, n(0) = 5, and his cubic for n(w).
    lam solves Z(N, 0; lam) / Z(N, 0; 1) = S / E_N, where E_N is the average N-over total implied
    by G50. High totals give lam > 1, which flattens the curves: runs are expected more evenly
    through the innings, so an early flurry earns less credit.
    """

    B = 0.03
    F = np.array([1, 0.889, 0.770, 0.643, 0.514, 0.388, 0.272, 0.171, 0.0927, 0.0365])
    NW = np.array([0.005 * w ** 3 - 0.0583 * w ** 2 - 0.1969 * w + 4.9979 for w in range(10)])

    @classmethod
    def z(cls, u, w, lam=1.0):
        """Z per unit Z0."""
        f, n = cls.F[w], cls.NW[w]
        return f * lam ** (n + 1) * (1 - np.exp(-cls.B * u / (f * lam ** n)))

    @classmethod
    def lam(cls, S, N, G50=245, high_only=False, expected=None):
        """expected: the average N-over total to compare S with; defaults to the one implied by G50."""
        if expected is None:
            expected = G50 * cls.z(N, 0) / cls.z(50, 0)
        ratio = S / expected
        if high_only and ratio <= 1:
            return 1.0
        return brentq(lambda l: cls.z(N, 0, l) / cls.z(N, 0) - ratio, 0.3, 5.0)

    @classmethod
    def resource(cls, u, w, N=50, lam=1.0):
        """Percent of a full N-over innings' resources remaining."""
        if w >= 10 or u <= 0:
            return 0.0
        return 100 * cls.z(u, w, lam) / cls.z(N, 0, lam)

    @classmethod
    def par(cls, S, k, N, wkts2, G50=245, high_only=False, **_):
        lam = cls.lam(S, N, G50, high_only)
        return S * (1 - cls.resource(N - k, wkts2, N, lam) / 100)


class RefitModel:
    """Z(u, w) = Z0 * F(w) * (1 - exp(-b * u / F(w))): expected further runs, u overs left, w down.

    This is the constrained form Duckworth & Lewis published (1998). F(0) = 1 and F falls with each
    wicket, which keeps the resource table monotone in wickets.
    """

    def __init__(self, N, z0, b, F):
        self.N, self.z0, self.b, self.F = N, z0, b, F

    def z(self, u, w):
        f = self.F[w]
        return self.z0 * f * (1 - np.exp(-self.b * u / f))

    @staticmethod
    def _unpack(theta):
        z0, b = np.exp(theta[0]), np.exp(theta[1])
        F = np.exp(-np.concatenate([[0], np.cumsum(np.exp(theta[2:]))]))  # decreasing, F[0] = 1
        return z0, b, F

    @classmethod
    def fit(cls, states, N):
        """states: DataFrame of first-innings states with columns u (overs left), w, remaining."""
        u, w, y = states.u.to_numpy(), states.w.to_numpy(), states.remaining.to_numpy()

        def resid(theta):
            z0, b, F = cls._unpack(theta)
            f = F[w]
            return z0 * f * (1 - np.exp(-b * u / f)) - y

        theta0 = np.concatenate([[np.log(300), np.log(0.03)], np.log(np.full(9, 0.2))])
        theta = least_squares(resid, theta0).x
        return cls(N, *cls._unpack(theta))

    def resource(self, u, w):
        """Percent of a full N-over innings' resources remaining."""
        if w >= 10 or u <= 0:
            return 0.0
        return 100 * self.z(u, w) / self.z(self.N, 0)

    def table(self):
        return pd.DataFrame({f"w{w}": [self.resource(u, w) for u in range(self.N, -1, -1)] for w in range(10)},
                            index=pd.Index(range(self.N, -1, -1), name="overs_left"))

    def par(self, S, k, N, wkts2, **_):
        r2 = 100 - self.resource(N - k, wkts2)
        return S * r2 / 100


def first_innings_states(overs, matches, since="2015-01-01"):
    """Over-end states of complete, uninterrupted first innings, with runs still to come."""
    ok = matches[(matches.rain == "") & (matches.date >= since)
                 & ((matches.wkts1 >= 10) | (matches.balls1 >= matches.sched_overs * 6))]
    o = overs[(overs.inn == 1) & overs.match_id.isin(ok.match_id)].merge(
        ok[["match_id", "runs1", "sched_overs"]], on="match_id")
    o = o[o.over < o.sched_overs]
    states = pd.DataFrame({"u": o.sched_overs - o.balls / 6, "w": o.wkts, "remaining": o.runs1 - o.runs})
    starts = pd.DataFrame({"u": ok.sched_overs.astype(float), "w": 0, "remaining": ok.runs1})
    states = pd.concat([starts, states], ignore_index=True)
    return states[states.w < 10]
