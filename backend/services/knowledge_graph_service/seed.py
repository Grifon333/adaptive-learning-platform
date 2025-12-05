import asyncio
import json
import os
import sys
import uuid

# Adjust path to import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

from src.database import close_driver, get_driver, init_driver

# --- Deterministic ID Generation ---
NAMESPACE_ALP = uuid.uuid5(uuid.NAMESPACE_DNS, "adaptive-learning-platform.com")


def get_uuid(name: str) -> str:
    return str(uuid.uuid5(NAMESPACE_ALP, name))


# --- DATASET ---

# 1. CONCEPTS
# Structure: Python Basics -> Control Flow -> Functions -> Data Structures -> OOP -> Error Handling
CONCEPTS_DATA = [
    {
        "name": "Python Syntax & Variables",
        "description": "Understanding variables, basic data types (int, float, str), and dynamic typing.",
        "difficulty": 1.0,
        "estimated_time": 45,
    },
    {
        "name": "Control Flow",
        "description": "Logic control using if-else statements, for loops, and while loops.",
        "difficulty": 1.5,
        "estimated_time": 60,
    },
    {
        "name": "Functions",
        "description": "Defining functions, arguments, return values, and scope.",
        "difficulty": 2.0,
        "estimated_time": 60,
    },
    {
        "name": "Data Structures",
        "description": "Working with Lists, Dictionaries, Sets, and Tuples.",
        "difficulty": 2.5,
        "estimated_time": 90,
    },
    {
        "name": "Object-Oriented Programming",
        "description": "Classes, Objects, Inheritance, and Encapsulation.",
        "difficulty": 3.0,
        "estimated_time": 120,
    },
    {
        "name": "Error Handling",
        "description": "Try-except blocks, raising exceptions, and debugging.",
        "difficulty": 2.0,
        "estimated_time": 45,
    },
]

# Generate UUIDs for linking
CONCEPTS = []
for c in CONCEPTS_DATA:
    c["id"] = get_uuid(str(c["name"]))
    CONCEPTS.append(c)

CID = {c["name"]: c["id"] for c in CONCEPTS}

# 2. RELATIONSHIPS
# (Start Name, End Name, Type, Weight)
# Implements Ep (Prerequisite) and Es (Semantic/Related)
RELATIONSHIPS_DATA = [
    # Prerequisites (Directed, Weighted)
    ("Python Syntax & Variables", "Control Flow", "PREREQUISITE", 0.9),
    ("Control Flow", "Data Structures", "PREREQUISITE", 0.8),
    ("Control Flow", "Functions", "PREREQUISITE", 0.85),
    ("Functions", "Object-Oriented Programming", "PREREQUISITE", 0.7),
    ("Data Structures", "Object-Oriented Programming", "PREREQUISITE", 0.6),
    # Semantic/Related (Bidirectional in Logic, Weight represents similarity)
    ("Control Flow", "Error Handling", "RELATED_TO", 0.5),  # Logic often needs error handling
    ("Functions", "Error Handling", "RELATED_TO", 0.4),  # Functions often raise errors
]

# 3. RESOURCES
# Linked by Concept Name
RESOURCES_DATA = [
    {
        "concept": "Python Syntax & Variables",
        "title": "Python Tutorial for Beginners - Full Course",
        "type": "video",
        "url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc",
        "duration": 60,
        "difficulty": 1.0,
    },
    {
        "concept": "Python Syntax & Variables",
        "title": "Official Python Docs - Variables",
        "type": "article",
        "url": "https://docs.python.org/3/tutorial/introduction.html",
        "duration": 15,
        "difficulty": 1.2,
    },
    {
        "concept": "Control Flow",
        "title": "Python If Else, For Loop, While Loop",
        "type": "video",
        "url": "https://www.youtube.com/watch?v=PqFKRqpHrjw",
        "duration": 30,
        "difficulty": 1.5,
    },
    {
        "concept": "Functions",
        "title": "Python Functions Explained",
        "type": "video",
        "url": "https://www.youtube.com/watch?v=NSbOtYzIQI0",
        "duration": 20,
        "difficulty": 2.0,
    },
    {
        "concept": "Data Structures",
        "title": "Lists, Tuples, Sets, and Dictionaries",
        "type": "video",
        "url": "https://www.youtube.com/watch?v=R-HLU9Fl5ug",
        "duration": 45,
        "difficulty": 2.5,
    },
    {
        "concept": "Object-Oriented Programming",
        "title": "OOP in Python",
        "type": "video",
        "url": "https://www.youtube.com/watch?v=JeznW_7DlB0",
        "duration": 50,
        "difficulty": 3.0,
    },
    {
        "concept": "Error Handling",
        "title": "Python Exception Handling",
        "type": "article",
        "url": "https://realpython.com/python-exceptions/",
        "duration": 20,
        "difficulty": 2.0,
    },
]


# 4. QUESTIONS (10 per concept)
# Helper to generate options JSON
def opts(correct_txt, *distractors):
    options = [{"text": correct_txt, "is_correct": True}]
    for d in distractors:
        options.append({"text": d, "is_correct": False})
    # Simple shuffle via sorting or leave as is (Frontend usually shuffles)
    return json.dumps(options)


QUESTIONS_DATA = [
    # --- C1: Syntax & Variables ---
    {
        "c": "Python Syntax & Variables",
        "t": "What is the output of `print(type(5))`?",
        "d": 1.0,
        "o": opts("<class 'int'>", "<class 'float'>", "int", "5"),
    },
    {
        "c": "Python Syntax & Variables",
        "t": "Which variable name is invalid?",
        "d": 1.0,
        "o": opts("2myvar", "myvar2", "_myvar", "MYVAR"),
    },
    {
        "c": "Python Syntax & Variables",
        "t": "How do you create a comment in Python?",
        "d": 1.0,
        "o": opts("# This is a comment", "// This is a comment", "", "/* Comment */"),
    },
    {
        "c": "Python Syntax & Variables",
        "t": "What is the correct file extension for Python files?",
        "d": 1.0,
        "o": opts(".py", ".python", ".pt", ".pyt"),
    },
    {
        "c": "Python Syntax & Variables",
        "t": "Which function outputs text to the screen?",
        "d": 1.0,
        "o": opts("print()", "echo()", "console.log()", "write()"),
    },
    {
        "c": "Python Syntax & Variables",
        "t": "x = '5'. What is the type of x?",
        "d": 1.2,
        "o": opts("String", "Integer", "Float", "Boolean"),
    },
    {
        "c": "Python Syntax & Variables",
        "t": "How do you cast a float 5.5 to an integer?",
        "d": 1.5,
        "o": opts("int(5.5)", "str(5.5)", "float(5.5)", "cast(5.5) "),
    },
    {
        "c": "Python Syntax & Variables",
        "t": "Which operator is used for exponentiation?",
        "d": 1.5,
        "o": opts("**", "^", "exp()", "power()"),
    },
    {
        "c": "Python Syntax & Variables",
        "t": "What is the value of 10 // 3?",
        "d": 1.8,
        "o": opts("3", "3.33", "3.0", "1"),
    },
    {
        "c": "Python Syntax & Variables",
        "t": "Is Python case sensitive?",
        "d": 1.0,
        "o": opts("Yes", "No", "Only for keywords", "Only for classes"),
    },
    # --- C2: Control Flow ---
    {"c": "Control Flow", "t": "Which keyword starts a loop?", "d": 1.5, "o": opts("for", "loop", "repeat", "cycle")},
    {
        "c": "Control Flow",
        "t": "How do you write an 'if' statement?",
        "d": 1.5,
        "o": opts("if x > y:", "if (x > y)", "if x > y then", "if x > y {}"),
    },
    {
        "c": "Control Flow",
        "t": "What does `break` do?",
        "d": 1.5,
        "o": opts("Stops the loop", "Restarts the loop", "Skips one iteration", "Exits the program"),
    },
    {
        "c": "Control Flow",
        "t": "What does `continue` do?",
        "d": 1.8,
        "o": opts("Skips to the next iteration", "Stops the loop", "Exits the function", "Nothing"),
    },
    {
        "c": "Control Flow",
        "t": "Which function generates a sequence of numbers?",
        "d": 1.5,
        "o": opts("range()", "seq()", "list()", "loop()"),
    },
    {
        "c": "Control Flow",
        "t": "What is the output of `bool(0)`?",
        "d": 1.8,
        "o": opts("False", "True", "None", "Error"),
    },
    {
        "c": "Control Flow",
        "t": "Which keyword handles the 'False' part of an condition?",
        "d": 1.5,
        "o": opts("else", "elif", "otherwise", "then"),
    },
    {
        "c": "Control Flow",
        "t": "What is the correct syntax for 'else if'?",
        "d": 1.5,
        "o": opts("elif", "else if", "elseif", "elsif"),
    },
    {"c": "Control Flow", "t": "How many times will `for i in range(3)` run?", "d": 1.5, "o": opts("3", "2", "4", "0")},
    {
        "c": "Control Flow",
        "t": "What signifies a block of code in Python?",
        "d": 1.2,
        "o": opts("Indentation", "Curly braces", "Parentheses", "Keywords"),
    },
    # --- C3: Functions ---
    {
        "c": "Functions",
        "t": "Which keyword defines a function?",
        "d": 2.0,
        "o": opts("def", "func", "function", "define"),
    },
    {
        "c": "Functions",
        "t": "How do you call a function named `my_func`?",
        "d": 2.0,
        "o": opts("my_func()", "call my_func", "my_func", "run my_func"),
    },
    {"c": "Functions", "t": "What keyword returns a value?", "d": 2.0, "o": opts("return", "output", "send", "result")},
    {
        "c": "Functions",
        "t": "Can a function call itself?",
        "d": 2.5,
        "o": opts("Yes, recursion", "No", "Only once", "Only in classes"),
    },
    {
        "c": "Functions",
        "t": "What are *args used for?",
        "d": 2.8,
        "o": opts("Variable positional arguments", "Keyword arguments", "Lists", "Tuples"),
    },
    {
        "c": "Functions",
        "t": "What are **kwargs used for?",
        "d": 2.8,
        "o": opts("Variable keyword arguments", "Positional arguments", "Dictionaries", "Sets"),
    },
    {
        "c": "Functions",
        "t": "What is a lambda function?",
        "d": 2.5,
        "o": opts("Anonymous small function", "A large class method", "A variable", "A loop"),
    },
    {
        "c": "Functions",
        "t": "Default arguments must follow non-default arguments.",
        "d": 2.2,
        "o": opts("True", "False", "Doesn't matter", "Python version dependent"),
    },
    {
        "c": "Functions",
        "t": "Variables defined inside a function are...",
        "d": 2.0,
        "o": opts("Local scope", "Global scope", "Universal scope", "Class scope"),
    },
    {
        "c": "Functions",
        "t": "Which keyword creates a global variable inside a function?",
        "d": 2.2,
        "o": opts("global", "all", "world", "extern"),
    },
    # --- C4: Data Structures ---
    {
        "c": "Data Structures",
        "t": "Which collection is ordered and changeable?",
        "d": 2.5,
        "o": opts("List", "Tuple", "Set", "Dictionary"),
    },
    {
        "c": "Data Structures",
        "t": "Which collection is ordered and unchangeable?",
        "d": 2.5,
        "o": opts("Tuple", "List", "Set", "Dictionary"),
    },
    {
        "c": "Data Structures",
        "t": "Which collection allows no duplicates?",
        "d": 2.5,
        "o": opts("Set", "List", "Tuple", "Dictionary"),
    },
    {
        "c": "Data Structures",
        "t": "How do you access a value in a dictionary?",
        "d": 2.5,
        "o": opts("Key", "Index", "Value", "Order"),
    },
    {"c": "Data Structures", "t": "What is the syntax for a list?", "d": 2.0, "o": opts("[]", "{}", "()", "<>")},
    {"c": "Data Structures", "t": "What is the syntax for a dictionary?", "d": 2.0, "o": opts("{}", "[]", "()", "<>")},
    {
        "c": "Data Structures",
        "t": "How do you add an item to a list?",
        "d": 2.2,
        "o": opts("append()", "add()", "push()", "insert()"),
    },
    {
        "c": "Data Structures",
        "t": "How do you remove the last item from a list?",
        "d": 2.2,
        "o": opts("pop()", "remove()", "delete()", "clear()"),
    },
    {
        "c": "Data Structures",
        "t": "Can a tuple contain a list?",
        "d": 2.8,
        "o": opts("Yes", "No", "Only if empty", "Only integers"),
    },
    {
        "c": "Data Structures",
        "t": "What is the length function?",
        "d": 2.0,
        "o": opts("len()", "length()", "count()", "size()"),
    },
    # --- C5: OOP ---
    {
        "c": "Object-Oriented Programming",
        "t": "Which keyword defines a class?",
        "d": 3.0,
        "o": opts("class", "object", "struct", "define"),
    },
    {
        "c": "Object-Oriented Programming",
        "t": "What is `__init__`?",
        "d": 3.0,
        "o": opts("Constructor", "Destructor", "Import", "String representation"),
    },
    {
        "c": "Object-Oriented Programming",
        "t": "What does `self` represent?",
        "d": 3.0,
        "o": opts("The current instance", "The class", "The parent", "Global scope"),
    },
    {
        "c": "Object-Oriented Programming",
        "t": "How do you inherit from a class?",
        "d": 3.2,
        "o": opts(
            "class Child(Parent):",
            "class Child extends Parent:",
            "class Child implements Parent:",
            "class Child : Parent",
        ),
    },
    {
        "c": "Object-Oriented Programming",
        "t": "What is polymorphism?",
        "d": 3.5,
        "o": opts("Different classes, same method name", "Hiding data", "Creating objects", "Importing modules"),
    },
    {
        "c": "Object-Oriented Programming",
        "t": "Which method returns string representation?",
        "d": 3.2,
        "o": opts("__str__", "__init__", "__repr__", "__string__"),
    },
    {
        "c": "Object-Oriented Programming",
        "t": "Can a class inherit multiple classes?",
        "d": 3.5,
        "o": opts("Yes", "No", "Only in Python 2", "Only interfaces"),
    },
    {
        "c": "Object-Oriented Programming",
        "t": "What is encapsulation?",
        "d": 3.2,
        "o": opts("Restricting access to methods/vars", "Inheriting methods", "Polymorphism", "Looping"),
    },
    {
        "c": "Object-Oriented Programming",
        "t": "How do you denote a private variable?",
        "d": 3.2,
        "o": opts("__var", "_var", "var", "private var"),
    },
    {
        "c": "Object-Oriented Programming",
        "t": "What is an instance?",
        "d": 3.0,
        "o": opts("An object created from a class", "A function", "A library", "A variable"),
    },
    # --- C6: Error Handling ---
    {
        "c": "Error Handling",
        "t": "Which block catches exceptions?",
        "d": 2.0,
        "o": opts("except", "catch", "error", "handle"),
    },
    {
        "c": "Error Handling",
        "t": "Which block runs regardless of errors?",
        "d": 2.2,
        "o": opts("finally", "always", "done", "end"),
    },
    {
        "c": "Error Handling",
        "t": "How do you manually trigger an error?",
        "d": 2.5,
        "o": opts("raise", "throw", "error", "trigger"),
    },
    {
        "c": "Error Handling",
        "t": "What is the parent class of most errors?",
        "d": 2.5,
        "o": opts("Exception", "Error", "Base", "Object"),
    },
    {
        "c": "Error Handling",
        "t": "Can you have multiple except blocks?",
        "d": 2.0,
        "o": opts("Yes", "No", "Only two", "Only nested"),
    },
    {
        "c": "Error Handling",
        "t": "What happens if an error is not caught?",
        "d": 2.0,
        "o": opts("Program crashes", "Ignored", "Retries", "Logs warning"),
    },
    {
        "c": "Error Handling",
        "t": "What does `else` do in a try-except block?",
        "d": 2.8,
        "o": opts("Runs if no error occurs", "Runs if error occurs", "Runs always", "Invalid syntax"),
    },
    {
        "c": "Error Handling",
        "t": "Is syntax error caught by try-except?",
        "d": 2.5,
        "o": opts("No, usually parsing error", "Yes", "Depends on OS", "Only in functions"),
    },
    {
        "c": "Error Handling",
        "t": "Can you catch multiple exceptions in one line?",
        "d": 2.5,
        "o": opts("Yes, (Error1, Error2)", "No", "Use OR", "Use AND"),
    },
    {
        "c": "Error Handling",
        "t": "Which error occurs for division by zero?",
        "d": 2.0,
        "o": opts("ZeroDivisionError", "MathError", "ValueError", "CalculationError"),
    },
]


async def seed():
    logger.info("Seeding Neo4j database with Python Track...")
    await init_driver()
    driver = get_driver()

    async with driver.session() as session:
        # 1. Clear DB
        logger.warning("Clearing existing database...")
        await session.run("MATCH (n) DETACH DELETE n")

        # 2. Insert Concepts
        logger.info(f"Inserting {len(CONCEPTS)} Concepts...")
        for c in CONCEPTS:
            await session.run(
                """
                MERGE (c:Concept {id: $id})
                SET c.name = $name,
                    c.description = $description,
                    c.difficulty = $difficulty,
                    c.estimated_time = $estimated_time
                """,
                **c,
            )

        # 3. Insert Resources
        logger.info(f"Inserting {len(RESOURCES_DATA)} Resources...")
        for r in RESOURCES_DATA:
            r_id = get_uuid(r["url"])  # Unique by URL
            c_id = CID.get(r["concept"])
            if not c_id:
                logger.warning(f"Skipping resource for unknown concept: {r['concept']}")
                continue

            # Create Resource
            await session.run(
                """
                MERGE (r:Resource {id: $id})
                SET r.title = $title,
                    r.type = $type,
                    r.url = $url,
                    r.duration = $duration,
                    r.difficulty = $difficulty
                """,
                id=r_id,
                **r,
            )
            # Link to Concept
            await session.run(
                """
                MATCH (c:Concept {id: $cid}), (r:Resource {id: $rid})
                MERGE (c)-[:HAS_RESOURCE]->(r)
                """,
                cid=c_id,
                rid=r_id,
            )

        # 4. Insert Questions
        logger.info(f"Inserting {len(QUESTIONS_DATA)} Questions...")
        for _i, q in enumerate(QUESTIONS_DATA):
            q_id = get_uuid(f"{q['c']}_{q['t']}")
            c_id = CID.get(q["c"])
            if not c_id:
                continue

            await session.run(
                """
                MERGE (q:Question {id: $id})
                SET q.text = $text,
                    q.options = $options,
                    q.difficulty = $difficulty
                """,
                id=q_id,
                text=q["t"],
                options=q["o"],
                difficulty=q["d"],
            )

            await session.run(
                """
                MATCH (c:Concept {id: $cid}), (q:Question {id: $qid})
                MERGE (c)-[:HAS_QUESTION]->(q)
                """,
                cid=c_id,
                qid=q_id,
            )

        # 5. Insert Relationships (Weighted & Types)
        logger.info(f"Inserting {len(RELATIONSHIPS_DATA)} Relationships...")
        for start_name, end_name, r_type, weight in RELATIONSHIPS_DATA:
            start_id = CID.get(start_name)
            end_id = CID.get(end_name)

            if not start_id or not end_id:
                logger.warning(f"Skipping link {start_name}->{end_name}")
                continue

            if r_type == "RELATED_TO":
                # Bidirectional for Es
                await session.run(
                    """
                    MATCH (a:Concept {id: $start}), (b:Concept {id: $end})
                    MERGE (a)-[r1:RELATED_TO]->(b) SET r1.weight = $w
                    MERGE (b)-[r2:RELATED_TO]->(a) SET r2.weight = $w
                    """,
                    start=start_id,
                    end=end_id,
                    w=weight,
                )
            else:
                # Directed for Ep
                await session.run(
                    """
                    MATCH (a:Concept {id: $start}), (b:Concept {id: $end})
                    MERGE (a)-[r:PREREQUISITE]->(b) SET r.weight = $w
                    """,
                    start=start_id,
                    end=end_id,
                    w=weight,
                )

    await close_driver()
    logger.success("Database seeded successfully with Python Logic Track!")


if __name__ == "__main__":
    asyncio.run(seed())
