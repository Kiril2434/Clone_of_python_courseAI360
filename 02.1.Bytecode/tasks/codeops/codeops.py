import types
import dis

def count_operations(source_code: types.CodeType) -> dict[str, int]:
    """Count byte code operations in given source code.

    :param source_code: the bytecode operation names to be extracted from
    :return: operation counts
    """
    res = {}
    for instr in dis.get_instructions(source_code):
        if (str(instr.opname) not in res):
            res[str(instr.opname)] = 0
        res[instr.opname] += 1
    for f in source_code.co_consts:
        if isinstance(f, types.CodeType):
            for name, number in count_operations(f).items():
                if (name not in res):
                    res[name] = 0
                res[name] += number
    return res
