from handler import *
import random
import re

ip_regex = r'^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$'

commands_help = '"help" - list of commands\n' \
                '"enter_chat <name>" - enter the chat\n' \
                '"new_chat" - create new chat\n' \
                '"join_chat" - join existing chat\n' \
                '"add_admin" - add admin to chat\n' \
                '"approve *name* *chat_id* *ip*" - approve invite'


def approve(a):
    if len(a.split()) != 4:
        print('Too few arguments')
        return
    ip = a.split()[3]
    if not re.fullmatch(ip_regex, ip):
        print("Invalid ip")
        return
    chat = Chat.get_or_none(chat_id=a.split()[2])
    if chat is None:
        print(f"Chat with chat_id {a.split()[2]} not found")
        return
    me = Member.get_or_none(chat_id=chat.chat_id, name=USER_NAME, ip=HOST, port=PORT)
    if me is not None:
        if me.is_admin is False:
            print("I cannot accept users since I am not admin")
            return
    members = Member.select().where(Member.chat_id == chat)
    member_l = []
    for mem in members:
        if mem.ip == a.split()[3]:
            continue
        if mem.approved is True:
            member_l.append({"ip": mem.ip, "port": mem.port, "name": mem.name, "is_admin": mem.is_admin})
    EncryptedMessage(json.dumps(member_l), Chat(name=a.split()[1], chat_id=a.split()[2], ip=ip, port=PORT),
                     type='join_acc').send_sjoin_acc_mes(chat_name=chat.name)
    new_mem = {"ip": ip, "port": PORT, "name": a.split()[1], "is_admin": False}
    new, _ = Member.get_or_create(chat=chat, ip=ip, name=a.split()[1])
    new.approved = True
    new.is_admin = False
    new.save()
    members = Member.select().where(Member.chat == Chat.get(chat_id=chat.chat_id))
    for mem in members:
        if mem.ip == '0.0.0.0' or mem.ip == ip:
            continue
        EncryptedMessage(json.dumps(new_mem),
                         Chat(name='none',
                              chat_id=a.split()[2],
                              ip=mem.ip,
                              port=PORT
                              ),
                         type='new_member').send_encrypted_message()


def chat_f(a):
    chat = Chat.get_or_none(name=a.split()[1])
    if chat is None:
        print("Chat not found")
        return
    history_count = restore_history()
    if history_count == 0:
        print(f'You are in chat "{chat.name}"')
    while True:
        print("you> ", end="")
        a = input()
        print("\033[A                             \033[A")
        print("you>", a)
        if a == "exit()":
            break
        if a == "":
            continue
        if a.split(":")[0] == 'ne':  # Not encrypted message
            members = Member.select().where(Member.chat == chat)
            for mem in members:
                send_mes((str(mem.ip), str(mem.port)), a)
        EncryptedMessage(a, chat).send_encrypted_message_to_all()
        add_message_to_db({"chat_id": chat.chat_id, 'name': USER_NAME}, a, ('0.0.0.0', PORT))


def restore_history():
    messages = [message for message in Message.select()]
    length = 0
    for message in messages:
        length += 1
        user_name = message.member.name
        if user_name == USER_NAME:
            print(f"you> {message.content}")
        else:
            print(f"{user_name}> {message.content}")
    return length


def new_f(a):
    name = input("Name of new chat:\n")
    chat = Chat.get_or_none(name=name)
    if chat is not None:
        print('Chat already exist')
        return
    if name in ['help', 'enter_chat', 'new_chat', 'join_chat', 'approve', 'add_admin']:
        print('Chat name should not be a reserved keyword')
        return
    chat_id = hex(random.randint(1, 10 ** 10))
    while True:
        if Chat.get_or_none(chat_id=chat_id) is not None:
            chat_id = hex(random.randint(1, 10 ** 10))
        else:
            break

    chat = Chat.create(name=name, chat_id=chat_id, ip=HOST, port=PORT, chat_id_changeable=False)
    Member(chat=chat, ip=HOST, port=PORT, name=USER_NAME, is_admin=True, approved=True).save()
    print(f"New chat id:{chat_id}")


def join_f(a):
    chat_id = input("Chat_id\n")
    while True:
        ip = input("Server ip\n")
        if not re.fullmatch(ip_regex, ip):
            print("Invalid ip")
            continue
        break
    EncryptedMessage(chat_id, Chat(name=USER_NAME,
                                   chat_id=chat_id,
                                   ip=ip,
                                   port=PORT),
                    type='sjoin').send_sdef_mes()


def select_chat_and_member(for_everyone, to_person):
    chat_name = input("Write chat name where to add admin\n")
    chat = Chat.get_or_none(name=chat_name)
    if chat is None:
        print('Chat not found')
        return
    me = Member.get_or_none(chat=chat, ip=HOST)
    if me is None:
        print('You have no access')
        return
    members = Member.select().where(Member.chat == chat)
    print('Chose user:')
    list_of_members = []
    for mem in members:
        if mem.ip == HOST or mem.is_admin is True or mem.approved is False:
            continue
        list_of_members.append(mem)
        print(f'#{len(list_of_members)} {mem.name} {mem.ip} {mem.port}')
    while True:
        num = input('Which should be admin? (type "exit()" to cancel)\n')
        if num == 'exit()':
            return
        elif not num.isnumeric():
            print('It is not a number')
        else:
            break
    if int(num) > 0 or int(num) <= len(list_of_members):
        try:
            memb = list_of_members[int(num) - 1]
        except IndexError:
            print('Invalid data')
            return
        mes = {"ip": memb.ip,
               "port": memb.port,
               "name": memb.name,
               'data': 'is required'}
        mmm = 'data is required'
        if for_everyone == 'add_admin':
            memb.is_admin = True
            memb.save()
        EncryptedMessage(json.dumps(mes), Chat(name=chat.name, chat_id=chat.chat_id, ip=memb.ip, port=memb.port),
                         type=for_everyone).send_encrypted_message_to_all()
        EncryptedMessage(mmm, Chat(name=chat.name, chat_id=chat.chat_id, ip=memb.ip, port=PORT),
                         type=to_person).send_encrypted_message()


def client_start():
    print("Welcome to decentralized chat!\n")
    print(commands_help)
    chats = Chat.select()
    for c in chats:
        print(f"Chat_name: {c.name}\n\tchat_id: {c.chat_id}\n\tchat_ip: {c.ip}")
    while True:
        print(">", end="")
        a = input()
        if a == '':
            continue
        if a.split()[0] == "enter_chat":
            chat_f(a)
        elif a.split()[0] == 'new_chat':
            new_f(a)
        elif a.split()[0] == 'join_chat':
            join_f(a)
        elif a.split()[0] == 'approve':
            approve(a)
        elif a.split()[0] == 'add_admin':
            select_chat_and_member('add_admin', 'you_is_admin')
        elif a.split()[0] == 'help':
            print(commands_help)
        else:
            print("Couldn't understand your command")
