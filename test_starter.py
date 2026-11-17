import asyncio
import unittest
from decimal import Decimal

from starter import recommend_price, sample_fetch_offers


def source(*offers, status="success"):
    async def fetch():
        return {"status": status, "offers": list(offers)}
    return fetch


def offer(seller, price, days: int | None = 1):
    return {"seller": seller, "price": Decimal(price), "delivery_days": days}


def run(fetch, current, minimum, timeout_s=2.0):
    return asyncio.run(recommend_price(fetch, Decimal(current), Decimal(minimum), timeout_s))


class RecommendPriceTest(unittest.TestCase):
    def test_example_from_task(self):
        # myshop и долгая доставка отсекаются остается PARTS 4800
        r = run(sample_fetch_offers, "4900.00", "4500.00")
        self.assertEqual(r["price"], Decimal("4728.00"))
        self.assertEqual(r["decision"], "APPLY")

    def test_timeout_gives_hold(self):
        async def slow():
            await asyncio.sleep(1)
            return {"status": "success", "offers": []}
        r = run(slow, "1000.00", "500.00", timeout_s=0.05)
        self.assertEqual((r["price"], r["decision"]), (Decimal("1000.00"), "HOLD"))

    def test_source_error_gives_hold(self):
        async def broken():
            raise ConnectionError("сайт лежит")
        r = run(broken, "1000.00", "500.00")
        self.assertEqual((r["price"], r["decision"]), (Decimal("1000.00"), "HOLD"))

    def test_partial_status_gives_hold(self):
        r = run(source(offer("A", "900.00"), status="partial"), "1000.00", "500.00")
        self.assertEqual((r["price"], r["decision"]), (Decimal("1000.00"), "HOLD"))

    def test_no_good_offers_hold_even_below_min(self):
        r = run(source(offer("MyShop", "100.00"), offer("X", "100.00", None)), "400.00", "500.00")
        self.assertEqual((r["price"], r["decision"]), (Decimal("400.00"), "HOLD"))

    def test_round_down_to_cent(self):
        # 100.01 * 0.985 = 98.50985 обычное округление дало бы 98.51
        r = run(source(offer("A", "100.01")), "100.00", "1.00")
        self.assertEqual(r["price"], Decimal("98.50"))

    def test_exactly_30_percent_is_apply(self):
        # 1000 * 0.985 = 985 меньше минимума значит берем 1300 ровно +30%
        r = run(source(offer("A", "1000.00")), "1000.00", "1300.00")
        self.assertEqual((r["price"], r["decision"]), (Decimal("1300.00"), "APPLY"))

    def test_more_than_30_percent_is_review(self):
        r = run(source(offer("A", "1000.00")), "1000.00", "1300.01")
        self.assertEqual((r["price"], r["decision"]), (Decimal("1300.01"), "REVIEW"))


if __name__ == "__main__":
    unittest.main()
