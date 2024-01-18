import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ConversationHandler
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler
from telegram.ext import filters
from .utils import format_transaction, logger, handle_state_error
from .storage import MongoDBWrapper
from .ai import generate_transactions

EDIT = 0

class TransactionGenerator:
    def __init__(self, storage:MongoDBWrapper):
        self.storage = storage

    @handle_state_error
    async def generate_transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        transactions = generate_transactions(update.message.text, self.storage.get_accounts())
        context.user_data['transactions'] = transactions
        context.user_data['index'] = 0
        if not transactions:
            await update.message.reply_text("No transactions generated for the given text")
            return ConversationHandler.END
        transaction = transactions[0]
        await update.message.reply_text(format_transaction(transaction), reply_markup=self.get_edit_buttons(), parse_mode='MarkdownV2')
        return EDIT

    def get_edit_buttons(self):
        # Send the transaction to the user with the InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("<", callback_data='prev'), InlineKeyboardButton(">", callback_data='next')],
            [InlineKeyboardButton("Accept", callback_data='accept'), InlineKeyboardButton("Cancel", callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        return reply_markup
    
    @handle_state_error
    async def handle_edit_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        cursor = context.user_data['index']
        current_transaction = context.user_data['transactions'][cursor]
        next_state = EDIT
        message = format_transaction(current_transaction)
        if query.data == 'prev':
            # Fetch the previous transaction and update the message
            if cursor == 0:
                message = format_transaction(current_transaction)+"\nNo previous candidate"
                if message == query.message.text_markdown_v2:
                    await query.answer('No previous candidate')
                    return EDIT
            else:
                context.user_data['index'] -= 1
                cursor = context.user_data['index']
                transaction = context.user_data['transactions'][cursor]
                message = format_transaction(transaction)
        elif query.data == 'next':
            # Fetch the next transaction and update the message
            if cursor == len(context.user_data['transactions']) - 1:
                message = format_transaction(current_transaction)+"\nNo next candidate"
                if message == query.message.text_markdown_v2:
                    await query.answer('No next candidate')
                    return EDIT
            else:
                context.user_data['index'] += 1
                cursor = context.user_data['index']
                transaction = context.user_data['transactions'][cursor]
                message = format_transaction(transaction)
        elif query.data == 'accept':
            # Ask the user for confirmation
            next_state = ConversationHandler.END
            message = format_transaction(current_transaction)+"\nAdded to transactions"
            self.storage.append(current_transaction)
        elif query.data == 'cancel':
            # End the conversation
            message = "Skipped"
            next_state = ConversationHandler.END
        else:
            raise ValueError(f"Invalid callback data: {query.data}")

        await query.answer()
        if next_state == EDIT:
            await query.edit_message_text(message, reply_markup=self.get_edit_buttons(), parse_mode='MarkdownV2')
        elif next_state == ConversationHandler.END:
            await query.edit_message_text(message, parse_mode='MarkdownV2')
        return next_state

    def get_handler(self):
        return ConversationHandler(
            entry_points=[MessageHandler(filters.User(username=os.environ['TELEGRAM_USERNAME']) & filters.TEXT & ~filters.COMMAND, self.generate_transactions)],
            states={
                EDIT: [CallbackQueryHandler(self.handle_edit_buttons)],
            },
            # fallbacks=[CommandHandler('cancel', self.cancel)]
            fallbacks=[]
        )