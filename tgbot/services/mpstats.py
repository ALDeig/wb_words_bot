import asyncio
import logging

import httpx
from fake_useragent import UserAgent

# from . import parser
from . import wildberries

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,\
application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "ru-RU,ru;q=0.9",
    "content_lenght": "73",
    "content-type": "application/x-www-form-urlencoded",
    "dnt": "1",
    "origin": "https://mpstats.io",
    "pragma": "no-cache",
    "referer": "https://mpstats.io/login",
    # "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0"
}

useragent = UserAgent()


def authorization(client: httpx.Client, login: str, password: str) -> bool:
    """Авторизация на сайте mpstats.io"""
    authorize = client.post(
        url="https://mpstats.io/login",
        data={"act": "login", "email": login, "password": password},
        timeout=60
    )
    if authorize.text:
        logging.error(f"Ошибка авторизации. Статус код авторизации - {authorize.status_code}")
        with open("auth.html", "w") as file:
            file.write(authorize.text)
        return False
    return True


def get_response_from_mpstats(client: httpx.Client, ids_product: str) -> dict | None:
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "ru-RU,ru;q=0.9",
        "content-type": "application/json",
        "dnt": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 \
Safari/537.36"
    }
    request = client.post(
        url="https://mpstats.io/api/seo/keywords/expanding",
        headers=headers,
        json={
            "query": ids_product,
            "type": "sku",
            "similar": "false",
            "stopWords": [],
            "searchFullWord": "false"
        },
        timeout=60
    )
    if str(request.status_code).startswith("4"):
        logging.error(f"Ошибка сбора данных из MPStats - {request.text}. Код ошибки - {request.status_code}")
        return
    logging.info(request.text)
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
    with httpx.Client(headers=HEADERS) as client:
        authorize = authorization(client, login, password)
        if not authorize:
            return
        all_popular_product = []
        for query in suggest_queries:
            # popular_product = await get_popular_product_for_query(client, query)
            popular_product = await wildberries.get_search_data(query.strip().lower())
            if not popular_product:
                continue
            all_popular_product.extend(popular_product)
            await asyncio.sleep(3)
        logging.info(f"Amount queries - {len(suggest_queries)}: products - {len(all_popular_product)}")
        if not all_popular_product:
            logging.error("No popular product")
            return
        unique_product = tuple(set(all_popular_product))
        response = get_response_from_mpstats(client, ",".join(unique_product[:100]))
        try:
            return response["result"]
        except (TypeError, KeyError):
            logging.error(f"Ответ MPStats - {response}")
            return


# if __name__ == "__main__":
    # data = asyncio.run(main("Джинсы"))
    # with httpx.Client() as client:
    #     # a = authorization(client, "kolpackir@yandex.ru", "potok522222")
    #     headers = {
    #         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    #         "accept-encoding": "gzip, deflate, br",
    #         "accept-language": "ru-RU,ru;q=0.9,en-GB;q=0.8,en-US;q=0.7,en;q=0.6",
    #         "cache-control": "no-cache",
    #         "dnt": "1",
    #         "pragma": "no-cache",
    #         "referer": "https://mpstats.io/",
    #         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
    #     }
    #     r = client.post(
    #         url="https://mpstats.io/login",
    #         headers=headers,
    #         data={"act": "login", "email": "kolpackir@yandex.ru", "password": "potok522222"}
    #     )
    #     print(r.text)
#     print(data)
    # if data:
    #     print("OK")
    #     save_file_xlsx("sample.xlsx", data["result"])
# 48816772
# 55577669
