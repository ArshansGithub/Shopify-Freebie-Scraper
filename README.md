# Shopify-Freebie-Scraper

**This project is intended for educational purposes only. The authors are not responsible for any misuse of the software. Users are solely responsible for ensuring their use complies with applicable laws and terms of service of the websites involved.**

Powerful Discord bot designed to scrape Shopify stores for freebies, generate quick 'Add to Cart' links, and export lists of free items.
<br><br>
![Discord_8pvsjiasZO](https://github.com/user-attachments/assets/d7a51f7d-29e9-4728-9759-7794b472035f)
![Screenshot 2024-08-08 at 20-44-13 Your Shopping Cart– T](https://github.com/user-attachments/assets/1fa9d520-4df5-41d0-a3c9-6c9dd8a95e9b)
<br>
## Features

- **Fully Asynchronous**: Leverages asynchronous processing for fast, non-blocking operations, ensuring efficient web-scraping and Discord interactions.
- **Domain Validation**: Ensures that only valid Shopify domains are used.
- **Product Scraping**: Efficiently scrapes Shopify stores to find products, with a focus on identifying potential freebies.
- **Checkout Link Generation**: Automatically creates 'Add to Cart' (ATC) links for individual or all free products.
- **Exportable Lists**: Generate and export comprehensive lists of freebies, categorized by shipping requirements, availability, and more.
- **Interactive Discord UI**: Utilizes Discord's UI components like modals and selects for a seamless user experience.
- **Customizable & Expandable**: Supports proxies to handle different scraping scenarios written with clean code for quick tweaks.

## Usage

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ArshansGithub/Shopify-Freebie-Scraper.git
   cd Shopify-Freebie-Scraper
   ```

2. **Install dependencies:**
   ```bash
   pip install httpx py-cord
   ```

3. **Configure the bot:**
   - Create a `config.json` file in the root directory:
     ```json
     {
       "bot_token": "YOUR_DISCORD_BOT_TOKEN",
       "proxies": ["http://proxy1", "http://proxy2"]
     }
     ```

4. **Run the bot:**
   ```bash
   python3 main.py
   ```

### Commands

- **/shopify check**: Initiates the freebie scraping process. Users input the Shopify store domain, and the bot takes care of the rest.

### Example

1. A user types `/shopify check` in a Discord server.
2. The bot prompts the user to enter a Shopify store domain.
3. The bot scrapes the store for freebies and presents options:
   - Pagination of freebies.
   - Export 'Add to Cart' link for a specific product.
   - Export all 'Add to Cart' links.
   - Add all freebies to cart.

## Contributions
Contributions are welcome! To contribute to the project, please fork the repository and use feature branches. Submit pull requests for review and inclusion.

## License

This project is licensed under the GNU V3 License. See the [LICENSE](LICENSE) file for details.

## Contact

For inquiries or support, please open a ticket on the [GitHub issues page](https://github.com/ArshansGithub/Shopify-Freebie-Scraper/issues).
