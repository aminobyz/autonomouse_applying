from playwright.sync_api import sync_playwright
from pathlib import Path

# Specify your HTML file path
html_file = "pretty_page.html"  # Change to your file name
output_pdf = "output.pdf"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
    # Convert local HTML file to PDF
    file_path = Path(html_file).absolute()
    page.goto(f"file://{file_path}")
    
    # Save as PDF
    page.pdf(path=output_pdf)
    
    browser.close()
    print(f"✓ Converted {html_file} to {output_pdf}")

    '''# Navigate to the page
        page.goto(URL)
        
        # Wait for job listings to load
        page.wait_for_selector("css=#mosaic-provider-jobcards", timeout=10000)

        # Handle cookie consent
        page.click("button:has-text('Alle ablehnen')")

        # Get page content
        html = page.content()

        # Parse and prettify HTML
        soup = BeautifulSoup(html, 'html.parser')
        pretty_html = soup.prettify()
        
        # Save to file
        with open("pretty_page.html", "w", encoding="utf-8") as f:
            f.write(pretty_html)'''