from bs4 import BeautifulSoup


def get_popular_product(src: str) -> list | None:
    soup = BeautifulSoup(src, "lxml")
    search_content = soup.find("div", class_="be-content")
    if not search_content:
        return
    raw_search_result = search_content.find("wb-search-result")
    if not raw_search_result:
        return
    raw_ids_products = raw_search_result.get("tpls")
    split_result = raw_ids_products.split(",")
    ids_products = [i.replace("]", "").replace("[", "").strip() for i in split_result[1::2]]
    return ids_products[:20]
