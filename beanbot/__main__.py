import os
import logging
import traceback
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from textwrap import dedent
# from .ai import generate_transaction
from .storage import MongoDBWrapper
from .edit import TransactionEditor
from .generate import TransactionGenerator
from .utils import handle_error
import dotenv

dotenv.load_dotenv()

storage = MongoDBWrapper()


@handle_error
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text(dedent(
        """
        ***********  HELP  ***********
        Use /help to show this message

        Use /download to download
            the transactions.beancount

        Use /cat [n] to cat transactions,
            optionally last n

        Use /archive to clear
            transactions.beancount
        
        Use /edit [archived] to enter interactive
            edit mode

        Send normal message to generate
            transactions.

        """))

@handle_error
async def download_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the transactions.beancount txt file."""
    args = context.args
    use_archived = True if args and args[0] == 'backup' else False
    file = storage.as_file(use_archived)
    await update.message.reply_document(open(file.as_posix(), 'rb'))


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

async def cat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cat last n transactions from the transaction file."""
    args = context.args


    transactions = storage.read()
    
    if args:
        try:
            n = int(args[0])
        except:
            update.message.reply_text("Invalid argument. Use `/cat [n]` where n is an integer.")
        transactions = transactions[-n:]

    await update.message.reply_text("```beancount\n{}\n```".format('\n\n'.join(transactions)), parse_mode='markdownV2')


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.environ['TELEGRAM_BOT_TOKEN']).build()

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("download", download_transactions))
    application.add_handler(CommandHandler("cat", cat))

    application.add_handler(CommandHandler("archive", confirm_clear_transactions))
    application.add_handler(CallbackQueryHandler(handle_clear_confirmation, pattern='acceptClear|rejectClear'))
    transactionEditor = TransactionEditor(storage)
    transactionGenerator = TransactionGenerator(storage)
    application.add_handler(transactionEditor.get_handler())
    application.add_handler(transactionGenerator.get_handler())
        
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()