#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import MySQLdb

from config import *
from peewee import *

database = MySQLDatabase(host=host, user=user, 
        passwd=password, database=db_name,
        port=port, charset=charset)

def create_tables():
    database.create_tables([SQLIRecords], True)

class SQLIRecords(Model):
    url = CharField()
    request_text = TextField()
    class Meta:
        database = database

