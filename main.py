from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from commands import *
import logging
import os


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    updater = Updater(os.environ['TOKEN'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    load(updater.job_queue, dp)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("set", set_time,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("show", show,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("delete", unset,
                                  pass_chat_data=True))
    dp.add_handler(CallbackQueryHandler(delete_button,
                                        pattern=r'(?P<hour>.{5});delete$',
                                        pass_groupdict=True,
                                        pass_chat_data=True))
    dp.add_handler(CallbackQueryHandler(alarm_button,
                                        pattern=r'(?P<nombre>.*);comida$',
                                        pass_groupdict=True))
    dp.add_handler(CommandHandler("restart", restart))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
