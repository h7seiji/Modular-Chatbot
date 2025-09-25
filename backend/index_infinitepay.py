"""
index_infinitepay.py

Crawl InfinitePay help center articles, generate Gemini embeddings,
and save as a local FAISS index.
"""

import re

from bs4 import BeautifulSoup
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings
import requests

BASE_URL = "https://ajuda.infinitepay.io/pt-BR"
INDEX_DIR = "infinitepay_faiss_index"

def get_collection_links():
    """Scrape collection links from InfinitePay help center."""
    resp = requests.get(BASE_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    links = set()
    for a in soup.select('a'):
        href = a.get('href')
        if href and re.search(r'/collections/\d+', href):
            if href.startswith('/'):
                href = "https://ajuda.infinitepay.io" + href
            links.add(href)
    return list(links)

def get_article_links(collection_link):
    """Scrape article links from a collection page."""
    resp = requests.get(collection_link)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    links = set()
    for a in soup.select('a'):
        href = a.get('href')
        if href and re.search(r'/articles/\d+', href):
            if href.startswith('/'):
                href = "https://ajuda.infinitepay.io" + href
            links.add(href)
    return links

def get_article_content(url):
    """Download one article content."""
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else url
    body = soup.select_one('.article')
    content = body.get_text("\n", strip=True) if body else ''
    return {"url": url, "title": title, "content": content}

def main():
    print("Fetching article links...")
    collection_links = get_collection_links()
    links = set()
    for collection_link in collection_links:
        links.update(get_article_links(collection_link))
    print(f"Found {len(links)} articles.")

    # Embeddings model
    embeddings = VertexAIEmbeddings(model_name="text-embedding-004")

    vectorstore = None
    existing_urls = set()

    # Filter out already indexed URLs
    new_links = [link for link in links if link not in existing_urls]
    print(f"{len(new_links)} new articles to index.")

    if not new_links:
        print("Nothing new to add. Done.")
        return

    print("Downloading new articles...")
    articles = [get_article_content(link) for link in new_links]

    print("Chunking text...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = []
    for art in articles:
        for chunk in text_splitter.split_text(art['content']):
            docs.append(Document(
                page_content=chunk,
                metadata={"source": art['url'], "title": art['title']}
            ))

    print("Generating embeddings with VertexAI...")
    vectorstore = FAISS.from_documents(docs, embeddings)

    print(f"Saving index locally to ./{INDEX_DIR}")
    vectorstore.save_local(INDEX_DIR)

    print("Done! New articles added.")

if __name__ == "__main__":
    main()
