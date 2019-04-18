#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests


class HttpRequest(object):
    def __init__(self):
        self.request_session = requests.Session()

    def get(self, url, **kwargs):
        with self.request_session as session:
            return session.get(url, **kwargs).json()


class GaoDeMap(object):
    def __init__(self, key, city):
        self.key = key  # 开发者key
        self.city = city  # 城市名
        self.http_request = HttpRequest()

    def get_location(self, address):
        """查询经纬度

        文档地址: https://lbs.amap.com/api/webservice/guide/api/georegeo

        :param address: 具体地点
        :type address: str
        :example address: 杭州东站

        :rtype str
        :return 地点的经纬度
        :example
        """
        url = "https://restapi.amap.com/v3/geocode/geo"
        params = {
            "key": self.key,
            "city": self.city,
            "address": address
        }
        result = self.http_request.get(url, params=params)
        return result["geocodes"][0]["location"]

    def get_bus_transit(self, origin, destination, extensions="base", strategy=0, nightflag=0, departure_time=None):
        """查询公交路线

        文档地址: https://lbs.amap.com/api/webservice/guide/api/direction

        :param origin: 出发点

        :param destination: 目的地

        :param extensions: 返回结果详略, 可选值：base(default)/all, base:返回基本信息；all：返回全部信息

        :param strategy: 公交换乘策略, 可选值：0：最快捷模式, 1：最经济模式, 2：最少换乘模式, 3：最少步行模式, 5：不乘地铁模式

        :param nightflag: 是否计算夜班车, 可选值：0：不计算夜班车, 1：计算夜班车

        :param departure_time: 出发时间, 根据出发时间和日期（未来时间点）筛选可乘坐的公交路线，格式：time=22:34。
                    在无需设置预计出发时间时，请不要在请求之中携带此参数。
        """
        url = "https://restapi.amap.com/v3/direction/transit/integrated"

        params = {
            "key": self.key,
            "city": self.city,
            "origin": origin,
            "destination": destination,
            "extensions": extensions,
            "strategy": strategy,
            "nightflag": nightflag,
        }
        if departure_time:
            params["time"] = departure_time

        result = self.http_request.get(url, params=params)
        return result


def parse_gao_de_map(result):
    """解析高德地图结果
    """
    route = result["route"]
    total_distance = route["distance"]  # 起点和终点的步行距离，单位: 米
    total_taxi_cost = route["taxi_cost"]  # 出租车费用，单位: 元

    transits = []
    # 遍历可能的坐车方案
    for item in route["transits"]:
        duration = item["duration"]  # 此换乘方案预期时间
        nightflag = item["nightflag"]  # 是否是夜班车
        walking_distance = item["walking_distance"]  # 此方案总步行距离, 单位： 米

        entrance = ""  # 地铁入口 E
        exit_ = ""  # 地铁出口 A

        segments = []

        # 换乘路段列表
        for res in item["segments"]:
            walk_distance = res["walking"]["distance"] if res["walking"] else 0  # 每段线路步行距离
            walk_duration = res["walking"]["duration"] if res["walking"] else 0  # 步行预计时间
            bus_lines = []

            # 多种换乘方案
            for bus in res["bus"]["buslines"]:
                departure_stop = bus["departure_stop"]["name"]  # 上车站
                arrival_stop = bus["arrival_stop"]["name"]  # 下车站
                bus_name = bus["name"]  # 公交线名
                via_num = bus["via_num"]  # 站数
                bus_duration = bus["duration"]  # 公交预计行驶时间
                bus_distance = bus["distance"]  # 公交行驶距离
                start_time = bus["start_time"]  # 首班车时间
                end_time = bus["end_time"]  # 末班车时间
                bus_type = bus["type"] if bus["type"] else ""  # 公交类型

                bus_lines.append({
                    "departure_stop": departure_stop,
                    "arrival_stop": arrival_stop,
                    "bus_name": bus_name,
                    "via_num": via_num,
                    "bus_duration": bus_duration,
                    "bus_distance": bus_distance,
                    "start_time": start_time,
                    "end_time": end_time,
                    "bus_type": bus_type
                })

            entrance = res["entrance"]["name"] if res["entrance"] else entrance  # 地铁入口 E
            exit_ = res["exit"]["name"] if res["exit"] else exit_  # 地铁出口 A
            segments.append({
                "walk_distance": walk_distance,
                "walk_duration": walk_duration,
                "bus_lines": bus_lines,
            })

        transits.append({
            "duration": duration,
            "nightflag": nightflag,
            "walking_distance": walking_distance,
            "entrance": entrance,
            "exit": exit_,
            "segments": segments
        })

    return {
        "total_distance": total_distance,
        "total_taxi_cost": total_taxi_cost,
        "transits": transits
    }
