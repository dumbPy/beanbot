from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ConversationHandler
from pathlib import Path
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from .utils import handle_state_error
from .storage import MongoDBWrapper

CONFIRM = 0


class AccountsUploader:
    def __init__(self, storage: MongoDBWrapper):
        self.storage = storage

    @handle_state_error
    async def handle_uploaded_file(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Handle uploaded file by reading the text content and saving it to storage."""
        file = await context.bot.get_file(update.message.document.file_id)
        path = await file.download_to_drive()
        file.file_path
        with path.open() as f:
            text = f.read()
        last_20_lines = "\n".join(text.splitlines()[-20:])
        context.user_data["file"] = path
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Yes", callback_data="acceptFile"),
                    InlineKeyboardButton("Cancel", callback_data="rejectFile"),
                ]
            ]
        )
        await update.message.reply_text(
            f"```{path.name} last few lines:\n{last_20_lines}``` Are you sure you want to use this file as accounts context for predicting transactions?",
            reply_markup=reply_markup,
            parse_mode="MarkdownV2",
        )
        return CONFIRM

    @handle_state_error
    async def handle_file_upload_confirmation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        # Delete the transaction and update the message
        query = update.callback_query
        choice = query.data
        await query.answer("Processing...")
        path: Path = context.user_data["file"]
        if choice == "acceptFile":
            self.storage.accounts_collection.delete_many({})
            self.storage.accounts_collection.insert_one({"content": path.read_text()})
            await query.edit_message_text("accounts.beancount updated")
        else:
            path.unlink()
            await query.edit_message_text("accounts.beancount updation skipped")

    def get_handler(self):
        return ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters.Document.TEXT
                    & (
                        filters.Document.FileExtension("txt")
                        | filters.Document.FileExtension("beancount")
                        | filters.Document.FileExtension("bean")
                        | filters.Document.FileExtension("beans")
                    ),
                    self.handle_uploaded_file,
                )
            ],
            states={
                CONFIRM: [CallbackQueryHandler(self.handle_file_upload_confirmation)],
            },
            fallbacks=[],
        )
