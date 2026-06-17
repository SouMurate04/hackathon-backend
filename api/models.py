from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from api.db import Base

# ユーザー
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(255), nullable=False, unique=True)
    name = Column(String(255))
    email = Column(String(255), nullable=False, unique=True)
    icon_url = Column(String(255))
    bio = Column(String(255))

# 商品
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)
    c0_id = Column(Integer, ForeignKey("categories.id"))
    c1_id = Column(Integer, ForeignKey("categories.id"))
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"))
    posted_at = Column(DateTime, nullable=False)
    bought_at = Column(DateTime)

# いいね(ジャンクション)
class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("item_id", "user_id", name="uq_likes_item_user"),)

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

# 画像(ジャンクション)
class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    url = Column(String(255), nullable=False)

# カテゴリーid(ジャンクション)
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"))
    level = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)

# タグ(ジャンクション)
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

# チャット(ジャンクション/発言ごとに管理)
class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)

# 通知
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)

# フォロー関係
class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("followee_id", "follower_id", name="uq_follows_followee_follower"),
    )

    id = Column(Integer, primary_key=True, index=True)
    followee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)