LEVENSHTEIN_RATIO_THRESHOLD = 0.5

# Database
DB_NAME = 'test'
DB_USER = 'postgres'
DB_PASSWORD = ''
DB_HOST = '127.0.0.1'
DB_PORT = 5432


def initialize():
    global core_add
    global core_del
    global core_mod
    global fs_add
    global fs_del
    global fs_mod
    global driver_add
    global driver_del
    global driver_mod
    global net_add
    global net_del
    global net_mod
    global arch_add
    global arch_del
    global arch_mod
    global misc_add
    global misc_del
    global misc_mod
    global firmware_add
    global firmware_del
    global firmware_mod
    global uniq_log_fun
    uniq_log_fun = set(line.strip() for line in open('uniq_log_func'))

    core_add = 0
    core_del = 0
    core_mod = 0
    fs_add = 0
    fs_del = 0
    fs_mod = 0
    driver_add = 0
    driver_del = 0
    driver_mod = 0
    net_add = 0
    net_del = 0
    net_mod = 0
    arch_add = 0
    arch_del = 0
    arch_mod = 0
    misc_add = 0
    misc_del = 0
    misc_mod = 0
    firmware_add = 0
    firmware_del = 0
    firmware_mod = 0
