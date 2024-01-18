from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ConversationHandler
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler
from .utils import format_transaction
from .storage import MongoDBWrapper

EDIT, DELETE = range(2)

class TransactionEditor:
    def __init__(self, storage:MongoDBWrapper):
        self.storage = storage

    async def edit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        arg = context.args
        if arg:
            if arg[0] != 'archived':
                await update.message.reply_text("Invalid argument. Use `/edit [archived]` where archived is optional to edit archived transactions.")
                return None
            context.user_data['transactions'] = list(self.storage.collection.find({'archived': True}))
        else:
            context.user_data['transactions'] = list(self.storage.collection.find({'archived': False}))
        context.user_data['index'] = len(context.user_data['transactions']) - 1
        
        if not context.user_data['transactions']:
            await update.message.reply_text("No transactions found.")
            return ConversationHandler.END


        transaction = context.user_data['transactions'][context.user_data['index']]
        await update.message.reply_text(format_transaction(transaction), reply_markup=self.get_edit_buttons(), parse_mode='MarkdownV2')
        return EDIT

    def get_edit_buttons(self):
        # Send the transaction to the user with the InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("<", callback_data='prev'), InlineKeyboardButton(">", callback_data='next')],
            [InlineKeyboardButton("Delete", callback_data='delete'), InlineKeyboardButton("End", callback_data='end')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        return reply_markup
    
    def get_delete_confirmation_buttons(self):
        keyboard = [
            [InlineKeyboardButton("Agree", callback_data='agree'), InlineKeyboardButton("Cancel", callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        return reply_markup

    async def handle_edit_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        cursor = context.user_data['index']
        current_transaction = context.user_data['transactions'][cursor]
        next_state = EDIT
        message = format_transaction(current_transaction)
        if query.data == 'prev':
            # Fetch the previous transaction and update the message
            if cursor == 0:
                message = format_transaction(current_transaction)+"\nNo previous transaction"
            else:
                context.user_data['index'] -= 1
                cursor = context.user_data['index']
                transaction = context.user_data['transactions'][cursor]
                message = format_transaction(transaction)
        elif query.data == 'next':
            # Fetch the next transaction and update the message
            if cursor == len(context.user_data['transactions']) - 1:
                message = format_transaction(current_transaction)+"\nNo next transaction"
            else:
                context.user_data['index'] += 1
                cursor = context.user_data['index']
                transaction = context.user_data['transactions'][cursor]
                message = format_transaction(transaction)
        elif query.data == 'delete':
            # Ask the user for confirmation
            next_state = DELETE
            message = format_transaction(current_transaction)+"\nConfirm Delete?"
        elif query.data == 'end':
            # End the conversation
            await query.edit_message_text("Edit mode ended.")
            return ConversationHandler.END
        else:
            raise ValueError(f"Invalid callback data: {query.data}")

        if next_state == EDIT:
            await query.edit_message_text(message, reply_markup=self.get_edit_buttons(), parse_mode='MarkdownV2')
            return EDIT
        elif next_state == DELETE:
            await query.edit_message_text(message, reply_markup=self.get_delete_confirmation_buttons(), parse_mode='MarkdownV2')
            return DELETE

    async def handle_delete_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        # Delete the transaction and update the message
        query = update.callback_query
        choice = query.data
        await query.answer()
        cursor = context.user_data['index']
        transaction = context.user_data['transactions'][cursor]
        if choice == 'agree':
            self.storage.collection.delete_one({'_id': transaction['_id']})
            context.user_data['transactions'].pop(cursor)
            if cursor == len(context.user_data['transactions']):
                context.user_data['index'] -= 1
            transaction = context.user_data['transactions'][cursor]
            next_message = "Deleted...\nNext Transaction:\n"+format_transaction(transaction)
        else:
            next_message = format_transaction(transaction)
        await query.edit_message_text(next_message, reply_markup=self.get_edit_buttons(), parse_mode='MarkdownV2')
        return EDIT
    
    def get_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler('edit', self.edit_command)],
            states={
                EDIT: [CallbackQueryHandler(self.handle_edit_buttons)],
                DELETE: [CallbackQueryHandler(self.handle_delete_confirmation, pattern='^agree|cancel$')]
            },
            # fallbacks=[CommandHandler('cancel', self.cancel)]
            fallbacks=[]
        )