import sys
import tasktracker_server.console_parser as parser

def run():
    args = sys.argv
    if len(args) == 1:
        print("Hello) It's task tracker")
        print("Now we have:")
        print("add to add")
        print("get to get")
        sys.exit(0)

    parser.parse(args[1:])

if __name__ == "__main__":
    run()