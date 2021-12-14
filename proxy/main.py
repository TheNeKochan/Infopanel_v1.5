from flask import Flask, Response
from requests import get
from SQLiteProxy import SQLiteProxy

app = Flask("proxy")
proxy = SQLiteProxy()
proxy.start()


@app.route("/")
def main():
    return Response(response=get("https://lyceum.nstu.ru/", verify=False).content)


@app.route("/novosti/itemlist/category/1-news")
def news1():
    return Response(response=get("https://lyceum.nstu.ru/novosti/itemlist/category/1-news", verify=False).content)


@app.route("/novosti/item/<news>")
def news_page(news):
    page = proxy.GetPage(news)
    if page is None:
        page = get(f"https://lyceum.nstu.ru/novosti/item/{news}", verify=False).content
        proxy.PutPage(news, page)
    return Response(response=page)


@app.route("/media/k2/items/cache/<pic>")
def pict(pic):
    page = proxy.GetPage(pic)
    if page is None:
        page = get(f"https://lyceum.nstu.ru/media/k2/items/cache/{pic}", verify=False).content
        proxy.PutPage(pic, page)
    return Response(response=page, mimetype="image/jpeg")


app.run(port=8080)
