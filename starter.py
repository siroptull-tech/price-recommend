"""Учебный фрагмент для тестового задания ТОЛЬКООПТ.

Python 3.10+, только стандартная библиотека. Запуск примера: python starter.py
В функции recommend_price намеренно есть ошибки. Исправьте её по правилам ниже.
sample_fetch_offers имитирует внешний источник: реальные запросы не нужны.

Контракт fetch_offers(): async-функция без аргументов, возвращает словарь
со status (success / partial / error) и offers (список предложений).
Все суммы на входе — положительные Decimal с точностью до копейки.
seller — строка; delivery_days — неотрицательное целое число или None.
Формат входных данных корректен; дополнительных проверок типов не требуется.
fetch_offers может завершиться исключением или долго ожидать ответа.
current_price — текущая цена; min_price — минимально допустимая цена.
timeout_s — положительное число секунд, по умолчанию 2.

ПРАВИЛА В ПОРЯДКЕ ПРИМЕНЕНИЯ
1. Ограничьте ожидание fetch_offers значением timeout_s. При ошибке источника,
   тайм-ауте или status != success верните текущую цену и HOLD.
2. Учитывайте предложения с известной доставкой не более 6 дней.
   Исключайте собственный магазин MYSHOP независимо от регистра букв.
3. Если подходящих предложений нет, верните текущую цену и HOLD,
   даже если текущая цена ниже min_price.
4. Минимальную цену подходящего конкурента уменьшите на 1,5% и округлите
   вниз до копейки. Рекомендация — максимум из этой суммы и min_price.
5. Если рекомендация отличается от текущей цены более чем на 30% в любую
   сторону, верните рекомендацию и REVIEW. Иначе — рекомендацию и APPLY.
   Ровно 30% допускается. REVIEW означает, что автоматическое применение
   запрещено до ручной проверки.

РЕЗУЛЬТАТ
Словарь с полями price (Decimal), decision (APPLY / REVIEW / HOLD),
reason (короткая понятная причина). Сохраните интерфейс recommend_price;
вспомогательные функции допустимы. Пример ниже после исправления должен
вернуть price = Decimal("4728.00"), decision = "APPLY".

ПРОВЕРКА
Добавьте минимум два автоматических теста: обычный расчёт и один сбой
или граничный случай на ваш выбор. Укажите команду запуска тестов.
Достаточно стандартной библиотеки; pytest также допустим.
"""

import asyncio
from decimal import ROUND_FLOOR, Decimal

OWN_SHOP = "myshop"
MAX_DELIVERY_DAYS = 6
DISCOUNT = Decimal("0.985")  # минус 1.5%
MAX_CHANGE = Decimal("0.30")
CENT = Decimal("0.01")


def _answer(price, decision, reason):
    return {"price": price, "decision": decision, "reason": reason}


def _good_offer(offer):
    # доставка известна и не дольше 6 дней и это не мы
    days = offer["delivery_days"]
    if days is None or days > MAX_DELIVERY_DAYS:
        return False
    return offer["seller"].casefold() != OWN_SHOP


async def recommend_price(fetch_offers, current_price, min_price, timeout_s=2.0):
    try:
        result = await asyncio.wait_for(fetch_offers(), timeout=timeout_s)
    except asyncio.TimeoutError:
        return _answer(current_price, "HOLD", f"источник не ответил за {timeout_s} с")
    except Exception as e:  # noqa: BLE001 любая ошибка источника это HOLD по правилу 1
        return _answer(current_price, "HOLD", f"ошибка источника: {e!r}")

    if result.get("status") != "success":
        return _answer(current_price, "HOLD", f"статус источника {result.get('status')}")

    prices = [o["price"] for o in result.get("offers", []) if _good_offer(o)]
    if not prices:
        return _answer(current_price, "HOLD", "нет подходящих предложений конкурентов")

    # все в Decimal без float чтобы не терять копейки
    competitor = min(prices)
    price = (competitor * DISCOUNT).quantize(CENT, rounding=ROUND_FLOOR)
    if price < min_price:
        price = min_price
        reason = f"цена конкурента {competitor} ниже допустимой ставим минимум {min_price}"
    else:
        reason = f"минимальная цена конкурента {competitor} минус 1.5%"

    # ровно 30% еще можно
    if abs(price - current_price) > current_price * MAX_CHANGE:
        return _answer(price, "REVIEW", reason + ", изменение больше 30% нужна ручная проверка")
    return _answer(price, "APPLY", reason)


async def sample_fetch_offers():
    return {
        "status": "success",
        "offers": [
            {"seller": "myshop", "price": Decimal("4300.00"), "delivery_days": 2},
            {"seller": "PARTS", "price": Decimal("4800.00"), "delivery_days": 3},
            {"seller": "SLOW", "price": Decimal("4700.00"), "delivery_days": 8},
        ],
    }


if __name__ == "__main__":
    print(asyncio.run(recommend_price(
        sample_fetch_offers,
        current_price=Decimal("4900.00"),
        min_price=Decimal("4500.00"),
    )))
