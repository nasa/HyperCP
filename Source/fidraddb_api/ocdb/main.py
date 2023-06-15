from ocdb.api import new_api
from ocdb.cli import cli


def main(args=None):
    cli.main(args=args, obj=new_api())


if __name__ == '__main__':
    main()

