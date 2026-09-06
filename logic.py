import sqlite3
from config import DATABASE

skills = [ (_,) for _ in (['Python', 'SQL', 'API', 'Telegram'])]
statuses = [ (_,) for _ in (['Проектирование', 'В процессе разработки', 'Разработан', 'Обновлен', 'Завершен/Не поддерживается'])]

class DB_Manager:
    def __init__(self, database):
        self.database = database
        
    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS projects (
                            project_id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            project_name TEXT NOT NULL,
                            description TEXT,
                            url TEXT,
                            status_id INTEGER,
                            FOREIGN KEY(status_id) REFERENCES status(status_id)
                        )''') 
            conn.execute('''CREATE TABLE IF NOT EXISTS skills (
                            skill_id INTEGER PRIMARY KEY,
                            skill_name TEXT
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS project_skills (
                            project_id INTEGER,
                            skill_id INTEGER,
                            FOREIGN KEY(project_id) REFERENCES projects(project_id),
                            FOREIGN KEY(skill_id) REFERENCES skills(skill_id)
                        )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS status (
                            status_id INTEGER PRIMARY KEY,
                            status_name TEXT
                        )''')
            conn.commit()

    def __executemany(self, sql, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()
    
    def __select_data(self, sql, data = tuple()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()
        
    def default_insert(self):
        for skill_name, in skills:
            self.insert_skill_type(skill_name)
        for status_name, in statuses:
            self.insert_status(status_name)


    def insert_project(self, data):
        sql = '''INSERT INTO projects
        (user_id, project_name, description, url, status_id)
        VALUES (?, ?, ?, ?, ?)'''
        self.__executemany(sql, data)


    def insert_status(self, status_name):
        """Добавляет статус в справочник, если его там ещё нет."""
        self.__executemany(
            'INSERT OR IGNORE INTO status (status_name) VALUES (?)',
            [(status_name,)],
        )


    def update_status(self, status_id, status_name):
        """Изменяет название статуса в справочнике."""
        self.__executemany(
            'UPDATE status SET status_name = ? WHERE status_id = ?',
            [(status_name, status_id)],
        )


    def update_project_status(self, user_id, project_name, status_name):
        """Устанавливает проекту статус из справочника."""
        status_id = self.get_status_id(status_name)
        self.__executemany(
            'UPDATE projects SET status_id = ? WHERE project_name = ? AND user_id = ?',
            [(status_id, project_name, user_id)],
        )


    def insert_skill_type(self, skill_name):
        """Добавляет навык в справочник, если его там ещё нет."""
        self.__executemany(
            'INSERT OR IGNORE INTO skills (skill_name) VALUES (?)',
            [(skill_name,)],
        )


    def update_skill_type(self, skill_id, skill_name):
        """Изменяет название навыка в справочнике."""
        self.__executemany(
            'UPDATE skills SET skill_name = ? WHERE skill_id = ?',
            [(skill_name, skill_id)],
        )

    def insert_skill(self, user_id, project_name, skill):
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        project_id = self.__select_data(sql, (project_name, user_id))[0][0]
        skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))[0][0]
        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES(?, ?)'
        self.__executemany(sql, data)


    def update_project_skill(self, user_id, project_name, old_skill, new_skill):
        """Заменяет один навык проекта на другой."""
        project_id = self.get_project_id(project_name, user_id)
        old_skill_id = self.__select_data(
            'SELECT skill_id FROM skills WHERE skill_name = ?',
            (old_skill,),
        )[0][0]
        new_skill_id = self.__select_data(
            'SELECT skill_id FROM skills WHERE skill_name = ?',
            (new_skill,),
        )[0][0]
        self.delete_skill(project_id, old_skill_id)
        self.__executemany(
            'INSERT OR IGNORE INTO project_skills VALUES(?, ?)',
            [(project_id, new_skill_id)],
        )


    def get_statuses(self):
        sql = 'SELECT status_name FROM status'
        return self.__select_data(sql)
        

    def get_status_id(self, status_name):
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res: return res[0][0]
        else: return None

    def get_projects(self, user_id):
        sql = '''SELECT * FROM projects
        WHERE user_id = ?'''
        return self.__select_data(sql, data=(user_id,))
        
    def get_project_id(self, project_name, user_id):
        return self.__select_data(sql='SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?  ', data = (project_name, user_id,))[0][0]
        
    def get_skills(self):
        return self.__select_data(sql='SELECT * FROM skills')
    
    def get_project_skills(self, project_name):
        res = self.__select_data(sql='''SELECT skill_name FROM projects 
JOIN project_skills ON projects.project_id = project_skills.project_id 
JOIN skills ON skills.skill_id = project_skills.skill_id 
WHERE project_name = ?''', data = (project_name,) )
        return ', '.join([x[0] for x in res])
    
    def get_project_info(self, user_id, project_name):
        sql = """
SELECT project_name, description, url, status_name FROM projects 
JOIN status ON
status.status_id = projects.status_id
WHERE project_name=? AND user_id=?
"""
        return self.__select_data(sql=sql, data = (project_name, user_id))


    def update_projects(self, param, data):
        sql = f'''UPDATE projects SET {param} = ?
        WHERE project_name = ? AND user_id = ?'''
        self.__executemany(sql, [data])


    def delete_project(self, user_id, project_id):
        sql = 'DELETE FROM projects WHERE user_id = ? AND project_id = ?'
        self.__executemany(sql, [(user_id, project_id)])
    
    def delete_skill(self, project_id, skill_id):
        sql = '''DELETE FROM project_skills
        WHERE skill_id = ? AND project_id = ?'''
        self.__executemany(sql, [(skill_id, project_id)])


STATUS_OPTIONS = [
    "Проектирование",
    "В процессе разработки",
    "Разработан",
    "Обновлен",
    "Завершен/Не поддерживается"
]

SKILL_OPTIONS = [
    "Python",
    "Telegram",
    "SQL",
    "API",
    "HTML",
    "CSS",
    "FLASK",
    "AI"
]

PROJECTS = [
    {
        "project_name": "PokeFinderBot",
        "description": "Бот создаёт случайного покемона через API, отправляет имя и картинку и сохраняет прогресс пользователя.",
        "url": "https://github.com/Exoticwinn/PokeFinderBot",
        "status": "Разработан",
        "skills": ["Python", "API", "Telegram"]
    },
    {
        "project_name": "GAMERProfile",
        "description": "Демонстрация класса игрока с именем, возрастом, ником и email.",
        "url": "https://github.com/Exoticwinn/GAMERProfile",
        "status": "Разработан",
        "skills": ["Python"]
    },
    {
        "project_name": "Helper1",
        "description": "Telegram-бот-помощник с базовой логикой команд и автоматизацией задач.",
        "url": "https://github.com/Exoticwinn/Helper1",
        "status": "Разработан",
        "skills": ["Python", "Telegram", "API"]
    },
    {
        "project_name": "Telegram-Image-Bot",
        "description": "Telegram-бот с машинным обучением, классификацией изображений, мини-играми и генераторами.",
        "url": "https://github.com/Exoticwinn/Telegram-Image-Bot",
        "status": "Обновлен",
        "skills": ["Python", "Telegram", "AI", "API"]
    },
    {
        "project_name": "TestBot",
        "description": "Проект для обучения работе с GitHub и выгрузкой файлов в удалённый репозиторий.",
        "url": "https://github.com/Exoticwinn/TestBot",
        "status": "Завершен/Не поддерживается",
        "skills": ["Python", "Telegram"]
    },
    {
        "project_name": "FluxorianBot",
        "description": "Простой Telegram-бот для личного использования.",
        "url": "https://github.com/Exoticwinn/FluxorianBot",
        "status": "Разработан",
        "skills": ["Python", "Telegram"]
    },
    {
        "project_name": "Fortnite-Shop-Bot",
        "description": "Telegram-бот, который показывает магазин Fortnite и случайный предмет.",
        "url": "https://github.com/Exoticwinn/Fortnite-Shop-Bot",
        "status": "Разработан",
        "skills": ["Python", "Telegram", "API"]
    },
    {
        "project_name": "portfolio-main",
        "description": "Персональный сайт-портфолио на Flask с проектами, GitHub интеграцией и формой обратной связи.",
        "url": "https://github.com/Exoticwinn/portfolio-main",
        "status": "Разработан",
        "skills": ["Python", "HTML", "CSS", "FLASK"]
    },
    {
        "project_name": "calculator-main",
        "description": "Калькулятор для оценки энергозатрат и качества энергопотребления в доме.",
        "url": "https://github.com/Exoticwinn/calculator-main",
        "status": "Разработан",
        "skills": ["Python", "HTML", "CSS", "FLASK"]
    },
    {
        "project_name": "VENV",
        "description": "Небольшой веб-сайт с несколькими разделами и базовой структурой страниц.",
        "url": "https://github.com/Exoticwinn/VENV",
        "status": "Завершен/Не поддерживается",
        "skills": ["Python", "HTML", "CSS"]
    },
    {
        "project_name": "new-htms_css",
        "description": "Небольшой проект на HTML и CSS.",
        "url": "https://github.com/Exoticwinn/new-htms_css",
        "status": "Завершен/Не поддерживается",
        "skills": ["HTML", "CSS"]
    },
    {
        "project_name": "QuickPassword",
        "description": "Консольный генератор паролей на Python с рандомной генерацией комбинаций символов.",
        "url": "https://github.com/Exoticwinn/QuickPassword",
        "status": "Разработан",
        "skills": ["Python"]
    }
]

if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    manager.create_tables()

    manager.default_insert()

    if not manager.get_projects(1):
        for project in PROJECTS:
            status_id = manager.get_status_id(project['status'])
            manager.insert_project([
                (1, project['project_name'], project['description'], project['url'], status_id)
            ])

            for skill in project['skills']:
                skill_rows = manager.get_skills()
                if any(skill_name == skill for _, skill_name in skill_rows):
                    manager.insert_skill(1, project['project_name'], skill)
    else:
        for project in PROJECTS:
            status_id = manager.get_status_id(project['status'])
            manager.update_projects(
                'status_id', (status_id, project['project_name'], 1)
            )

    print('Статусы:', manager.get_statuses())
    print('Проекты:', manager.get_projects(1))
    print('Навыки проекта PokeFinderBot:', manager.get_project_skills('PokeFinderBot'))
