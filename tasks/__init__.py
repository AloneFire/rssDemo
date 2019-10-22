from gevent import monkey
import gevent
from gevent.pool import Pool
from PyRSS2Gen import RSS2
import datetime
import importlib
import os
import re
import functools

monkey.patch_all()
monkey.patch_socket()
rss_generators = []


def rss_generate_register(title, link, description="", categories=None, image=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper():
            file_name = func.__module__[6:]
            items = func()
            rss = RSS2(title=title, link=link,
                       description="", items=items, lastBuildDate=datetime.datetime.now(), ttl=60, categories=categories, image=image)
            rss.write_xml(open(f"rss/{file_name}.xml", "w",
                               encoding="utf8"), encoding="utf8")
            return rss
        rss_generators.append(wrapper)
        return wrapper
    return decorator


def generate_all_rss():
    import_files = [f"tasks.{fn[:-3]}" for fn in os.listdir(
        "tasks") if re.match(r"^[^_].*\.py", fn)]
    print(import_files)
    for mod in import_files:
        importlib.import_module(mod)
    pool = Pool(20)
    jobs = [pool.spawn(f) for f in rss_generators]
    gevent.joinall(jobs)
