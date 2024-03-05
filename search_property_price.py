#!/usr/bin/env python

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from config import CONFIG
import sys

class PropertyFinder:
    def __init__(self, id):
        self.id = id
        self.found = asyncio.Event()
        self.base_url = CONFIG["base_url"]
        self.pages = CONFIG["pages"]

    async def get_property_price(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        price_tag = soup.find('span', class_='ant-typography price')
                        if price_tag:
                            price_text = price_tag.find('strong').text.strip()
                            if price_tag:
                                print(price_text)
                                self.found.set()
                                return
            print(f"Price not found for id {self.id}")
        except Exception as e:
            print("Error when obtaining the price of the property:", e)

    async def search_property(self, session, section, page):
        url = f"{self.base_url}/{section}/inmuebles/pagina{page}"
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                link = soup.find('a', class_='lc-cardCover', href=lambda href: href and self.id in href)
                if link:
                    return f"{self.base_url}{link['href']}"
        return None

    async def get_property_url(self, section):
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for page in range(1, self.pages + 1):
                    if not self.found.is_set():
                        tasks.append(self.search_property(session, section, page))
                results = await asyncio.gather(*tasks)
                return next((url for url in results if url), None)
        except Exception as e:
            print("Error when searching for the property URL:", e)
        return None

    async def search_property_by_section(self, section):
        url = await self.get_property_url(section)
        if url:
            await self.get_property_price(url)
        else:
            print(f"No property found with ID {self.id} in the {section} section.")

async def main(id):
    property_finder = PropertyFinder(id)
    await property_finder.search_property_by_section("venta")
    if not property_finder.found.is_set():
        await property_finder.search_property_by_section("alquiler")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: search_property_price <property_id>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
