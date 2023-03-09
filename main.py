import os

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from curl_handler import CurlHandler
from database_handler import DatabaseHandler


def reply(update: Update, text: str):
    return update.message.reply_text(text)


class VehicleFleetBot:
    def __init__(self):
        self.__database_handler = DatabaseHandler()
        self.__curl_handler = CurlHandler()

        application = Application.builder().token(os.getenv('TELEGRAM_API_KEY')).build()

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        application.add_handler(CommandHandler("login", self.login))
        application.add_handler(CommandHandler("logout", self.logout))
        application.add_handler(CommandHandler("distance_report", self.distance_report))

        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.help))

        application.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_html(
            rf"Hi {user.mention_html()}!",
            reply_markup=ForceReply(selective=True),
        )
        await self.help(update, context)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text(
            'Login: /login <username> <password>\n'
            'Logout: /logout\n'
            'Distance travelled : /distance_report <time unit: "days" or "months"> <vehicle id> <start date> <end date>'
        )

    async def login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_message.chat_id
        if self.__database_handler.is_logged_in(chat_id):
            await reply(update, "You are already logged in!")
            return
        try:
            username = context.args[0]
            password = context.args[1]
        except (IndexError, ValueError):
            await reply(update, "Usage: /login <username> <password>")
            return
        if self.__curl_handler.login(username, password):
            self.__database_handler.persist_session(chat_id, username, password)
            await reply(update, "Successfully logged in!")
            return
        await reply(update, "Invalid credentials!")

    async def logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_message.chat_id
        if self.__database_handler.is_logged_in(chat_id):
            self.__database_handler.remove_session(update.effective_message.chat_id)
            await reply(update, "Logged out!")
            return
        await reply(update, "You are not logged in!")

    async def distance_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_message.chat_id
        if not self.__database_handler.is_logged_in(chat_id):
            await reply(update, "You are not logged in!")
        try:
            time_unit = context.args[0]
            if time_unit not in ['days', 'months']:
                raise ValueError
            vehicle_id = int(context.args[1])
            start_date = context.args[2]
            end_date = context.args[3]
        except (IndexError, ValueError):
            await reply(
                update,
                'Usage: /distance_report <time unit: "days" or "months"> <vehicle id> <start date> <end date>'
            )
            return
        credentials = self.__database_handler.get_credentials(chat_id)
        results = self.__curl_handler.get_distance_report(
            credentials[1], credentials[2], vehicle_id, time_unit, start_date, end_date)
        result_str = ""
        for result in results:
            result_str += result[0] + ': ' + result[1] + '\n'
        await reply(
                update,
                'Distance travelled report by {} from {} to {}\n'.format(time_unit, start_date, end_date) +
                'Format: "<time period>: <distance, km>"\n' +
                result_str
            )


if __name__ == "__main__":
    bot = VehicleFleetBot()
