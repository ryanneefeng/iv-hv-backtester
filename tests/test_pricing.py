import math

import numpy as np
import pytest

from core.pricing import Option


# Shared baseline params for most tests: at-the-money, 1yr, moderate vol
S, K, T, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.20


def test_put_call_parity():
    """C - P should equal S - K*e^(-rT) to within floating point tolerance."""
    opt = Option(S, K, T, r, sigma)
    lhs = opt.call_price() - opt.put_price()
    rhs = S - K * math.exp(-r * T)
    assert lhs == pytest.approx(rhs, abs=1e-8)


def test_call_and_put_prices_nonnegative_and_bounded():
    """Prices must be non-negative; a call can never be worth more than the
    stock itself, a put never more than the discounted strike."""
    opt = Option(S, K, T, r, sigma)
    call = opt.call_price()
    put = opt.put_price()
    assert call >= 0
    assert put >= 0
    assert call <= S
    assert put <= K * math.exp(-r * T)


def test_delta_call_in_bounds():
    opt = Option(S, K, T, r, sigma)
    assert 0.0 <= opt.delta_call() <= 1.0


def test_delta_put_in_bounds():
    opt = Option(S, K, T, r, sigma)
    assert -1.0 <= opt.delta_put() <= 0.0


def test_gamma_and_vega_positive():
    """Gamma and vega are shared between calls and puts and must be positive
    for any option with positive time value."""
    opt = Option(S, K, T, r, sigma)
    assert opt.gamma() > 0
    assert opt.vega() > 0


def test_deep_itm_call_approaches_intrinsic_value():
    """A call that's deep in the money with little time value left should
    price close to its discounted intrinsic value, S - K*e^(-rT)."""
    opt = Option(S=200.0, K=100.0, T=1 / 365, r=r, sigma=sigma)
    intrinsic = 200.0 - 100.0 * math.exp(-r * (1 / 365))
    assert opt.call_price() == pytest.approx(intrinsic, abs=0.5)


def test_implied_volatility_recovers_known_sigma():
    """Price an option at a known sigma, then solve for IV off that price.
    The solver should recover the original sigma."""
    true_sigma = 0.35
    priced = Option(S, K, T, r, true_sigma)

    call_iv = Option(S, K, T, r, 0.20).implied_volatility_call(priced.call_price())
    put_iv = Option(S, K, T, r, 0.20).implied_volatility_put(priced.put_price())

    assert call_iv == pytest.approx(true_sigma, abs=1e-4)
    assert put_iv == pytest.approx(true_sigma, abs=1e-4)


@pytest.mark.parametrize(
    "bad_S,bad_K,bad_T,bad_sigma",
    [
        (0, K, T, sigma),
        (-10, K, T, sigma),
        (S, 0, T, sigma),
        (S, K, 0, sigma),
        (S, K, T, 0),
        (S, K, T, -0.1),
    ],
)
def test_invalid_inputs_raise_value_error(bad_S, bad_K, bad_T, bad_sigma):
    with pytest.raises(ValueError):
        Option(bad_S, bad_K, bad_T, r, bad_sigma)


def test_monte_carlo_matches_black_scholes():
    """MC with antithetic variates should converge close to the analytical
    BS price, well within its own reported confidence interval."""
    np.random.seed(42)
    opt = Option(S, K, T, r, sigma)
    bs_call = opt.call_price()
    bs_put = opt.put_price()

    mc_call, ci_call = opt.monte_carlo_call(num_sims=200_000)
    mc_put, ci_put = opt.monte_carlo_put(num_sims=200_000)

    assert abs(mc_call - bs_call) < 3 * ci_call
    assert abs(mc_put - bs_put) < 3 * ci_put