import json
import asyncio
from typing import List, Dict, Union
from httpx import AsyncClient, Response, HTTPStatusError, TimeoutException
from parsel import Selector
from loguru import logger as log
from database import connection, insert_postgres
import argparse
import re
import sys

client = AsyncClient(
    http2=True,
    timeout=5,
    headers={
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cookie": "intl_splash=false"
    },
    follow_redirects=True
)

def parse_subreddit(response: Response) -> List[Dict]:
    """parse reddit post from the  main page of subreddit using xpath"""
    selector = Selector(response.text)
    url = str(response.url)
    info = {}
    info["id"] = url.split("/r")[-1].replace("/", "")
    info["description"] = selector.xpath("//shreddit-subreddit-header/@description").get()
    members = selector.xpath("//shreddit-subreddit-header/@subscribers").get()
    rank = selector.xpath("//strong[@id='position']/*/@number").get()    
    info["members"] = int(members) if members else None
    info["rank"] = int(rank) if rank else None
    info["bookmarks"] = {}
    for item in selector.xpath("//div[faceplate-tracker[@source='community_menu']]/faceplate-tracker"):
        name = item.xpath(".//a/span/span/span/text()").get()
        link = item.xpath(".//a/@href").get()
        info["bookmarks"][name] = link

    info["url"] = url
    post_data = []
    for box in selector.xpath("//article"):
        text = None
        link = box.xpath(".//a/@href").get()
        author = box.xpath(".//shreddit-post/@author").get()
        post_label = box.xpath(".//faceplate-tracker[@source='post']/a/span/div/text()").get()
        upvotes = box.xpath(".//shreddit-post/@score").get()
        comment_count = box.xpath(".//shreddit-post/@comment-count").get()
        attachment_type = box.xpath(".//shreddit-post/@post-type").get()
        if attachment_type and attachment_type == "image":
            attachment_link = box.xpath(".//shreddit-media-lightbox-listener/*/*/@src").get()
        elif attachment_type == "video":
            log.warning("found video not implemented yet!")
            attachment_link = box.xpath(".//shreddit-player/@preview").get()
        else:
            attachment_link = box.xpath(".//div[@slot='thumbnail']/a/@href").get()
            ##sometimes the post is just a title
            uneclean_text = box.xpath(f'.//div[@id="{box.xpath(".//shreddit-post/@id").get()}-post-rtjson-content"]').get()
            if uneclean_text: 
                text = re.sub(r'<[^>]+>','', uneclean_text)
        post_data.append({
            "authorProfile": "https://www.reddit.com/user/" + author if author else None,
            "authorId": box.xpath(".//shreddit-post/@author-id").get() if author != '[deleted]' else 'delete',            
            "title": box.xpath("./@aria-label").get(),
            "link": "https://www.reddit.com" + link if link else None,
            "publishingDate": box.xpath(".//shreddit-post/@created-timestamp").get(),
            "postId": box.xpath(".//shreddit-post/@id").get(),
            "postLabel": post_label.strip() if post_label else None,
            "postUpvotes": int(upvotes) if upvotes else None,
            "commentCount": int(comment_count) if comment_count else None,
            "attachmentType": attachment_type,
            "attachmentLink": attachment_link,
            "text": text,
        })
    cursor_id = selector.xpath("//shreddit-post/@more-posts-cursor").get()
    return {"post_data": post_data, "info": info, "cursor": cursor_id}


async def parse_user(data:List[Dict]) -> List[Dict]:
    """parse user karma and cake day from the user profile impossible to get it 
        from the main page (use selenium) in the future """
    for user in data["post_data"]:
        try :
            response = await client.get(user["authorProfile"])
        except TimeoutException:
            log.error(f"Request to {user["authorProfile"]} timed out.")
        except HTTPStatusError as exc:
            log.error(f"HTTP error: {exc.response.status_code} for {user["authorProfile"]}")
        if response.status_code == 200:
            selector = Selector(response.text)
            karma_value = selector.xpath(".//span[@data-testid='karma-number']/text()").getall()
            if len(karma_value) > 0 :
                user_karma = karma_value[0].strip()
                comment_user_karma = karma_value[1].strip()
                cake_day = selector.xpath(".//time[@data-testid='cake-day']/text()").get().strip()
                user.update({'user_karma': int(user_karma.replace(',', '')),'comment_user_karma' : int(comment_user_karma.replace(',', '')), 'cake_day': cake_day})
            else:
                log.warning(f"User {user['authorId']} not found for {user["authorProfile"]}")
                user.update({'user_karma': -1,'comment_user_karma' : -1, 'cake_day': None}) ## reddit return 200 even if the user is deleted
        else:
            log.warning(f"User {user['authorId']} not found for {user["authorProfile"]}")
            user.update({'user_karma': -1,'comment_user_karma' : -1, 'cake_day': None})
    return data


async def scrape_subreddit(subreddit_id: str, sort: Union["new", "hot", "old"], max_pages: int = None):
    """get ther main page of the subreddit and change page using the cursor id"""
    base_url = f"https://www.reddit.com/r/{subreddit_id}/"
    try:
        response = await client.get(base_url)
    except TimeoutException:
        log.error(f"Request to {base_url} timed out.")
    except HTTPStatusError as exc:
        log.error(f"HTTP error: {exc.response.status_code} for {base_url}")
    subreddit_data = {}
    data = parse_subreddit(response)
    data = await parse_user(data)
    subreddit_data["info"] = data["info"]
    subreddit_data["posts"] = data["post_data"]
    cursor = data["cursor"]
    old_cursor = cursor

    def make_pagination_url(cursor_id: str):
        return f"https://www.reddit.com/svc/shreddit/community-more-posts/hot/?after={cursor_id}%3D%3D&t=year&name=AskMec&feedLength=3&sort={sort}" 
    while (max_pages is None or max_pages > 0):
        if cursor == None:
            cursor = old_cursor
        url = make_pagination_url(cursor)
        log.debug(f"Moving to page {max_pages}")
        try:
            response = await client.get(url)
        except TimeoutException:
            log.error(f"Request to {url} timed out.")
        except HTTPStatusError as exc:
            log.error(f"HTTP error: {exc.response.status_code} for {url}")
        if response:
            data = parse_subreddit(response)
            data = await parse_user(data)
            cursor = data["cursor"]
            old_cursor = cursor
            post_data = data["post_data"]
            subreddit_data["posts"].extend(post_data)
            if max_pages is not None:
                max_pages -= 1
        else:
            log.error(f"Error fetching data from {url}")
            break
        log.success(f"scraped {len(subreddit_data['posts'])} posts from the rubreddit: r/{subreddit_id}")
    return subreddit_data

async def run(args : argparse.Namespace):
    """main function to run the script"""
    subreddit_id = "AskMec"
    log.debug("connecting to database ....")
    try:
        conn = connection()
    except Exception as e:
        log.error(f"an error occured during connection to the database {e}")
        sys.exit(1)

    log.debug(f"begining crawling subreddit: {subreddit_id}")
    data = await scrape_subreddit(
        subreddit_id=subreddit_id,
        sort="new",
        max_pages=100
    )
    if args.debug:
        with open(args.debug, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    insert_postgres(conn, data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Example script to handle arguments.")
    parser.add_argument('--debug', type=str, help="Path to the debug file", required=False)
    args = parser.parse_args()

    asyncio.run(run(args))
