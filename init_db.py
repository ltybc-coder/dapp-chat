from config import DB_URI
from models import *

db = SqliteDatabase(DB_URI)
db.create_tables([Key, Chat, Member, Message])
