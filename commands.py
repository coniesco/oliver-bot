import logging
import re
import os
import sys
import time as python_time
from datetime import time
from functools import wraps
from sqlite3 import IntegrityError
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from data_utils import Database


logger = logging.getLogger(__name__)

hour = re.compile(r"^(?P<hour>\d{1,2}):(?P<minute>\d{2})$")

data = Database()


# Command handlers
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text='*Uso* '
                          '\n /set nombre hh:mm - Agenda una alarma en *formato 24 horas*'
                          '\n /show - Muestra alarmas agendadas'
                          '\n /delete - Elimina una alarma',
                     parse_mode=ParseMode.MARKDOWN)


def alarm(bot, job):
    """Function to send the alarm message, shows an inline button"""
    keyboard = [[InlineKeyboardButton("Hecho", callback_data=job.name + ";comida")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(job.context['id'],
                     text='Hora de {}'.format(job.name),
                     reply_markup=reply_markup)


def alarm_button(bot, update, groupdict):
    """Callback method from alarm button, displays completed job"""
    user = update.effective_user['first_name']
    if update.effective_user['username']:
        username = ' (@{})'.format(update.effective_user['username'])
    else:
        username = ''
    done = update.callback_query.edit_message_text(text="Hora de {} ✔".format(groupdict['nombre']),
                                                   parse_mode=ParseMode.MARKDOWN)
    bot.send_message(update.effective_chat['id'],
                     text="{}{} se hizo cargo".format(user, username),
                     reply_to_message_id=done.message_id)


def set_time(bot, update, args, job_queue, chat_data):
    """Adds a job to the queue"""
    chat_id = update.message.chat_id

    try:

        due = hour.match(args[1])
        if not due:
            raise ValueError

        # Add job to queue
        alert_time = to_time(due.group(0))

        data.save(context=chat_id, hour=due.group(0), name=args[0])
        context = {'id': chat_id}

        job = job_queue.run_daily(alarm, alert_time, context=context, name=args[0])
        logger.info("Added job for {} at {} named {}".format(chat_id, due.group(0), args[0]))
        chat_data[due.group(0)] = job

        bot.send_message(chat_id=chat_id,
                         text='Alarma *{}* agendada a las *{}*'.format(args[0], due.group(0)),
                         parse_mode=ParseMode.MARKDOWN)

    except (IndexError, ValueError):
        bot.send_message(chat_id=chat_id,
                         text='*Uso* \n /set nombre hh:mm',
                         parse_mode=ParseMode.MARKDOWN)

    except IntegrityError:
        update.message.reply_text('Ya tienes una alarma agendada a esta hora')


def show(bot, update, chat_data):
    """Shows a list of all scheduled jobs"""
    job_list = "\n".join(["{} - {}".format(job.name, due) for due, job in chat_data.items()])

    bot.send_message(chat_id=update.message.chat_id,
                     text='*Alarmas agendadas* \n' + job_list,
                     parse_mode=ParseMode.MARKDOWN)


def unset(bot, update, chat_data):
    """Removes the job if the user changed their mind, user chooses from a list"""

    keyboard = [[InlineKeyboardButton("{} - {}".format(job.name, due), callback_data=due+";delete")]
                for due, job in chat_data.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Elige la alarma que quieres eliminar', reply_markup=reply_markup)


def delete_button(bot, update, groupdict, chat_data):
    """Callback function from unset alarm button. Deletes the job"""

    query = update.callback_query
    j_time = groupdict['hour']

    job = chat_data.get(j_time, None)
    job.schedule_removal()

    data.delete(query.message.chat_id, j_time)
    del chat_data[j_time]

    logger.info('Deleted job for {} at {} named {}'.format(query.message.chat_id, j_time, job.name))

    query.edit_message_text(text="Alarma *{}* a las *{}* eliminada".format(job.name, j_time),
                            parse_mode=ParseMode.MARKDOWN)


# Helper methods and handlers
def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def to_time(string):
    """Quickly get time from string"""
    due = [int(x) for x in string.split(':')]
    return time(hour=due[0], minute=due[1])


def load(job_queue, dispatcher):
    """Loads all the jobs in the database"""
    for item in data.load_jobs():
        user_id = int(item[0])
        job_time = item[1]
        name = item[2]

        context = {"id": user_id}

        chat_data = dispatcher.chat_data[user_id]
        job = job_queue.run_daily(alarm, to_time(job_time), context=context, name=name)
        logger.info("Added job for {} at {} named {}".format(user_id, job_time, name))

        chat_data[job_time] = job


def restricted(func):
    """Restricts use of a command to ADMIN users"""
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if user_id not in os.environ['ADMINS']:
            logger.warning("Unauthorized access denied for {}.".format(user_id))
            return
        return func(bot, update, *args, **kwargs)
    return wrapped


@restricted
def restart(bot, update):
    """Restarts bot"""
    bot.send_message(update.message.chat_id, "Reiniciando...")
    python_time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)
