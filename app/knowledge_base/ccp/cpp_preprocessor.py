
import ctypes
from pathlib import Path

dll_path = Path(__file__).parent / "text_preprocessor.dll"

cpp_lib = ctypes.CDLL(str(dll_path))

cpp_lib.preprocess_text.argtypes = [
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_int
]

cpp_lib.preprocess_text.restype = ctypes.c_int


def preprocess_text(text: str) -> str:
    input_text = text.encode("utf-8")
    output_buffer = ctypes.create_string_buffer(len(input_text) + 1)
    result = cpp_lib.preprocess_text(
        input_text,
        output_buffer,
        len(output_buffer)
    )

    if result < 0:
        raise ValueError(f"C++ preprocessing error: {result}")

    return output_buffer.value.decode("utf-8")
