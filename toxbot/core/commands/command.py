

class CommandData:

    def __init__(self, method_name, allowed_roles, description=''):
        self._method_name = method_name
        self._allowed_roles = allowed_roles
        self._description = description

    def get_method_name(self):
        return self._method_name

    method_name = property(get_method_name)

    def get_roles(self):
        return self._allowed_roles

    roles = property(get_roles)

    def get_description(self):
        return self._description

    description = property(get_description)


# TODO: more commands

_commands = {
    'name': CommandData('set_name', ['admin'], 'Sets my name'),
    'status': CommandData('set_status', ['admin'], 'Sets my status'),
    'status_message': CommandData('set_status_message', ['admin'], 'Sets my status message'),
    'id': CommandData('get_id', ['user', 'admin'], 'Gets my TOX ID'),
    'info': CommandData('get_info', ['user', 'admin'], 'Prints my current status'),
    'help': CommandData('print_help', ['user', 'admin'], 'Prints commands list'),
    'message': CommandData('send_message', ['admin'], 'Sends message'),
    'stop': CommandData('stop', ['admin'], 'Stops bot'),
    'ban nick': CommandData('ban_nick', ['admin'], 'Ban user by nick'),
    'ban pk': CommandData('ban_public_key', ['admin'], 'Ban user by public key'),
    'roles': CommandData('send_roles', ['user', 'admin'], 'Prints your roles'),
    'reconnect': CommandData('reconnect', ['admin'], 'Asks bot to reconnect'),
    'auto_reconnection': CommandData('set_auto_reconnection_interval', ['admin'],
                                     'Sets automatic reconnection interval in seconds (0 to disable)'),
    'groups': CommandData('send_groups_list', ['user', 'admin'], 'Prints groups list'),
    'leave': CommandData('leave_group', ['admin'], 'Leave group'),
    'invite': CommandData('invite_to_group', ['user', 'admin'], 'Invites to group')
}


def get_commands_descriptions():
    s = ''
    for key in _commands:
        s += '{}: {}\n'.format(key, _commands[key].description)
    return s


def extend_command_list(new_commands):
    _commands.update(new_commands)


class BaseCommand:

    def execute(self):
        pass


class ExecutableCommand(BaseCommand):

    def __init__(self, action):
        super().__init__()
        self._action = action

    def execute(self):
        self._action()


class BaseDefaultCommand(BaseCommand):

    def __init__(self, bot, command, *arguments):
        super().__init__()
        self._bot = bot
        self._command = command
        self._arguments = arguments

    def execute(self):
        if self._command in _commands:
            command_data = _commands[self._command]
            method = getattr(self._bot, command_data.method_name)
            self.run_method(method, command_data.roles)
        else:
            self.invalid_command()

    def invalid_command(self):
        pass

    def run_method(self, method, roles):
        pass


class Command(BaseDefaultCommand):

    def __init__(self, bot, friend_number, command, *arguments):
        super().__init__(bot, command, *arguments)
        self._friend_number = friend_number

    def invalid_command(self):
        self._bot.invalid_command(self._friend_number)
        print('Unknown command: ' + self._command)

    def run_method(self, method, roles):
        method(roles, self._friend_number, *self._arguments)


class GcCommand(BaseDefaultCommand):

    def __init__(self, bot, gc_number, peer_number, command, *arguments):
        super().__init__(bot, command, *arguments)
        self._gc_number = gc_number
        self._peer_number = peer_number

    def invalid_command(self):
        self._bot.invalid_gc_command(self._gc_number, self._peer_number)
        print('Unknown gc command: ' + self._command)

    def run_method(self, method, roles):
        method(roles, self._gc_number, self._peer_number, *self._arguments)
