from tools.h2_apt_utility4_inplace_context_composition import caller_result


def test_observed_caller_readiness_branches():
    assert caller_result(1, 0) == 0
    assert caller_result(0xFFFFFFFF, 0) == 0
    assert caller_result(0, 1) == 0
    assert caller_result(0, 0) == 1
