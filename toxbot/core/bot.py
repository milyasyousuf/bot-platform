from core.permissions_checker import *
from wrapper.toxcore_enums_and_consts import *
from core.util import log, get_time, time_from_seconds
from core.common.tox_save import ToxSave
import threading


class Bot(ToxSave):

    def __init__(self, tox, settings, profile_manager, permission_checker, stop_action, reconnect_action):
        super().__init__(tox)
        self._settings = settings
        self._profile_manager = profile_manager
        self._permission_checker = permission_checker
        self._stop_action = stop_action
        self._reconnect_action = reconnect_action

        self._start_time = get_time()
        self._timer = None
        self._waiting_for_reconnection = False

        self._print_info()

    # -----------------------------------------------------------------------------------------------------------------
    # Common methods
    # -----------------------------------------------------------------------------------------------------------------

    def check_permissions(self, command, roles, friend_number):
        if not self._permission_checker.check_permissions(roles, friend_number):
            raise PermissionsException(friend_number, command)

    def process_friend_request(self, public_key, message):
        if not self._permission_checker.accept_request_from(public_key):
            return
        password = self._settings['friend_request_password']
        if password is not None and message != password:
            return
        self._tox.friend_add_norequest(public_key)
        self._profile_manager.save_profile()
        self._settings['users'][public_key] = [self._settings['auto_rights']]
        self._settings.save()

    def process_gc_invite_request(self, friend_number, invite_data):
        if self._permission_checker.accept_gc_invite_from(friend_number):
            self._tox.group_invite_accept(invite_data, friend_number)
            self._profile_manager.save_profile()

    def process_conference_invite_request(self, friend_number, invite_data):
        if self._permission_checker.accept_gc_invite_from(friend_number):
            self._tox.conference_join(invite_data, friend_number)
            self._profile_manager.save_profile()

    def update_connection_status(self, connection_status):
        if connection_status == TOX_CONNECTION['NONE'] and not self._waiting_for_reconnection:
            self._waiting_for_reconnection = True
            self._set_timer(self._settings['reconnection_timeout'], self._check_connection)

    def send_message_to_friend(self, friend_number, message, message_type=TOX_MESSAGE_TYPE['NORMAL']):
        """
        :param friend_number: friend number
        :param message_type: type of message
        :param message: message text
        """
        messages = self._split_message(message)
        for tox_message in messages:
            self._tox.friend_send_message(friend_number, message_type, tox_message)

    def send_message_to_group(self, group_number, message, message_type=TOX_MESSAGE_TYPE['NORMAL']):
        """
        :param group_number: group number
        :param message_type: type of message
        :param message: message text
        """
        messages = self._split_message(message)
        for tox_message in messages:
            self._tox.group_send_message(group_number, message_type, tox_message)

    def send_private_message_to_gc_peer(self, group_number, peer_number,
                                        message, message_type=TOX_MESSAGE_TYPE['NORMAL']):
        """
        :param group_number: group number
        :param peer_number: destination peer number
        :param message_type: type of message
        :param message: message text
        """
        messages = self._split_message(message)
        for tox_message in messages:
            self._tox.group_send_private_message(group_number, peer_number, message_type, tox_message)

    # -----------------------------------------------------------------------------------------------------------------
    # Overridable methods
    # -----------------------------------------------------------------------------------------------------------------

    def create_info(self):
        current_time = get_time()
        online_time = time_from_seconds(current_time - self._start_time)
        friends_list = self._get_friends_list()
        friends_count = len(friends_list)
        online_friends_count = sum([
            self._tox.friend_get_connection_status(friend) != TOX_CONNECTION['NONE'] for friend in friends_list
        ])
        messages = [
            'Uptime: ' + online_time,
            'Friends: {} ({} online)'.format(friends_count, online_friends_count)
        ]

        return messages

    # -----------------------------------------------------------------------------------------------------------------
    # Bot commands
    # -----------------------------------------------------------------------------------------------------------------

    def invalid_command(self, friend_number):
        self.send_message_to_friend(friend_number, 'Invalid command.')

    def invalid_gc_command(self, gc_number, peer_number):
        pass

    def invalid_gc_private_command(self, gc_number, peer_number):
        pass

    @authorize
    def set_name(self, friend_number, name):
        self._tox.self_set_name(name.encode('utf-8'))

    @authorize
    def set_status(self, friend_number, status):
        self._tox.self_set_status(status)

    @authorize
    def set_status_message(self, friend_number, status_message):
        self._tox.self_set_status_message(status_message.encode('utf-8'))

    @authorize
    def get_id(self, friend_number):
        tox_id = self._get_tox_id()
        self.send_message_to_friend(friend_number, tox_id)

    @authorize
    def get_info(self, friend_number):
        messages = self.create_info()
        for message in messages:
            self.send_message_to_friend(friend_number, message)

    @authorize
    def remove_friend_by_public_key(self, friend_number, public_key):
        try:
            friend = self._tox.friend_by_public_key(public_key)
            self._tox.friend_delete(friend)
        except Exception as ex:
            log('Exception on friend delete command: ' + str(ex))
            self.send_message_to_friend(friend_number, 'No such friend is known.')
        else:
            self.send_message_to_friend(friend_number, 'Friend was deleted successfully!')

    @authorize
    def send_message(self, friend_number, message, destination_friend=None):
        friends_list = [destination_friend] if destination_friend is not None else self._get_friends_list()
        for friend in friends_list:
            self.send_message_to_friend(friend, message)

    @authorize
    def send_group_message(self, friend_number, message, destination_group=None):
        if destination_group is not None:
            groups_list = [destination_group]
        else:
            groups_list = range(self._tox.group_get_number_groups())
        for group in groups_list:
            self.send_message_to_group(group, message)

    @authorize
    def stop(self, friend_number):
        log('Closing application after stop command from friend ' + str(friend_number))
        self._stop_action()

    @authorize
    def reconnect(self, friend_number):
        log('Reconnecting after command from friend ' + str(friend_number))
        self._reconnect()

    @authorize
    def set_auto_reconnection_interval(self, friend_number, interval):
        log('Auto reconnection interval was set to {} by friend {}'.format(interval, friend_number))
        self._settings['automatic_reconnection_interval'] = interval
        self._settings.save()
        self.send_message_to_friend(friend_number, 'Successfully updated!')

    @authorize
    def set_roles_of_friend_by_public_key(self, friend_number, public_key, roles):
        pass

    def get_friend_roles(self, friend_number):
        roles = self._permission_checker.get_user_roles(friend_number)
        message = 'Roles:\n' + '\n'.join(roles)
        self.send_message_to_friend(friend_number, message)

    @authorize
    def ban_nick(self, friend_number, nick):
        log('Nick "{}" was banned by friend number {}'.format(nick, friend_number))
        if nick not in self._settings['ban']['nicks']:
            self._settings['ban']['nicks'].append(nick)
            self._settings.save()
        self.send_message_to_friend(friend_number, 'Successfully banned nickname ' + nick)

    @authorize
    def ban_public_key(self, friend_number, public_key):
        log('Public key "{}" was banned by friend number {}'.format(public_key, friend_number))
        if public_key not in self._settings['ban']['public_keys']:
            self._settings['ban']['public_keys'].append(public_key)
            self._settings.save()
        self.send_message_to_friend(friend_number, 'Successfully banned public key ' + public_key)

    def print_help(self, friend_number, help_message):
        self.send_message_to_friend(friend_number, help_message)

    # -----------------------------------------------------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------------------------------------------------

    @staticmethod
    def _split_message(message):
        message = message.encode('utf-8')
        messages = []
        while len(message) > TOX_MAX_MESSAGE_LENGTH:
            size = TOX_MAX_MESSAGE_LENGTH * 4 / 5
            last_part = message[size:TOX_MAX_MESSAGE_LENGTH]
            if ' ' in last_part:
                index = last_part.index(' ')
            elif ',' in last_part:
                index = last_part.index(',')
            elif '.' in last_part:
                index = last_part.index('.')
            else:
                index = TOX_MAX_MESSAGE_LENGTH - size - 1
            index += size + 1
            messages.append(message[:index])
            message = message[index:]
        if message:
            messages.append(message)

        return messages

    def _check_connection(self):
        friends = self._get_friends_list()
        statuses = map(lambda n: self._tox.friend_get_connection_status(n) != TOX_CONNECTION['NONE'], friends)
        any_friends_available = any(statuses)
        if not any_friends_available:
            self._reconnect()
        elif self._settings['automatic_reconnection_interval']:
            self._set_timer(self._settings['automatic_reconnection_interval'], self._reconnect)

    def _reconnect(self):
        self._reconnect_action()
        self._set_timer(self._settings['reconnection_timeout'], self._check_connection)

    def _set_timer(self, interval, handler):
        self._stop_timer_if_needed()
        self._timer = threading.Timer(interval, handler)
        self._timer.start()

    def _stop_timer_if_needed(self):
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _get_friends_list(self):
        return self._tox.self_get_friend_list()

    def _print_info(self):
        class_name = self.__class__.__name__
        tox_id = self._get_tox_id()
        log('Starting bot "{}" with ID {}'.format(class_name, tox_id))

    def _get_tox_id(self):
        return self._tox.self_get_address()
