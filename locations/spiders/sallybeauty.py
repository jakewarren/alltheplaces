# -*- coding: utf-8 -*-
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from scrapy.selector import Selector
from urllib.parse import urlencode


class SallyBeautySpider(scrapy.Spider):
    name = "sallybeauty"
    item_attributes = {"brand": "Sally Beauty"}
    allowed_domains = ["sallybeauty.com"]

    def start_requests(self):
        base_url = "https://www.sallybeauty.com/on/demandware.store/Sites-SA-Site/default/Stores-FindStores?"

        point_files = [
            "./locations/searchable_points/us_centroids_100mile_radius.csv",
            "./locations/searchable_points/ca_centroids_100mile_radius.csv",
        ]

        params = {
            "showmap": "true",
            "radius": "100",
        }

        for point_file in point_files:
            with open(point_file) as points:
                next(points)
                for point in points:
                    _, lat, lon = point.strip().split(",")
                    params.update({"lat": lat, "long": lon})
                    yield scrapy.Request(url=base_url + urlencode(params))

    def parse_hours(self, hours):
        hrs = Selector(text=hours)
        days = hrs.xpath('//div[@class="store-hours-day"]/text()').extract()
        hours = hrs.xpath('//div[@class="store-hours-day"]/span/text()').extract()

        opening_hours = OpeningHours()

        for d, h in zip(days, hours):
            try:
                day = d.strip(": ")
                open_time, close_time = h.split(" - ")
                open_time = open_time.lstrip("0")
                opening_hours.add_range(
                    day=day[:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M %p",
                )
            except:
                continue

        return opening_hours.as_opening_hours()

    def parse(self, response):
        jdata = response.json()

        for row in jdata.get("stores", []):

            properties = {
                "ref": row["ID"],
                "name": row["name"],
                "addr_full": " ".join(
                    [row["address1"], row.get("address2", "") or ""]
                ).strip(),
                "city": row["city"],
                "postcode": row["postalCode"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "phone": row["phone"],
                "state": row["stateCode"],
            }

            store_hours = row.get("storeHours")
            if store_hours:
                hours = self.parse_hours(store_hours)

                if hours:
                    properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
