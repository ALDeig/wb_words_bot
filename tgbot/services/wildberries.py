import json.decoder
import logging

import httpx
from fake_useragent import UserAgent

user_agent = UserAgent()


headers = {
    "accept-language": "ru-RU,ru;q=0.9,en-GB;q=0.8,en-US;q=0.7,en;q=0.6",
    "dnt": "1",
    "user-agent": user_agent.random
    # "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
}

url = "https://hints.wildberries.ru/api/v1/hint"


async def get_suggest_queries(query) -> list | None:
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



