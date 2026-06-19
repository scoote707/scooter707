import requests
from concurrent.futures import ThreadPoolExecutor

HEADERS = {
    "User-Agent": "GamePriceFinder/1.0"
}


class StoreResult:
    def __init__(
        self,
        store,
        title,
        price,
        discount=0,
        url=""
    ):
        self.store = store
        self.title = title
        self.price = price
        self.discount = discount
        self.url = url


def request_json(url, params=None):
    try:
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except (
        requests.RequestException,
        ValueError
    ):
        return None


# ---------- STEAM ----------

def steam_search(title):

    data = request_json(
        "https://store.steampowered.com/api/storesearch/",
        {"term": title}
    )

    items = data.get("items") if data else []

    if not items:
        return None

    item = items[0]

    price_data = item.get("price")

    price = (
        price_data.get("final", 0) / 100
        if price_data
        else 0
    )

    return StoreResult(
        "Steam",
        item.get("name", title),
        price,
        item.get("discount_percent", 0),
        f"https://store.steampowered.com/app/{item.get('id', '')}"
    )


# ---------- CHEAPSHARK ----------

def cheapshark_search(title):

    data = request_json(
        "https://www.cheapshark.com/api/1.0/games",
        {"title": title}
    )

    if not data or len(data) == 0:
        return None

    game = data[0]

    cheapest = game.get("cheapest")

    # FIXED LINE 54
    try:
        price = float(cheapest) if cheapest else 0
    except (TypeError, ValueError):
        price = 0

    return StoreResult(
        "CheapShark",
        game.get("external", title),
        price,
        0,
        "https://www.cheapshark.com"
    )


# ---------- GOG ----------

def gog_search(title):

    data = request_json(
        "https://catalog.gog.com/v1/catalog",
        {"query": title}
    )

    if not data:
        return None

    # FIXED LINE 87
    products = data.get("products") or []

    # FIXED LINE 90
    if not products:
        return None

    p = products[0]

    price = 0

    price_info = p.get("price")

    if (
        isinstance(price_info, dict)
        and price_info.get("base")
    ):
        try:
            price = float(
                price_info["base"]
            )
        except (TypeError, ValueError):
            price = 0

    return StoreResult(
        "GOG",
        p.get("title", title),
        price,
        0,
        f"https://www.gog.com/game/{p.get('slug', '')}"
    )


# ---------- EPIC ----------

def epic_search(title):

    # Placeholder until API integration
    return None


# ---------- MAIN ----------

def compare_prices(game):

    stores = [
        steam_search,
        cheapshark_search,
        gog_search,
        epic_search
    ]

    results = []

    # FIXED LINE 121
    with ThreadPoolExecutor(
        max_workers=max(1, len(stores))
    ) as pool:

        futures = [
            pool.submit(
                store,
                game
            )
            for store in stores
        ]

        for future in futures:

            try:
                result = future.result()

                if result:
                    results.append(result)

            except (
                RuntimeError,
                ValueError
            ):
                pass

    return sorted(
        results,
        key=lambda r: r.price
    )


def print_results(results):

    if not results:
        print("\nNo deals found.")
        return

    # FIXED LINE 154
    cheapest = results[0]

    print("\nPRICE COMPARISON\n")

    for r in results:

        sale = (
            f" (-{r.discount}%)"
            if r.discount > 0
            else ""
        )

        print(
            f"{r.store:<12}"
            f"${r.price:.2f}"
            f"{sale}"
        )

        print(
            f"  {r.title}"
        )

    print("\nBEST DEAL")

    print(
        f"{cheapest.store}"
    )

    print(
        f"${cheapest.price:.2f}"
    )

    print(
        cheapest.url
    )


def main():

    game = input(
        "Enter game title: "
    ).strip()

    if not game:
        print(
            "Please enter a game title."
        )
        return

    results = compare_prices(
        game
    )

    print_results(
        results
    )


if __name__ == "__main__":
    main()