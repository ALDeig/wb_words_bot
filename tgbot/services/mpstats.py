import asyncio
import logging

import httpx

# from . import parser
from . import wildberries

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "ru-RU,ru;q=0.9",
    "content_lenght": "73",
    "content-type": "application/x-www-form-urlencoded",
    "dnt": "1",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
}


async def authorization(client: httpx.AsyncClient, login: str, password: str) -> bool:
    """Авторизация на сайте mpstats.io"""
    authorize = await client.post(
        url="https://mpstats.io/login",
        data={"act": "login", "email": login, "password": password},
        timeout=60
    )
    if authorize.text:
        return False
    return True


async def get_response_from_mpstats(client: httpx.AsyncClient, ids_product: str) -> dict | None:
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "ru-RU,ru;q=0.9",
        "content-type": "application/json",
        "dnt": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 \
                       Safari/537.36"
    }
    request = await client.post(
        url="https://mpstats.io/api/seo/keywords/expanding",
        headers=headers,
        json={
            "query": ids_product,
            "type": "sku",
            "similar": False,
            "stopWords": [],
            "searchFullWord": False
        },
        timeout=60
    )
    if str(request.status_code).startswith("4"):
        return
    return request.json()


# async def get_popular_product_for_query(client: httpx.AsyncClient, query: str) -> list | None:
#     headers = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,\
#         application/signed-exchange;v=b3;q=0.9",
#         "accept-encoding": "gzip, deflate, br",
#         "accept-language": "ru-RU,ru;q=0.9,en-GB;q=0.8,en-US;q=0.7,en;q=0.6",
#         "cache-control": "no-cache",
#         # "content-length": "1672",
#         "content-type": "application/json",
#         "dnt": "1",
#         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
#     }
#     response = await client.get(
#         url="https://mpstats.io/wb/bysearch",
#         headers=headers,
#         params={"query": query + " "},
#         timeout=120
#     )
#     return parser.get_popular_product(response.text)


def get_list_queries(queries: str):
    queries_list = list(filter(bool, queries.split("\n")))
    clear_queries = list(map(str.strip, queries_list))
    return clear_queries


async def main(queries: str, login, password) -> list | None:
    suggest_queries = get_list_queries(queries)
    async with httpx.AsyncClient(headers=HEADERS) as client:
        authorize = await authorization(client, login, password)
        if not authorize:
            return
        all_popular_product = []
        logging.info(f"Amount queries - {len(suggest_queries)}")
        for query in suggest_queries:
            # popular_product = await get_popular_product_for_query(client, query)
            popular_product = await wildberries.get_search_data(query.strip().lower())
            if not popular_product:
                continue
            all_popular_product.extend(popular_product)
            await asyncio.sleep(3)
        logging.info(f"Amount popular products - {len(all_popular_product)}")
        if not all_popular_product:
            return
        response = await get_response_from_mpstats(client, "\n".join(set(all_popular_product)))
        return response["result"]


# if __name__ == "__main__":
#     data = asyncio.run(main("Джинсы"))
#     print(data)
    # if data:
    #     print("OK")
    #     save_file_xlsx("sample.xlsx", data["result"])
# 48816772
# 55577669
