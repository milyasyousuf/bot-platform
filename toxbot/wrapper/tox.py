# -*- coding: utf-8 -*-
from ctypes import c_char_p, Structure, c_bool, byref, c_int, c_size_t, POINTER, c_uint16, c_void_p, c_uint64
from ctypes import create_string_buffer, ArgumentError, CFUNCTYPE, c_uint32, sizeof, c_uint8
from wrapper.toxcore_enums_and_consts import *
from wrapper.toxav import ToxAV
from wrapper.libtox import LibToxCore


class ToxOptions(Structure):
    _fields_ = [
        ('ipv6_enabled', c_bool),
        ('udp_enabled', c_bool),
        ('local_discovery_enabled', c_bool),
        ('proxy_type', c_int),
        ('proxy_host', c_char_p),
        ('proxy_port', c_uint16),
        ('start_port', c_uint16),
        ('end_port', c_uint16),
        ('tcp_port', c_uint16),
        ('hole_punching_enabled', c_bool),
        ('savedata_type', c_int),
        ('savedata_data', c_char_p),
        ('savedata_length', c_size_t),
        ('log_callback', c_void_p),
        ('log_user_data', c_void_p)
    ]


class GroupChatSelfPeerInfo(Structure):
    _fields_ = [
        ('nick', c_char_p),
        ('nick_length', c_uint8),
        ('user_status', c_int)
    ]


def string_to_bin(tox_id):
    return c_char_p(bytes.fromhex(tox_id)) if tox_id is not None else None


def bin_to_string(raw_id, length):
    res = ''.join('{:02x}'.format(ord(raw_id[i])) for i in range(length))
    return res.upper()


class Tox:
    libtoxcore = LibToxCore()

    def __init__(self, tox_options=None, tox_pointer=None):
        """
        Creates and initialises a new Tox instance with the options passed.

        This function will bring the instance into a valid state. Running the event loop with a new instance will
        operate correctly.

        :param tox_options: An options object. If this parameter is None, the default options are used.
        :param tox_pointer: Tox instance pointer. If this parameter is not None, tox_options will be ignored.
        """
        if tox_pointer is not None:
            self._tox_pointer = tox_pointer
        else:
            tox_err_new = c_int()
            Tox.libtoxcore.tox_new.restype = POINTER(c_void_p)
            self._tox_pointer = Tox.libtoxcore.tox_new(tox_options, byref(tox_err_new))
            tox_err_new = tox_err_new.value
            if tox_err_new == TOX_ERR_NEW['NULL']:
                raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
            elif tox_err_new == TOX_ERR_NEW['MALLOC']:
                raise MemoryError('The function was unable to allocate enough '
                                  'memory to store the internal structures for the Tox object.')
            elif tox_err_new == TOX_ERR_NEW['PORT_ALLOC']:
                raise RuntimeError('The function was unable to bind to a port. This may mean that all ports have '
                                   'already been bound, e.g. by other Tox instances, or it may mean a permission error.'
                                   ' You may be able to gather more information from errno.')
            elif tox_err_new == TOX_ERR_NEW['PROXY_BAD_TYPE']:
                raise ArgumentError('proxy_type was invalid.')
            elif tox_err_new == TOX_ERR_NEW['PROXY_BAD_HOST']:
                raise ArgumentError('proxy_type was valid but the proxy_host passed had an invalid format or was NULL.')
            elif tox_err_new == TOX_ERR_NEW['PROXY_BAD_PORT']:
                raise ArgumentError('proxy_type was valid, but the proxy_port was invalid.')
            elif tox_err_new == TOX_ERR_NEW['PROXY_NOT_FOUND']:
                raise ArgumentError('The proxy address passed could not be resolved.')
            elif tox_err_new == TOX_ERR_NEW['LOAD_ENCRYPTED']:
                raise ArgumentError('The byte array to be loaded contained an encrypted save.')
            elif tox_err_new == TOX_ERR_NEW['LOAD_BAD_FORMAT']:
                raise ArgumentError('The data format was invalid. This can happen when loading data that was saved by'
                                    ' an older version of Tox, or when the data has been corrupted. When loading from'
                                    ' badly formatted data, some data may have been loaded, and the rest is discarded.'
                                    ' Passing an invalid length parameter also causes this error.')

            self.self_connection_status_cb = None
            self.friend_name_cb = None
            self.friend_status_message_cb = None
            self.friend_status_cb = None
            self.friend_connection_status_cb = None
            self.friend_request_cb = None
            self.friend_read_receipt_cb = None
            self.friend_typing_cb = None
            self.friend_message_cb = None
            self.file_recv_control_cb = None
            self.file_chunk_request_cb = None
            self.file_recv_cb = None
            self.file_recv_chunk_cb = None
            self.friend_lossy_packet_cb = None
            self.friend_lossless_packet_cb = None
            self.group_moderation_cb = None
            self.group_join_fail_cb = None
            self.group_self_join_cb = None
            self.group_invite_cb = None
            self.group_custom_packet_cb = None
            self.group_private_message_cb = None
            self.group_private_message_cb = None
            self.group_message_cb = None
            self.group_password_cb = None
            self.group_peer_limit_cb = None
            self.group_privacy_state_cb = None
            self.group_topic_cb = None
            self.group_peer_status_cb = None
            self.group_peer_name_cb = None
            self.group_peer_exit_cb = None
            self.group_peer_join_cb = None

            self.AV = ToxAV(self._tox_pointer)

    def __del__(self):
        del self.AV
        Tox.libtoxcore.tox_kill(self._tox_pointer)

    # -----------------------------------------------------------------------------------------------------------------
    # Startup options
    # -----------------------------------------------------------------------------------------------------------------

    @staticmethod
    def options_default(tox_options):
        """
        Initialises a Tox_Options object with the default options.

        The result of this function is independent of the original options. All values will be overwritten, no values
        will be read (so it is permissible to pass an uninitialised object).

        If options is NULL, this function has no effect.

        :param tox_options: A pointer to options object to be filled with default options.
        """
        Tox.libtoxcore.tox_options_default(tox_options)

    @staticmethod
    def options_new():
        """
        Allocates a new Tox_Options object and initialises it with the default options. This function can be used to
        preserve long term ABI compatibility by giving the responsibility of allocation and deallocation to the Tox
        library.

        Objects returned from this function must be freed using the tox_options_free function.

        :return: A pointer to new ToxOptions object with default options or raise MemoryError.
        """
        tox_err_options_new = c_int()
        f = Tox.libtoxcore.tox_options_new
        f.restype = POINTER(ToxOptions)
        result = f(byref(tox_err_options_new))
        tox_err_options_new = tox_err_options_new.value
        if tox_err_options_new == TOX_ERR_OPTIONS_NEW['OK']:
            return result
        elif tox_err_options_new == TOX_ERR_OPTIONS_NEW['MALLOC']:
            raise MemoryError('The function failed to allocate enough memory for the options struct.')

    @staticmethod
    def options_free(tox_options):
        """
        Releases all resources associated with an options objects.

        Passing a pointer that was not returned by tox_options_new results in undefined behaviour.

        :param tox_options: A pointer to new ToxOptions object
        """
        Tox.libtoxcore.tox_options_free(tox_options)

    # -----------------------------------------------------------------------------------------------------------------
    # Creation and destruction
    # -----------------------------------------------------------------------------------------------------------------

    def get_savedata_size(self):
        """
        Calculates the number of bytes required to store the tox instance with tox_get_savedata.
        This function cannot fail. The result is always greater than 0.

        :return: number of bytes
        """
        return Tox.libtoxcore.tox_get_savedata_size(self._tox_pointer)

    def get_savedata(self, savedata=None):
        """
        Store all information associated with the tox instance to a byte array.

        :param savedata: pointer (c_char_p) to a memory region large enough to store the tox instance data.
        Call tox_get_savedata_size to find the number of bytes required. If this parameter is None, this function
        allocates memory for the tox instance data.
        :return: pointer (c_char_p) to a memory region with the tox instance data
        """
        if savedata is None:
            savedata_size = self.get_savedata_size()
            savedata = create_string_buffer(savedata_size)
        Tox.libtoxcore.tox_get_savedata(self._tox_pointer, savedata)
        return savedata[:]

    # -----------------------------------------------------------------------------------------------------------------
    # Connection lifecycle and event loop
    # -----------------------------------------------------------------------------------------------------------------

    def bootstrap(self, address, port, public_key):
        """
        Sends a "get nodes" request to the given bootstrap node with IP, port, and public key to setup connections.

        This function will attempt to connect to the node using UDP. You must use this function even if
        Tox_Options.udp_enabled was set to false.

        :param address: The hostname or IP address (IPv4 or IPv6) of the node.
        :param port: The port on the host on which the bootstrap Tox instance is listening.
        :param public_key: The long term public key of the bootstrap node (TOX_PUBLIC_KEY_SIZE bytes).
        :return: True on success.
        """
        tox_err_bootstrap = c_int()
        result = Tox.libtoxcore.tox_bootstrap(self._tox_pointer, c_char_p(address), c_uint16(port),
                                              string_to_bin(public_key), byref(tox_err_bootstrap))
        tox_err_bootstrap = tox_err_bootstrap.value
        if tox_err_bootstrap == TOX_ERR_BOOTSTRAP['OK']:
            return bool(result)
        elif tox_err_bootstrap == TOX_ERR_BOOTSTRAP['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_bootstrap == TOX_ERR_BOOTSTRAP['BAD_HOST']:
            raise ArgumentError('The address could not be resolved to an IP '
                                'address, or the IP address passed was invalid.')
        elif tox_err_bootstrap == TOX_ERR_BOOTSTRAP['BAD_PORT']:
            raise ArgumentError('The port passed was invalid. The valid port range is (1, 65535).')

    def add_tcp_relay(self, address, port, public_key):
        """
        Adds additional host:port pair as TCP relay.

        This function can be used to initiate TCP connections to different ports on the same bootstrap node, or to add
         TCP relays without using them as bootstrap nodes.

        :param address: The hostname or IP address (IPv4 or IPv6) of the TCP relay.
        :param port: The port on the host on which the TCP relay is listening.
        :param public_key: The long term public key of the TCP relay (TOX_PUBLIC_KEY_SIZE bytes).
        :return: True on success.
        """
        tox_err_bootstrap = c_int()
        result = Tox.libtoxcore.tox_add_tcp_relay(self._tox_pointer, c_char_p(address), c_uint16(port),
                                                  string_to_bin(public_key), byref(tox_err_bootstrap))
        tox_err_bootstrap = tox_err_bootstrap.value
        if tox_err_bootstrap == TOX_ERR_BOOTSTRAP['OK']:
            return bool(result)
        elif tox_err_bootstrap == TOX_ERR_BOOTSTRAP['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_bootstrap == TOX_ERR_BOOTSTRAP['BAD_HOST']:
            raise ArgumentError('The address could not be resolved to an IP '
                                'address, or the IP address passed was invalid.')
        elif tox_err_bootstrap == TOX_ERR_BOOTSTRAP['BAD_PORT']:
            raise ArgumentError('The port passed was invalid. The valid port range is (1, 65535).')

    def self_get_connection_status(self):
        """
        Return whether we are connected to the DHT. The return value is equal to the last value received through the
        `self_connection_status` callback.

        :return: TOX_CONNECTION
        """
        return Tox.libtoxcore.tox_self_get_connection_status(self._tox_pointer)

    def callback_self_connection_status(self, callback):
        """
        Set the callback for the `self_connection_status` event. Pass None to unset.

        This event is triggered whenever there is a change in the DHT connection state. When disconnected, a client may
        choose to call tox_bootstrap again, to reconnect to the DHT. Note that this state may frequently change for
        short amounts of time. Clients should therefore not immediately bootstrap on receiving a disconnect.

        :param callback: Python function. Should take pointer (c_void_p) to Tox object,
        TOX_CONNECTION (c_int),
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_int, c_void_p)
        self.self_connection_status_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_self_connection_status(self._tox_pointer,
                                                           self.self_connection_status_cb)

    def iteration_interval(self):
        """
        Return the time in milliseconds before tox_iterate() should be called again for optimal performance.
        :return: time in milliseconds
        """
        return Tox.libtoxcore.tox_iteration_interval(self._tox_pointer)

    def iterate(self, user_data=None):
        """
        The main loop that needs to be run in intervals of tox_iteration_interval() milliseconds.
        """
        if user_data is not None:
            user_data = c_char_p(user_data)
        Tox.libtoxcore.tox_iterate(self._tox_pointer, user_data)

    # -----------------------------------------------------------------------------------------------------------------
    # Internal client information (Tox address/id)
    # -----------------------------------------------------------------------------------------------------------------

    def self_get_address(self, address=None):
        """
        Writes the Tox friend address of the client to a byte array. The address is not in human-readable format. If a
        client wants to display the address, formatting is required.

        :param address: pointer (c_char_p) to a memory region of at least TOX_ADDRESS_SIZE bytes. If this parameter is
        None, this function allocates memory for address.
        :return: Tox friend address
        """
        if address is None:
            address = create_string_buffer(TOX_ADDRESS_SIZE)
        Tox.libtoxcore.tox_self_get_address(self._tox_pointer, address)
        return bin_to_string(address, TOX_ADDRESS_SIZE)

    def self_set_nospam(self, nospam):
        """
        Set the 4-byte nospam part of the address.

        :param nospam: Any 32 bit unsigned integer.
        """
        Tox.libtoxcore.tox_self_set_nospam(self._tox_pointer, c_uint32(nospam))

    def self_get_nospam(self):
        """
        Get the 4-byte nospam part of the address.

        :return: nospam part of the address
        """
        return Tox.libtoxcore.tox_self_get_nospam(self._tox_pointer)

    def self_get_public_key(self, public_key=None):
        """
        Copy the Tox Public Key (long term) from the Tox object.

        :param public_key: A memory region of at least TOX_PUBLIC_KEY_SIZE bytes. If this parameter is NULL, this
        function allocates memory for Tox Public Key.
        :return: Tox Public Key
        """
        if public_key is None:
            public_key = create_string_buffer(TOX_PUBLIC_KEY_SIZE)
        Tox.libtoxcore.tox_self_get_public_key(self._tox_pointer, public_key)
        return bin_to_string(public_key, TOX_PUBLIC_KEY_SIZE)

    def self_get_secret_key(self, secret_key=None):
        """
        Copy the Tox Secret Key from the Tox object.

        :param secret_key: pointer (c_char_p) to a memory region of at least TOX_SECRET_KEY_SIZE bytes. If this
        parameter is NULL, this function allocates memory for Tox Secret Key.
        :return: Tox Secret Key
        """
        if secret_key is None:
            secret_key = create_string_buffer(TOX_SECRET_KEY_SIZE)
        Tox.libtoxcore.tox_self_get_secret_key(self._tox_pointer, secret_key)
        return bin_to_string(secret_key, TOX_SECRET_KEY_SIZE)

    # -----------------------------------------------------------------------------------------------------------------
    # User-visible client information (nickname/status)
    # -----------------------------------------------------------------------------------------------------------------

    def self_set_name(self, name):
        """
        Set the nickname for the Tox client.

        Nickname length cannot exceed TOX_MAX_NAME_LENGTH. If length is 0, the name parameter is ignored
        (it can be None), and the nickname is set back to empty.
        :param name: New nickname.
        :return: True on success.
        """
        tox_err_set_info = c_int()
        name = bytes(name, 'utf-8')
        result = Tox.libtoxcore.tox_self_set_name(self._tox_pointer, c_char_p(name),
                                                  c_size_t(len(name)), byref(tox_err_set_info))
        tox_err_set_info = tox_err_set_info.value
        if tox_err_set_info == TOX_ERR_SET_INFO['OK']:
            return bool(result)
        elif tox_err_set_info == TOX_ERR_SET_INFO['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_set_info == TOX_ERR_SET_INFO['TOO_LONG']:
            raise ArgumentError('Information length exceeded maximum permissible size.')

    def self_get_name_size(self):
        """
        Return the length of the current nickname as passed to tox_self_set_name.

        If no nickname was set before calling this function, the name is empty, and this function returns 0.

        :return: length of the current nickname
        """
        return Tox.libtoxcore.tox_self_get_name_size(self._tox_pointer)

    def self_get_name(self, name=None):
        """
        Write the nickname set by tox_self_set_name to a byte array.

        If no nickname was set before calling this function, the name is empty, and this function has no effect.

        Call tox_self_get_name_size to find out how much memory to allocate for the result.

        :param name: pointer (c_char_p) to a memory region location large enough to hold the nickname. If this parameter
        is NULL, the function allocates memory for the nickname.
        :return: nickname
        """
        if name is None:
            name = create_string_buffer(self.self_get_name_size())
        Tox.libtoxcore.tox_self_get_name(self._tox_pointer, name)
        return str(name.value, 'utf-8')

    def self_set_status_message(self, status_message):
        """
        Set the client's status message.

        Status message length cannot exceed TOX_MAX_STATUS_MESSAGE_LENGTH. If length is 0, the status parameter is
        ignored, and the user status is set back to empty.

        :param status_message: new status message
        :return: True on success.
        """
        tox_err_set_info = c_int()
        status_message = bytes(status_message, 'utf-8')
        result = Tox.libtoxcore.tox_self_set_status_message(self._tox_pointer, c_char_p(status_message),
                                                            c_size_t(len(status_message)), byref(tox_err_set_info))
        tox_err_set_info = tox_err_set_info.value
        if tox_err_set_info == TOX_ERR_SET_INFO['OK']:
            return bool(result)
        elif tox_err_set_info == TOX_ERR_SET_INFO['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_set_info == TOX_ERR_SET_INFO['TOO_LONG']:
            raise ArgumentError('Information length exceeded maximum permissible size.')

    def self_get_status_message_size(self):
        """
        Return the length of the current status message as passed to tox_self_set_status_message.

        If no status message was set before calling this function, the status is empty, and this function returns 0.

        :return: length of the current status message
        """
        return Tox.libtoxcore.tox_self_get_status_message_size(self._tox_pointer)

    def self_get_status_message(self, status_message=None):
        """
        Write the status message set by tox_self_set_status_message to a byte array.

        If no status message was set before calling this function, the status is empty, and this function has no effect.

        Call tox_self_get_status_message_size to find out how much memory to allocate for the result.

        :param status_message: pointer (c_char_p) to a valid memory location large enough to hold the status message.
        If this parameter is None, the function allocates memory for the status message.
        :return: status message
        """
        if status_message is None:
            status_message = create_string_buffer(self.self_get_status_message_size())
        Tox.libtoxcore.tox_self_get_status_message(self._tox_pointer, status_message)
        return str(status_message.value, 'utf-8')

    def self_set_status(self, status):
        """
        Set the client's user status.

        :param status: One of the user statuses listed in the enumeration TOX_USER_STATUS.
        """
        Tox.libtoxcore.tox_self_set_status(self._tox_pointer, c_int(status))

    def self_get_status(self):
        """
        Returns the client's user status.

        :return: client's user status
        """
        return Tox.libtoxcore.tox_self_get_status(self._tox_pointer)

    # -----------------------------------------------------------------------------------------------------------------
    # Friend list management
    # -----------------------------------------------------------------------------------------------------------------

    def friend_add(self, address, message):
        """
        Add a friend to the friend list and send a friend request.

        A friend request message must be at least 1 byte long and at most TOX_MAX_FRIEND_REQUEST_LENGTH.

        Friend numbers are unique identifiers used in all functions that operate on friends. Once added, a friend number
        is stable for the lifetime of the Tox object. After saving the state and reloading it, the friend numbers may
        not be the same as before. Deleting a friend creates a gap in the friend number set, which is filled by the next
        adding of a friend. Any pattern in friend numbers should not be relied on.

        If more than INT32_MAX friends are added, this function causes undefined behaviour.

        :param address: The address of the friend (returned by tox_self_get_address of the friend you wish to add) it
        must be TOX_ADDRESS_SIZE bytes.
        :param message: The message that will be sent along with the friend request.
        :return: the friend number on success, UINT32_MAX on failure.
        """
        tox_err_friend_add = c_int()
        result = Tox.libtoxcore.tox_friend_add(self._tox_pointer, string_to_bin(address), c_char_p(message),
                                               c_size_t(len(message)), byref(tox_err_friend_add))
        tox_err_friend_add = tox_err_friend_add.value
        if tox_err_friend_add == TOX_ERR_FRIEND_ADD['OK']:
            return result
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['TOO_LONG']:
            raise ArgumentError('The length of the friend request message exceeded TOX_MAX_FRIEND_REQUEST_LENGTH.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['NO_MESSAGE']:
            raise ArgumentError('The friend request message was empty. This, and the TOO_LONG code will never be'
                                ' returned from tox_friend_add_norequest.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['OWN_KEY']:
            raise ArgumentError('The friend address belongs to the sending client.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['ALREADY_SENT']:
            raise ArgumentError('A friend request has already been sent, or the address belongs to a friend that is'
                                ' already on the friend list.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['BAD_CHECKSUM']:
            raise ArgumentError('The friend address checksum failed.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['SET_NEW_NOSPAM']:
            raise ArgumentError('The friend was already there, but the nospam value was different.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['MALLOC']:
            raise MemoryError('A memory allocation failed when trying to increase the friend list size.')

    def friend_add_norequest(self, public_key):
        """
        Add a friend without sending a friend request.

        This function is used to add a friend in response to a friend request. If the client receives a friend request,
        it can be reasonably sure that the other client added this client as a friend, eliminating the need for a friend
        request.

        This function is also useful in a situation where both instances are controlled by the same entity, so that this
        entity can perform the mutual friend adding. In this case, there is no need for a friend request, either.

        :param public_key: A byte array of length TOX_PUBLIC_KEY_SIZE containing the Public Key (not the Address) of the
        friend to add.
        :return: the friend number on success, UINT32_MAX on failure.
        """
        tox_err_friend_add = c_int()
        result = Tox.libtoxcore.tox_friend_add_norequest(self._tox_pointer, string_to_bin(public_key),
                                                         byref(tox_err_friend_add))
        tox_err_friend_add = tox_err_friend_add.value
        if tox_err_friend_add == TOX_ERR_FRIEND_ADD['OK']:
            return result
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['TOO_LONG']:
            raise ArgumentError('The length of the friend request message exceeded TOX_MAX_FRIEND_REQUEST_LENGTH.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['NO_MESSAGE']:
            raise ArgumentError('The friend request message was empty. This, and the TOO_LONG code will never be'
                                ' returned from tox_friend_add_norequest.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['OWN_KEY']:
            raise ArgumentError('The friend address belongs to the sending client.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['ALREADY_SENT']:
            raise ArgumentError('A friend request has already been sent, or the address belongs to a friend that is'
                                ' already on the friend list.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['BAD_CHECKSUM']:
            raise ArgumentError('The friend address checksum failed.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['SET_NEW_NOSPAM']:
            raise ArgumentError('The friend was already there, but the nospam value was different.')
        elif tox_err_friend_add == TOX_ERR_FRIEND_ADD['MALLOC']:
            raise MemoryError('A memory allocation failed when trying to increase the friend list size.')

    def friend_delete(self, friend_number):
        """
        Remove a friend from the friend list.

        This does not notify the friend of their deletion. After calling this function, this client will appear offline
        to the friend and no communication can occur between the two.

        :param friend_number: Friend number for the friend to be deleted.
        :return: True on success.
        """
        tox_err_friend_delete = c_int()
        result = Tox.libtoxcore.tox_friend_delete(self._tox_pointer, c_uint32(friend_number),
                                                  byref(tox_err_friend_delete))
        tox_err_friend_delete = tox_err_friend_delete.value
        if tox_err_friend_delete == TOX_ERR_FRIEND_DELETE['OK']:
            return bool(result)
        elif tox_err_friend_delete == TOX_ERR_FRIEND_DELETE['FRIEND_NOT_FOUND']:
            raise ArgumentError('There was no friend with the given friend number. No friends were deleted.')

    # -----------------------------------------------------------------------------------------------------------------
    # Friend list queries
    # -----------------------------------------------------------------------------------------------------------------

    def friend_by_public_key(self, public_key):
        """
        Return the friend number associated with that Public Key.

        :param public_key: A byte array containing the Public Key.
        :return: friend number
        """
        tox_err_friend_by_public_key = c_int()
        result = Tox.libtoxcore.tox_friend_by_public_key(self._tox_pointer, string_to_bin(public_key),
                                                         byref(tox_err_friend_by_public_key))
        tox_err_friend_by_public_key = tox_err_friend_by_public_key.value
        if tox_err_friend_by_public_key == TOX_ERR_FRIEND_BY_PUBLIC_KEY['OK']:
            return result
        elif tox_err_friend_by_public_key == TOX_ERR_FRIEND_BY_PUBLIC_KEY['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_friend_by_public_key == TOX_ERR_FRIEND_BY_PUBLIC_KEY['NOT_FOUND']:
            raise ArgumentError('No friend with the given Public Key exists on the friend list.')

    def friend_exists(self, friend_number):
        """
        Checks if a friend with the given friend number exists and returns true if it does.
        """
        return bool(Tox.libtoxcore.tox_friend_exists(self._tox_pointer, c_uint32(friend_number)))

    def self_get_friend_list_size(self):
        """
        Return the number of friends on the friend list.

        This function can be used to determine how much memory to allocate for tox_self_get_friend_list.

        :return: number of friends
        """
        return Tox.libtoxcore.tox_self_get_friend_list_size(self._tox_pointer)

    def self_get_friend_list(self, friend_list=None):
        """
        Copy a list of valid friend numbers into an array.

        Call tox_self_get_friend_list_size to determine the number of elements to allocate.

        :param friend_list: pointer (c_char_p) to a memory region with enough space to hold the friend list. If this
        parameter is None, this function allocates memory for the friend list.
        :return: friend list
        """
        friend_list_size = self.self_get_friend_list_size()
        if friend_list is None:
            friend_list = create_string_buffer(sizeof(c_uint32) * friend_list_size)
            friend_list = POINTER(c_uint32)(friend_list)
        Tox.libtoxcore.tox_self_get_friend_list(self._tox_pointer, friend_list)
        return friend_list[0:friend_list_size]

    def friend_get_public_key(self, friend_number, public_key=None):
        """
        Copies the Public Key associated with a given friend number to a byte array.

        :param friend_number: The friend number you want the Public Key of.
        :param public_key: pointer (c_char_p) to a memory region of at least TOX_PUBLIC_KEY_SIZE bytes. If this
        parameter is None, this function allocates memory for Tox Public Key.
        :return: Tox Public Key
        """
        if public_key is None:
            public_key = create_string_buffer(TOX_PUBLIC_KEY_SIZE)
        tox_err_friend_get_public_key = c_int()
        Tox.libtoxcore.tox_friend_get_public_key(self._tox_pointer, c_uint32(friend_number), public_key,
                                                 byref(tox_err_friend_get_public_key))
        tox_err_friend_get_public_key = tox_err_friend_get_public_key.value
        if tox_err_friend_get_public_key == TOX_ERR_FRIEND_GET_PUBLIC_KEY['OK']:
            return bin_to_string(public_key, TOX_PUBLIC_KEY_SIZE)
        elif tox_err_friend_get_public_key == TOX_ERR_FRIEND_GET_PUBLIC_KEY['FRIEND_NOT_FOUND']:
            raise ArgumentError('No friend with the given number exists on the friend list.')

    def friend_get_last_online(self, friend_number):
        """
        Return a unix-time timestamp of the last time the friend associated with a given friend number was seen online.
        This function will return UINT64_MAX on error.

        :param friend_number: The friend number you want to query.
        :return: unix-time timestamp
        """
        tox_err_last_online = c_int()
        result = Tox.libtoxcore.tox_friend_get_last_online(self._tox_pointer, c_uint32(friend_number),
                                                           byref(tox_err_last_online))
        tox_err_last_online = tox_err_last_online.value
        if tox_err_last_online == TOX_ERR_FRIEND_GET_LAST_ONLINE['OK']:
            return result
        elif tox_err_last_online == TOX_ERR_FRIEND_GET_LAST_ONLINE['FRIEND_NOT_FOUND']:
            raise ArgumentError('No friend with the given number exists on the friend list.')

    # -----------------------------------------------------------------------------------------------------------------
    # Friend-specific state queries (can also be received through callbacks)
    # -----------------------------------------------------------------------------------------------------------------

    def friend_get_name_size(self, friend_number):
        """
        Return the length of the friend's name. If the friend number is invalid, the return value is unspecified.

        The return value is equal to the `length` argument received by the last `friend_name` callback.
        """
        tox_err_friend_query = c_int()
        result = Tox.libtoxcore.tox_friend_get_name_size(self._tox_pointer, c_uint32(friend_number),
                                                         byref(tox_err_friend_query))
        tox_err_friend_query = tox_err_friend_query.value
        if tox_err_friend_query == TOX_ERR_FRIEND_QUERY['OK']:
            return result
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['NULL']:
            raise ArgumentError('The pointer parameter for storing the query result (name, message) was NULL. Unlike'
                                ' the `_self_` variants of these functions, which have no effect when a parameter is'
                                ' NULL, these functions return an error in that case.')
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number did not designate a valid friend.')

    def friend_get_name(self, friend_number, name=None):
        """
        Write the name of the friend designated by the given friend number to a byte array.

        Call tox_friend_get_name_size to determine the allocation size for the `name` parameter.

        The data written to `name` is equal to the data received by the last `friend_name` callback.

        :param friend_number: number of friend
        :param name: pointer (c_char_p) to a valid memory region large enough to store the friend's name.
        :return: name of the friend
        """
        if name is None:
            name = create_string_buffer(self.friend_get_name_size(friend_number))
        tox_err_friend_query = c_int()
        Tox.libtoxcore.tox_friend_get_name(self._tox_pointer, c_uint32(friend_number), name,
                                           byref(tox_err_friend_query))
        tox_err_friend_query = tox_err_friend_query.value
        if tox_err_friend_query == TOX_ERR_FRIEND_QUERY['OK']:
            return str(name.value, 'utf-8')
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['NULL']:
            raise ArgumentError('The pointer parameter for storing the query result (name, message) was NULL. Unlike'
                                ' the `_self_` variants of these functions, which have no effect when a parameter is'
                                ' NULL, these functions return an error in that case.')
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number did not designate a valid friend.')

    def callback_friend_name(self, callback):
        """
        Set the callback for the `friend_name` event. Pass None to unset.

        This event is triggered when a friend changes their name.

        :param callback: Python function. Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the friend whose name changed,
        A byte array (c_char_p) containing the same data as tox_friend_get_name would write to its `name` parameter,
        A value (c_size_t) equal to the return value of tox_friend_get_name_size,
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_char_p, c_size_t, c_void_p)
        self.friend_name_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_friend_name(self._tox_pointer, self.friend_name_cb)

    def friend_get_status_message_size(self, friend_number):
        """
        Return the length of the friend's status message. If the friend number is invalid, the return value is SIZE_MAX.

        :return: length of the friend's status message
        """
        tox_err_friend_query = c_int()
        result = Tox.libtoxcore.tox_friend_get_status_message_size(self._tox_pointer, c_uint32(friend_number),
                                                                   byref(tox_err_friend_query))
        tox_err_friend_query = tox_err_friend_query.value
        if tox_err_friend_query == TOX_ERR_FRIEND_QUERY['OK']:
            return result
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['NULL']:
            raise ArgumentError('The pointer parameter for storing the query result (name, message) was NULL. Unlike'
                                ' the `_self_` variants of these functions, which have no effect when a parameter is'
                                ' NULL, these functions return an error in that case.')
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number did not designate a valid friend.')

    def friend_get_status_message(self, friend_number, status_message=None):
        """
        Write the status message of the friend designated by the given friend number to a byte array.

        Call tox_friend_get_status_message_size to determine the allocation size for the `status_name` parameter.

        The data written to `status_message` is equal to the data received by the last `friend_status_message` callback.

        :param friend_number:
        :param status_message: pointer (c_char_p) to a valid memory region large enough to store the friend's status
        message.
        :return: status message of the friend
        """
        if status_message is None:
            status_message = create_string_buffer(self.friend_get_status_message_size(friend_number))
        tox_err_friend_query = c_int()
        Tox.libtoxcore.tox_friend_get_status_message(self._tox_pointer, c_uint32(friend_number), status_message,
                                                     byref(tox_err_friend_query))
        tox_err_friend_query = tox_err_friend_query.value
        if tox_err_friend_query == TOX_ERR_FRIEND_QUERY['OK']:
            return str(status_message.value, 'utf-8')
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['NULL']:
            raise ArgumentError('The pointer parameter for storing the query result (name, message) was NULL. Unlike'
                                ' the `_self_` variants of these functions, which have no effect when a parameter is'
                                ' NULL, these functions return an error in that case.')
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number did not designate a valid friend.')

    def callback_friend_status_message(self, callback):
        """
        Set the callback for the `friend_status_message` event. Pass NULL to unset.

        This event is triggered when a friend changes their status message.

        :param callback: Python function. Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the friend whose status message changed,
        A byte array (c_char_p) containing the same data as tox_friend_get_status_message would write to its
        `status_message` parameter,
        A value (c_size_t) equal to the return value of tox_friend_get_status_message_size,
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_char_p, c_size_t, c_void_p)
        self.friend_status_message_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_friend_status_message(self._tox_pointer,
                                                          self.friend_status_message_cb)

    def friend_get_status(self, friend_number):
        """
        Return the friend's user status (away/busy/...). If the friend number is invalid, the return value is
        unspecified.

        The status returned is equal to the last status received through the `friend_status` callback.

        :return: TOX_USER_STATUS
        """
        tox_err_friend_query = c_int()
        result = Tox.libtoxcore.tox_friend_get_status(self._tox_pointer, c_uint32(friend_number),
                                                      byref(tox_err_friend_query))
        tox_err_friend_query = tox_err_friend_query.value
        if tox_err_friend_query == TOX_ERR_FRIEND_QUERY['OK']:
            return result
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['NULL']:
            raise ArgumentError('The pointer parameter for storing the query result (name, message) was NULL. Unlike'
                                ' the `_self_` variants of these functions, which have no effect when a parameter is'
                                ' NULL, these functions return an error in that case.')
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number did not designate a valid friend.')

    def callback_friend_status(self, callback):
        """
        Set the callback for the `friend_status` event. Pass None to unset.

        This event is triggered when a friend changes their user status.

        :param callback: Python function. Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the friend whose user status changed,
        The new user status (TOX_USER_STATUS),
        pointer (c_void_p) to user_data
        :param user_data: pointer (c_void_p) to user data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_int, c_void_p)
        self.friend_status_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_friend_status(self._tox_pointer, self.friend_status_cb)

    def friend_get_connection_status(self, friend_number):
        """
        Check whether a friend is currently connected to this client.

        The result of this function is equal to the last value received by the `friend_connection_status` callback.

        :param friend_number: The friend number for which to query the connection status.
        :return: the friend's connection status (TOX_CONNECTION) as it was received through the
        `friend_connection_status` event.
        """
        tox_err_friend_query = c_int()
        result = Tox.libtoxcore.tox_friend_get_connection_status(self._tox_pointer, c_uint32(friend_number),
                                                                 byref(tox_err_friend_query))
        tox_err_friend_query = tox_err_friend_query.value
        if tox_err_friend_query == TOX_ERR_FRIEND_QUERY['OK']:
            return result
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['NULL']:
            raise ArgumentError('The pointer parameter for storing the query result (name, message) was NULL. Unlike'
                                ' the `_self_` variants of these functions, which have no effect when a parameter is'
                                ' NULL, these functions return an error in that case.')
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number did not designate a valid friend.')

    def callback_friend_connection_status(self, callback):
        """
        Set the callback for the `friend_connection_status` event. Pass NULL to unset.

        This event is triggered when a friend goes offline after having been online, or when a friend goes online.

        This callback is not called when adding friends. It is assumed that when adding friends, their connection status
        is initially offline.

        :param callback: Python function. Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the friend whose connection status changed,
        The result of calling tox_friend_get_connection_status (TOX_CONNECTION) on the passed friend_number,
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_int, c_void_p)
        self.friend_connection_status_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_friend_connection_status(self._tox_pointer,
                                                             self.friend_connection_status_cb)

    def friend_get_typing(self, friend_number):
        """
        Check whether a friend is currently typing a message.

        :param friend_number: The friend number for which to query the typing status.
        :return: true if the friend is typing.
        """
        tox_err_friend_query = c_int()
        result = Tox.libtoxcore.tox_friend_get_typing(self._tox_pointer, c_uint32(friend_number),
                                                      byref(tox_err_friend_query))
        tox_err_friend_query = tox_err_friend_query.value
        if tox_err_friend_query == TOX_ERR_FRIEND_QUERY['OK']:
            return bool(result)
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['NULL']:
            raise ArgumentError('The pointer parameter for storing the query result (name, message) was NULL. Unlike'
                                ' the `_self_` variants of these functions, which have no effect when a parameter is'
                                ' NULL, these functions return an error in that case.')
        elif tox_err_friend_query == TOX_ERR_FRIEND_QUERY['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number did not designate a valid friend.')

    def callback_friend_typing(self, callback):
        """
        Set the callback for the `friend_typing` event. Pass NULL to unset.

        This event is triggered when a friend starts or stops typing.

        :param callback: Python function. Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the friend who started or stopped typing,
        The result of calling tox_friend_get_typing (c_bool) on the passed friend_number,
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_bool, c_void_p)
        self.friend_typing_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_friend_typing(self._tox_pointer, self.friend_typing_cb)

    # -----------------------------------------------------------------------------------------------------------------
    # Sending private messages
    # -----------------------------------------------------------------------------------------------------------------

    def self_set_typing(self, friend_number, typing):
        """
        Set the client's typing status for a friend.

        The client is responsible for turning it on or off.

        :param friend_number: The friend to which the client is typing a message.
        :param typing: The typing status. True means the client is typing.
        :return: True on success.
        """
        tox_err_set_typing = c_int()
        result = Tox.libtoxcore.tox_self_set_typing(self._tox_pointer, c_uint32(friend_number),
                                                    c_bool(typing), byref(tox_err_set_typing))
        tox_err_set_typing = tox_err_set_typing.value
        if tox_err_set_typing == TOX_ERR_SET_TYPING['OK']:
            return bool(result)
        elif tox_err_set_typing == TOX_ERR_SET_TYPING['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend number did not designate a valid friend.')

    def friend_send_message(self, friend_number, message_type, message):
        """
        Send a text chat message to an online friend.

        This function creates a chat message packet and pushes it into the send queue.

        The message length may not exceed TOX_MAX_MESSAGE_LENGTH. Larger messages must be split by the client and sent
        as separate messages. Other clients can then reassemble the fragments. Messages may not be empty.

        The return value of this function is the message ID. If a read receipt is received, the triggered
        `friend_read_receipt` event will be passed this message ID.

        Message IDs are unique per friend. The first message ID is 0. Message IDs are incremented by 1 each time a
        message is sent. If UINT32_MAX messages were sent, the next message ID is 0.

        :param friend_number: The friend number of the friend to send the message to.
        :param message_type: Message type (TOX_MESSAGE_TYPE).
        :param message: A non-None message text.
        :return: message ID
        """
        tox_err_friend_send_message = c_int()
        result = Tox.libtoxcore.tox_friend_send_message(self._tox_pointer, c_uint32(friend_number),
                                                        c_int(message_type), c_char_p(message), c_size_t(len(message)),
                                                        byref(tox_err_friend_send_message))
        tox_err_friend_send_message = tox_err_friend_send_message.value
        if tox_err_friend_send_message == TOX_ERR_FRIEND_SEND_MESSAGE['OK']:
            return result
        elif tox_err_friend_send_message == TOX_ERR_FRIEND_SEND_MESSAGE['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_friend_send_message == TOX_ERR_FRIEND_SEND_MESSAGE['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend number did not designate a valid friend.')
        elif tox_err_friend_send_message == TOX_ERR_FRIEND_SEND_MESSAGE['FRIEND_NOT_CONNECTED']:
            raise ArgumentError('This client is currently not connected to the friend.')
        elif tox_err_friend_send_message == TOX_ERR_FRIEND_SEND_MESSAGE['SENDQ']:
            raise MemoryError('An allocation error occurred while increasing the send queue size.')
        elif tox_err_friend_send_message == TOX_ERR_FRIEND_SEND_MESSAGE['TOO_LONG']:
            raise ArgumentError('Message length exceeded TOX_MAX_MESSAGE_LENGTH.')
        elif tox_err_friend_send_message == TOX_ERR_FRIEND_SEND_MESSAGE['EMPTY']:
            raise ArgumentError('Attempted to send a zero-length message.')

    def callback_friend_read_receipt(self, callback):
        """
        Set the callback for the `friend_read_receipt` event. Pass None to unset.

        This event is triggered when the friend receives the message sent with tox_friend_send_message with the
        corresponding message ID.

        :param callback: Python function. Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the friend who received the message,
        The message ID (c_uint32) as returned from tox_friend_send_message corresponding to the message sent,
        pointer (c_void_p) to user_data
        :param user_data: pointer (c_void_p) to user data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_void_p)
        self.friend_read_receipt_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_friend_read_receipt(self._tox_pointer,
                                                        self.friend_read_receipt_cb)

    # -----------------------------------------------------------------------------------------------------------------
    # Receiving private messages and friend requests
    # -----------------------------------------------------------------------------------------------------------------

    def callback_friend_request(self, callback):
        """
        Set the callback for the `friend_request` event. Pass None to unset.

        This event is triggered when a friend request is received.

        :param callback: Python function. Should take pointer (c_void_p) to Tox object,
        The Public Key (c_uint8 array) of the user who sent the friend request,
        The message (c_char_p) they sent along with the request,
        The size (c_size_t) of the message byte array,
        pointer (c_void_p) to user_data
        :param user_data: pointer (c_void_p) to user data
        """
        c_callback = CFUNCTYPE(None, c_void_p, POINTER(c_uint8), c_char_p, c_size_t, c_void_p)
        self.friend_request_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_friend_request(self._tox_pointer, self.friend_request_cb)

    def callback_friend_message(self, callback):
        """
        Set the callback for the `friend_message` event. Pass None to unset.

        This event is triggered when a message from a friend is received.

        :param callback: Python function. Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the friend who sent the message,
        Message type (TOX_MESSAGE_TYPE),
        The message data (c_char_p) they sent,
        The size (c_size_t) of the message byte array.
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_int, c_char_p, c_size_t, c_void_p)
        self.friend_message_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_friend_message(self._tox_pointer, self.friend_message_cb)

    # -----------------------------------------------------------------------------------------------------------------
    # File transmission: common between sending and receiving
    # -----------------------------------------------------------------------------------------------------------------

    @staticmethod
    def hash(data, hash=None):
        """
        Generates a cryptographic hash of the given data.

        This function may be used by clients for any purpose, but is provided primarily for validating cached avatars.
        This use is highly recommended to avoid unnecessary avatar updates.

        If hash is NULL or data is NULL while length is not 0 the function returns false, otherwise it returns true.

        This function is a wrapper to internal message-digest functions.

        :param hash: A valid memory location the hash data. It must be at least TOX_HASH_LENGTH bytes in size.
        :param data: Data to be hashed or NULL.
        :return: true if hash was not NULL.
        """
        if hash is None:
            hash = create_string_buffer(TOX_HASH_LENGTH)
        Tox.libtoxcore.tox_hash(hash, c_char_p(data), len(data))
        return bin_to_string(hash, TOX_HASH_LENGTH)

    def file_control(self, friend_number, file_number, control):
        """
        Sends a file control command to a friend for a given file transfer.

        :param friend_number: The friend number of the friend the file is being transferred to or received from.
        :param file_number: The friend-specific identifier for the file transfer.
        :param control: The control (TOX_FILE_CONTROL) command to send.
        :return: True on success.
        """
        tox_err_file_control = c_int()
        result = Tox.libtoxcore.tox_file_control(self._tox_pointer, c_uint32(friend_number), c_uint32(file_number),
                                                 c_int(control), byref(tox_err_file_control))
        tox_err_file_control = tox_err_file_control.value
        if tox_err_file_control == TOX_ERR_FILE_CONTROL['OK']:
            return bool(result)
        elif tox_err_file_control == TOX_ERR_FILE_CONTROL['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number passed did not designate a valid friend.')
        elif tox_err_file_control == TOX_ERR_FILE_CONTROL['FRIEND_NOT_CONNECTED']:
            raise ArgumentError('This client is currently not connected to the friend.')
        elif tox_err_file_control == TOX_ERR_FILE_CONTROL['NOT_FOUND']:
            raise ArgumentError('No file transfer with the given file number was found for the given friend.')
        elif tox_err_file_control == TOX_ERR_FILE_CONTROL['NOT_PAUSED']:
            raise RuntimeError('A RESUME control was sent, but the file transfer is running normally.')
        elif tox_err_file_control == TOX_ERR_FILE_CONTROL['DENIED']:
            raise RuntimeError('A RESUME control was sent, but the file transfer was paused by the other party. Only '
                               'the party that paused the transfer can resume it.')
        elif tox_err_file_control == TOX_ERR_FILE_CONTROL['ALREADY_PAUSED']:
            raise RuntimeError('A PAUSE control was sent, but the file transfer was already paused.')
        elif tox_err_file_control == TOX_ERR_FILE_CONTROL['SENDQ']:
            raise RuntimeError('Packet queue is full.')

    def callback_file_recv_control(self, callback):
        """
        Set the callback for the `file_recv_control` event. Pass NULL to unset.

        This event is triggered when a file control command is received from a friend.

        :param callback: Python function.
        When receiving TOX_FILE_CONTROL_CANCEL, the client should release the resources associated with the file number
        and consider the transfer failed.

        Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the friend who is sending the file.
        The friend-specific file number (c_uint32) the data received is associated with.
        The file control (TOX_FILE_CONTROL) command received.
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_int, c_void_p)
        self.file_recv_control_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_file_recv_control(self._tox_pointer,
                                                      self.file_recv_control_cb)

    def file_seek(self, friend_number, file_number, position):
        """
        Sends a file seek control command to a friend for a given file transfer.

        This function can only be called to resume a file transfer right before TOX_FILE_CONTROL_RESUME is sent.

        :param friend_number: The friend number of the friend the file is being received from.
        :param file_number: The friend-specific identifier for the file transfer.
        :param position: The position that the file should be seeked to.
        :return: True on success.
        """
        tox_err_file_seek = c_int()
        result = Tox.libtoxcore.tox_file_control(self._tox_pointer, c_uint32(friend_number), c_uint32(file_number),
                                                 c_uint64(position), byref(tox_err_file_seek))
        tox_err_file_seek = tox_err_file_seek.value
        if tox_err_file_seek == TOX_ERR_FILE_SEEK['OK']:
            return bool(result)
        elif tox_err_file_seek == TOX_ERR_FILE_SEEK['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number passed did not designate a valid friend.')
        elif tox_err_file_seek == TOX_ERR_FILE_SEEK['FRIEND_NOT_CONNECTED']:
            raise ArgumentError('This client is currently not connected to the friend.')
        elif tox_err_file_seek == TOX_ERR_FILE_SEEK['NOT_FOUND']:
            raise ArgumentError('No file transfer with the given file number was found for the given friend.')
        elif tox_err_file_seek == TOX_ERR_FILE_SEEK['SEEK_DENIED']:
            raise IOError('File was not in a state where it could be seeked.')
        elif tox_err_file_seek == TOX_ERR_FILE_SEEK['INVALID_POSITION']:
            raise ArgumentError('Seek position was invalid')
        elif tox_err_file_seek == TOX_ERR_FILE_SEEK['SENDQ']:
            raise RuntimeError('Packet queue is full.')

    def file_get_file_id(self, friend_number, file_number, file_id=None):
        """
        Copy the file id associated to the file transfer to a byte array.

        :param friend_number: The friend number of the friend the file is being transferred to or received from.
        :param file_number: The friend-specific identifier for the file transfer.
        :param file_id: A pointer (c_char_p) to memory region of at least TOX_FILE_ID_LENGTH bytes. If this parameter is
        None, this function has no effect.
        :return: file id.
        """
        if file_id is None:
            file_id = create_string_buffer(TOX_FILE_ID_LENGTH)
        tox_err_file_get = c_int()
        Tox.libtoxcore.tox_file_get_file_id(self._tox_pointer, c_uint32(friend_number), c_uint32(file_number), file_id,
                                            byref(tox_err_file_get))
        tox_err_file_get = tox_err_file_get.value
        if tox_err_file_get == TOX_ERR_FILE_GET['OK']:
            return bin_to_string(file_id, TOX_FILE_ID_LENGTH)
        elif tox_err_file_get == TOX_ERR_FILE_GET['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_file_get == TOX_ERR_FILE_GET['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number passed did not designate a valid friend.')
        elif tox_err_file_get == TOX_ERR_FILE_GET['NOT_FOUND']:
            raise ArgumentError('No file transfer with the given file number was found for the given friend.')

    # -----------------------------------------------------------------------------------------------------------------
    # File transmission: sending
    # -----------------------------------------------------------------------------------------------------------------

    def file_send(self, friend_number, kind, file_size, file_id, filename):
        """
        Send a file transmission request.

        Maximum filename length is TOX_MAX_FILENAME_LENGTH bytes. The filename should generally just be a file name, not
        a path with directory names.

        If a non-UINT64_MAX file size is provided, it can be used by both sides to determine the sending progress. File
        size can be set to UINT64_MAX for streaming data of unknown size.

        File transmission occurs in chunks, which are requested through the `file_chunk_request` event.

        When a friend goes offline, all file transfers associated with the friend are purged from core.

        If the file contents change during a transfer, the behaviour is unspecified in general. What will actually
        happen depends on the mode in which the file was modified and how the client determines the file size.

        - If the file size was increased
            - and sending mode was streaming (file_size = UINT64_MAX), the behaviour will be as expected.
            - and sending mode was file (file_size != UINT64_MAX), the file_chunk_request callback will receive length =
            0 when Core thinks the file transfer has finished. If the client remembers the file size as it was when
            sending the request, it will terminate the transfer normally. If the client re-reads the size, it will think
            the friend cancelled the transfer.
        - If the file size was decreased
            - and sending mode was streaming, the behaviour is as expected.
            - and sending mode was file, the callback will return 0 at the new (earlier) end-of-file, signalling to the
            friend that the transfer was cancelled.
        - If the file contents were modified
            - at a position before the current read, the two files (local and remote) will differ after the transfer
            terminates.
            - at a position after the current read, the file transfer will succeed as expected.
            - In either case, both sides will regard the transfer as complete and successful.

        :param friend_number: The friend number of the friend the file send request should be sent to.
        :param kind: The meaning of the file to be sent.
        :param file_size: Size in bytes of the file the client wants to send, UINT64_MAX if unknown or streaming.
        :param file_id: A file identifier of length TOX_FILE_ID_LENGTH that can be used to uniquely identify file
        transfers across core restarts. If NULL, a random one will be generated by core. It can then be obtained by
        using tox_file_get_file_id().
        :param filename: Name of the file. Does not need to be the actual name. This name will be sent along with the
        file send request.
        :return: A file number used as an identifier in subsequent callbacks. This number is per friend. File numbers
        are reused after a transfer terminates. On failure, this function returns UINT32_MAX. Any pattern in file
        numbers should not be relied on.
        """
        tox_err_file_send = c_int()
        result = self.libtoxcore.tox_file_send(self._tox_pointer, c_uint32(friend_number), c_uint32(kind),
                                               c_uint64(file_size),
                                               string_to_bin(file_id),
                                               c_char_p(filename),
                                               c_size_t(len(filename)), byref(tox_err_file_send))
        tox_err_file_send = tox_err_file_send.value
        if tox_err_file_send == TOX_ERR_FILE_SEND['OK']:
            return result
        elif tox_err_file_send == TOX_ERR_FILE_SEND['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_file_send == TOX_ERR_FILE_SEND['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend_number passed did not designate a valid friend.')
        elif tox_err_file_send == TOX_ERR_FILE_SEND['FRIEND_NOT_CONNECTED']:
            raise ArgumentError('This client is currently not connected to the friend.')
        elif tox_err_file_send == TOX_ERR_FILE_SEND['NAME_TOO_LONG']:
            raise ArgumentError('Filename length exceeded TOX_MAX_FILENAME_LENGTH bytes.')
        elif tox_err_file_send == TOX_ERR_FILE_SEND['TOO_MANY']:
            raise RuntimeError('Too many ongoing transfers. The maximum number of concurrent file transfers is 256 per'
                               'friend per direction (sending and receiving).')

    def file_send_chunk(self, friend_number, file_number, position, data):
        """
        Send a chunk of file data to a friend.

        This function is called in response to the `file_chunk_request` callback. The length parameter should be equal
        to the one received though the callback. If it is zero, the transfer is assumed complete. For files with known
        size, Core will know that the transfer is complete after the last byte has been received, so it is not necessary
        (though not harmful) to send a zero-length chunk to terminate. For streams, core will know that the transfer is
        finished if a chunk with length less than the length requested in the callback is sent.

        :param friend_number: The friend number of the receiving friend for this file.
        :param file_number: The file transfer identifier returned by tox_file_send.
        :param position: The file or stream position from which to continue reading.
        :param data: Chunk of file data
        :return: true on success.
        """
        tox_err_file_send_chunk = c_int()
        result = self.libtoxcore.tox_file_send_chunk(self._tox_pointer, c_uint32(friend_number), c_uint32(file_number),
                                                     c_uint64(position), c_char_p(data), c_size_t(len(data)),
                                                     byref(tox_err_file_send_chunk))
        tox_err_file_send_chunk = tox_err_file_send_chunk.value
        if tox_err_file_send_chunk == TOX_ERR_FILE_SEND_CHUNK['OK']:
            return bool(result)
        elif tox_err_file_send_chunk == TOX_ERR_FILE_SEND_CHUNK['NULL']:
            raise ArgumentError('The length parameter was non-zero, but data was NULL.')
        elif tox_err_file_send_chunk == TOX_ERR_FILE_SEND_CHUNK['FRIEND_NOT_FOUND']:
            ArgumentError('The friend_number passed did not designate a valid friend.')
        elif tox_err_file_send_chunk == TOX_ERR_FILE_SEND_CHUNK['FRIEND_NOT_CONNECTED']:
            raise ArgumentError('This client is currently not connected to the friend.')
        elif tox_err_file_send_chunk == TOX_ERR_FILE_SEND_CHUNK['NOT_FOUND']:
            raise ArgumentError('No file transfer with the given file number was found for the given friend.')
        elif tox_err_file_send_chunk == TOX_ERR_FILE_SEND_CHUNK['NOT_TRANSFERRING']:
            raise ArgumentError('File transfer was found but isn\'t in a transferring state: (paused, done, broken, '
                                'etc...) (happens only when not called from the request chunk callback).')
        elif tox_err_file_send_chunk == TOX_ERR_FILE_SEND_CHUNK['INVALID_LENGTH']:
            raise ArgumentError('Attempted to send more or less data than requested. The requested data size is '
                                'adjusted according to maximum transmission unit and the expected end of the file. '
                                'Trying to send less or more than requested will return this error.')
        elif tox_err_file_send_chunk == TOX_ERR_FILE_SEND_CHUNK['SENDQ']:
            raise RuntimeError('Packet queue is full.')
        elif tox_err_file_send_chunk == TOX_ERR_FILE_SEND_CHUNK['WRONG_POSITION']:
            raise ArgumentError('Position parameter was wrong.')

    def callback_file_chunk_request(self, callback):
        """
        Set the callback for the `file_chunk_request` event. Pass None to unset.

        This event is triggered when Core is ready to send more file data.

        :param callback: Python function.
        If the length parameter is 0, the file transfer is finished, and the client's resources associated with the file
        number should be released. After a call with zero length, the file number can be reused for future file
        transfers.

        If the requested position is not equal to the client's idea of the current file or stream position, it will need
        to seek. In case of read-once streams, the client should keep the last read chunk so that a seek back can be
        supported. A seek-back only ever needs to read from the last requested chunk. This happens when a chunk was
        requested, but the send failed. A seek-back request can occur an arbitrary number of times for any given chunk.

        In response to receiving this callback, the client should call the function `tox_file_send_chunk` with the
        requested chunk. If the number of bytes sent through that function is zero, the file transfer is assumed
        complete. A client must send the full length of data requested with this callback.

        Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the receiving friend for this file.
        The file transfer identifier (c_uint32) returned by tox_file_send.
        The file or stream position (c_uint64) from which to continue reading.
        The number of bytes (c_size_t) requested for the current chunk.
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_uint64, c_size_t, c_void_p)
        self.file_chunk_request_cb = c_callback(callback)
        self.libtoxcore.tox_callback_file_chunk_request(self._tox_pointer, self.file_chunk_request_cb)

    # -----------------------------------------------------------------------------------------------------------------
    # File transmission: receiving
    # -----------------------------------------------------------------------------------------------------------------

    def callback_file_recv(self, callback):
        """
        Set the callback for the `file_recv` event. Pass None to unset.

        This event is triggered when a file transfer request is received.

        :param callback: Python function.
        The client should acquire resources to be associated with the file transfer. Incoming file transfers start in
        the PAUSED state. After this callback returns, a transfer can be rejected by sending a TOX_FILE_CONTROL_CANCEL
        control command before any other control commands. It can be accepted by sending TOX_FILE_CONTROL_RESUME.

        Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the friend who is sending the file transfer request.
        The friend-specific file number (c_uint32) the data received is associated with.
        The meaning of the file (c_uint32) to be sent.
        Size in bytes (c_uint64) of the file the client wants to send, UINT64_MAX if unknown or streaming.
        Name of the file (c_char_p). Does not need to be the actual name. This name will be sent along with the file
        send request.
        Size in bytes (c_size_t) of the filename.
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_uint32, c_uint64, c_char_p, c_size_t, c_void_p)
        self.file_recv_cb = c_callback(callback)
        self.libtoxcore.tox_callback_file_recv(self._tox_pointer, self.file_recv_cb)

    def callback_file_recv_chunk(self, callback):
        """
        Set the callback for the `file_recv_chunk` event. Pass NULL to unset.

        This event is first triggered when a file transfer request is received, and subsequently when a chunk of file
        data for an accepted request was received.

        :param callback: Python function.
        When length is 0, the transfer is finished and the client should release the resources it acquired for the
        transfer. After a call with length = 0, the file number can be reused for new file transfers.

        If position is equal to file_size (received in the file_receive callback) when the transfer finishes, the file
        was received completely. Otherwise, if file_size was UINT64_MAX, streaming ended successfully when length is 0.

        Should take pointer (c_void_p) to Tox object,
        The friend number (c_uint32) of the friend who is sending the file.
        The friend-specific file number (c_uint32) the data received is associated with.
        The file position (c_uint64) of the first byte in data.
        A byte array (c_char_p) containing the received chunk.
        The length (c_size_t) of the received chunk.
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_uint64, POINTER(c_uint8), c_size_t, c_void_p)
        self.file_recv_chunk_cb = c_callback(callback)
        self.libtoxcore.tox_callback_file_recv_chunk(self._tox_pointer, self.file_recv_chunk_cb)

    # -----------------------------------------------------------------------------------------------------------------
    # Low-level custom packet sending and receiving
    # -----------------------------------------------------------------------------------------------------------------

    def friend_send_lossy_packet(self, friend_number, data):
        """
        Send a custom lossy packet to a friend.
        The first byte of data must be in the range 200-254. Maximum length of a
        custom packet is TOX_MAX_CUSTOM_PACKET_SIZE.

        Lossy packets behave like UDP packets, meaning they might never reach the
        other side or might arrive more than once (if someone is messing with the
        connection) or might arrive in the wrong order.

        Unless latency is an issue, it is recommended that you use lossless custom packets instead.

        :param friend_number: The friend number of the friend this lossy packet
        :param data: python string containing the packet data
        :return: True on success.
        """
        tox_err_friend_custom_packet = c_int()
        result = self.libtoxcore.tox_friend_send_lossy_packet(self._tox_pointer, c_uint32(friend_number),
                                                              c_char_p(data), c_size_t(len(data)),
                                                              byref(tox_err_friend_custom_packet))
        tox_err_friend_custom_packet = tox_err_friend_custom_packet.value
        if tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['OK']:
            return bool(result)
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend number did not designate a valid friend.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['FRIEND_NOT_CONNECTED']:
            raise ArgumentError('This client is currently not connected to the friend.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['INVALID']:
            raise ArgumentError('The first byte of data was not in the specified range for the packet type.'
                                'This range is 200-254 for lossy, and 160-191 for lossless packets.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['EMPTY']:
            raise ArgumentError('Attempted to send an empty packet.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['TOO_LONG']:
            raise ArgumentError('Packet data length exceeded TOX_MAX_CUSTOM_PACKET_SIZE.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['SENDQ']:
            raise RuntimeError('Packet queue is full.')

    def friend_send_lossless_packet(self, friend_number, data):
        """
        Send a custom lossless packet to a friend.
        The first byte of data must be in the range 160-191. Maximum length of a
        custom packet is TOX_MAX_CUSTOM_PACKET_SIZE.

        Lossless packet behaviour is comparable to TCP (reliability, arrive in order)
        but with packets instead of a stream.

        :param friend_number: The friend number of the friend this lossless packet
        :param data: python string containing the packet data
        :return: True on success.
        """
        tox_err_friend_custom_packet = c_int()
        result = self.libtoxcore.tox_friend_send_lossless_packet(self._tox_pointer, c_uint32(friend_number),
                                                                 c_char_p(data), c_size_t(len(data)),
                                                                 byref(tox_err_friend_custom_packet))
        tox_err_friend_custom_packet = tox_err_friend_custom_packet.value
        if tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['OK']:
            return bool(result)
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['NULL']:
            raise ArgumentError('One of the arguments to the function was NULL when it was not expected.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['FRIEND_NOT_FOUND']:
            raise ArgumentError('The friend number did not designate a valid friend.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['FRIEND_NOT_CONNECTED']:
            raise ArgumentError('This client is currently not connected to the friend.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['INVALID']:
            raise ArgumentError('The first byte of data was not in the specified range for the packet type.'
                                'This range is 200-254 for lossy, and 160-191 for lossless packets.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['EMPTY']:
            raise ArgumentError('Attempted to send an empty packet.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['TOO_LONG']:
            raise ArgumentError('Packet data length exceeded TOX_MAX_CUSTOM_PACKET_SIZE.')
        elif tox_err_friend_custom_packet == TOX_ERR_FRIEND_CUSTOM_PACKET['SENDQ']:
            raise RuntimeError('Packet queue is full.')

    def callback_friend_lossy_packet(self, callback):
        """
        Set the callback for the `friend_lossy_packet` event. Pass NULL to unset.

        :param callback: Python function.
        Should take pointer (c_void_p) to Tox object,
        friend_number (c_uint32) - The friend number of the friend who sent a lossy packet,
        A byte array (c_uint8 array) containing the received packet data,
        length (c_size_t) - The length of the packet data byte array,
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, POINTER(c_uint8), c_size_t, c_void_p)
        self.friend_lossy_packet_cb = c_callback(callback)
        self.libtoxcore.tox_callback_friend_lossy_packet(self._tox_pointer, self.friend_lossy_packet_cb)

    def callback_friend_lossless_packet(self, callback):
        """
        Set the callback for the `friend_lossless_packet` event. Pass NULL to unset.

        :param callback: Python function.
        Should take pointer (c_void_p) to Tox object,
        friend_number (c_uint32) - The friend number of the friend who sent a lossless packet,
        A byte array (c_uint8 array) containing the received packet data,
        length (c_size_t) - The length of the packet data byte array,
        pointer (c_void_p) to user_data
        """
        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, POINTER(c_uint8), c_size_t, c_void_p)
        self.friend_lossless_packet_cb = c_callback(callback)
        self.libtoxcore.tox_callback_friend_lossless_packet(self._tox_pointer, self.friend_lossless_packet_cb)

    # -----------------------------------------------------------------------------------------------------------------
    # Low-level network information
    # -----------------------------------------------------------------------------------------------------------------

    def self_get_dht_id(self, dht_id=None):
        """
        Writes the temporary DHT public key of this instance to a byte array.

        This can be used in combination with an externally accessible IP address and the bound port (from
        tox_self_get_udp_port) to run a temporary bootstrap node.

        Be aware that every time a new instance is created, the DHT public key changes, meaning this cannot be used to
        run a permanent bootstrap node.

        :param dht_id: pointer (c_char_p) to a memory region of at least TOX_PUBLIC_KEY_SIZE bytes. If this parameter is
        None, this function allocates memory for dht_id.
        :return: dht_id
        """
        if dht_id is None:
            dht_id = create_string_buffer(TOX_PUBLIC_KEY_SIZE)
        Tox.libtoxcore.tox_self_get_dht_id(self._tox_pointer, dht_id)
        return bin_to_string(dht_id, TOX_PUBLIC_KEY_SIZE)

    def self_get_udp_port(self):
        """
        Return the UDP port this Tox instance is bound to.
        """
        tox_err_get_port = c_int()
        result = Tox.libtoxcore.tox_self_get_udp_port(self._tox_pointer, byref(tox_err_get_port))
        tox_err_get_port = tox_err_get_port.value
        if tox_err_get_port == TOX_ERR_GET_PORT['OK']:
            return result
        elif tox_err_get_port == TOX_ERR_GET_PORT['NOT_BOUND']:
            raise RuntimeError('The instance was not bound to any port.')

    def self_get_tcp_port(self):
        """
        Return the TCP port this Tox instance is bound to. This is only relevant if the instance is acting as a TCP
        relay.
        """
        tox_err_get_port = c_int()
        result = Tox.libtoxcore.tox_self_get_tcp_port(self._tox_pointer, byref(tox_err_get_port))
        tox_err_get_port = tox_err_get_port.value
        if tox_err_get_port == TOX_ERR_GET_PORT['OK']:
            return result
        elif tox_err_get_port == TOX_ERR_GET_PORT['NOT_BOUND']:
            raise RuntimeError('The instance was not bound to any port.')

    # -----------------------------------------------------------------------------------------------------------------
    # Group chat instance management
    # -----------------------------------------------------------------------------------------------------------------

    def group_new(self, privacy_state, group_name, nick, status):
        """
        Creates a new group chat.

        This function creates a new group chat object and adds it to the chats array.

        The client should initiate its peer list with self info after calling this function, as
        the peer_join callback will not be triggered.

        :param privacy_state: The privacy state of the group. If this is set to TOX_GROUP_PRIVACY_STATE_PUBLIC,
        the group will attempt to announce itself to the DHT and anyone with the Chat ID may join.
        Otherwise a friend invite will be required to join the group.
        :param group_name: The name of the group. The name must be non-NULL.

        :return group number on success, UINT32_MAX on failure.
        """

        error = c_int()
        peer_info = self.group_self_peer_info_new()
        nick = bytes(nick, 'utf-8')
        group_name = group_name.encode('utf-8')
        peer_info.contents.nick = c_char_p(nick)
        peer_info.contents.nick_length = len(nick)
        peer_info.contents.user_status = status
        result = Tox.libtoxcore.tox_group_new(self._tox_pointer, privacy_state, group_name,
                                              len(group_name), peer_info, byref(error))
        return result

    def group_join(self, chat_id, password, nick, status):
        """
        Joins a group chat with specified Chat ID.

        This function creates a new group chat object, adds it to the chats array, and sends
        a DHT announcement to find peers in the group associated with chat_id. Once a peer has been
        found a join attempt will be initiated.

        :param chat_id: The Chat ID of the group you wish to join. This must be TOX_GROUP_CHAT_ID_SIZE bytes.
        :param password: The password required to join the group. Set to NULL if no password is required.

        :return group_number on success, UINT32_MAX on failure.
        """

        error = c_int()
        peer_info = self.group_self_peer_info_new()
        nick = bytes(nick, 'utf-8')
        peer_info.contents.nick = c_char_p(nick)
        peer_info.contents.nick_length = len(nick)
        peer_info.contents.user_status = status
        result = Tox.libtoxcore.tox_group_join(self._tox_pointer, string_to_bin(chat_id),
                                               password,
                                               len(password) if password is not None else 0,
                                               peer_info,
                                               byref(error))
        return result

    def group_reconnect(self, group_number):
        """
        Reconnects to a group.

        This function disconnects from all peers in the group, then attempts to reconnect with the group.
        The caller's state is not changed (i.e. name, status, role, chat public key etc.)

        :param group_number: The group number of the group we wish to reconnect to.
        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_reconnect(self._tox_pointer, group_number, byref(error))
        return result

    def group_is_connected(self, group_number):
        error = c_int()
        result = Tox.libtoxcore.tox_group_is_connected(self._tox_pointer, group_number, byref(error))
        return result

    def group_disconnect(self, group_number):
        error = c_int()
        result = Tox.libtoxcore.tox_group_disconnect(self._tox_pointer, group_number, byref(error))
        return result

    def group_leave(self, group_number, message=''):
        """
        Leaves a group.

        This function sends a parting packet containing a custom (non-obligatory) message to all
        peers in a group, and deletes the group from the chat array. All group state information is permanently
        lost, including keys and role credentials.

        :param group_number: The group number of the group we wish to leave.
        :param message: The parting message to be sent to all the peers. Set to NULL if we do not wish to
        send a parting message.

        :return True if the group chat instance was successfully deleted.
        """

        error = c_int()
        f = Tox.libtoxcore.tox_group_leave
        f.restype = c_bool
        result = f(self._tox_pointer, group_number, message,
                   len(message) if message is not None else 0, byref(error))
        return result

    # -----------------------------------------------------------------------------------------------------------------
    # Group user-visible client information (nickname/status/role/public key)
    # -----------------------------------------------------------------------------------------------------------------

    def group_self_set_name(self, group_number, name):
        """
        Set the client's nickname for the group instance designated by the given group number.

        Nickname length cannot exceed TOX_MAX_NAME_LENGTH. If length is equal to zero or name is a NULL
        pointer, the function call will fail.

        :param name: A byte array containing the new nickname.

        :return True on success.
        """

        error = c_int()
        name = bytes(name, 'utf-8')
        result = Tox.libtoxcore.tox_group_self_set_name(self._tox_pointer, group_number, name, len(name), byref(error))
        return result

    def group_self_get_name_size(self, group_number):
        """
        Return the length of the client's current nickname for the group instance designated
        by group_number as passed to tox_group_self_set_name.

        If no nickname was set before calling this function, the name is empty,
        and this function returns 0.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_self_get_name_size(self._tox_pointer, group_number, byref(error))
        return result

    def group_self_get_name(self, group_number):
        """
        Write the nickname set by tox_group_self_set_name to a byte array.

        If no nickname was set before calling this function, the name is empty,
        and this function has no effect.

        Call tox_group_self_get_name_size to find out how much memory to allocate for the result.
        :return nickname
        """

        error = c_int()
        size = self.group_self_get_name_size(group_number)
        name = create_string_buffer(size)
        result = Tox.libtoxcore.tox_group_self_get_name(self._tox_pointer, group_number, name, byref(error))
        return str(name[:size], 'utf-8')

    def group_self_set_status(self, group_number, status):

        """
        Set the client's status for the group instance. Status must be a TOX_USER_STATUS.
        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_self_set_status(self._tox_pointer, group_number, status, byref(error))
        return result

    def group_self_get_status(self, group_number):
        """
        returns the client's status for the group instance on success.
        return value is unspecified on failure.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_self_get_status(self._tox_pointer, group_number, byref(error))
        return result

    def group_self_get_role(self, group_number):
        """
        returns the client's role for the group instance on success.
        return value is unspecified on failure.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_self_get_role(self._tox_pointer, group_number, byref(error))
        return result

    def group_self_get_peer_id(self, group_number):
        """
        returns the client's peer id for the group instance on success.
        return value is unspecified on failure.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_self_get_peer_id(self._tox_pointer, group_number, byref(error))
        return result

    def group_self_get_public_key(self, group_number):
        """
        Write the client's group public key designated by the given group number to a byte array.

        This key will be permanently tied to the client's identity for this particular group until
        the client explicitly leaves the group or gets kicked/banned. This key is the only way for
        other peers to reliably identify the client across client restarts.

        `public_key` should have room for at least TOX_GROUP_PEER_PUBLIC_KEY_SIZE bytes.

        :return public key
        """

        error = c_int()
        key = create_string_buffer(TOX_GROUP_PEER_PUBLIC_KEY_SIZE)
        result = Tox.libtoxcore.tox_group_self_get_public_key(self._tox_pointer, group_number,
                                                              key, byref(error))
        return bin_to_string(key, TOX_GROUP_PEER_PUBLIC_KEY_SIZE)

    # -----------------------------------------------------------------------------------------------------------------
    # Peer-specific group state queries.
    # -----------------------------------------------------------------------------------------------------------------

    def group_peer_get_name_size(self, group_number, peer_id):
        """
        Return the length of the peer's name. If the group number or ID is invalid, the
        return value is unspecified.

        The return value is equal to the `length` argument received by the last
        `group_peer_name` callback.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_peer_get_name_size(self._tox_pointer, group_number, peer_id, byref(error))
        return result

    def group_peer_get_name(self, group_number, peer_id):
        """
        Write the name of the peer designated by the given ID to a byte
        array.

        Call tox_group_peer_get_name_size to determine the allocation size for the `name` parameter.

        The data written to `name` is equal to the data received by the last
        `group_peer_name` callback.

        :param group_number: The group number of the group we wish to query.
        :param peer_id: The ID of the peer whose name we want to retrieve.

        :return name.
        """
        error = c_int()
        size = self.group_peer_get_name_size(group_number, peer_id)
        name = create_string_buffer(size)
        result = Tox.libtoxcore.tox_group_peer_get_name(self._tox_pointer, group_number, peer_id, name, byref(error))
        return str(name[:], 'utf-8')

    def group_peer_get_status(self, group_number, peer_id):
        """
        Return the peer's user status (away/busy/...). If the ID or group number is
        invalid, the return value is unspecified.

        The status returned is equal to the last status received through the
        `group_peer_status` callback.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_peer_get_status(self._tox_pointer, group_number, peer_id, byref(error))
        return result

    def group_peer_get_role(self, group_number, peer_id):
        """
        Return the peer's role (user/moderator/founder...). If the ID or group number is
        invalid, the return value is unspecified.

        The role returned is equal to the last role received through the
        `group_moderation` callback.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_peer_get_role(self._tox_pointer, group_number, peer_id, byref(error))
        return result

    def group_peer_get_public_key(self, group_number, peer_id):
        """
        Write the group public key with the designated peer_id for the designated group number to public_key.

        This key will be permanently tied to a particular peer until they explicitly leave the group or
        get kicked/banned, and is the only way to reliably identify the same peer across client restarts.

        `public_key` should have room for at least TOX_GROUP_PEER_PUBLIC_KEY_SIZE bytes.

        :return public key
        """

        error = c_int()
        key = create_string_buffer(TOX_GROUP_PEER_PUBLIC_KEY_SIZE)
        result = Tox.libtoxcore.tox_group_peer_get_public_key(self._tox_pointer, group_number, peer_id,
                                                              key, byref(error))
        return bin_to_string(key, TOX_GROUP_PEER_PUBLIC_KEY_SIZE)

    def callback_group_peer_name(self, callback, user_data):
        """
        Set the callback for the `group_peer_name` event. Pass NULL to unset.
        This event is triggered when a peer changes their nickname.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_char_p, c_size_t, c_void_p)
        self.group_peer_name_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_peer_name(self._tox_pointer, self.group_peer_name_cb, user_data)

    def callback_group_peer_status(self, callback, user_data):
        """
        Set the callback for the `group_peer_status` event. Pass NULL to unset.
        This event is triggered when a peer changes their status.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_int, c_void_p)
        self.group_peer_status_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_peer_status(self._tox_pointer, self.group_peer_status_cb, user_data)

    # -----------------------------------------------------------------------------------------------------------------
    # Group chat state queries and events.
    # -----------------------------------------------------------------------------------------------------------------

    def group_set_topic(self, group_number, topic):
        """
        Set the group topic and broadcast it to the rest of the group.

        topic length cannot be longer than TOX_GROUP_MAX_TOPIC_LENGTH. If length is equal to zero or
        topic is set to NULL, the topic will be unset.

        :return True on success.
        """

        error = c_int()
        topic = bytes(topic, 'utf-8')
        result = Tox.libtoxcore.tox_group_set_topic(self._tox_pointer, group_number, topic, len(topic), byref(error))
        return result

    def group_get_topic_size(self, group_number):
        """
        Return the length of the group topic. If the group number is invalid, the
        return value is unspecified.

        The return value is equal to the `length` argument received by the last
        `group_topic` callback.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_get_topic_size(self._tox_pointer, group_number, byref(error))
        return result

    def group_get_topic(self, group_number):
        """
        Write the topic designated by the given group number to a byte array.
        Call tox_group_get_topic_size to determine the allocation size for the `topic` parameter.
        The data written to `topic` is equal to the data received by the last
        `group_topic` callback.

        :return topic
        """

        error = c_int()
        size = self.group_get_topic_size(group_number)
        topic = create_string_buffer(size)
        result = Tox.libtoxcore.tox_group_get_topic(self._tox_pointer, group_number, topic, byref(error))
        return str(topic[:size], 'utf-8')

    def group_get_name_size(self, group_number):
        """
        Return the length of the group name. If the group number is invalid, the
        return value is unspecified.
        """
        error = c_int()
        result = Tox.libtoxcore.tox_group_get_name_size(self._tox_pointer, group_number, byref(error))
        return int(result)

    def group_get_name(self, group_number):
        """
        Write the name of the group designated by the given group number to a byte array.
        Call tox_group_get_name_size to determine the allocation size for the `name` parameter.
        :return true on success.
        """

        error = c_int()
        size = self.group_get_name_size(group_number)
        name = create_string_buffer(size)
        result = Tox.libtoxcore.tox_group_get_name(self._tox_pointer, group_number,
                                                   name, byref(error))
        return str(name[:size], 'utf-8')

    def group_get_chat_id(self, group_number):
        """
        Write the Chat ID designated by the given group number to a byte array.
        `chat_id` should have room for at least TOX_GROUP_CHAT_ID_SIZE bytes.
        :return chat id.
        """

        error = c_int()
        buff = create_string_buffer(TOX_GROUP_CHAT_ID_SIZE)
        result = Tox.libtoxcore.tox_group_get_chat_id(self._tox_pointer, group_number,
                                                      buff, byref(error))
        return bin_to_string(buff, TOX_GROUP_CHAT_ID_SIZE)

    def group_get_number_groups(self):
        """
        Return the number of groups in the Tox chats array.
        """

        result = Tox.libtoxcore.tox_group_get_number_groups(self._tox_pointer)
        return result

    def groups_get_list(self):
        groups_list_size = self.group_get_number_groups()
        groups_list = create_string_buffer(sizeof(c_uint32) * groups_list_size)
        groups_list = POINTER(c_uint32)(groups_list)
        Tox.libtoxcore.tox_groups_get_list(self._tox_pointer, groups_list)
        return groups_list[0:groups_list_size]

    def group_get_privacy_state(self, group_number):
        """
        Return the privacy state of the group designated by the given group number. If group number
        is invalid, the return value is unspecified.

        The value returned is equal to the data received by the last
        `group_privacy_state` callback.

        see the `Group chat founder controls` section for the respective set function.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_get_privacy_state(self._tox_pointer, group_number, byref(error))
        return result

    def group_get_peer_limit(self, group_number):
        """
        Return the maximum number of peers allowed for the group designated by the given group number.
        If the group number is invalid, the return value is unspecified.

        The value returned is equal to the data received by the last
        `group_peer_limit` callback.

        see the `Group chat founder controls` section for the respective set function.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_get_peer_limit(self._tox_pointer, group_number, byref(error))
        return result

    def group_get_password_size(self, group_number):
        """
        Return the length of the group password. If the group number is invalid, the
        return value is unspecified.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_get_password_size(self._tox_pointer, group_number, byref(error))
        return result

    def group_get_password(self, group_number):
        """
        Write the password for the group designated by the given group number to a byte array.

        Call tox_group_get_password_size to determine the allocation size for the `password` parameter.

        The data received is equal to the data received by the last
        `group_password` callback.

        see the `Group chat founder controls` section for the respective set function.

        :return password
        """

        error = c_int()
        size = self.group_get_password_size(group_number)
        password = create_string_buffer(size)
        result = Tox.libtoxcore.tox_group_get_password(self._tox_pointer, group_number,
                                                       password, byref(error))
        return str(password[:size], 'utf-8')

    def callback_group_topic(self, callback, user_data):
        """
        Set the callback for the `group_topic` event. Pass NULL to unset.
        This event is triggered when a peer changes the group topic.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_char_p, c_size_t, c_void_p)
        self.group_topic_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_topic(self._tox_pointer, self.group_topic_cb, user_data)

    def callback_group_privacy_state(self, callback, user_data):
        """
        Set the callback for the `group_privacy_state` event. Pass NULL to unset.
        This event is triggered when the group founder changes the privacy state.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_int, c_void_p)
        self.group_privacy_state_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_privacy_state(self._tox_pointer, self.group_privacy_state_cb, user_data)

    def callback_group_peer_limit(self, callback, user_data):
        """
        Set the callback for the `group_peer_limit` event. Pass NULL to unset.
        This event is triggered when the group founder changes the maximum peer limit.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_void_p)
        self.group_peer_limit_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_peer_limit(self._tox_pointer, self.group_peer_limit_cb, user_data)

    def callback_group_password(self, callback, user_data):
        """
        Set the callback for the `group_password` event. Pass NULL to unset.
        This event is triggered when the group founder changes the group password.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_char_p, c_size_t, c_void_p)
        self.group_password_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_password(self._tox_pointer, self.group_password_cb, user_data)

    # -----------------------------------------------------------------------------------------------------------------
    # Group message sending
    # -----------------------------------------------------------------------------------------------------------------

    def group_send_custom_packet(self, group_number, lossless, data):
        """
        Send a custom packet to the group.

        If lossless is true the packet will be lossless. Lossless packet behaviour is comparable
        to TCP (reliability, arrive in order) but with packets instead of a stream.

        If lossless is false, the packet will be lossy. Lossy packets behave like UDP packets,
        meaning they might never reach the other side or might arrive more than once (if someone
        is messing with the connection) or might arrive in the wrong order.

        Unless latency is an issue or message reliability is not important, it is recommended that you use
        lossless custom packets.

        :param group_number: The group number of the group the message is intended for.
        :param lossless: True if the packet should be lossless.
        :param data A byte array containing the packet data.
        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_send_custom_packet(self._tox_pointer, group_number, lossless, data,
                                                             len(data), byref(error))
        return result

    def group_send_private_message(self, group_number, peer_id, message_type, message):
        """
        Send a text chat message to the specified peer in the specified group.

        This function creates a group private message packet and pushes it into the send
        queue.

        The message length may not exceed TOX_MAX_MESSAGE_LENGTH. Larger messages
        must be split by the client and sent as separate messages. Other clients can
        then reassemble the fragments. Messages may not be empty.

        :param group_number: The group number of the group the message is intended for.
        :param peer_id: The ID of the peer the message is intended for.
        :param message: A non-NULL pointer to the first element of a byte array containing the message text.

        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_send_private_message(self._tox_pointer, group_number, peer_id,
                                                               message_type, message,
                                                               len(message), byref(error))
        return result

    def group_send_message(self, group_number, type, message):
        """
        Send a text chat message to the group.

        This function creates a group message packet and pushes it into the send
        queue.

        The message length may not exceed TOX_MAX_MESSAGE_LENGTH. Larger messages
        must be split by the client and sent as separate messages. Other clients can
        then reassemble the fragments. Messages may not be empty.

        :param group_number: The group number of the group the message is intended for.
        :param type: Message type (normal, action, ...).
        :param message: A non-NULL pointer to the first element of a byte array containing the message text.

        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_send_message(self._tox_pointer, group_number, type, message, len(message),
                                                       byref(error))
        return result

    # -----------------------------------------------------------------------------------------------------------------
    # Group message receiving
    # -----------------------------------------------------------------------------------------------------------------

    def callback_group_message(self, callback, user_data):
        """
        Set the callback for the `group_message` event. Pass NULL to unset.
        This event is triggered when the client receives a group message.

        Callback: python function with params:
        tox Tox* instance
        group_number The group number of the group the message is intended for.
        peer_id The ID of the peer who sent the message.
        type The type of message (normal, action, ...).
        message The message data.
        length The length of the message.
        user_data - user data
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_int, c_char_p, c_size_t, c_void_p)
        self.group_message_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_message(self._tox_pointer, self.group_message_cb, user_data)

    def callback_group_private_message(self, callback, user_data):
        """
        Set the callback for the `group_private_message` event. Pass NULL to unset.
        This event is triggered when the client receives a private message.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_uint8, c_char_p, c_size_t, c_void_p)
        self.group_private_message_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_private_message(self._tox_pointer, self.group_private_message_cb, user_data)

    def callback_group_custom_packet(self, callback, user_data):
        """
        Set the callback for the `group_custom_packet` event. Pass NULL to unset.

        This event is triggered when the client receives a custom packet.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, POINTER(c_uint8), c_void_p)
        self.group_custom_packet_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_custom_packet(self._tox_pointer, self.group_custom_packet_cb, user_data)

    # -----------------------------------------------------------------------------------------------------------------
    # Group chat inviting and join/part events
    # -----------------------------------------------------------------------------------------------------------------

    def group_invite_friend(self, group_number, friend_number):
        """
        Invite a friend to a group.

        This function creates an invite request packet and pushes it to the send queue.

        :param group_number: The group number of the group the message is intended for.
        :param friend_number: The friend number of the friend the invite is intended for.

        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_invite_friend(self._tox_pointer, group_number, friend_number, byref(error))
        return result

    @staticmethod
    def group_self_peer_info_new():
        error = c_int()
        f = Tox.libtoxcore.tox_group_self_peer_info_new
        f.restype = POINTER(GroupChatSelfPeerInfo)
        result = f(byref(error))

        return result

    def group_invite_accept(self, invite_data, friend_number, nick, status, password=None):
        """
        Accept an invite to a group chat that the client previously received from a friend. The invite
        is only valid while the inviter is present in the group.

        :param invite_data: The invite data received from the `group_invite` event.
        :param password: The password required to join the group. Set to NULL if no password is required.
        :return the group_number on success, UINT32_MAX on failure.
        """

        error = c_int()
        f = Tox.libtoxcore.tox_group_invite_accept
        f.restype = c_uint32
        peer_info = self.group_self_peer_info_new()
        nick = bytes(nick, 'utf-8')
        peer_info.contents.nick = c_char_p(nick)
        peer_info.contents.nick_length = len(nick)
        peer_info.contents.user_status = status
        result = f(self._tox_pointer, friend_number, invite_data, len(invite_data), password,
                   len(password) if password is not None else 0, peer_info, byref(error))
        print('Invite accept. Result:', result, 'Error:', error.value)
        return result

    def callback_group_invite(self, callback, user_data):
        """
        Set the callback for the `group_invite` event. Pass NULL to unset.

        This event is triggered when the client receives a group invite from a friend. The client must store
        invite_data which is used to join the group via tox_group_invite_accept.

        Callback: python function with params:
        tox - Tox*
        friend_number The friend number of the contact who sent the invite.
        invite_data The invite data.
        length The length of invite_data.
        user_data - user data
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, POINTER(c_uint8), c_size_t,
                               POINTER(c_uint8), c_size_t, c_void_p)
        self.group_invite_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_invite(self._tox_pointer, self.group_invite_cb, user_data)

    def callback_group_peer_join(self, callback, user_data):
        """
        Set the callback for the `group_peer_join` event. Pass NULL to unset.

        This event is triggered when a peer other than self joins the group.
        Callback: python function with params:
        tox - Tox*
        group_number - group number
        peer_id - peer id
        user_data - user data
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_void_p)
        self.group_peer_join_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_peer_join(self._tox_pointer, self.group_peer_join_cb, user_data)

    def callback_group_peer_exit(self, callback, user_data):
        """
        Set the callback for the `group_peer_exit` event. Pass NULL to unset.

        This event is triggered when a peer other than self exits the group.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_char_p, c_size_t, c_void_p)
        self.group_peer_exit_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_peer_exit(self._tox_pointer, self.group_peer_exit_cb, user_data)

    def callback_group_self_join(self, callback, user_data):
        """
        Set the callback for the `group_self_join` event. Pass NULL to unset.

        This event is triggered when the client has successfully joined a group. Use this to initialize
        any group information the client may need.
        Callback: python fucntion with params:
        tox - *Tox
        group_number - group number
        user_data - user data
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_void_p)
        self.group_self_join_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_self_join(self._tox_pointer, self.group_self_join_cb, user_data)

    def callback_group_join_fail(self, callback, user_data):
        """
        Set the callback for the `group_join_fail` event. Pass NULL to unset.

        This event is triggered when the client fails to join a group.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_int, c_void_p)
        self.group_join_fail_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_join_fail(self._tox_pointer, self.group_join_fail_cb, user_data)

    # -----------------------------------------------------------------------------------------------------------------
    # Group chat founder controls (these only work for the group founder)
    # -----------------------------------------------------------------------------------------------------------------

    def group_founder_set_password(self, group_number, password):
        """
        Set or unset the group password.

        This function sets the groups password, creates a new group shared state including the change,
        and distributes it to the rest of the group.

        :param group_number: The group number of the group for which we wish to set the password.
        :param password: The password we want to set. Set password to NULL to unset the password.

        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_founder_set_password(self._tox_pointer, group_number, password,
                                                               len(password), byref(error))
        return result

    def group_founder_set_privacy_state(self, group_number, privacy_state):
        """
        Set the group privacy state.

        This function sets the group's privacy state, creates a new group shared state
        including the change, and distributes it to the rest of the group.

        If an attempt is made to set the privacy state to the same state that the group is already
        in, the function call will be successful and no action will be taken.

        :param group_number: The group number of the group for which we wish to change the privacy state.
        :param privacy_state: The privacy state we wish to set the group to.

        :return true on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_founder_set_privacy_state(self._tox_pointer, group_number, privacy_state,
                                                                    byref(error))
        return result

    def group_founder_set_peer_limit(self, group_number, max_peers):
        """
        Set the group peer limit.

        This function sets a limit for the number of peers who may be in the group, creates a new
        group shared state including the change, and distributes it to the rest of the group.

        :param group_number: The group number of the group for which we wish to set the peer limit.
        :param max_peers: The maximum number of peers to allow in the group.

        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_founder_set_peer_limit(self._tox_pointer, group_number,
                                                                 max_peers, byref(error))
        return result

    # -----------------------------------------------------------------------------------------------------------------
    # Group chat moderation
    # -----------------------------------------------------------------------------------------------------------------

    def group_toggle_ignore(self, group_number, peer_id, ignore):
        """
        Ignore or unignore a peer.

        :param group_number: The group number of the group the in which you wish to ignore a peer.
        :param peer_id: The ID of the peer who shall be ignored or unignored.
        :param ignore: True to ignore the peer, false to unignore the peer.

        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_toggle_ignore(self._tox_pointer, group_number, peer_id, ignore, byref(error))
        return result

    def group_mod_set_role(self, group_number, peer_id, role):
        """
        Set a peer's role.

        This function will first remove the peer's previous role and then assign them a new role.
        It will also send a packet to the rest of the group, requesting that they perform
        the role reassignment. Note: peers cannot be set to the founder role.

        :param group_number: The group number of the group the in which you wish set the peer's role.
        :param peer_id: The ID of the peer whose role you wish to set.
        :param role: The role you wish to set the peer to.

        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_mod_set_role(self._tox_pointer, group_number, peer_id, role, byref(error))
        return result

    def group_mod_remove_peer(self, group_number, peer_id, set_ban):
        """
        Kick/ban a peer.

        This function will remove a peer from the caller's peer list and optionally add their IP address
        to the ban list. It will also send a packet to all group members requesting them
        to do the same.

        :param group_number: The group number of the group the ban is intended for.
        :param peer_id: The ID of the peer who will be kicked and/or added to the ban list.
        :param set_ban: Set to true if a ban shall be set on the peer's IP address.

        :return True on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_mod_remove_peer(self._tox_pointer, group_number, peer_id,
                                                          set_ban, byref(error))
        return result

    def group_mod_remove_ban(self, group_number, ban_id):
        """
        Removes a ban.

        This function removes a ban entry from the ban list, and sends a packet to the rest of
        the group requesting that they do the same.

        :param group_number: The group number of the group in which the ban is to be removed.
        :param ban_id: The ID of the ban entry that shall be removed.

        :return True on success
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_mod_remove_ban(self._tox_pointer, group_number, ban_id, byref(error))
        return result

    def callback_group_moderation(self, callback, user_data):
        """
        Set the callback for the `group_moderation` event. Pass NULL to unset.

        This event is triggered when a moderator or founder executes a moderation event.
        """

        c_callback = CFUNCTYPE(None, c_void_p, c_uint32, c_uint32, c_uint32, c_int, c_void_p)
        self.group_moderation_cb = c_callback(callback)
        Tox.libtoxcore.tox_callback_group_moderation(self._tox_pointer, self.group_moderation_cb, user_data)

    # -----------------------------------------------------------------------------------------------------------------
    # Group chat ban list queries
    # -----------------------------------------------------------------------------------------------------------------

    def group_ban_get_list_size(self, group_number):
        """
        Return the number of entries in the ban list for the group designated by
        the given group number. If the group number is invalid, the return value is unspecified.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_ban_get_list_size(self._tox_pointer, group_number, byref(error))
        return result

    def group_ban_get_list(self, group_number):
        """
        Copy a list of valid ban list ID's into an array.

        Call tox_group_ban_get_list_size to determine the number of elements to allocate.
        return true on success.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_ban_get_list(self._tox_pointer, group_number, POINTER(c_uint32)(
            create_string_buffer(sizeof(c_uint32) * self.group_ban_get_list_size(group_number)), byref(error)))
        return result

    def group_ban_get_target_size(self, group_number, ban_id):
        """
        Return the length of the name for the ban list entry designated by ban_id, in the
        group designated by the given group number. If either group_number or ban_id is invalid,
        the return value is unspecified.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_ban_get_target_size(self._tox_pointer, group_number, ban_id, byref(error))
        return result

    def group_ban_get_target(self, group_number, ban_id):
        """
        Write the name of the ban entry designated by ban_id in the group designated by the
        given group number to a byte array.

        Call tox_group_ban_get_name_size to find out how much memory to allocate for the result.

        :return name
        """

        error = c_int()
        size = self.group_ban_get_target_size(group_number, ban_id)
        target = create_string_buffer(size)

        result = Tox.libtoxcore.tox_group_ban_get_target(self._tox_pointer, group_number, ban_id,
                                                         target, byref(error))
        return str(target[:size], 'utf-8')

    def group_ban_get_time_set(self, group_number, ban_id):
        """
        Return a time stamp indicating the time the ban was set, for the ban list entry
        designated by ban_id, in the group designated by the given group number.
        If either group_number or ban_id is invalid, the return value is unspecified.
        """

        error = c_int()
        result = Tox.libtoxcore.tox_group_ban_get_time_set(self._tox_pointer, group_number, ban_id, byref(error))
        return result
