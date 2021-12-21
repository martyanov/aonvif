#!/usr/bin/python

import argparse
import ast
import cmd
import os.path
import re

import zeep.exceptions
import zeep.xsd

from . import client
from . import exceptions
from . import wsdl


SUPPORTED_SERVICES = wsdl.SERVICES.keys()


class ThrowingArgumentParser(argparse.ArgumentParser):
    """Exception throwing argument parser."""

    def error(self, message):
        usage = self.format_usage()
        raise ValueError(f'{message}\n{usage}')


def success(message):
    """Print success message."""
    print(f'True: {message!r}')


def error(message):
    """Print error message."""
    print(f'False: {message!r}')


class ONVIFCLI(cmd.Cmd):
    """ONVIF CLI class."""

    prompt = 'ONVIF >>> '
    client = None
    cmd_parser = None

    def setup(self, args):
        """Setup parser."""
        # Create onvif camera client
        self.client = client.ONVIFCamera(
            args.host,
            args.port,
            args.user,
            args.password,
            args.wsdl,
            encrypt=args.encrypt,
        )

        # Create cmd argument parser
        self.create_cmd_parser()

    def create_cmd_parser(self):
        """Create parser to parse CMD, params is optional."""
        cmd_parser = ThrowingArgumentParser(
            prog='ONVIF CMD',
            usage='CMD service operation [params]',
        )
        cmd_parser.add_argument('service')
        cmd_parser.add_argument('operation')
        cmd_parser.add_argument(
            'params',
            default='{}',
            nargs=argparse.REMAINDER,
        )
        self.cmd_parser = cmd_parser

    def do_cmd(self, line):
        """Usage: CMD service operation [parameters]."""
        try:
            args = self.cmd_parser.parse_args(line.split())
        except ValueError as err:
            return error(err)

        # Check if args.service is valid
        if args.service not in SUPPORTED_SERVICES:
            return error(f'No Service: {args.service}')

        args.params = ''.join(args.params)
        # params is optional
        if not args.params.strip():
            args.params = '{}'

        # params must be a dictionary format string
        match = re.match(r'^.*?(\{.*\}).*$', args.params)
        if not match:
            return error('Invalid params')

        try:
            args.params = dict(ast.literal_eval(match.group(1)))
        except ValueError as e:
            return error(f'Invalid params: {e!r}')

        try:
            # Get ONVIF service
            service = self.client.get_service(args.service)
            # Actually execute the command and get the response
            response = getattr(service, args.operation)(args.params)
        except zeep.exceptions.LookupError:
            return error(f'No Operation: {args.operation}')
        except Exception as err:
            return error(err)

        if isinstance(response, (zeep.xsd.String, bool)):
            return success(response)
        # Try to convert instance to dictionary
        try:
            success(client.ONVIFService.to_dict(response))
        except exceptions.ONVIFError:
            error({})

    def complete_cmd(self, text, line, begidx, endidx):
        """Complete command."""
        if not text:
            completions = SUPPORTED_SERVICES[:]
        else:
            completions = [
                key
                for key in SUPPORTED_SERVICES
                if key.startswith(text)
            ]
        return completions

    def emptyline(self):
        """Empty line."""
        return ''

    def do_EOF(self, line):  # noqa: N802
        """End of file."""
        return True


def create_parser():
    """Create parser."""
    parser = ThrowingArgumentParser(description=__doc__)
    # Dealwith dependency for service, operation and params
    parser.add_argument(
        'service',
        nargs='?',
        help='Service defined by ONVIF WSDL document',
    )
    parser.add_argument(
        'operation',
        nargs='?',
        default='',
        help='Operation to be execute defined by ONVIF WSDL document',
    )
    parser.add_argument(
        'params',
        default='',
        nargs='?',
        help='JSON format params passed to the operation. E.g., "{"Name": "NewHostName"}"',
    )
    parser.add_argument(
        '--host',
        required=True,
        help='ONVIF camera host, e.g. 192.168.2.123, www.example.com',
    )
    parser.add_argument(
        '--port',
        default=80,
        type=int,
        help='Port number for camera, default: 80',
    )
    parser.add_argument(
        '-u',
        '--user',
        required=True,
        help='Username for authentication',
    )
    parser.add_argument(
        '-a',
        '--password',
        required=True,
        help='Password for authentication',
    )
    parser.add_argument(
        '-w',
        '--wsdl',
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wsdl'),
        help='directory to store ONVIF WSDL documents',
    )
    parser.add_argument(
        '-e',
        '--encrypt',
        default='False',
        help='Encrypt password or not',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='increase output verbosity',
    )
    parser.add_argument(
        '--cache-location',
        dest='cache_location',
        default='/tmp/onvif/',
        help='location to cache suds objects, default to /tmp/onvif/',
    )
    parser.add_argument(
        '--cache-duration',
        dest='cache_duration',
        help='how long will the cache be exist',
    )

    return parser


def main():
    """Main entrypoint."""
    # Create argument parser
    parser = create_parser()
    try:
        args = parser.parse_args()
    except ValueError as err:
        print(str(err))
        return
    # Also need parse configuration file.

    # Interactive command loop
    cli = ONVIFCLI(stdin=input)
    cli.setup(args)
    if args.service:
        cmd = ' '.join(['cmd', args.service, args.operation, args.params])
        cli.onecmd(cmd)
    # Execute command specified and exit
    else:
        cli.cmdloop()


if __name__ == '__main__':
    main()
