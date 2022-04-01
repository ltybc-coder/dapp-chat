# dapp-chat
# Обзор

Мы создали децентрализованное Peer-to-Peer чат с использованием Python.

Приложение имеет:
- шифрование RSA; 
- имена для пользователей и комнат; 
- многопользовательские чаты;
- создание и присоединение к чатам;
- добавление админа;
- сохранённую историю чатов.

# Особенности

Каждое сообщение подписывается с использованием вашего закрытого ключа RSA, поэтому получатель может проверить, что Вы отправляете это сообщение с использованием Вашего открытого ключа.

В каждом чате есть администраторы. В любом чате первый администратор является создателем чата.
Вы можете добавить администратора, отправив приглашение стать администратором. Если пользователь принимает его, информация об этом отправляется всем, и каждый считает этого пользователя ещё одним администратором.

Вы можете написать прямое сообщение, используя IP-адрес другого пользователя, который тоже запускает это приложение.
Сообщение может быть обычным или зашифрованным текстом. Значение по умолчанию -- зашифрованный текст.

У каждой ноды есть клиент и сервер. Клиент посылает запросы на другие ноды, на которые подписывается. Сервер каждой из нод принимает эти запросы.

На каждой из нод есть своя SQL Lite база данных, которая локально у себя in-memory сохраняет всю историю чатов. 
Запуск происходит на виртуальных машинах. Каждая нода идентифицируется по IP, а в чате -- через chat_id.

# Инструкция по установке
Запускать на разных нодах!!!
1. `pip3 install -r requirentments.txt`.
2. `python3 create_db.py`.
3. `python3 main.py`.
4. Profit!

# Идентификация
Для идентификации себя в файле config.py поменять USERNAME на каждой ноде

