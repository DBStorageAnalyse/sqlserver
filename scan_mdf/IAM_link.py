# -*- coding: utf-8 -*-
# sql server 拼接碎片, 通过IAM页 和 逻辑对象
import sqlite3
import init
import time
import struct


def iam_unload(data):
    a = 0
