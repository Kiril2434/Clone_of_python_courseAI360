import builtins
import dis
import operator
import types
import typing as tp

from arg_binding import bind_args

NULL = object()
CO_COROUTINE = 0x0080
CO_ASYNC_GENERATOR = 0x0200

BINARY_OPS = {
    0: operator.add,
    1: operator.and_,
    2: operator.floordiv,
    3: operator.lshift,
    4: operator.matmul,
    5: operator.mul,
    6: operator.mod,
    7: operator.or_,
    8: operator.pow,
    9: operator.rshift,
    10: operator.sub,
    11: operator.truediv,
    12: operator.xor,
    13: operator.iadd,
    14: operator.iand,
    15: operator.ifloordiv,
    16: operator.ilshift,
    17: operator.imatmul,
    18: operator.imul,
    19: operator.imod,
    20: operator.ior,
    21: operator.ipow,
    22: operator.irshift,
    23: operator.isub,
    24: operator.itruediv,
    25: operator.ixor,
}

CMP_OPS = {
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
}


class CellType:
    def __init__(self, cell_contents=None):
        self.cell_contents = cell_contents


class VMTypeAlias:
    def __init__(self, name: str, evaluator: tp.Callable[[], tp.Any]):
        self.__name__ = name
        self._evaluator = evaluator

    @property
    def __value__(self) -> tp.Any:
        return self._evaluator()


class VMGenerator:
    def __init__(self, frame):
        self.frame = frame
        self.started = False
        self.finished = False
        flags = frame.code.co_flags
        self.is_coroutine = bool(flags & CO_COROUTINE)
        self.is_async_generator = bool(flags & CO_ASYNC_GENERATOR)

    def __iter__(self):
        return self

    def __await__(self):
        if not self.is_coroutine:
            raise TypeError("object is not awaitable")
        return self

    def __aiter__(self):
        if not self.is_async_generator:
            raise TypeError("object is not an async iterator")
        return self

    def __anext__(self):
        if not self.is_async_generator:
            raise TypeError("object is not an async iterator")

        gen = self

        class _AwaitableAnext:
            def __await__(self_inner):
                try:
                    value = gen.send(None)
                except StopIteration as e:
                    raise StopAsyncIteration(getattr(e, "value", None))
                if False:
                    yield None
                return value

        return _AwaitableAnext()

    def __next__(self):
        return self.send(None)

    def send(self, value):
        if self.finished:
            raise StopIteration(self.frame.return_value)

        if not self.started:
            if value is not None:
                raise TypeError("can't send non-None value to a just-started generator")
            self.started = True
        else:
            self.frame.push(value)

        self.frame.yielded = False

        try:
            val = self.frame.run()
        except StopIteration:
            self.finished = True
            raise
        except Exception:
            self.finished = True
            raise

        if self.frame.yielded:
            return val

        self.finished = True
        raise StopIteration(self.frame.return_value)

    def throw(self, typ, val=None, tb=None):
        raise typ(val).with_traceback(tb)

    def close(self):
        self.finished = True


class VMfunc:
    __slots__ = (
        "__code__",
        "__defaults__",
        "__kwdefaults__",
        "__closure__",
        "__annotations__",
        "_builtins",
        "_globals",
        "_locals",
        "__dict__",
    )

    def __init__(self, code, builtins_, globals_, locals_):
        self.__code__ = code
        self.__defaults__ = None
        self.__kwdefaults__ = None
        self.__closure__ = None
        self.__annotations__ = {}
        self.__name__ = code.co_name
        self.__qualname__ = code.co_qualname
        self.__module__ = globals_.get("__name__") if isinstance(globals_, dict) else None
        self.__doc__ = code.co_consts[0] if code.co_consts and isinstance(code.co_consts[0], str) else None
        self._builtins = builtins_
        self._globals = globals_
        self._locals = locals_

    def __call__(self, *args, **kwargs):
        parsed_args = bind_args(self, *args, **kwargs)
        frame = Frame(self.__code__, self._builtins, self._globals, dict(parsed_args), self.__closure__)
        return frame.run()

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return types.MethodType(self, instance)


class Frame:
    def __init__(
        self,
        frame_code: types.CodeType,
        frame_builtins: dict[str, tp.Any],
        frame_globals: dict[str, tp.Any],
        frame_locals: dict[str, tp.Any],
        closure: tuple = tuple(),
    ) -> None:
        self.code = frame_code
        if isinstance(frame_builtins, types.ModuleType):
            self.builtins = vars(frame_builtins)
        else:
            self.builtins = frame_builtins
        self.globals = frame_globals
        self.locals = frame_locals
        self.data_stack: tp.Any = []
        self.return_value: tp.Any = None
        self.index = 0
        self.instruction_index = {}
        self.instruction_count = 0
        self.yielded = False
        self.closure = closure if closure is not None else tuple()
        self.current_exception: BaseException | None = None

        self.cells = {}
        for var in self.code.co_cellvars:
            self.cells[var] = CellType()
        for var in self.code.co_freevars:
            self.cells[var] = CellType()

    def top(self) -> tp.Any:
        return self.data_stack[-1]

    def pop(self) -> tp.Any:
        return self.data_stack.pop()

    def push(self, *values: tp.Any) -> None:
        self.data_stack.extend(values)

    def popn(self, n: int) -> tp.Any:
        if n > 0:
            returned = self.data_stack[-n:]
            self.data_stack[-n:] = []
            return returned
        else:
            return []

    def run(self) -> tp.Any:
        instructions = list(dis.get_instructions(self.code))
        for i, instruction in enumerate(instructions):
            self.instruction_index[instruction.offset] = i

        if getattr(self, "initialized", False) is False:
            self.index = 0
            self.instruction_count = len(instructions)
            self.initialized = True

        self.yielded = False

        exception_table: tp.Iterable[tp.Any] = ()
        try:
            parse_exception_table = getattr(dis, "_parse_exception_table", None)
            if callable(parse_exception_table):
                exception_table = tp.cast(tp.Iterable[tp.Any], parse_exception_table(self.code))
        except Exception:
            pass

        while self.index < self.instruction_count:
            instruction = instructions[self.index]
            op_name = instruction.opname.lower() + "_op"
            op_func = getattr(self, op_name, None)

            if op_func is None:
                raise NotImplementedError(f"Opcode not implemented: {op_name}")

            try:
                op_func(instruction)
                self.index += 1
                if self.yielded:
                    return self.return_value
            except Exception as e:
                if isinstance(e, NotImplementedError):
                    raise e

                offset = instruction.offset
                handler_found = False
                for entry in exception_table:
                    if entry.start <= offset < entry.end:
                        self.data_stack = self.data_stack[: entry.depth]
                        if entry.lasti:
                            self.push(offset)
                        self.push(e)
                        self.index = self.instruction_index.get(entry.target, self.index + 1)
                        handler_found = True
                        break
                if not handler_found:
                    raise e

        return self.return_value

    def resume_op(self, instr: tp.Any) -> tp.Any:
        pass

    def push_null_op(self, instr: tp.Any) -> tp.Any:
        self.push(NULL)

    def precall_op(self, instr: tp.Any) -> tp.Any:
        pass

    def pop_top_op(self, instr: tp.Any) -> None:
        self.pop()

    def to_bool_op(self, instr: tp.Any):
        self.push(bool(self.pop()))

    def unpack_sequence_op(self, instr: tp.Any):
        seq = list(self.pop())
        expected = instr.arg
        actual = len(seq)
        if actual < expected:
            raise ValueError(f"not enough values to unpack (expected {expected}, got {actual})")
        if actual > expected:
            raise ValueError(f"too many values to unpack (expected {expected})")
        for item in reversed(seq):
            self.push(item)

    def unpack_ex_op(self, instr: tp.Any):
        seq = list(self.pop())
        before = instr.arg & 0xFF
        after = instr.arg >> 8
        first = seq[:before]
        if after > 0:
            middle = seq[before:-after]
            last = seq[-after:]
        else:
            middle = seq[before:]
            last = []
        for item in reversed(last):
            self.push(item)
        self.push(middle)
        for item in reversed(first):
            self.push(item)

    def load_name_op(self, instr: tp.Any) -> None:
        name = instr.argval
        if name in self.locals:
            self.push(self.locals[name])
        elif name in self.globals:
            self.push(self.globals[name])
        elif name in self.builtins:
            self.push(self.builtins[name])
        else:
            raise NameError(f"name '{name}' is not defined")

    def load_global_op(self, instr: tp.Any) -> None:
        name = instr.argval
        if name in self.globals:
            val = self.globals[name]
        elif name in self.builtins:
            val = self.builtins[name]
        else:
            raise NameError(f"name '{name}' is not defined")

        if instr.arg & 1:
            self.push(val)
            self.push(NULL)
        else:
            self.push(val)

    def load_const_op(self, instr: tp.Any) -> None:
        self.push(instr.argval)

    def load_fast_op(self, instr: tp.Any):
        name = instr.argval
        if name in self.locals:
            self.push(self.locals[name])
        else:
            raise UnboundLocalError(f"cannot access local variable '{name}' where it is not associated with a value")

    def load_fast_check_op(self, instr: tp.Any):
        name = instr.argval
        if name in self.locals:
            self.push(self.locals[name])
        else:
            raise UnboundLocalError(f"cannot access local variable '{name}' where it is not associated with a value")

    def load_fast_load_fast_op(self, instr):
        name1, name2 = instr.argval
        for name in (name1, name2):
            if name in self.locals:
                self.push(self.locals[name])
            else:
                raise UnboundLocalError(
                    f"cannot access local variable '{name}' where it is not associated with a value"
                )

    def load_fast_borrow_load_fast_borrow_op(self, instr: tp.Any):
        name1, name2 = instr.argval
        for name in (name1, name2):
            if name in self.locals:
                self.push(self.locals[name])
            else:
                raise UnboundLocalError(
                    f"cannot access local variable '{name}' where it is not associated with a value"
                )

    def load_attr_op(self, instr: tp.Any):
        obj = self.pop()
        name = instr.argval
        attr = getattr(obj, name)
        if instr.arg & 1:
            self.push(attr)
            self.push(NULL)
        else:
            self.push(attr)

    def store_name_op(self, instr: tp.Any) -> None:
        const = self.pop()
        self.locals[instr.argval] = const

    def store_global_op(self, instr: tp.Any) -> None:
        const = self.pop()
        self.globals[instr.argval] = const

    def store_fast_op(self, instr: tp.Any):
        val = self.pop()
        name = instr.argval
        self.locals[name] = val
        if name in self.cells:
            self.cells[name].cell_contents = val

    def store_fast_store_fast_op(self, instr: tp.Any):
        name1, name2 = instr.argval
        val1 = self.pop()
        val2 = self.pop()
        self.locals[name1] = val1
        if name1 in self.cells:
            self.cells[name1].cell_contents = val1
        self.locals[name2] = val2
        if name2 in self.cells:
            self.cells[name2].cell_contents = val2

    def store_fast_load_fast_op(self, instr: tp.Any):
        name1, name2 = instr.argval
        val1 = self.pop()
        self.locals[name1] = val1
        if name1 in self.cells:
            self.cells[name1].cell_contents = val1

        if name2 in self.locals:
            self.push(self.locals[name2])
        else:
            raise UnboundLocalError(f"cannot access local variable '{name2}' where it is not associated with a value")

    def format_with_spec_op(self, instr: tp.Any):
        spec = self.pop()
        value = self.pop()
        result = value.__format__(spec)
        self.push(result)

    def load_build_class_op(self, instr: tp.Any):
        def cl(func, name, *bases, **kwargs):
            resolved_bases = types.resolve_bases(bases)
            meta, ns, kwds = types.prepare_class(name, resolved_bases, kwargs)
            frame = Frame(func.__code__, func._builtins, func._globals, ns, func.__closure__)
            frame.run()
            class_cell = ns.pop("__classcell__", None)
            classdict_cell = ns.pop("__classdictcell__", None)
            cls = meta(name, resolved_bases, ns, **kwds)
            if isinstance(class_cell, CellType):
                class_cell.cell_contents = cls
            if isinstance(classdict_cell, CellType):
                classdict_cell.cell_contents = cls.__dict__
            return cls

        self.push(cl)

    def setup_annotations_op(self, instr: tp.Any):
        if "__annotations__" not in self.locals:
            self.locals["__annotations__"] = {}

    def extended_arg_op(self, instr: tp.Any):
        pass

    def return_const_op(self, instr: tp.Any) -> None:
        self.return_value = instr.argval
        self.index = self.instruction_count

    def return_value_op(self, instr: tp.Any) -> None:
        self.return_value = self.pop()
        self.index = self.instruction_count

    def return_generator_op(self, instr: tp.Any):
        gen = VMGenerator(self)
        self.return_value = gen
        self.yielded = True
        # In 3.13 generator code, RETURN_GENERATOR is followed by a synthetic POP_TOP.
        # Skip it so the first send() resumes at RESUME.
        self.index += 1

    def yield_value_op(self, instr: tp.Any):
        self.return_value = self.pop()
        self.yielded = True

    def binary_op_op(self, instr: tp.Any) -> tp.Any:
        rhs = self.pop()
        lhs = self.pop()
        self.push(BINARY_OPS[instr.arg](lhs, rhs))

    def contains_op_op(self, instr: tp.Any):
        b, a = self.pop(), self.pop()
        if instr.arg == 1:
            self.push(a not in b)
        else:
            self.push(a in b)

    def is_op_op(self, instr: tp.Any):
        b, a = self.pop(), self.pop()
        if instr.arg == 1:
            self.push(a is not b)
        else:
            self.push(a is b)

    def compare_op_op(self, instr: tp.Any):
        a, b = self.pop(), self.pop()
        op_str = dis.cmp_op[instr.arg >> 5]
        result = CMP_OPS[op_str](b, a)
        if instr.arg & 16:
            result = bool(result)
        self.push(result)

    def build_list_op(self, instr: tp.Any):
        if instr.arg == 0:
            value = []
        else:
            value = [self.pop() for _ in range(instr.arg)][::-1]
        self.push(value)

    def build_tuple_op(self, instr: tp.Any):
        if instr.arg == 0:
            value = ()
        else:
            value = tuple([self.pop() for _ in range(instr.arg)][::-1])
        self.push(value)

    def build_set_op(self, instr: tp.Any):
        if instr.arg == 0:
            value = set()
        else:
            value = set([self.pop() for _ in range(instr.arg)][::-1])
        self.push(value)

    def build_map_op(self, instr: tp.Any):
        res = {}
        items = []
        for i in range(instr.arg):
            value = self.pop()
            key = self.pop()
            items.append((key, value))
        for key, value in reversed(items):
            res[key] = value
        self.push(res)

    def dict_update_op(self, instr: tp.Any):
        map_obj = self.pop()
        self.data_stack[-instr.arg].update(map_obj)

    def dict_merge_op(self, instr: tp.Any):
        map_obj = self.pop()
        target = self.data_stack[-instr.arg]
        for key in map_obj:
            if key in target:
                raise KeyError(f"duplicate key: {key}")
            target[key] = map_obj[key]

    def list_extend_op(self, instr: tp.Any):
        seq = self.pop()
        list.extend(self.data_stack[-instr.arg], seq)

    def list_append_op(self, instr: tp.Any):
        val = self.pop()
        self.data_stack[-instr.arg].append(val)

    def map_add_op(self, instr: tp.Any):
        value = self.pop()
        key = self.pop()
        self.data_stack[-instr.arg][key] = value

    def set_add_op(self, instr: tp.Any):
        val = self.pop()
        self.data_stack[-instr.arg].add(val)

    def build_const_key_map_op(self, instr: tp.Any):
        seq = self.pop()
        values = [self.pop() for _ in range(instr.arg)][::-1]
        self.push({seq[i]: values[i] for i in range(instr.arg)})

    def set_update_op(self, instr: tp.Any):
        seq = self.pop()
        set.update(self.data_stack[-instr.arg], seq)

    def convert_value_op(self, instr: tp.Any):
        value = self.pop()
        if instr.arg == 1:
            result = str(value)
        elif instr.arg == 2:
            result = repr(value)
        else:
            result = ascii(value)
        self.push(result)

    def format_simple_op(self, instr: tp.Any):
        value = self.pop()
        result = value.__format__("")
        self.push(result)

    def build_string_op(self, instr: tp.Any):
        values = [self.pop() for _ in range(instr.arg)][::-1]
        self.push("".join(values))

    def store_subscr_op(self, instr: tp.Any):
        key = self.pop()
        container = self.pop()
        value = self.pop()
        container[key] = value

    def swap_op(self, instr: tp.Any):
        self.data_stack[-instr.arg], self.data_stack[-1] = self.data_stack[-1], self.data_stack[-instr.arg]

    def nop_op(self, instr: tp.Any):
        pass

    def binary_subscr_op(self, instr: tp.Any):
        __slice = self.pop()
        a = self.pop()
        self.push(a[__slice])

    def delete_subscr_op(self, instr: tp.Any):
        key = self.pop()
        container = self.pop()
        del container[key]

    def build_slice_op(self, instr: tp.Any):
        if instr.arg == 2:
            end = self.pop()
            start = self.pop()
            self.push(slice(start, end))
        else:
            step = self.pop()
            end = self.pop()
            start = self.pop()
            self.push(slice(start, end, step))

    def binary_slice_op(self, instr: tp.Any):
        end = self.pop()
        start = self.pop()
        container = self.pop()
        self.push(container[start:end])

    def store_slice_op(self, instr: tp.Any):
        end = self.pop()
        start = self.pop()
        container = self.pop()
        value = self.pop()
        container[start:end] = value

    def call_op(self, instr: tp.Any) -> None:
        arguments = self.popn(instr.arg)
        obj = self.pop()
        func = self.pop()
        if obj is not NULL:
            arguments = [obj] + arguments
        self.push(func(*arguments))

    def call_kw_op(self, instr: tp.Any):
        tpl = self.pop()
        arguments = self.popn(instr.arg)
        obj = self.pop()
        func = self.pop()
        arg = [arguments[i] for i in range(instr.arg - len(tpl))]
        kw = {tpl[i - instr.arg + len(tpl)]: arguments[i] for i in range(instr.arg - len(tpl), instr.arg)}
        if obj is not NULL:
            arg = [obj] + arg
        self.push(func(*arg, **kw))

    def call_function_ex_op(self, instr: tp.Any):
        if instr.arg & 1:
            kwargs = self.pop()
        else:
            kwargs = {}
        args = self.pop()
        obj = self.pop()
        func = self.pop()
        if obj is not NULL:
            args = (obj, *args)
        self.push(func(*args, **kwargs))

    def call_intrinsic_1_op(self, instr: tp.Any):
        value = self.pop()
        result = None
        match instr.arg:
            case 2:
                names = []
                if hasattr(value, "__all__"):
                    names = value.__all__
                else:
                    names = [name for name in dir(value) if name[0] != "_"]
                for name in names:
                    self.locals[name] = getattr(value, name)
            case 3:
                if isinstance(value, StopIteration):
                    err = RuntimeError("generator raised StopIteration")
                    err.__cause__ = value
                    err.__context__ = value
                    result = err
                else:
                    result = value
            case 5:
                result = +value
            case 6:
                result = tuple(value)
            case 4:
                result = value
            case 11:
                if isinstance(value, tuple) and len(value) == 3 and callable(value[2]):
                    name, _type_params, evaluator = value
                    result = VMTypeAlias(name, evaluator)
                else:
                    result = tp.TypeAliasType("TypeAlias", value)
        self.push(result)

    def call_intrinsic_2_op(self, instr: tp.Any):
        right = self.pop()
        left = self.pop()
        result = None
        match instr.arg:
            case 1:
                items: list[BaseException] = []
                if isinstance(right, list):
                    for item in right:
                        if isinstance(item, BaseException):
                            items.append(item)
                if not items:
                    result = None
                elif len(items) == 1:
                    result = items[0]
                else:
                    message = left.args[0] if isinstance(left, BaseExceptionGroup) and left.args else ""
                    result = ExceptionGroup(message, items)
        self.push(result)

    def make_function_op(self, instr):
        code = self.pop()
        fn = VMfunc(code, self.builtins, self.globals, self.locals)
        self.push(fn)

    def store_attr_op(self, instr: tp.Any):
        obj = self.pop()
        value = self.pop()
        setattr(obj, instr.argval, value)

    def delete_attr_op(self, instr: tp.Any):
        obj = self.pop()
        delattr(obj, instr.argval)

    def delete_name_op(self, instr: tp.Any) -> None:
        if instr.argval in self.locals:
            del self.locals[instr.argval]
        else:
            raise NameError(f"name '{instr.argval}' is not defined")

    def delete_global_op(self, instr: tp.Any) -> None:
        if instr.argval in self.globals:
            del self.globals[instr.argval]
        else:
            raise NameError(f"name '{instr.argval}' is not defined")

    def delete_fast_op(self, instr: tp.Any):
        name = instr.argval
        if name in self.locals:
            del self.locals[name]
        else:
            raise UnboundLocalError(f"cannot access local variable '{name}' where it is not associated with a value")

    def copy_op(self, instr: tp.Any):
        self.push(self.data_stack[-instr.arg])

    def import_name_op(self, instr: tp.Any):
        fromlist = self.pop()
        level = self.pop()
        module = __import__(instr.argval, self.globals, self.locals, fromlist, level)
        self.push(module)

    def import_from_op(self, instr: tp.Any):
        self.push(getattr(self.data_stack[-1], instr.argval))

    def set_function_attribute_op(self, instr: tp.Any):
        func = self.pop()
        value = self.pop()
        match instr.arg:
            case 0x01:
                func.__defaults__ = value
            case 0x02:
                func.__kwdefaults__ = value
            case 0x04:
                if isinstance(value, tuple):
                    func.__annotations__ = {value[i]: value[i + 1] for i in range(0, len(value), 2)}
                else:
                    func.__annotations__ = value
            case 0x08:
                if value is None:
                    func.__closure__ = None
                else:
                    func.__closure__ = tuple(cell if isinstance(cell, CellType) else CellType(cell) for cell in value)
        self.push(func)

    def unary_negative_op(self, instr: tp.Any):
        self.data_stack[-1] = -self.data_stack[-1]

    def unary_positive_op(self, instr: tp.Any):
        self.data_stack[-1] = +self.data_stack[-1]

    def unary_not_op(self, instr: tp.Any):
        self.data_stack[-1] = not self.data_stack[-1]

    def unary_invert_op(self, instr: tp.Any):
        self.data_stack[-1] = ~self.data_stack[-1]

    def get_iter_op(self, instr: tp.Any):
        self.push(iter(self.pop()))

    def for_iter_op(self, instr: tp.Any):
        try:
            self.push(next(self.top()))
        except StopIteration:
            self.index = self.instruction_index.get(instr.argval, self.index + 1) - 1

    def end_for_op(self, instr: tp.Any):
        pass

    def jump_backward_op(self, instr: tp.Any):
        self.index = self.instruction_index[instr.argval] - 1

    def jump_backward_no_interrupt_op(self, instr: tp.Any):
        self.index = self.instruction_index[instr.argval] - 1

    def jump_forward_op(self, instr: tp.Any):
        self.index = self.instruction_index[instr.argval] - 1

    def pop_jump_if_false_op(self, instr: tp.Any):
        if not self.pop():
            self.index = self.instruction_index[instr.argval] - 1

    def pop_jump_if_true_op(self, instr: tp.Any):
        if self.pop():
            self.index = self.instruction_index[instr.argval] - 1

    def load_assertion_error_op(self, instr: tp.Any):
        self.push(AssertionError)

    def raise_varargs_op(self, instr: tp.Any):
        if instr.arg == 0:
            if self.current_exception is None:
                raise RuntimeError("No active exception to reraise")
            raise self.current_exception
        elif instr.arg == 1:
            raise self.pop()
        else:
            t1, t2 = self.pop(), self.pop()
            raise t2 from t1

    def make_cell_op(self, instr: tp.Any):
        name = instr.argval
        if name not in self.cells:
            self.cells[name] = CellType()
        if name in self.locals:
            self.cells[name].cell_contents = self.locals[name]
        self.locals[name] = self.cells[name]

    def copy_free_vars_op(self, instr: tp.Any):
        if self.closure:
            for i, name in enumerate(self.code.co_freevars):
                if i < len(self.closure):
                    cell = self.closure[i]
                    if not isinstance(cell, CellType):
                        cell = CellType(cell)
                    self.cells[name] = cell
                    self.locals[name] = cell.cell_contents

    def load_closure_op(self, instr: tp.Any):
        self.push(self.cells[instr.argval])

    def load_deref_op(self, instr: tp.Any):
        self.push(self.cells[instr.argval].cell_contents)

    def store_deref_op(self, instr: tp.Any):
        val = self.pop()
        self.cells[instr.argval].cell_contents = val
        self.locals[instr.argval] = val

    def delete_deref_op(self, instr: tp.Any):
        try:
            del self.cells[instr.argval].cell_contents
        except AttributeError:
            pass

    def load_fast_and_clear_op(self, instr: tp.Any):
        name = instr.argval
        if name in self.locals:
            self.push(self.locals[name])
            del self.locals[name]
        else:
            self.push(NULL)

    def send_op(self, instr: tp.Any):
        val = self.pop()
        gen = self.top()
        try:
            if val is None:
                res = next(gen)
            else:
                if hasattr(gen, "send"):
                    res = gen.send(val)
                else:
                    raise TypeError("can't send non-None value to a just-started generator")
            self.push(res)
        except StopIteration as e:
            self.push(getattr(e, "value", None))
            self.index = self.instruction_index[instr.argval] - 1

    def end_send_op(self, instr: tp.Any):
        val = self.pop()
        self.pop()
        self.push(val)

    def get_yield_from_iter_op(self, instr: tp.Any):
        tos = self.top()
        if not hasattr(tos, "send"):
            self.data_stack[-1] = iter(tos)

    def get_awaitable_op(self, instr: tp.Any):
        obj = self.pop()
        if hasattr(obj, "__await__"):
            self.push(iter(obj.__await__()))
        elif hasattr(obj, "send"):
            self.push(obj)
        else:
            raise TypeError(f"object {type(obj).__name__!r} can't be used in 'await' expression")

    def get_aiter_op(self, instr: tp.Any):
        obj = self.pop()
        self.push(obj.__aiter__())

    def get_anext_op(self, instr: tp.Any):
        aiter = self.top()
        self.push(aiter.__anext__())

    def before_async_with_op(self, instr: tp.Any):
        mgr = self.top()
        exit_fn = mgr.__aexit__
        enter_awaitable = mgr.__aenter__()
        self.pop()
        self.push(exit_fn)
        self.push(enter_awaitable)

    def end_async_for_op(self, instr: tp.Any):
        exc = self.pop()
        if not isinstance(exc, StopAsyncIteration):
            raise exc

    def cleanup_throw_op(self, instr: tp.Any):
        exc = self.pop()
        if isinstance(exc, StopIteration):
            self.pop()
            self.push(getattr(exc, "value", None))
        else:
            raise exc

    def push_exc_info_op(self, instr: tp.Any):
        exc = self.pop()
        prev_exc = self.current_exception
        self.current_exception = exc if isinstance(exc, BaseException) else None
        self.push(prev_exc)
        self.push(exc)

    def pop_except_op(self, instr: tp.Any):
        prev_exc = self.pop()
        if isinstance(prev_exc, BaseException):
            self.current_exception = prev_exc
        else:
            self.current_exception = None

    def check_exc_match_op(self, instr: tp.Any):
        exc_type = self.pop()
        exc = self.top()
        self.push(isinstance(exc, exc_type))

    def check_eg_match_op(self, instr: tp.Any):
        exc_type = self.pop()
        exc = self.pop()
        if isinstance(exc, BaseExceptionGroup):
            matched, rest = exc.split(exc_type)
            self.push(rest)
            self.push(matched)
        else:
            self.push(None)
            self.push(None)

    def reraise_op(self, instr: tp.Any):
        if instr.arg == 0:
            raise self.pop()
        elif instr.arg in (1, 2):
            for i in range(1, min(4, len(self.data_stack)) + 1):
                exc = self.data_stack[-i]
                if isinstance(exc, BaseException):
                    raise exc
            raise TypeError("exceptions must derive from BaseException")

    def with_except_start_op(self, instr: tp.Any):
        exc = self.top()
        exit_fn = self.data_stack[-4]
        res = exit_fn(type(exc), exc, exc.__traceback__)
        self.push(res)

    def before_with_op(self, instr: tp.Any):
        mgr = self.top()
        exit_fn = mgr.__exit__
        res = mgr.__enter__()
        self.pop()
        self.push(exit_fn)
        self.push(res)

    def match_sequence_op(self, instr: tp.Any):
        self.push(isinstance(self.top(), (list, tuple)))

    def match_mapping_op(self, instr: tp.Any):
        self.push(isinstance(self.top(), dict))

    def match_keys_op(self, instr: tp.Any):
        keys = self.top()
        subject = self.data_stack[-2]
        if all(k in subject for k in keys):
            self.push(tuple(subject[k] for k in keys))
        else:
            self.push(None)

    def match_class_op(self, instr: tp.Any):
        names = self.pop()
        cls = self.pop()
        subject = self.pop()
        if isinstance(subject, cls):
            try:
                res = []
                match_args = getattr(cls, "__match_args__", ())
                for i in range(instr.arg):
                    res.append(getattr(subject, match_args[i]))
                for name in names:
                    res.append(getattr(subject, name))
                self.push(tuple(res))
            except Exception:
                self.push(None)
        else:
            self.push(None)

    def get_len_op(self, instr: tp.Any):
        self.push(len(self.top()))

    def pop_jump_if_none_op(self, instr: tp.Any):
        if self.pop() is None:
            self.index = self.instruction_index[instr.argval] - 1

    def pop_jump_if_not_none_op(self, instr: tp.Any):
        if self.pop() is not None:
            self.index = self.instruction_index[instr.argval] - 1

    def load_super_attr_op(self, instr: tp.Any):
        name = instr.argval
        self_val = self.pop()
        cls = self.pop()
        self.pop()
        sup = super(cls, self_val)
        attr = getattr(sup, name)
        if instr.arg & 1:
            self.push(attr)
            self.push(NULL)
        else:
            self.push(attr)

    def load_locals_op(self, instr: tp.Any):
        self.push(self.locals)

    def load_from_dict_or_globals_op(self, instr: tp.Any):
        d = self.pop()
        name = instr.argval
        if name in d:
            self.push(d[name])
        elif name in self.globals:
            self.push(self.globals[name])
        else:
            self.push(self.builtins[name])

    def load_from_dict_or_deref_op(self, instr: tp.Any):
        name = instr.argval
        d = self.pop()
        if name in d:
            self.push(d[name])
        else:
            self.push(self.cells[name].cell_contents)


class VirtualMachine:
    def run(self, code_obj: types.CodeType) -> None:
        globals_context: dict[str, tp.Any] = {}
        frame = Frame(code_obj, builtins.globals()["__builtins__"], globals_context, globals_context)
        return frame.run()
