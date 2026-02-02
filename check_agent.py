from pydantic_ai import Agent
from pydantic import BaseModel
import pydantic_ai


class M(BaseModel):
    x: int


print(f"Pydantic AI version: {pydantic_ai.__version__}")
try:
    a = Agent("google-gla:gemini-1.5-flash", result_type=M)
    print("Agent created succeeded with result_type")
except TypeError as e:
    print(f"Agent failed with TypeError: {e}")
except Exception as e:
    print(f"Agent failed with other error: {e}")

try:
    a = Agent("google-gla:gemini-1.5-flash", output_type=M)
    print("Agent created succeeded with output_type")
except TypeError as e:
    print(f"Agent failed with TypeError: {e}")
except Exception as e:
    print(f"Agent failed with other error: {e}")
