from pymongo import MongoClient
from pathlib import Path
import os

class MongoDBWrapper:
    def __init__(self):
        self.client = MongoClient(os.environ['MONGO_URI'])
        self.db = self.client[os.environ['MONGO_DATABASE']]
        try:
            self.db.create_collection('transactions')
        except:
            pass
        self.collection = self.db['transactions']
    
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

    def read(self, include_archived=False)->list[str]:
        filter = {} if include_archived else {'archived': False}
        data = self.deserialize(self.collection.find(filter))
        if not data:
            return [';; transactions.beancount is empty']
        return data

    def as_file(self, include_archived=False)->Path:
        data = "\n\n".join(self.read(include_archived))
        with open('/tmp/transactions.beancount', 'w') as f:
            f.write(data)
        return Path('/tmp/transactions.beancount')
    
    def length(self):
        self.collection.find().next()
        return len(self.collection.count_documents({}))

    def get_accounts(self):
        # TODO: implement this in db
        with open('accounts.beancount', 'r') as f:
            return f.read()