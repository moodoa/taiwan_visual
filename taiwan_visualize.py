import json
import time
import requests
import pandas as pd
import plotly.express as px
from random import randint, choice
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.request import urlopen


class VISUALTAIWAN:
    def get_geojson(self):
        with urlopen(
            "https://raw.githubusercontent.com/g0v/twgeojson/master/json/twCounty2010.geo.json"
        ) as response:
            counties = json.load(response)
        return counties

    def label_city_id(self, counties):
        city = {}
        idx = 1
        for country in counties["features"]:
            if country["properties"]["name"] == "桃園縣":
                city["桃園市"] = idx
            else:
                city[country["properties"]["name"]] = idx
            idx += 1
        for country in counties["features"]:
            if country["properties"]["name"] == "桃園縣":
                country["id"] = city["桃園市"]
            else:
                country["id"] = city[country["properties"]["name"]]
        return city, counties

    def collect_news(self, keywords, start_time, end_time):
        contents = []
        for keyword in keywords:
            idx = 1
            keepgoing = True
            while keepgoing:
                keepgoing = False
                text = requests.get(
                    f"https://search.ltn.com.tw/list?keyword={keyword}&start_time={start_time}&end_time={end_time}&sort=date&type=all&page={idx}"
                ).text
                soup = BeautifulSoup(text, "lxml")
                for content in soup.select("div.cont"):
                    if len(content.text) > 10 and keyword in content.text:
                        contents.append(content.text)
                        keepgoing = True
                idx += 1
        return contents

    def make_scope_info(self, contents, city):
        cities = list(city.keys())
        scope_info = {}
        for c in cities:
            scope_info[c] = 0
        for content in tqdm(contents):
            if "北市" in content:
                if "新北市" in content:
                    scope_info["新北市"] += 1
                    if "台北市" in content:
                        scope_info["台北市"] += 1
                else:
                    scope_info["台北市"] += 1
            if "桃市" in content or "桃園市" in content:
                scope_info["桃園市"] += 1
            for c in cities:
                if c in content and c not in ["新北市", "台北市", "桃園市"]:
                    scope_info[c] += 1
        return scope_info

    def make_df(self, city, scope_info, keyword):
        data = pd.DataFrame(data=city.items(), columns=["name", "val"])
        data[keyword] = data["name"].apply(lambda x: scope_info[x])
        return data

    def draw(self, data, counties, keyword):
        fig = px.choropleth(
            data,
            geojson=counties,
            locations="val",
            color=keyword,
            scope="asia",
#             若要多張圖對比得固定單一數值
            range_color=(0, 22),
#         若單張圖顏色範圍可設定0~前90%
#             range_color = (0, int(data[keyword].quantile(0.9)))
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.show()
        fig.write_image(f"./{keyword}.png")
        print(data)
        return "FINISH!!"


if __name__ == "__main__":
    visual = VISUALTAIWAN()
    counties = visual.get_geojson()
    city, counties = visual.label_city_id(counties)
    keywords = input("輸入關鍵字並以/分隔：")
    keywords = keywords.split("/")
    start_time = input("開始時間 e.g. 20220101：")
    end_time = input("結束時間 e.g. 20221222：")
    print("蒐集中...")
    contents = visual.collect_news(keywords, start_time, end_time)
    scope_info = visual.make_scope_info(contents, city)
    data = visual.make_df(city, scope_info, keywords[0])
    draw = visual.draw(data, counties, keywords[0])
