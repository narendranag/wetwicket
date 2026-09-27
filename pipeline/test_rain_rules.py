"""Worked examples 1-6 from the ICC D-L Standard Edition playing conditions (data/reference/doc2.txt)."""
from rain_rules import par_dl_se, se_innings_resource, se_target


def test_example1_team1_interrupted_uplift():
    R1 = se_innings_resource(300, [(180, 3, 120)])
    R2 = se_innings_resource(240)
    assert round(R1, 1) == 87.5 and R2 == 89.3
    assert se_target(180, R1, R2) == 185


def test_example2_team2_delayed():
    assert se_target(212, se_innings_resource(270), se_innings_resource(210)) == 185


def test_example3_team2_interrupted():
    R2 = se_innings_resource(300, [(228, 1, 168)])
    assert round(R2, 1) == 86.8
    assert se_target(250, 100.0, R2) == 218


def test_example4_abandoned_par():
    R2 = se_innings_resource(300, [(228, 1, 168), (108, 3, 96), (7 * 6 + 4, 6, 0)])
    assert round(R2, 1) == 63.8
    assert se_target(250, 100.0, R2) - 1 == 159  # par score at abandonment


def test_example5_team1_terminated_midover():
    R1 = se_innings_resource(300, [(17, 8, 0)])
    assert round(R1, 1) == 93.1
    assert se_target(226, R1, se_innings_resource(198)) == 194


def test_example6():
    R1 = se_innings_resource(300, [(17, 8, 0)])
    R2 = se_innings_resource(198, [(48, 2, 18)])
    assert round(R2, 1) == 64.7
    assert se_target(226, R1, R2) == 158


def test_par_after_k_overs_matches_general_calculator():
    # 50-over chase ended after 30 overs at 3 down, chasing 250.
    assert par_dl_se(S=250, k=30, N=50, wkts2=3) == se_target(250, 100.0, se_innings_resource(300, [(120, 3, 0)])) - 1


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
