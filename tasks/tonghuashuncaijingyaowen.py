from jinja2 import Template
from tasks import rss_generate_register
from PyRSS2Gen import RSSItem
import time
from requests_html import HTMLSession
from gevent.pool import Pool
import gevent


def get_article(link):
    session = HTMLSession()
    resp = session.get(link)
    plist = resp.html.find(".atc-content>p")
    if plist:
        return "".join(p.html for p in plist if p.attrs.get("class") is None)
    else:
        return ""


def get_messages():
    session = HTMLSession()
    resp = session.get("http://news.10jqka.com.cn/today_list/")
    if resp.status_code == 200:
        rel = []

        def el_convert(el):
            item = {
                "title": el.find(".arc-title>a", first=True).text,
                "link": el.find(".arc-title>a", first=True).attrs.get("href")
            }
            item["content"] = get_article(item["link"]) if item.get(
                "link") and el.find(".arc-cont", first=True).text != "..." else ""
            rel.append(item)

        pool = Pool(20)

        jobs = [pool.spawn(el_convert, el)
                for el in resp.html.find(".list-con>ul>li")]
        gevent.joinall(jobs)
        return rel, None

    return [], Exception("request error")


def generate_item(msg):
    content_template = """
    {{msg.get("content")}}
    <div><a href="{{msg.get("link")}}">阅读原文</a></div>
    """

    content = Template(content_template).render(msg=msg)

    return RSSItem(title=msg.get("title"),
                   link=msg.get("link"),
                   description=content,
                   pubDate=msg.get("pubdate"),
                   enclosure=msg.get("enclosure")
                   )


@rss_generate_register("同花顺财经要闻", "http://news.10jqka.com.cn/today_list/")
def generate_rss():
    messages, error = get_messages()

    if not error:
        items = [generate_item(msg) for msg in messages]
        return items
    return []
