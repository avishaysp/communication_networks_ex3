from arg_parser import ArgParser as ap
from cman_server_impl import CManServer


def main():
    port = ap().server_parse_arguments()
    cman_server = CManServer(port)
    cman_server.start_server()



if __name__ == "__main__":
    main()