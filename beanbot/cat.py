import re
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from beanbot.utils import handle_state_error
from beanbot.storage import MongoDBWrapper
from .utils import DataType

class TransactionCat:
    def __init__(self, storage:MongoDBWrapper):
        self.storage = storage

    @handle_state_error
    async def cat(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Cat last n transactions from the transaction file, or archived transactions or accounts"""
        args = ' '.join(context.args)

        try:
            match = re.match(r'^(?P<n>\d+)?\s?(?P<type>transactions|archived|accounts)?$', args)
            groups = match.groupdict()
        except:
            await update.message.reply_text("Invalid arguments. Use `/cat [n] [transactions|archived|accounts]`\n\nwhere n is last n items and type is optional and defaults to transactions")
            return


        cat_type = 'transactions' if groups.get('type', None) is None else groups['type']
        n = 100 if groups.get('n', None) is None else int(groups['n'])
        if cat_type == 'accounts':
            data = self.storage.get_accounts()
            data = "\n\n".join(data.split('\n\n')[-n:])
        elif cat_type == 'archived':
            data = self.storage.read(DataType.ARCHIVED)[-n:]
            data = '\n\n'.join(data)
        else:
            data = self.storage.read(DataType.TRANSACTIONS)[-n:]
            data = '\n\n'.join(data)

        await update.message.reply_text("```beancount\n{}\n```".format(data), parse_mode='markdownV2')
    
    def get_handler(self):
        return CommandHandler('cat', self.cat)