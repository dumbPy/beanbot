import logging
import traceback
from telegram.ext import ConversationHandler
from enum import Enum

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def format_transaction(transaction:dict[str,str]|str)->str:
    if isinstance(transaction, str):
        return '```beancount\n{}\n```'.format(transaction)
    return '```beancount\n{}\n```'.format(transaction['content'])

class DataType(Enum):
    TRANSACTIONS = 'transactions'
    ARCHIVED = 'archived'
    ACCOUNTS = 'accounts'

DataTypePattern = r'(?P<dataType>transactions|archived|accounts)'


def handle_error(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                update = args[0]  # Assuming the first argument is the `update` object
                await update.message.reply_text(f"An error occurred: {str(e)}")
                logger.error(traceback.format_exc())
        return wrapper
    

def handle_state_error(func):
    """Main reason for error in edit is the loss of context.user_data."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            update = args[1]  # Assuming the first argument is the `update` object since 0th would be self for a class method
            try:
                # if the error occurs in a callback, edit the message
                await update.callback_query.edit_message_text(f"An error occurred: {str(e)}")
            except:
                # if the error occurs during first message, reply to the message
                await update.message.reply_text(f"An error occurred: {str(e)}")
            finally:
                logger.error(traceback.format_exc())
            return ConversationHandler.END
    return wrapper