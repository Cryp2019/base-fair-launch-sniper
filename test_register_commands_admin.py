import asyncio
import sniper_bot

# Monkeypatch admin check to always return True for this test
sniper_bot.admin_manager.is_admin = lambda uid, uname: True

class FakeMessage:
    async def reply_text(self, text):
        print("[FakeMessage.reply_text]", text)

class FakeUser:
    def __init__(self):
        self.id = 999999
        self.username = 'testadmin'

class FakeUpdate:
    def __init__(self):
        self.effective_user = FakeUser()
        self.message = FakeMessage()

class FakeBot:
    async def set_my_commands(self, cmds, scope=None):
        print("[FakeBot.set_my_commands] Registered commands:")
        for c in cmds:
            print(f" - {c.command}: {c.description}")

class FakeContext:
    def __init__(self):
        self.bot = FakeBot()

async def main():
    update = FakeUpdate()
    context = FakeContext()
    await sniper_bot.register_commands_admin(update, context)

if __name__ == '__main__':
    asyncio.run(main())
