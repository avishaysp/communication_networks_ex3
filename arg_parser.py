import argparse
from consts import DEFAULT_PORT, STR_TO_ROLE

class ArgParser:

    def _create_parser(self, description):
        return argparse.ArgumentParser(description=description)

    def server_parse_arguments(self):
        parser = self._create_parser("A server script that accepts a port number.")

        parser.add_argument(
            "-p", "--port",
            type=int,
            default=DEFAULT_PORT,
            help=f"The port number the server should listen on (default: {DEFAULT_PORT})"
        )

        return parser.parse_args().port

    def client_parse_arguments(self):
        parser = self._create_parser("A client script for connecting to a server.")

        parser.add_argument(
            "role",
            type=str,
            help="The role of the client (e.g., cman, ghost, spectator)",
            choices=STR_TO_ROLE.keys()
        )
        parser.add_argument(
            "addr",
            type=str,
            help="The address to connect to (e.g., 127.0.0.1)"
        )
        parser.add_argument(
            "-p", "--port",
            type=int,
            default=DEFAULT_PORT,
            help=f"The port number to connect to (default: {DEFAULT_PORT})"
        )
        args = parser.parse_args()
        return STR_TO_ROLE[args.role], args.addr, args.port