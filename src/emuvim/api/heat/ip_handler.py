from resources.net import Net
import threading

lock = threading.Lock()

__issued_ips = dict()
__default_subnet_size = 256
__default_subnet_bitmask = 24
__first_ip = Net.ip_2_int('10.0.0.0')
__last_ip = Net.ip_2_int('10.255.255.255')
__current_ip = __first_ip


def get_new_cidr(uuid):
    global lock
    lock.acquire()

    global __current_ip
    while __current_ip < __last_ip and __current_ip >= __first_ip and __issued_ips.has_key(__current_ip):
        __current_ip += __default_subnet_size

    if __current_ip >= __last_ip or __current_ip < __first_ip or __issued_ips.has_key(__current_ip):
        return None

    __issued_ips[__current_ip] = uuid
    lock.release()

    return Net.int_2_ip(__current_ip) + '/' + str(__default_subnet_bitmask)


def free_cidr(cidr, uuid):
    if cidr is None:
        return False

    global __current_ip
    int_ip = Net.cidr_2_int(cidr)

    global lock
    lock.acquire()

    if __issued_ips.has_key(int_ip) and __issued_ips[int_ip] == uuid:
        del __issued_ips[int_ip]
        if int_ip < __current_ip:
            __current_ip = int_ip
        lock.release()
        return True
    lock.release()
    return False


def is_cidr_issued(cidr):
    if cidr is None:
        return False

    int_ip = Net.cidr_2_int(cidr)

    if __issued_ips.has_key(int_ip):
        return True
    return False


def is_my_cidr(cidr, uuid):
    if cidr is None:
        return False

    int_ip = Net.cidr_2_int(cidr)

    if not __issued_ips.has_key(int_ip):
        return False

    if __issued_ips[int_ip] == uuid:
        return True
    return False


def assign_cidr(cidr, uuid):
    if cidr is None:
        return False

    int_ip = Net.cidr_2_int(cidr)

    if __issued_ips.has_key(int_ip):
        return False

    global lock
    lock.acquire()
    __issued_ips[int_ip] = uuid
    lock.release()
    return True
