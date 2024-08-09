import ssl
import httpcore
import httpx
import json
import re
from typing import Any, Dict, List, Optional
import random
import logging
import discord
import discord.ext
import io
import asyncio

shopify_author = "github.com/arshansgithub"
shopify_author_url = ""
author_footer = discord.EmbedFooter(
    text=f"Developer: {shopify_author}", icon_url=shopify_author_url
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ShopifySelect(discord.ui.Select):
    def __init__(self, products: Dict[str, any], key: int, domain: str):
        self.products = products
        self.products_keys = list(products.keys())
        self.key = key
        self.domain = domain

        exportATC = discord.SelectOption(
            label="Export ATC Link", value="Export ATC Link"
        )
        AATC = discord.SelectOption(label="Add ALL to Cart", value="Add ALL to Cart")
        exportAllATC = discord.SelectOption(
            label="Export All ATC Links", value="Export All ATC Links"
        )

        options = [AATC, exportATC, exportAllATC]

        super().__init__(placeholder="Action", options=options)

    async def callback(self, interaction: discord.Interaction):
        title = self.products_keys[self.key]
        current_product = self.products[title]

        if self.values[0] == "Export ATC Link":

            modal = ShopifyATC(title, current_product, self.domain)

            await interaction.response.send_modal(modal)

        elif self.values[0] == "Export All ATC Links":
            await interaction.response.defer()
            embed = discord.Embed(
                title="Exported. Check your DMs!",
                description="Make sure you have your DMs enabled!",
                color=discord.Color.random(),
                footer=author_footer,
            )
            embed2 = discord.Embed(
                title="Exported Freebies",
                description="Here are the freebies you requested",
                color=discord.Color.random(),
                footer=author_footer,
            )

            file_contents = await ShopifyPagination.export_all(
                self.products, self.domain
            )

            file = discord.File(
                io.StringIO(file_contents),
                filename=f"{self.domain.split('.')[0]}-freebies.txt",
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

            await interaction.user.send(embed=embed2, file=file)

        elif self.values[0] == "Add ALL to Cart":
            allIds = [product.get("id") for product in self.products.values()]
            link = await ShopifyScraper.build_all_to_cart_link(allIds, self.domain)

            embed = discord.Embed(
                title="Add ALL to Cart",
                color=discord.Color.random(),
                footer=author_footer,
            )
            embed.add_field(
                name="Checkout link", value=f"[ATC]({link})\n\n||{link}||", inline=True
            )

            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except discord.errors.HTTPException:
                file = discord.File(
                    io.StringIO(link),
                    filename=f"{self.domain.split('.')[0]}-ATC-freebies.txt",
                )

                embed = discord.Embed(
                    title="Checkout link is too long",
                    color=discord.Color.random(),
                    footer=author_footer,
                )
                embed.description = "The checkout link is too long to be sent in an embed. Attached is a file with the link."

                await interaction.response.send_message(
                    embed=embed, file=file, ephemeral=True
                )


class DiscordDomainModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Shopify Store Domain", timeout=None)
        self.add_item(
            discord.ui.InputText(
                label="Domain",
                placeholder="Enter domain",
                row=0,
                min_length=1,
                max_length=253,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Checking store...",
            description="Please wait while we check the store",
            color=discord.Color.random(),
            footer=author_footer,
        )
        await interaction.response.send_message(
            content=f"{interaction.user.mention}", embed=embed, ephemeral=True
        )

        domain = self.children[0].value

        validate = await scraper.validate_domain(domain)

        if not validate:
            embed = discord.Embed(
                title="Invalid domain",
                description="Please enter a valid domain",
                color=discord.Color.random(),
                footer=author_footer,
            )
            await interaction.edit_original_response(
                content=f"{interaction.user.mention}", embed=embed
            )
            return

        domain = validate

        getProducts = await scraper.get_products(domain)

        if not getProducts["products"]:
            embed = discord.Embed(
                title="No products found",
                description=f"No products found on this {domain}. It may not be a shopify store.",
                color=discord.Color.random(),
                footer=author_footer,
            )
            await interaction.edit_original_response(
                content=f"{interaction.user.mention}", embed=embed
            )
            return

        freebies = await scraper.search_products(getProducts.get("products"))

        if not freebies:
            embed = discord.Embed(
                title="No freebies found",
                description=f"No freebies found on '{domain}'",
                color=discord.Color.random(),
                footer=author_footer,
            )
            await interaction.edit_original_response(
                content=f"{interaction.user.mention}", embed=embed
            )
            return

        embed = await ShopifyPagination.build_embed(0, freebies)

        Pagination = ShopifyPagination(freebies, domain)

        await interaction.edit_original_response(
            content=f"{interaction.user.mention}", embed=embed, view=Pagination
        )


class ShopifyATC(discord.ui.Modal):
    def __init__(self, product_title: str, product: Dict[str, any], domain: str):
        super().__init__(title="Quantity for freebie", timeout=None)

        self.domain = domain
        self.product_title = product_title
        self.product = product
        self.timeout = None

        self.add_item(
            discord.ui.InputText(
                label="Quantity",
                placeholder="Enter quantity",
                row=0,
                min_length=1,
                max_length=3,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        quantity = self.children[0].value

        checkout_link = await ShopifyScraper.build_checkout_link(
            self.product, quantity, self.domain
        )

        embed = discord.Embed(
            title=f"ATC Link - {self.product_title}",
            color=discord.Color.random(),
            footer=author_footer,
        )
        embed.add_field(
            name="Checkout Link",
            value=f"[ATC]({checkout_link})\n\n||{checkout_link}||",
            inline=True,
        )

        await interaction.followup.send(embed=embed, ephemeral=True)


class ShopifyPagination(discord.ui.View):
    def __init__(self, pages: Dict[str, any], domain: str):
        super().__init__(timeout=None)

        self.domain = domain

        self.page_keys = list(pages.keys())
        self.pages = pages
        self.current_page = 0

        self.add_item(ShopifySelect(self.pages, self.current_page, self.domain))

    @staticmethod
    async def build_embed(current_page: int = 0, pages: Dict[str, any] = None):
        fields_to_display = [
            "requires_shipping",
            "available",
            "compare_at_price",
            "price",
            "suspected_freebie",
        ]

        title = list(pages.keys())[current_page]
        page = pages.get(title)

        embed = discord.Embed(
            title=title, color=discord.Color.random(), footer=author_footer
        )

        for field in fields_to_display:
            if page.get(field) is None:
                continue

            original_field = field

            if "_" in field:
                field = field.replace("_", " ")
            field = field.title()

            embed.add_field(name=field, value=page.get(original_field), inline=True)

        embed.set_image(url=page.get("image_url"))
        embed.set_footer(text=f"Freebie {current_page + 1}/{len(list(pages.keys()))}")

        return embed

    @staticmethod
    async def export_all(products: Dict[str, dict], domain: str):
        file_contents = (
            f"Developer: {shopify_author} - Exported freebies from: {domain}\n\n"
        )

        requires_shipping = []
        does_not_require_shipping = []
        suspected_freebies = []
        unavailable_items = []

        for key, value in products.items():
            atc_link = await ShopifyScraper.build_checkout_link(value, 1, domain)
            if value.get("suspected_freebie"):
                suspected_freebies.append(f"Name: {key}\nLink: {atc_link}\n\n")
            elif value.get("requires_shipping"):
                requires_shipping.append(f"Name: {key}\nLink: {atc_link}\n\n")
            elif not value.get("available"):
                unavailable_items.append(f"{key} - {atc_link}")
            else:
                does_not_require_shipping.append(f"{key} - {atc_link}")

        file_contents += "---Requires Shipping---\n"
        file_contents += "\n".join(requires_shipping)
        
        if requires_shipping:
            allIds = [product.get("id") for product in products.values() if product.get("requires_shipping")]
            link = await ShopifyScraper.build_all_to_cart_link(allIds, domain)
            file_contents += f"\n\nATC: {link}\n\n"
        
        file_contents += "\n\n---Does Not Require Shipping---\n"
        file_contents += "\n".join(does_not_require_shipping)
        
        if does_not_require_shipping:
            allIds = [product.get("id") for product in products.values() if not product.get("requires_shipping")]
            link = await ShopifyScraper.build_all_to_cart_link(allIds, domain)
            file_contents += f"\n\nATC: {link}\n\n"
        
        file_contents += "\n\n---Suspected Freebies---\n"
        file_contents += "\n".join(suspected_freebies)
        
        if suspected_freebies:
            allIds = [product.get("id") for product in products.values() if product.get("suspected_freebie")]
            link = await ShopifyScraper.build_all_to_cart_link(allIds, domain)
            file_contents += f"\n\nATC: {link}\n\n"
        
        file_contents += "\n\n---Unavailable Items---\n"
        file_contents += "\n".join(unavailable_items)
        
        if unavailable_items:
            allIds = [product.get("id") for product in products.values() if not product.get("available")]
            link = await ShopifyScraper.build_all_to_cart_link(allIds, domain)
            file_contents += f"\n\nATC: {link}\n\n"

        return file_contents

    async def show_page(self, interaction: discord.Interaction):

        embed = await self.build_embed(current_page=self.current_page, pages=self.pages)

        self.remove_item(self.children[-1])

        self.add_item(ShopifySelect(self.pages, self.current_page, self.domain))

        await interaction.edit_original_response(
            content=f"{interaction.user.mention}", embed=embed, view=self
        )

    @discord.ui.button(
        label="Go to Beginning", row=0, style=discord.ButtonStyle.primary, emoji="🏃"
    )
    async def first_page(
        self, button: discord.Button, interaction: discord.Interaction
    ):
        await interaction.response.defer()

        self.current_page = 0

        await self.show_page(interaction)

    @discord.ui.button(
        label="Previous Freebie", row=0, style=discord.ButtonStyle.primary, emoji="⬅️"
    )
    async def previous_page(
        self, button: discord.Button, interaction: discord.Interaction
    ):
        await interaction.response.defer()

        if self.current_page == 0:
            self.current_page = len(self.pages) - 1
        else:
            self.current_page -= 1

        await self.show_page(interaction)

    @discord.ui.button(
        label="Next Freebie", row=0, style=discord.ButtonStyle.primary, emoji="➡️"
    )
    async def next_page(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        if self.current_page == len(self.pages) - 1:
            self.current_page = 0
        else:
            self.current_page += 1

        await self.show_page(interaction)

    @discord.ui.button(
        label="Go to End", row=0, style=discord.ButtonStyle.primary, emoji="🏃‍♂️"
    )
    async def last_page(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        self.current_page = len(self.pages) - 1

        await self.show_page(interaction)


class ShopifyScraper:
    def __init__(self, proxies: List[str] = None):
        self.setup_clients(proxies)

        self.domain_regex = (
            r"^(?=.{1,253}\.?$)(?:(?!-|[^.]+_)[A-Za-z0-9-_]{1,63}(?<!-)(?:\.|$)){2,}$"
        )

        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        }

    def setup_clients(self, proxies: List[str]):
        pool_limits = httpx.Limits(max_connections=500)
        timeout = httpx.Timeout(6.0, connect=4.0)
        self.clients = [
            httpx.AsyncClient(proxies=proxy, limits=pool_limits, timeout=timeout)
            for proxy in proxies
        ]

    async def make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json_data: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
        retries: int = 10,
    ) -> httpx.Response:
        try:
            someClient = random.choice(self.clients)
            response = await someClient.request(
                method=method,
                url=url,
                headers=headers,
                cookies=cookies,
                json=json_data,
                follow_redirects=True,
            )

            if response is None or response.status_code == 403:
                return await self.make_request(
                    method, url, headers, json_data, cookies, retries - 2
                )

            return response
        except (
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
            httpcore.ConnectError,
            httpx.ConnectError,
            httpx.RemoteProtocolError,
            httpx.ProxyError,
            ssl.SSLError,
            httpx.PoolTimeout,
        ) as e:
            if retries > 0:
                logging.warning(f"Retrying: {url} ({retries} attempts left)")
                return await self.make_request(
                    method, url, headers, json_data, cookies, retries - 1
                )

    @staticmethod
    async def build_checkout_link(
        product: Dict[str, Any], quantity: int, domain: str
    ) -> str:
        product_id = product.get("id")

        checkout_link = f"https://{domain}/cart/{product_id}:{quantity}?discount=FREESHIPPING,FREESHIP,SHIPFREE,FREE,SHIP,firstorder"

        return checkout_link + "&edis=true"

    @staticmethod
    async def build_all_to_cart_link(ids: list, domain: str) -> str:
        link = f"https://{domain}/cart/add?"

        for product in ids:
            link += f"id[]={product}&quantity=1&"

        return link + "edis=true"

    async def discover_product_image(self, product: Dict[str, Any]) -> str:
        image = None

        if product.get("images"):
            image = product.get("images")[0].get("src")

        if image is None:
            image = "https://i.imgflip.com/8zm3bh.jpg"

        return image

    async def search_products(
        self,
        products: List[Dict[str, any]],
        results: Dict[str, dict] = {},
    ):
        results = {}

        for product in products:
            #suspected_freebie = "FREE" in product["title"].upper()
            suspected_freebie = False
            for variant in product.get("variants", []):
                if suspected_freebie or variant["price"] == "0.00" or float(variant["price"]) < 0.99:
                    key = f'{product["title"]} - {variant["title"]}'

                    if variant.get("featured_image") is None or variant.get("featured_image").get("src") is None:
                        img_url = await self.discover_product_image(
                            product
                        )
                    else:
                        img_url = variant.get("featured_image").get("src")

                    results[key] = {
                        "id": variant["id"],
                        "requires_shipping": variant["requires_shipping"],
                        "available": variant["available"],
                        "compare_at_price": variant["compare_at_price"],
                        "price": variant["price"],
                        "2nd_title": product["title"],
                        "image_url": img_url,
                        "suspected_freebie": suspected_freebie,
                    }

        return results

    async def get_products(self, domain: str) -> List[Dict[str, Any]]:
        products_base = f"https://{domain}/products.json"

        temp = self.headers.copy()
        temp["Referer"] = f"https://{domain}"

        all_products = []
        finished = False

        for multiplier in range(0, 10):
            tasks = []
            for e in range(50 * multiplier, 50 * (multiplier + 1)):

                url = f"{products_base}?page={e + 1}&limit=250"
                tasks.append(self.make_request("GET", url, temp))

            responses = await asyncio.gather(*tasks)

            for response in responses:
                if response.status_code == 200:
                    products = json.loads(response.text)

                    if not products.get("products"):
                        finished = True
                        break

                    all_products.extend(products.get("products"))
                else:
                    finished = True
                    break
            else:
                continue
            finished = True
            break

        if not finished:
            for multiplier in range(10, 50):
                tasks = []
                for e in range(1000 * multiplier, 1000 * (multiplier + 1)):

                    url = f"{products_base}?page={e}&limit=250"
                    tasks.append(self.make_request("GET", url, temp))

                responses = await asyncio.gather(*tasks)

                for response in responses:
                    if response.status_code == 200:
                        products = json.loads(response.text)

                        if not products.get("products"):
                            finished = True
                            break

                        all_products.extend(products.get("products"))
                    else:
                        finished = True
                        break
                else:
                    continue
                finished = True
                break

        return {"products": all_products}

    async def validate_domain(self, domain: str) -> str | bool:
        if not domain:
            return False

        if "." not in domain:
            return False

        if domain.startswith("http://") or domain.startswith("https://"):
            domain = domain.split("://")[1]

        if domain.startswith("www."):
            domain = domain.split("www.")[1]

        if domain.endswith("/"):
            domain = domain[:-1]

        if not re.match(self.domain_regex, domain):
            return False

        return domain


if __name__ == "__main__":

    try:
        config = json.load(open("config.json"))

        proxies = config.get("proxies")

        bot_token = config.get("bot_token")

    except Exception as e:
        print(f"Your config.json file is corrupted: {e}")
        input()
        exit()

    scraper = ShopifyScraper(proxies)

    bot = discord.Bot(activity=discord.Game(name="with shopify freebies!"))
    shopifyCommands = bot.create_group("shopify", "Shopify freebie commands")

    @shopifyCommands.command(
        description="Scrape a shopify store for freebies", guild_only=True
    )
    async def check(ctx: discord.context):
        modal = DiscordDomainModal()

        await ctx.send_modal(modal)

    try:
        bot.run(bot_token)
    except KeyboardInterrupt:
        print("Shutting down...")
        bot.close()
    except Exception as e:
        print(e)
        input()
