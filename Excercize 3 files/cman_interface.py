from arg_parser import ArgParser as ap
from cman_client import Client

def main():
    role, addr, port = ap().client_parse_arguments()
    cman_client = Client(role, (addr, port))
    cman_client.run()

if __name__ == '__main__':
    main()