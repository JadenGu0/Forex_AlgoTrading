# encoding=utf-8

from enum import Enum


class OrderType(Enum):
    """
    Enum used for OrderType
    """
    BUY = 0
    SELL = 1


class OrderStatus(Enum):
    """
    Enum used for OrderStatus
    """
    HOLDING = 0
    CLOSED = 1


class EventType(Enum):
    """
    Enum used for EventType
    """
    MARKET = 0
    ORDER_SEND = 1
    ORDER_CLOSE = 2
    ORDER_MODIFY = 3
