from pymongo import MongoClient
from pathlib import Path
import os
import logging
from enum import Enum
from .utils import DataType, get_date_in_locale

logger = logging.getLogger('beanbot.storage')


class MongoDBWrapper:
    def __init__(self):
        logger.debug(f"Connecting to MongoDB at {os.environ['MONGO_URI']}")
        self.client = MongoClient(os.environ['MONGO_URI'])
        logger.debug(f"Using mongo database {os.environ['MONGO_DATABASE']}")
        self.db = self.client[os.environ['MONGO_DATABASE']]
        try:
            self.db.create_collection('transactions')
            logger.debug("Created collection transactions")
        except:
            logger.info("Collection transactions already exists. Skipping...")
            pass
        self.collection = self.db['transactions']
        self.accounts_collection = self.db['accounts']
    
    def deserialize(self, data:list[dict[str, str]])->str:
        return ([t["content"] for t in data])
    
    def serialize(self, data:str | list[str])->list[dict[str, str]]:
        if isinstance(data, str):
            data = data.split('\n\n')
        return [{'content': t, 'archived':False} for t in data if t.strip()]

    def append(self, transaction:str):
        self.collection.insert_many(self.serialize(transaction))

    def archive_all(self):
        self.collection.update_many({'archived':False}, {'$set': {'archived': True}})

    def read(self, type:DataType)->list[str]:
        collection = self.accounts_collection if type == DataType.ACCOUNTS else self.collection
        match type:
            case DataType.TRANSACTIONS:
                filter = {'archived': False}
            case DataType.ARCHIVED:
                filter = {'archived': True}
            case DataType.ACCOUNTS:
                filter = {}
        data = self.deserialize(collection.find(filter))
        if not data:
            return [';; No transactions to show']
        return data

    def as_file(self, type:DataType)->Path:
        data = "\n\n".join(self.read(type))
        match type:
            case DataType.TRANSACTIONS:
                path = Path(f'/tmp/{get_date_in_locale()}.transactions.txt')
            case DataType.ARCHIVED:
                path = Path(f'/tmp/{get_date_in_locale}.archived.txt')
            case DataType.ACCOUNTS:
                path = Path(f'/tmp/{get_date_in_locale}.accounts.txt')
        path.write_text(data)
        return path
    
    def length(self):
        return len(self.collection.count_documents({}))

    def get_accounts(self)->str:
        return self.accounts_collection.find().next()['content']