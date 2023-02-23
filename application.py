from src import application
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug',
                        type=bool,
                        required=False,
                        help='Run server in debug mode.')
    args = parser.parse_args()
    application.run(host='0.0.0.0', debug=args.debug)
