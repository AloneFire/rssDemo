import requests
from gevent.pool import Pool
import gevent
import time
import datetime
from jinja2 import Template
from tasks import rss_generate_register
from PyRSS2Gen import RSSItem


def get_xugubao_news_content_image(news_id):
    api_url = f"https://baoer-api-prod.xuangubao.cn/api/v6/message/content_image/{news_id}"
    params = {
        "content_type": 1,
        "width": 680,
        "dpi": 72,
        "font_size": 16,
        "font_color": 0,
        "bg_alpha": 0
    }
    resp = requests.get(api_url, params=params)
    if resp.status_code == 200:
        return resp.json().get("data", {}).get("img_str")
    return None


def get_xugubao_news(subj_ids=[9, 10, 723, 35, 469, 821], has_explain=False, cursor=None):
    api_url = "https://baoer-api.xuangubao.cn/api/v6/message/newsflash"
    params = {
        "limit": 20,
        "subj_ids": subj_ids,
        "platform": "pcweb",
        "has_explain": has_explain
    }
    if cursor:
        params["cursor"] = cursor

    resp = requests.get(api_url, params=params)
    if resp.status_code == 200:
        data = resp.json().get("data")
        messages, next_cursor = data.get("messages"), data.get("next_cursor")
        pool = Pool(20)

        def add_content_image(msg):
            if msg.get("is_subscribed"):
                msg["content_image"] = get_xugubao_news_content_image(
                    msg.get("id"))
        jobs = [pool.spawn(add_content_image, message)
                for message in messages if message.get("is_subscribed")]
        gevent.joinall(jobs)

        return messages, next_cursor
    return None, None


def generate_content(msg):
    templte = """
    <div>
        {{msg.get("summary")}}
        {% if msg.get("content_image") %}
        <img src="data:image/png;base64,{{msg.get("content_image")}}" />
        {% endif %}
    </div>

    {% for explain_info in msg.get("explain_infos") %}
    <div>
        <a href="https://xuangubao.cn/article/{{explain_info.get("explain_msg_id")}}">{{explain_info.get("explain_msg_title")}}</a>
        <p>{{explain_info.get("explain_msg_summary")}}</p>
    </div>
    {% endfor %}
    """
    return Template(templte).render(msg=msg)


@rss_generate_register("选股宝财经快讯", "https://xuangubao.cn/live")
def generate_rss():
    messages, _ = get_xugubao_news()

    items = [RSSItem(title=msg.get("title") if msg.get("title") else f'<img src="data:image/png;base64,{msg.get("content_image")}" />',
                     link=f'https://xuangubao.cn/article/{msg.get("id")}',
                     description=generate_content(msg),
                     pubDate=time.strftime(
                     "%Y-%m-%d %H:%M:%S", time.localtime(msg.get("created_at")))
                     ) for msg in messages]

    return items
