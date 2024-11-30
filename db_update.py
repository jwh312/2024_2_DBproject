import random
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

# MongoDB 연결
client = MongoClient("mongodb://localhost:3041/")
db = client["sports_game"]


# marketplace 데이터
marketplace_data = [
    {
        "_id": ObjectId("674a0b568a9cf41ed508ee77"),
        "player_id": "674a143ed3e5c8aae5b88192",
        "price": 90000,
        "listed_by": "674a143dd3e5c8aae5b8817d",
        "listed_at": datetime.strptime("2024-11-29T10:12:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
    },
    {
        "_id": ObjectId("674a0b568a9cf41ed508ee78"),
        "player_id": "674a143ed3e5c8aae5b88193",
        "price": 110000,
        "listed_by": "674a143dd3e5c8aae5b88181",
        "listed_at": datetime.strptime("2024-11-30T09:20:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
    },
    {
        "_id": ObjectId("674a0b568a9cf41ed508ee79"),
        "player_id": "674a143ed3e5c8aae5b88194",
        "price": 60000,
        "listed_by": "674a143dd3e5c8aae5b88185",
        "listed_at": datetime.strptime("2024-11-29T15:40:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
    },
    {
        "_id": ObjectId("674a0b568a9cf41ed508ee80"),
        "player_id": "674a143ed3e5c8aae5b88195",
        "price": 95000,
        "listed_by": "674a143dd3e5c8aae5b8817d",
        "listed_at": datetime.strptime("2024-11-30T08:50:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
    },
    {
        "_id": ObjectId("674a0b568a9cf41ed508ee81"),
        "player_id": "674a144ac4a8e39e97f708f3",
        "price": 130000,
        "listed_by": "674a143dd3e5c8aae5b88181",
        "listed_at": datetime.strptime("2024-11-29T17:30:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
    }
]

# 데이터 삽입
db.marketplace.insert_many(marketplace_data)

print("Marketplace data inserted successfully.")