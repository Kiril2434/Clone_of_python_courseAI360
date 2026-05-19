import typing

import pytest

try:
    from .banner_engine import (
        BannerStat, Banner, BannerStorage, EmptyBannerStorageError, EpsilonGreedyBannerEngine
    )
except ImportError:
    from banner_engine import (
        BannerStat, Banner, BannerStorage, EmptyBannerStorageError, EpsilonGreedyBannerEngine
    )

TEST_DEFAULT_CTR = 0.1

def count_ctr(clicks: int, shows: int, default_ctr: float = TEST_DEFAULT_CTR) -> float:
    if shows == 0:
        return default_ctr
    else:
        return clicks / shows

@pytest.fixture(scope="function")
def test_banners() -> list[Banner]:
    return [
        Banner("b1", cost=1, stat=BannerStat(10, 20)),
        Banner("b2", cost=250, stat=BannerStat(20, 20)),
        Banner("b3", cost=100, stat=BannerStat(0, 20)),
        Banner("b4", cost=100, stat=BannerStat(1, 20)),
    ]


@pytest.mark.parametrize("clicks, shows, expected_ctr", [(1, 1, 1.0), (20, 100, 0.2), (5, 100, 0.05)])
def test_banner_stat_ctr_value(clicks: int, shows: int, expected_ctr: float) -> None:
    assert BannerStat(clicks, shows).compute_ctr(TEST_DEFAULT_CTR) == expected_ctr


def test_empty_stat_compute_ctr_returns_default_ctr() -> None:
    assert BannerStat(0, 0).compute_ctr(TEST_DEFAULT_CTR) == TEST_DEFAULT_CTR


def test_banner_stat_add_show_lowers_ctr() -> None:
    zn = [(1, 1), (20, 100), (5, 100)]
    for clicks, shows in zn:
        baner_stat = BannerStat(clicks, shows)
        baner_stat.add_show()
        assert count_ctr(baner_stat.clicks, baner_stat.shows) == pytest.approx(count_ctr(clicks, shows + 1))


def test_banner_stat_add_click_increases_ctr() -> None:
    zn = [(1, 1), (20, 100), (5, 100)]
    for clicks, shows in zn:
        baner_stat = BannerStat(clicks, shows)
        baner_stat.add_click()
        assert count_ctr(baner_stat.clicks, baner_stat.shows) == pytest.approx(count_ctr(clicks + 1, shows))


def test_get_banner_with_highest_cpc_returns_banner_with_highest_cpc(test_banners: list[Banner]) -> None:
    banners = BannerStorage(test_banners)
    best_cpc = 0.0
    for banner in test_banners:
        cpc = banner.cost * banner.stat.compute_ctr(TEST_DEFAULT_CTR)
        best_cpc = cpc if cpc > best_cpc else best_cpc
    best_banner = banners.banner_with_highest_cpc()
    best_banner_cpr = best_banner.stat.compute_ctr(TEST_DEFAULT_CTR)
    assert best_cpc == best_banner_cpr * best_banner.cost

def test_banner_engine_raise_empty_storage_exception_if_constructed_with_empty_storage() -> None:
    with pytest.raises(EmptyBannerStorageError):
        EpsilonGreedyBannerEngine(BannerStorage([]), 1.0)

def test_engine_send_click_not_fails_on_unknown_banner(test_banners: list[Banner]) -> None:
    EpsilonGreedyBannerEngine(BannerStorage(test_banners), 1.0).send_click("b1111")


def test_engine_with_zero_random_probability_shows_banner_with_highest_cpc(test_banners: list[Banner]) -> None:
    banners = BannerStorage(test_banners)
    engine = EpsilonGreedyBannerEngine(banners, 0.0)
    assert engine.show_banner() == banners.banner_with_highest_cpc().banner_id

@pytest.mark.parametrize("expected_random_banner", ["b1", "b2", "b3", "b4"])
def test_engine_with_1_random_banner_probability_gets_random_banner(
        expected_random_banner: str,
        test_banners: list[Banner],
        monkeypatch: typing.Any
        ) -> None:
    banners = BannerStorage(test_banners)
    engine = EpsilonGreedyBannerEngine(banners, 1.0)
    for i in range(4):
        monkeypatch.setattr(banners, "banner_with_highest_cpc", lambda: test_banners[i])
        monkeypatch.setattr(banners, "random_banner", lambda: banners.get_banner(expected_random_banner))
        assert engine.show_banner() == expected_random_banner


def test_total_cost_equals_to_cost_of_clicked_banners(test_banners: list[Banner]) -> None:
    banners = BannerStorage(test_banners)
    engine = EpsilonGreedyBannerEngine(banners, 0.0)
    cost = 0
    for banner in test_banners:
        cost += banner.cost
        engine.send_click(banner.banner_id)
        assert engine.total_cost == cost


def test_engine_show_increases_banner_show_stat(test_banners: list[Banner]) -> None:
    banners = BannerStorage(test_banners)
    engine_0 = EpsilonGreedyBannerEngine(banners, 0.0)
    engine_1 = EpsilonGreedyBannerEngine(banners, 1.0)
    shows = {}
    for banner in test_banners:
        shows[banner.banner_id] = banner.stat.shows
    banner1 = engine_0.show_banner()
    banner2 = engine_1.show_banner()
    if banner1 == banner2:
        assert shows[banner1] + 2 == banners.get_banner(banner1).stat.shows
    else:
        assert shows[banner1] + 1 == banners.get_banner(banner1).stat.shows and \
            shows[banner2] + 1 == banners.get_banner(banner2).stat.shows


def test_engine_click_increases_banner_click_stat(test_banners: list[Banner]) -> None:
    banners = BannerStorage(test_banners)
    engine_0 = EpsilonGreedyBannerEngine(banners, 0.0)
    for i in range(4):
        clicks_i = test_banners[i].stat.clicks
        engine_0.send_click(test_banners[i].banner_id)
        assert clicks_i + 1 == test_banners[i].stat.clicks
