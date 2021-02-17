###################################
#      John Moore - COMP 431      #
#     FTP Client Starter Code     #
#           Version 1.0           #
###################################

# This program will ultimately be a complete FTP client according to the client specifications 
# provided in the assignment writeup. Currently, this program reads user input from stdin, 
# parses the input, and generates the appropriate FTP commands. Your task is to integrate this I/O 
# with sockets to allow actual communication with the server program. A completed client program will
# read high-level commands from stdin, convert these commands into FTP commands that get sent to the server
# over an established socket, and then parse the command replies the server sends back over the socket. 
# Additionally, file data will be read over an ftp_data connection, and subsequently written to an appropriately
# named file on the client machine.

import sys
import os
import socket

# Define dictionary of useful ASCII codes
# Use ord(char) to get decimal ascii code for char
ascii_codes = {
    "A": ord("A"), "Z": ord("Z"), 
    "a": ord("a"), "z": ord("z"), 
    "0": ord("0"), "9": ord("9"),
    "min_ascii_val": 0, "max_ascii_val": 127}

##############################################################################################
#                                                                                            # 
#     This function is intended to manage the command processing loop.                       #
#     The general idea is to loop over the input stream, identify which command              #
#     was entered, and then delegate the command-processing to the appropriate function.     #
#                                                                                            #
##############################################################################################
def read_commands():
    # Initially, only the CONNECT command is valid
    expected_commands = ["CONNECT"]

    for command in sys.stdin:
        # Echo command exactly as it was input
        sys.stdout.write(command)

        # Extract command name from input, assuming commands are case-insensitive
        command_name = command.split()[0]

        if command.split()[0].upper() in expected_commands:
            if command_name == "CONNECT":
                response, port_num = parse_connect(command)
                print(response)
                if "ERROR" not in response:
                    generate_connect_output()
                    expected_commands = ["CONNECT", "GET", "QUIT"]
            elif command_name == "GET":
                response, file_path = parse_get(command)
                if "ERROR" not in response:
                    print(response)
                    generate_get_output(port_num, file_path)
                    port_num += 1
                    expected_commands = ["CONNECT", "GET", "QUIT"]
            elif command_name == "QUIT":
                if "ERROR" not in response:
                    response = parse_quit(command)
                    print(response)
                    generate_quit_output()
        else:
            print("ERROR -- Command Unexpected/Unknown")

##############################################################
#       The following three methods are for generating       #
#       the appropriate output for each valid command.       #
##############################################################
def generate_connect_output():
    print("USER anonymous")
    print("PASS guest@")
    print("SYST")
    print("TYPE I")

def generate_get_output(port_num, file_path):
    my_ip = socket.gethostbyname(socket.gethostname()).replace('.', ',')
    port_num_formatted = f"{int(int(port_num) / 256)},{int(port_num) % 256}"      # int() automatically floors its arg
    print(f"PORT {my_ip},{port_num_formatted}")
    print(f"RETR {file_path}")

def generate_quit_output():
    print("QUIT")
    sys.exit(0)


##############################################################
#         Any method below this point is for parsing         #
##############################################################

# CONNECT<SP>+<server-host><SP>+<server-port><EOL>
def parse_connect(command):
    server_host = ""

    if command[0:7] != "CONNECT" or len(command) == 7:
        return "ERROR -- request", server_host
    command = command[7:]
    
    command = parse_space(command)
    if len(command) > 1:
        command, server_host = parse_server_host(command)
    else:
        command = "ERROR -- server-host"

    if "ERROR" in command:
        return command, server_host

    command = parse_space(command)
    if len(command) > 1:
        command, server_port = parse_server_port(command)
    else:
        command = "ERROR -- server-port"

    server_port = int(server_port)
    
    if "ERROR" in command:
        return command, server_host
    elif command != '\r\n' and command != '\n':
        return "ERROR -- <CRLF>", server_host
    return f"CONNECT accepted for FTP server at host {server_host} and port {server_port}", server_port

# GET<SP>+<pathname><EOL>
def parse_get(command):
    if command[0:3] != "GET":
        return "ERROR -- request"
    command = command[3:]
    
    command = parse_space(command)
    command, pathname = parse_pathname(command)

    if "ERROR" in command:
        return command
    elif command != '\r\n' and command != '\n':
        return "ERROR -- <CRLF>"
    return f"GET accepted for {pathname}", pathname

# QUIT<EOL>
def parse_quit(command):
    if command != "QUIT\r\n" and command != "QUIT\n":
        return "ERROR -- <CRLF>"
    else:
        return "QUIT accepted, terminating FTP client"

# <server-host> ::= <domain>
def parse_server_host(command):
    command, server_host = parse_domain(command)
    if command == "ERROR":
        return "ERROR -- server-host", server_host
    else:
        return command, server_host

# <server-port> ::= character representation of a decimal integer in the range 0-65535 (09678 is not ok; 9678 is ok)
def parse_server_port(command):
    port_nums = []
    port_string = ""
    for char in command:
        if ord(char) >= ascii_codes["0"] and ord(char) <= ascii_codes["9"]:
            port_nums.append(char)
            port_string += char
        else:
            break
    if len(port_nums) < 5:
        if ord(port_nums[0]) == ascii_codes["0"] and len(port_nums) > 1:
            return "ERROR -- server-port"
        return command[len(port_nums):], port_string
    elif len(port_nums) == 5:
        if ord(port_nums[0]) == ascii_codes["0"] or  int(command[0:5]) > 65535:
            return "ERROR -- server-port"
    return command[len(port_nums):], port_string

# <pathname> ::= <string>
# <string> ::= <char> | <char><string>
# <char> ::= any one of the 128 ASCII characters
def parse_pathname(command):
    pathname = ""
    if command[0] == '\n' or command[0:2] == '\r\n':
        return "ERROR -- pathname", pathname
    else:
        while len(command) > 1:
            if len(command) == 2 and command[0:2] == '\r\n':
                return command, pathname
            elif ord(command[0]) >= ascii_codes["min_ascii_val"] and ord(command[0]) <= ascii_codes["max_ascii_val"]:
                pathname += command[0]
                command = command[1:]
            else:
                return "ERROR -- pathname", pathname
        return command, pathname

# <domain> ::= <element> | <element>"."<domain>
def parse_domain(command):
    command, server_host = parse_element(command)
    return command, server_host

# <element> ::= <a><let-dig-hyp-str>
def parse_element(command, element_string=""):
    # Keep track of all elements delimited by "." to return to calling function

    # Ensure first character is a letter
    if (ord(command[0]) >= ascii_codes["A"] and ord(command[0]) <= ascii_codes["Z"]) \
    or (ord(command[0]) >= ascii_codes["a"] and ord(command[0]) <= ascii_codes["z"]):
        element_string += command[0]
        command, let_dig_string = parse_let_dig_str(command[1:])
        element_string += let_dig_string
        if command[0] == ".":
            element_string += "."
            return parse_element(command[1:], element_string)
        elif command[0] == ' ':
            return command, element_string
        else:
            return "ERROR", element_string
    elif command[0] == ' ':
        return command, element_string
    return "ERROR", element_string

# <let-dig-hyp-str> ::= <let-dig-hyp> | <let-dig-hyp><let-dig-hyp-str>
# <a> ::= any one of the 52 alphabetic characters "A" through "Z"in upper case and "a" through "z" in lower case
# <d> ::= any one of the characters representing the ten digits 0 through 9
def parse_let_dig_str(command):
    let_dig_string = ""
    while (ord(command[0]) >= ascii_codes["A"] and ord(command[0]) <= ascii_codes["Z"]) \
    or (ord(command[0]) >= ascii_codes["a"] and ord(command[0]) <= ascii_codes["z"]) \
    or (ord(command[0]) >= ascii_codes["0"] and ord(command[0]) <= ascii_codes["9"]) \
    or (ord(command[0]) == ord('-')):
        let_dig_string += command[0]
        if len(command) > 1:
            command = command[1:]
        else:
            return command, let_dig_string
    return command, let_dig_string

# <SP>+ ::= one or more space characters
def parse_space(line):
    if line[0] != ' ':
        return "ERROR"
    while line[0] == ' ':
        line = line[1:]
    return line

read_commands()