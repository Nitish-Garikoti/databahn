import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
import html2text
from mcp.server.fastmcp import FastMCP

# --- Prerequisite Installation ---
# Make sure you have the required libraries installed:
# pip install aiohttp beautifulsoup4 html2text

logger = logging.getLogger(__name__)

# --- Server Definition ---
mcp = FastMCP(name="INTERNET_SEARCH_CRAWLER_SERVER")

async def internet_search(session: aiohttp.ClientSession, query: str) -> list:
    """
    Performs an asynchronous internet search using DuckDuckGo's HTML endpoint 
    and returns the result URLs.
    """
    if not query:
        return []
    
    # Using DuckDuckGo's HTML version which is more scraper-friendly
    search_url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        async with session.post(search_url, data=params, headers=headers) as response:
            response.raise_for_status()
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            links = []
            # DuckDuckGo's HTML results are in divs with class 'result'
            for result in soup.find_all('div', class_='result'):
                link_tag = result.find('a', class_='result__a')
                if link_tag and link_tag.has_attr('href'):
                    links.append(link_tag['href'])
            return links
    except aiohttp.ClientError as e:
        logger.error(f"An error occurred during internet search: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during search: {e}")
        return []

async def crawl_page(session: aiohttp.ClientSession, url: str) -> str:
    """
    Asynchronously crawls a single web page and converts its main content to Markdown.
    """
    print(f"Crawling: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            response.raise_for_status()
            html = await response.text()

            soup = BeautifulSoup(html, 'html.parser')
            content = soup.find('article') or soup.find('main') or soup.body
            
            if content:
                h = html2text.HTML2Text()
                h.ignore_links = False
                markdown = h.handle(str(content))
                return f"--- Content from {url} ---\n\n{markdown}"
            return f"--- No main content found at {url} ---"
        
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.error(f"Failed to crawl {url}. Error: {e}")
        return f"Error: Could not retrieve content from {url}."
    except Exception as e:
        logger.error(f"An unexpected error occurred during crawling of {url}: {e}")
        return f"Error: An unexpected error occurred while processing {url}."


@mcp.tool()
async def perform_internet_search_and_crawl(query: str, top_k_links: int = 3) -> str:
    """
    Asynchronously searches the internet, crawls the first two results concurrently, 
    and returns their content as Markdown.
    query: 
      input_query with for which user wants information about
      top_k_links - number of top most searched links we want to use - by deault its 3.
    joined_crawled_results:
        appended text content from the crawled web links
    """
    print(f"Received async search and crawl query: {query}")
    try:
        async with aiohttp.ClientSession() as session:
            search_results = await internet_search(session, query)
            
            if not search_results:
                return "No search results found."
            
            # Limit to the first 2 links
            links_to_crawl = search_results[:2]
            # Create a list of crawl tasks to run concurrently
            tasks = [crawl_page(session, link) for link in links_to_crawl]
            
            # Run tasks concurrently and gather results
            crawled_results = await asyncio.gather(*tasks)
            joined_crawled_results = "\n\n".join(crawled_results)
            return joined_crawled_results

    except Exception as e:
        logger.error(f"Failed to execute search and crawl: {e}")
        return "An error occurred during the search and crawl process."

async def method_main_test():
    """A test function to directly call the search and crawl tool."""
    print("--- Running a direct test of the search tool ---")
    results = await perform_internet_search_and_crawl("what are the incidents reported in April 2025 w.r.t cloud misconfigurations?")
    print("--- Test Results ---")
    print(results)


if __name__ == '__main__':
    print("Starting server...")
    # Initialize and run the server
    mcp.run(transport="stdio")
    # asyncio.run(method_main_test())

