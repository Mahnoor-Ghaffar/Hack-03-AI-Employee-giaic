import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def post_linkedin(post_content):
    linkedin_email = os.environ.get("LINKEDIN_EMAIL")
    linkedin_password = os.environ.get("LINKEDIN_PASSWORD")

    if not linkedin_email or not linkedin_password:
        print("Error: LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables must be set.")
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto("https://www.linkedin.com/login")

            await page.fill("#username", linkedin_email)
            await page.fill("#password", linkedin_password)
            await page.click(".btn__primary--large")

            # Wait for navigation after login
            await page.wait_for_url("https://www.linkedin.com/feed/")

            await page.click(".share-box__trigger")

            # Fill the post content
            await page.fill("div[aria-label='Text editor for creating content']", post_content)

            # Click the post button
            await page.click(".share-actions__primary-action")

            print("LinkedIn post created successfully!")

        except Exception as e:
            print(f"Error creating LinkedIn post: {e}")
            sys.exit(1)
        finally:
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python post_linkedin.py \"<post_content>\"")
        sys.exit(1)

    post_content = sys.argv[1]
    asyncio.run(post_linkedin(post_content))
