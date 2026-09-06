from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove() 

cancel_button = "Отмена 🚫"
def cansel(message):
    bot.send_message(message.chat.id, "Чтобы посмотреть команды, используй - /info", reply_markup=hideBoard)
  
def no_projects(message):
    bot.send_message(message.chat.id, 'У тебя пока нет проектов!\nМожешь добавить их с помошью команды /new_project')

def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=row))
    return markup

def gen_markup(rows):
    markup = ReplyKeyboardMarkup(
        one_time_keyboard=True,
        resize_keyboard=True,
        input_field_placeholder="Выбери вариант ниже",
    )
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

attributes_of_projects = {'Имя проекта' : ["Введите новое имя проекта", "project_name"],
                          "Описание" : ["Введите новое описание проекта", "description"],
                          "Ссылка" : ["Введите новую ссылку на проект", "url"],
                          "Статус" : ["Выберите новый статус задачи", "status_id"]}

def info_project(message, user_id, project_name):
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name)
    if not skills:
        skills = 'Пока не добавлены'
    bot.send_message(message.chat.id, f"""📦 <b>{info[0]}</b>

📝 <b>Описание:</b> {info[1] or 'Не указано'}
🔗 <b>Ссылка:</b> {info[2] or 'Не указана'}
🚦 <b>Статус:</b> {info[3]}
🧰 <b>Навыки:</b> {skills}""", parse_mode="HTML")

# Показывает приветствие и список доступных возможностей.
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, """Привет! Я бот-менеджер проектов
Помогу тебе сохранить твои проекты и информацию о них!) 
""")
    info(message)
    
# Показывает подробную справку по всем командам бота.
@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id,
"""🧭 <b>Команды бота</b>

🆕 <b>/new_project</b> — добавить проект: название, ссылку и статус.
📚 <b>/projects</b> — показать все проекты в виде списка.
🛠 <b>/skills</b> — добавить технологии выбранному проекту.
✏️ <b>/update_projects</b> — изменить название, описание, ссылку или статус.
🗑 <b>/delete</b> — удалить проект.
ℹ️ <b>/info</b> — открыть эту справку.

💬 Можно просто отправить название проекта, чтобы посмотреть его карточку.
Кнопка «Отмена 🚫» завершает любой пошаговый сценарий.""", parse_mode="HTML")
    

# Запускает пошаговое добавление нового проекта.
@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    bot.send_message(message.chat.id, "Введите название проекта:")
    bot.register_next_step_handler(message, name_project)

def name_project(message):
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "📝 Введи описание проекта:")
    bot.register_next_step_handler(message, description_project, data=data)


def description_project(message, data):
    """Получает описание проекта и переводит пользователя к вводу ссылки."""
    if message.text == cancel_button:
        cansel(message)
        return
    data.append(message.text)
    bot.send_message(message.chat.id, "🔗 Введи ссылку на проект:")
    bot.register_next_step_handler(message, link_project, data=data)

def link_project(message, data):
    data.append(message.text)
    statuses = [x[0] for x in manager.get_statuses()] 
    bot.send_message(message.chat.id, "🚦 Выбери текущий статус проекта:", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

def callback_project(message, data, statuses):
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if status not in statuses:
        bot.send_message(message.chat.id, "Ты выбрал статус не из списка, попробуй еще раз!)", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.extend([None, status_id])
    manager.insert_project([tuple(data)])
    bot.send_message(message.chat.id, "✅ Проект сохранён!", reply_markup=hideBoard)


# Запускает добавление навыка к выбранному проекту.
@bot.message_handler(commands=['skills'])
def skill_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, '🛠 Выбери проект, которому добавим навык:', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)


def skill_project(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
        
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!) Выбери проект для которого нужно выбрать навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]
        bot.send_message(message.chat.id, '🧰 Выбери навык:', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

def set_skill(message, project_name, skills):
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
        
    if skill not in skills:
        bot.send_message(message.chat.id, 'Видимо, ты выбрал навык. не из спика, попробуй еще раз!) Выбери навык', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill )
    bot.send_message(message.chat.id, f'✅ Навык {skill} добавлен проекту {project_name}!', reply_markup=hideBoard)


# Показывает список проектов и добавляет к нему inline-кнопки.
@bot.message_handler(commands=['projects'])
def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"📦 <b>{x[2]}</b>\n🔗 {x[4]}\n" for x in projects])
        bot.send_message(message.chat.id, "📚 <b>Твои проекты:</b>\n\n" + text, parse_mode="HTML", reply_markup=gen_inline_markup([x[2] for x in projects]))
    else:
        no_projects(message)

# Показывает подробности проекта после нажатия inline-кнопки.
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    project_name = call.data
    bot.answer_callback_query(call.id)
    info_project(call.message, call.from_user.id, project_name)


# Запускает пошаговое удаление проекта.
@bot.message_handler(commands=['delete'])
def delete_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"📦 <b>{x[2]}</b>\n🔗 {x[4]}\n" for x in projects])
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "🗑 <b>Выбери проект для удаления:</b>\n\n" + text, parse_mode="HTML", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
    else:
        no_projects(message)

def delete_project(message, projects):
    project = message.text
    user_id = message.from_user.id

    if message.text == cancel_button:
        cansel(message)
        return
    if project not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй выбрать еще раз!', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f'✅ Проект {project} удалён!', reply_markup=hideBoard)


# Запускает пошаговое редактирование проекта.
@bot.message_handler(commands=['update_projects'])
def update_project(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "✏️ Выбери проект, который хочешь изменить:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects )
    else:
        no_projects(message)

def update_project_step_2(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, "Что-то пошло не так!) Выбери проект, который хочешь изменить еще раз:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects )
        return
    bot.send_message(message.chat.id, "🧩 Что требуется изменить?", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

def update_project_step_3(message, project_name):
    attribute = message.text
    reply_markup = None 
    if message.text == cancel_button:
        cansel(message)
        return
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "Кажется, ты ошибся, попробуй еще раз!)", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    elif attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup=gen_markup([x[0] for x in rows])
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup = reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])

def update_project_step_4(message, project_name, attribute): 
    update_info = message.text
    if attribute== "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        elif update_info == cancel_button:
            cansel(message)
            return
        else:
            bot.send_message(message.chat.id, "Был выбран неверный статус, попробуй еще раз!)", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)
    bot.send_message(message.chat.id, "Готово! Обновления внесены!)")


# Ищет проект по его названию или направляет пользователя в справку.
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    projects =[ x[2] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
        return
    bot.reply_to(message, "Тебе нужна помощь?")
    info(message)

    
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.infinity_polling()
