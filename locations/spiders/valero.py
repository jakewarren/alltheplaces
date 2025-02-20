# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem

usa_bbox = [-125, 24, -65, 51]
xstep = 5
ystep = 3


class ValeroSpider(scrapy.Spider):
    name = "valero"
    item_attributes = {"brand": "Valero", "brand_wikidata": "Q1283291"}
    allowed_domains = ["valero.com"]

    def make_search(self, xmin, ymin, xmax, ymax):
        return scrapy.FormRequest(
            "https://locations.valero.com/en-us/Home/SearchForLocations",
            formdata={
                "NEBound_Lat": str(ymax),
                "NEBound_Long": str(xmax),
                "SWBound_Lat": str(ymin),
                "SWBound_Long": str(xmin),
            },
            meta={
                "dont_redirect": True,
            },
        )

    def start_requests(self):
        xs = list(range(usa_bbox[0], usa_bbox[2] + xstep, xstep))
        ys = list(range(usa_bbox[1], usa_bbox[3] + ystep, ystep))
        for (xmin, xmax) in zip(xs, xs[1:]):
            for (ymin, ymax) in zip(ys, ys[1:]):
                yield self.make_search(xmin, ymin, xmax, ymax)

    def parse(self, response):
        for row in response.json():
            amenities = [detail["Description"] for detail in row["LocationDetails"]]
            website = f"https://locations.valero.com/en-us/LocationDetails/Index/{row['DetailPageUrlID']}/{row['LocationID']}"
            item = {
                "ref": row["LocationID"],
                "lat": row["Latitude"],
                "lon": row["Longitude"],
                "name": row["Name"],
                "phone": row["Phone"],
                "website": website,
                "street_address": row["AddressLine1"],
                "city": row["City"],
                "state": row["State"],
                "country": row["Country"],
                "postcode": row["PostalCode"],
                "opening_hours": "24/7" if "24 Hour" in amenities else None,
                "extras": {
                    "atm": "ATM" in amenities or None,
                    "amenity:fuel": True,
                    "amenity:toilets": "Public Restroom" in amenities or None,
                    "car_wash": "Car Wash" in amenities or None,
                    "fuel:diesel": "Diesel" in amenities or None,
                    "fuel:e85": "E-85" in amenities or None,
                },
            }
            yield GeojsonPointItem(**item)
