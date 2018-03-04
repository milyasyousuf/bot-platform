from core.commands.default_commands import *
from core.permissions_checker import *
from core.util import log


class Interpreter:

    def __init__(self, bot):
        self._bot = bot

    def interpret(self, message, friend_number):
        message = message.strip()
        command = self.parse_command(message, friend_number)
        self.execute_command(command)

    def execute_command(self, command):
        try:
            command.execute()
        except PermissionsException as ex:
            log('Permissions error: ' + str(ex))
        except Exception as ex:
            log('Exception: ' + str(ex))

    def parse_command(self, message, friend_number):
        if message == 'help':
            return HelpCommand(self._bot, friend_number)
        elif message.startswith('name'):
            new_name = message[len('name'):]
            return self.create_command(friend_number, 'name', new_name)
        elif message.startswith('status'):
            new_status = message[len('status'):]
            return self.create_command(friend_number, 'status', int(new_status))
        elif message.startswith('status_message'):
            new_status_message = message[len('status_message'):]
            return self.create_command(friend_number, 'status_message', new_status_message)
        elif message == 'id':
            return self.create_command(friend_number, 'id')
        elif message == 'info':
            return self.create_command(friend_number, 'info')
        else:
            return InvalidCommand(self._bot, friend_number)

    def create_command(self, friend_number, name, *arguments):
        return Command(self._bot, friend_number, name, *arguments)
