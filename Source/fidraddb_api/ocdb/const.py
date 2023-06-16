import stat

CONFIG_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR
CONFIG_DIR_MODE = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
