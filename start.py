'''Start point of console app

When app will be installed, this script will be used as enter point in console app
Run this script manually with python interpreter to launch console app without
installing it
'''
import tasktracker_console.console_parser as parser

def run():
    parser.parse()

if __name__ == "__main__":
    run()