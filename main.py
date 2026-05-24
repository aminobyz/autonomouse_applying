import asyncio
import random
import requests
from datetime import datetime
from pathlib import Path
import traceback

from bson.binary import Binary
from bs4 import BeautifulSoup
from mongodb import MongoDB
from patchright.async_api import async_playwright
from playwright_captcha import CaptchaType, ClickSolver, FrameworkType

class Scraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

        # Initialize MongoDB connection
        self.db = MongoDB(database_name="mydatabase", collection_name="indeed")
        self.client, self.collection = self.db.connect()

    async def start(self):
        # Start Playwright and launch browser with anti-detection settings
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir="./indeed_profile",
            channel="chrome",
            headless=False,
            no_viewport=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                
            ]
        )
        self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()

    async def stop(self):
        if self.page:
            await self.page.close()
            self.page = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    def write_to_html(self, html_content, filename):
        """
        Save HTML content as a prettified file with timestamp.

        Args:
            html_content (str): Raw HTML content from the page
            filename (str): Base filename to save as
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        pretty_html = soup.prettify()

        # Define html filename that gets saved in the current directory
        filename = f"{filename}.html"

        # Save the prettified HTML to a local file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(pretty_html)

        return filename

    async def convert_html_to_pdf(self, html_file_name):
        """
        Convert a saved local HTML page to PDF using Playwright Async API.

        Args:
            html_file_name (str): Local HTML filename

        Returns:
            bytes: PDF bytes
        """
        # Create a new page for PDF generation
        page = await self.browser.new_page()
        html_uri = Path(html_file_name).absolute().as_uri()
        # Use 'domcontentloaded' to ensure the page is fully loaded before PDF generation
        await page.goto(html_uri, wait_until='domcontentloaded')

        # Handle cookie consent if it appears
        cookie_accept = page.locator("button:has-text('Alle ablehnen')")
        if await cookie_accept.count() > 0:
            await cookie_accept.click()
            print("✓ Cookie handled")

        # Generate PDF bytes
        pdf_bytes = await page.pdf()
        await page.close()       

        print(f"✓ Converted {html_file_name} to PDF")
        return pdf_bytes

    def save_to_mongoDB_directly(self, pdf_bytes, url=None, website=None):
        # Save PDF bytes directly to MongoDB with metadata
        document = {
            "website": website,
            "url": url,
            "file_data": Binary(pdf_bytes),
            "created_at": datetime.now()
        }
        # Insert the document into MongoDB
        self.collection.insert_one(document)

    async def scrap_indeed(self, url, website):
        # Scrape the given URL, convert to PDF, and save to MongoDB
        try:
            print(f"🔍 Navigating to: {url}")
            #await self.page.goto(url, wait_until='networkidle')
            # Create ClickSolver BEFORE navigating to the page
            async with ClickSolver(framework=FrameworkType.PATCHRIGHT, page=self.page) as solver:
                await self.page.goto(url, wait_until='networkidle')

                # Solve Cloudflare Turnstile if present
                await solver.solve_captcha(
                    captcha_container=self.page,
                    captcha_type=CaptchaType.CLOUDFLARE_TURNSTILE
            )

            cookie_accept = self.page.locator("button:has-text('Alle ablehnen')")
            if await cookie_accept.count() > 0:
                await cookie_accept.click()
                print("✓ Cookie handled")
            
            html = await self.page.content()

            # Save the HTML content to a local file and get the filename
            saved_html_filename = self.write_to_html(html, "pretty_page")
            print(f"✓ Saved prettified HTML as: {saved_html_filename}")

            # Convert the saved HTML to PDF bytes
            pdf_bytes = await self.convert_html_to_pdf(saved_html_filename)

            # Save the PDF bytes directly to MongoDB with metadata
            self.save_to_mongoDB_directly(pdf_bytes=pdf_bytes, url=url, website=website)
            print(f"✓ Successfully saved PDF bytes to MongoDB for URL: {url}")

            return pdf_bytes , self.page.url
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")
            traceback.print_exc()
        return None


async def main():
    print("🚀 Starting Indeed scraper...")
    scraper = Scraper()
    await scraper.start()
    last_page_url = None
    i = 1
    try:
        while True:
            if i == 1:
                URL = "https://de.indeed.com/jobs?q=Data+Engineer&l=Deutschland&radius=35&sort=date&vjk"
            else:
                URL = f"https://de.indeed.com/jobs?q=Data+Engineer&l=Deutschland&radius=35&sort=date&start={(i - 1) * 10}&vjk"

            pdf_bytes, actual_url = await scraper.scrap_indeed(url=URL, website="Indeed")
            if not pdf_bytes:
                continue

            # Check if we have reached the last page by comparing the current URL with the last one
            if last_page_url == actual_url:
                break

            # Change the last_page_url to the current one for the next iteration
            last_page_url = actual_url

            # Increment pagination counter 
            i += 1
            print(f"✓ Scraped URL: {actual_url}")

            print(f"PDF size: {len(pdf_bytes)} bytes")
            # 
            Path("pdfs").mkdir(exist_ok=True, parents=True)
            #path = Path.mkdir("pdfs", exist_ok=True, parents=True)

            with open(f'pdfs/manual_save{i}.pdf', 'wb') as f:
                f.write(pdf_bytes)

            BASE_URL = "http://localhost:8000"
            payload = {
                "url": URL,
                "website": "Indeed",
                "role": "Data Scientist",
                "date": datetime.now().isoformat(),
                "file_size": len(pdf_bytes),
                "pdf_file": pdf_bytes.decode('latin-1')
            }

            response = await asyncio.to_thread(
                lambda: requests.post(f"{BASE_URL}/test", json=payload)
            )

            if response.status_code == 200:
                print("✓ Successfully sent data to API server")
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
            print("-"*50)

            await asyncio.sleep(random.uniform(3, 5))  # Random delay to mimic human behavior

    except Exception as e:
        print(f"❌ An error occurred during scraping or API communication: {str(e)}")
        traceback.print_exc()
    finally:
        await scraper.stop()
        print("🔒 Browser closed")
        print("🚀 Scraper finished.")


if __name__ == "__main__":
    asyncio.run(main())