from bilibili.util_classes import Command

command_mapping = {}




def parse_command(command, local="main"):
    if not command_mapping.get(local + "_" + command.split(" ")[0]):
        print("未知命令!")
        return
    command_class: Command = command_mapping.get(local + "_" + command.split(" ")[0])
    if len(command.split(" ")) - 1 > command_class.length:
        print("参数过多!")
        return
    if len(command.split(" ")) - 1 < command_class.length:
        print("参数过少!")
        return
    if command_class.should_run:
        command_class.run(*command.split(" ")[1:], *command_class.args, **command_class.kwargs)
    else:
        return command.split(" ")[0], command.split(" ")[1:]


def parse_text_command(command, local="main"):
    if not command_mapping.get(local + "_" + command.split(" ")[0]):
        print("未知命令!")
        return None, None
    command_class: Command = command_mapping.get(local + "_" + command.split(" ")[0])
    if len(command.split(" ")) - 1 > command_class.length:
        print("参数过多!")
        return None, None
    if len(command.split(" ")) - 1 < command_class.length:
        print("参数过少!")
        return None, None
    return command.split(" ")[0], command.split(" ")[1:]


def register_command(command, length, local="main", run=lambda: None, should_run=True, args=(), kwargs={}):
    command_mapping[local + "_" + command] = Command(local + "_" + command, length, run, should_run, args=args,
                                                     kwargs=kwargs)
