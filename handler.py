from message_encryption import *
from datetime import datetime
from models import *
import logging
import random
import rsa


def validate(fields: list, data: dict, addr):
    for field in fields:
        if field not in data.keys():
            send_error(addr, f'Invalid fields: {fields}')
            return False
    return True


def get_content_of_encrypted_message(data: dict, addr):
    mess = ""
    my = get_rsa_priv_from_str(get_my_rsa().priv_key)
    host_pub = get_rsa_pub_from_str(get_rsa_key(addr).pub_key)
    for ms in data['data']:
        try:
            mess += rsa.decrypt(bytes.fromhex(ms), my).decode('utf-8')
        except rsa.DecryptionError:
            mes = {"type": "pub_key", "data": str(get_my_rsa().pub_key)}
            ip, port = addr
            send((ip, PORT), json.dumps(mes))
            return 'Error in decryption', False
    return mess, rsa.verify(mess.encode('utf-8'), bytes.fromhex(data['sign']), host_pub)


def add_message_to_db(data, mess, addr):
    ip, port = addr
    chat = Chat.get_or_none(chat_id=data['chat_id'])
    if chat is None:
        if ip == '0.0.0.0':
            return
        send_error(addr, f"Error: couldn't find chat with id: {data['chat_id']}")
        return 'err'
    mem, _ = Member.get_or_create(chat=chat, ip=str(ip), port=str(PORT), name=data['name'])
    Message(chat=chat, member=mem, content=mess).save()
    return 'ok'


def is_member(addr, data):
    ip, port = addr
    chat = Chat.get_or_none(chat_id=data['chat_id'])
    if chat is None:
        return False
    a = Member.get_or_none(ip=ip, name=data['name'], chat_id=chat)
    if a is None:
        return False
    return True


def check_chat_id_IETS(chat_id):
    suggest_new_name = False
    new_chat_id = chat_id
    while True:
        if Chat.get_or_none(chat_id=new_chat_id) is not None:
            new_chat_id = hex(random.randint(1, 10 ** 10))
            suggest_new_name = True
        else:
            break
    if suggest_new_name is True:
        send_new_name_suggestion(chat_id, new_chat_id)
    if chat_id != new_chat_id:
        return new_chat_id
    return None


def checker(data, addr, check_fields=None, verify_sign=None, verify_if_chat_exists=None, verify_is_member=None):
    if check_fields is not None:
        if not validate(check_fields, data, addr):
            return False
    if verify_sign is True:
        mess, is_verified = get_content_of_encrypted_message(data, addr)
        if not is_verified:
            print(f"Error: from: {addr}; name:{data['name']}")
            return False
    if verify_if_chat_exists is not None:
        if Chat.get_or_none(chat_id=verify_if_chat_exists) is None:
            send_error(addr, f"Error: couldn't find chat with id: {data['chat_id']}")
            return False
    if verify_is_member is True:
        if not is_member(addr, data):
            print(f"Error. You received message from {data['name']} who is not member of chat_id {data['chat_id']} ")
            return False
    return True


def handle_requests(message, addr):
    logging.debug(f'New request. {addr} {message}')
    try:
        data = json.loads(message)
        ip, port = addr
        port = PORT
    except json.decoder.JSONDecodeError:
        send(addr, "Error: unparsable json")
        logging.error(f"[{datetime.datetime.now()}] Error: unparsable json from {addr}. {message}")
        return
    if data["type"] == 'mes':
        mes_process(data)
    elif data["type"] == 'get_pub_key':
        gut_pub_key_process(addr)
    elif data["type"] == 'pub_key':
        if checker(data, addr, check_fields=['data']) is False:
            return
        pub_key_process(addr, data)
    elif data['type'] == 'encrypted_message':
        if checker(data, addr, check_fields=['name', 'chat_id', 'data', 'sign'], verify_sign=True,
                   verify_is_member=True) is False:
            return
        mess = encrypted_message_process(addr, data)
        if add_message_to_db(data, mess, addr) == 'err':
            return
    elif data['type'] == 'error':
        if 'data' in data.keys():
            logging.error(f'[{datetime.datetime.now()}] Error. {data["data"]}')
    elif data['type'] == 'sjoin':
        if checker(data, addr, check_fields=['name', 'chat_id', 'data', 'sign'], verify_sign=True) is False:
            return
        mes, ver = get_content_of_encrypted_message(data, addr)
        if checker(data, addr, verify_if_chat_exists=mes) is False:
            return
        ip, port = addr
        chat = Chat.get(chat_id=mes)
        if Member.get_or_none(ip=ip, port=port, name=data['name'], chat_id=chat) is not None:
            return
        sjoin_process(addr, chat, data, ip)
    elif data['type'] == 'join_acc':
        if checker(data, addr, check_fields=['name', 'chat_id', 'data', 'sign', 'chat_name', 'chat_id_changeable'],
                   verify_sign=True) is False:
            return
        mess, is_verified = get_content_of_encrypted_message(data, addr)
        if data['chat_id_changeable'] == 'True':
            new_chat_id = check_chat_id_IETS(data['chat_id'])
            if new_chat_id is not None:
                data['chat_id'] = new_chat_id
        else:
            chat_local = Chat.get_or_none(data['chat_id'])
            if chat_local is not None:
                print(f'Error. You already have such chat_id')
                logging.warning(f'Chat_id collusion')
                return
        chat_name = data['chat_name']
        while True:
            if Chat.get_or_none(name=chat_name) is not None:
                chat_name = chat_name + str(hex(random.randint(1, 10 ** 7)))
            else:
                break
        join_acc_process(addr, chat_name, data, mess)
    elif data['type'] == 'new_chat_id':
        if checker(check_fields=['old', 'new'], verify_if_chat_exists=data['old']) is False:
            return
        if checker(verify_is_member=True) is False:
            return
        new_chat_id_process(addr, data)
    elif data['type'] == 'add_admin':
        if checker(data, addr, check_fields=['data', 'chat_id', 'sign', 'name'],
                   verify_sign=True) is False:
            return
        if checker(data, addr, verify_if_chat_exists=data['chat_id'], verify_is_member=True) is False:
            return
        mess, is_verified = get_content_of_encrypted_message(data, addr)
        mes = json.loads(mess)
        chat = Chat.get(chat_id=data['chat_id'])
        mem = Member.get_or_none(ip=mes['ip'], port=mes['port'], name=mes['name'], chat=chat)
        if mem is None:
            send_error(addr, f"User is not a member of this chat")
            return
        if Member.get_or_none(chat=chat, ip=ip, name=data['name']).is_admin is not True:
            send_error(addr, f"Error. Not enough rights")
            return
        if data['type'] == 'add_admin':
            mem.is_admin = True
            mem.save()
    elif data['type'] == 'new_member':
        if checker(data, addr, check_fields=['sign', 'data', 'name', 'chat_id'], verify_sign=True) is False:
            return
        if checker(data, addr, verify_if_chat_exists=data['chat_id'], verify_is_member=True) is False:
            return
        chat = Chat.get(chat_id=data['chat_id'])
        host = Member.get(chat=chat, name=data['name'], ip=ip)
        mes, vr = get_content_of_encrypted_message(data, addr)
        try:
            mes = json.loads(mes)
        except json.decoder.JSONDecodeError:
            send(addr, "Error: could't parse json")
            logging.error(f"[{datetime.datetime.now()}] Error: could't parse json from {addr}. {message}")
            return
        if checker(mes, addr, check_fields=['ip', 'name', 'is_admin']) is False:
            return
        if host.is_admin is True:
            new, _ = Member.get_or_create(chat=chat, ip=mes['ip'], port=PORT, name=mes['name'], approved=True)
        else:
            send_error(addr, 'Not enough rights')

    elif data['type'] == 'you_is_admin' or data['type'] == 'you_blocked':
        if checker(data, addr, check_fields=['chat_id', 'sign', 'name', 'data'], verify_sign=True) is False:
            return
        if checker(data, addr, verify_if_chat_exists=data['chat_id'], verify_is_member=True) is False:
            return
        chat = Chat.get(chat_id=data['chat_id'])
        if Member.get_or_none(chat=chat, ip=ip, name=data['name']).is_admin is not True:
            send_error(addr, f"Not enough rights")
            return
        me, _ = Member.get_or_create(chat=chat, ip='0.0.0.0', port=PORT, name=USER_NAME, approved=True)
        if data['type'] == 'you_is_admin':
            me.is_admin = True
            me.save()


def new_chat_id_process(addr, data):
    chat = Chat.get(chat_id=data['old'])
    if chat.chat_id_changeable is False:
        send_error(addr, "Error. Chat_id is not changeable")
    chat_id = data['new']
    nchat = check_chat_id_IETS(chat_id)
    if nchat == data['new']:
        chat.chat_id = data['new']
    else:
        chat.chat_id = nchat


def join_acc_process(addr, chat_name, data, mess):
    mem_list = json.loads(mess)
    ip, port = addr
    chat = Chat.create(chat_id=data['chat_id'], name=chat_name, ip=ip, port=PORT)
    for member in mem_list:
        if member['ip'] == '0.0.0.0':
            ip, port = addr
            member['ip'] = ip
            member['port'] = PORT
        Member(name=member['name'], ip=member['ip'], port=member['port'], chat_id=chat,
               is_admin=member['is_admin'], approved=True).save()
    Member(name=USER_NAME, ip=HOST, port=PORT, chat_id=chat, is_admin=False, approved=True).save()
    print(f"You are now member of chat {chat.name}")


def sjoin_process(addr, chat, data, ip):
    Member.get_or_create(ip=ip, port=PORT, name=data['name'], chat_id=chat)
    print(f'{data["name"]} {addr} wants to join in chat {chat.name}. '
          f'Type "approve {data["name"]} {chat.chat_id} '
          f'{ip}" to give him access')


def encrypted_message_process(addr, data):
    mess, is_verified = get_content_of_encrypted_message(data, addr)
    print()
    print("\033[A                             \033[A")
    print(f"{data['name']}> {mess}")
    print("you>", end="")
    return mess


def pub_key_process(addr, data):
    ip, port = addr
    k = Key.get_or_none(ip=ip, port=PORT)
    if k is None:
        k = Key(ip=ip, port=PORT, pub_key=data["data"])
    else:
        k.pub_key = data["data"]
    k.save()


def gut_pub_key_process(addr):
    mes = {"type": "pub_key", "data": str(get_my_rsa().pub_key)}
    ip, port = addr
    send((ip, PORT), json.dumps(mes))


def mes_process(data):
    print()
    print("\033[A                             \033[A")
    print(f"{data['name']}> {data['data']}")
    print("you>", end="")
