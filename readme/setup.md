## Установка проекта

### 0. Клонирование проекта

`cd /var/www && git clone https://github.com/Xoma163/xoma163site.git`  

`cd xoma163site`

### 1. Подготовка группы в ВК
ToDo
<your_token>
<your_group_id>

### 2. Подготовка БД
-   `apt install postgresql`
-   `su - postgres` 
-   `psql` 

```postgresql
CREATE ROLE <your_username> WITH LOGIN ENCRYPTED PASSWORD '<your_password>';
CREATE DATABASE <your_database> WITH OWNER <your_username>;
SET TIMEZONE=<your_timezone>;
```

### 3. Указание учётных данных
Внеси все свои данные по боту ВК и различным API в файл secrets/.env  

За основу можно и нужно взять secrets/example.env  

`cp secrets/secrets.env secrets/.env` 

В первую очередь нужно заполнить:
-   `SECRET_KEY` - секретный ключ django
-   `DATABASE_URL` - данные базы данных
-   `VK_BOT_TOKEN` - токен бота
-   `VK_BOT_GROUP_ID` - id группы бота
-   `VK_BOT_MENTIONS` - список обращений, на которые будет реагировать бот
-   `VK_ADMIN_ID` - id админа

### 4. Указание своих данных в конфигах
-   в config/petrovich.service нужно указать пользователя от имени которого будет выполняться служба 
-   в config/petrovich_site.service нужно указать пользователя от имени которого будет выполняться служба 
-   в config/petrovich_nginx.conf нужно указать имя сервера, на которое будет реагировать nginx и порт. 

### 5. Запуск автонастройки (создание окружение, установка зависимостей)
-   `chmod +x setup.sh`
-   `./setup.sh`

Обратите внимание. Скрипт заменяет некоторые абсолютные пути на тот путь, откуда вы будете запускать скрипт. Рекомендуется это делать из папки проекта

### 6. Запуск
-   `systemctl start petrovich` - запуск бота
-   `systemctl start petrovich_site` - запуск админки и сайта
