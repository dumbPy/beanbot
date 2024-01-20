import os
import logging
import re
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from textwrap import dedent
from argparse import ArgumentParser
# from .ai import generate_transaction
from .storage import MongoDBWrapper
from .edit import TransactionEditor
from .generate import TransactionGenerator
from .upload_accounts import AccountsUploader
from .utils import handle_error, DataType
from .cat import TransactionCat
import dotenv

logger = logging.getLogger('beanbot')
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO').upper())

logger.debug(f"System environment variables: {os.environ}")
dotenv.load_dotenv()
logger.debug(f"Final environment variables: {os.environ}")

storage = MongoDBWrapper()

@handle_error
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text(dedent(
        """
        ```
        ***********  HELP  ***********
        Use /help to show this message

        Use /download [{transactions|archived|accounts}]
            to download the transactions.beancount or
            archived transactions or accounts

        Use /cat [n] [{transactions|archived|accounts}]
            to cat transactions, optionally last n

        Use /archive to archive all transactions
            transactions.beancount
        
        Use /edit [archived] to enter interactive
            edit mode

        Send normal message to generate
            transactions.
        
        Upload <anyName>.bean[s|count] to save it
            as accounts.beancount for 
            generating transactions.
        ```
        """), parse_mode='markdownV2')

@handle_error
async def download_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the transactions.beancount txt file."""
    args = ' '.join(context.args)
    groups = re.match(r'^(?P<type>transactions|archived|accounts)?$', args).groupdict()
    data_type = DataType(groups.get('type') if groups.get('type', None) is not None else 'transactions')
    file = storage.as_file(data_type)
    await update.message.reply_document(file.open('rb'))


@handle_error
async def confirm_clear_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the transactions.beancount txt file."""
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data='acceptClear'),
            InlineKeyboardButton("Cancel", callback_data='rejectClear'),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = update.message if update.message is not None else update.edited_message
    await message.reply_text("Are you sure you want to clear transactions\.beancount ?", parse_mode='markdownV2', reply_markup=reply_markup)

@handle_error
async def handle_clear_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    
    # Skip if cancel was pressed
    if query.data == 'rejectClear':
        await query.edit_message_text("Clearing of transactions.beancount skipped...")
        return None


    # archive all transactions
    storage.archive_all()
    await query.edit_message_text("Cleared transactions.beancount")


def populate_accounts_if_present():
    path = Path('accounts.beancount')
    if path.exists() and storage.accounts_collection.count_documents({}) == 0:
        logger.info('Found accounts.beancount, populating database')
        storage.accounts_collection.delete_many({})
        storage.accounts_collection.insert_one({'content': path.read_text()})

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.environ['TELEGRAM_BOT_TOKEN']).build()

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("start", help_command))
    application.add_handler(CommandHandler("download", download_transactions))
    application.add_handler(CallbackQueryHandler(handle_clear_confirmation, pattern='acceptClear|rejectClear'))
    application.add_handler(CommandHandler("archive", confirm_clear_transactions))

    application.add_handler(TransactionCat(storage).get_handler())
    application.add_handler(TransactionEditor(storage).get_handler())
    application.add_handler(TransactionGenerator(storage).get_handler())
    application.add_handler(AccountsUploader(storage).get_handler())
    populate_accounts_if_present()
        
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()