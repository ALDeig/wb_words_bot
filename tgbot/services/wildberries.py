import json.decoder
import logging

import httpx
from fake_useragent import UserAgent

from tgbot.services.errors import WBAuthorizedError

user_agent = UserAgent()
WB_MAIN_URL = "https://suppliers-api.wildberries.ru/"


async def get_suggest_queries(query) -> list | None:
    headers = {
        "accept-language": "ru-RU,ru;q=0.9,en-GB;q=0.8,en-US;q=0.7,en;q=0.6",
        "dnt": "1",
        "user-agent": user_agent.random
    }
    url = "https://hints.wildberries.ru/api/v1/hint"
    # async with httpx.AsyncClient(proxies="http://160.116.216.196:8000") as client:
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers, params={"query": query})
        try:
            json_res = res.json()
        except json.decoder.JSONDecodeError:
            logging.error(res.text)
            return
        result = []
        for elem in json_res:
            if elem["type"] == "suggest":
                result.append(elem["name"].strip())
        return result


async def get_params_query(query, headers):
    query_search = '+'.join(query.split()).lower()
    url = "https://wbxsearch.wildberries.ru/exactmatch/v2/common"
    params = {'query': query_search}
    async with httpx.AsyncClient() as client:
        result = await client.get(url=url, headers=headers, params=params)
        return result.json()


async def get_search_data(query) -> list | None:
    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        'user-agent': user_agent.random
    }
    url = 'https://wbxcatalog-ru.wildberries.ru/{category}/catalog'
    params_query = await get_params_query(query, headers)
    if not params_query:
        return
    queries = params_query.get('query').split('&')
    params = {
        'spp': '0',
        'regions': '75,64,4,38,30,33,70,66,40,71,22,31,68,80,69,48,1',
        'stores': '119261,122252,122256,117673,122258,122259,121631,122466,122467,122495,122496,122498,122590,122591,\
122592,123816,123817,123818,123820,123821,123822,124093,124094,124095,124096,124097,124098,124099,124100,124101,124583,\
124584,125238,125239,125240,132318,132320,132321,125611,133917,132871,132870,132869,132829,133084,133618,132994,133348,\
133347,132709,132597,132807,132291,132012,126674,126676,127466,126679,126680,127014,126675,126670,126667,125186,116433,\
119400,507,3158,117501,120602,6158,121709,120762,124731,1699,130744,2737,117986,1733,686,132043',
        'pricemarginCoeff': '1.0',
        'reg': '0',
        'appType': '1',
        'offlineBonus': '0',
        'onlineBonus': '0',
        'emp': '0',
        'locale': 'ru',
        'lang': 'ru',
        'curr': 'rub',
        'couponsGeo': '12,3,18,15,21',
        'xfilters': params_query.get('filters'),
        'xparams': params_query.get('query'),
        'xshard': params_query.get('shardKey'),
        'search': query,
        'xsearch': 'true'
    }
    for query in queries:
        query = query.split('=')
        params[query[0]] = query[-1]
    async with httpx.AsyncClient() as client:
        result = await client.get(
            url=url.format(category=params_query.get("shardKey")),
            headers=headers,
            params=params
        )
    try:
        products = [str(product["id"]) for product in result.json()["data"]["products"][:20]]
    except Exception as er:
        logging.error(er)
        return
    return products


async def _get_card_list_with_offset(client: httpx.AsyncClient, offset: int):
    response = await client.post(
        url=f"{WB_MAIN_URL}card/list",
        json={
            "id": 1,
            "jsonrpc": "2.0",
            "params": {"query": {"limit": 50, "offset": offset}}
        }
    )
    if response.text in ("invalid token", "unauthorized"):
        raise WBAuthorizedError(response.text)
    return response.json()


async def _get_card_list(client: httpx.AsyncClient) -> dict:
    card_list = await _get_card_list_with_offset(client, 0)
    total_cards = card_list["result"]["cursor"]["total"]
    if total_cards > 50:
        for offset in range(50, total_cards, 50):
            next_card_list =  await _get_card_list_with_offset(client, offset)
            card_list["result"]["cards"].extend(next_card_list["result"]["cards"])
    return card_list


def _find_card_by_scu(card_list: dict, scu: int) -> dict | None:
    cnt = 0
    for card in card_list["result"]["cards"]:
        cnt += 1
        for nomenclature in card["nomenclatures"]:
            if int(nomenclature["nmId"]) == scu:
                return card


def _update_name_in_card(card: dict, new_name: str):
    for params in card["addin"]:
        if params["type"] == "Наименование":
            params["params"][0]["value"] = new_name
            return card


async def _send_changes_to_wb(client: httpx.AsyncClient, card_with_new_name: dict):
    response = await client.post(
        url=f"{WB_MAIN_URL}card/update",
        json={
            "id": 1,
            "jsonrpc": "2.0",
            "params": {"card": card_with_new_name}
        }
    )
    result = response.json()
    if "error" in result:
        raise WBUpdateNameError(result["error"]["couse"]["err"])


async def update_name_wb_card(api_key: str, scu: int, new_name: str) -> bool:
    async with httpx.AsyncClient(headers={"Authorization": api_key}) as client:
        card_list = await _get_card_list(client)
        card = _find_card_by_scu(card_list, scu)
        card_with_new_name = _update_name_in_card(card, new_name)
        await _send_changes_to_wb(client, card_with_new_name)
        return True


