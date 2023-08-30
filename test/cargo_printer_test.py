import unittest
from dataclasses import dataclass
from enum import Enum
from typing import List

from models.decorators import desynced_object
from models.decorators_options import FieldOptions, ListFieldOptions, annotate
from wiki.cargo.analyze_type import ListTypeInfo, TypeInfo, analyze_type
from wiki.cargo.cargo_printer import CargoPrinter


class TestAnalyzeType(unittest.TestCase):
    def test_analyze_simple_dataclass(self):
        @dataclass
        class Simple:
            name: str
            age: int

        type_info = analyze_type(Simple)
        self.assertDictEqual(
            type_info.fields, {"name": TypeInfo(str), "age": TypeInfo(int)}
        )

    def test_analyze_list_with_max_length(self):
        @desynced_object
        class WithList:
            items: List[int] = annotate(ListFieldOptions(max_length=5))

        type_info = analyze_type(WithList)
        self.assertDictEqual(
            type_info.fields,
            {
                "items": ListTypeInfo(
                    type=TypeInfo(int),
                    list_options=ListFieldOptions(max_length=5),
                )
            },
        )


class TestDataclassPrinter(unittest.TestCase):
    def test_print_simple_dataclass(self):
        @desynced_object
        class Simple:
            name: str
            age: int

        obj = Simple(name="Alice", age=28)
        output = CargoPrinter().print_dataclass(obj, analyze_type(Simple))
        self.assertListEqual(output, ["|name = Alice", "|age = 28"])

    def test_print_list_with_max_length(self):
        @desynced_object
        class WithList:
            items: List[int] = annotate(ListFieldOptions(max_length=5))

        obj = WithList(items=[1, 2])
        output = CargoPrinter().print_dataclass(obj, analyze_type(WithList))
        self.assertListEqual(
            output,
            [
                "|items1 = 1",
                "|items2 = 2",
                "|items3 = ",
                "|items4 = ",
                "|items5 = ",
            ],
        )

    def test_print_nested_dataclass(self):
        @desynced_object
        class Nested:
            inner_field: str

        @desynced_object
        class Parent:
            name: str
            nested_obj: Nested

        obj = Parent(name="Bob", nested_obj=Nested(inner_field="value"))
        output = CargoPrinter().print_dataclass(obj, analyze_type(Parent))
        self.assertListEqual(output, ["|name = Bob", "|innerField = value"])

    def test_empty_dataclass(self):
        @dataclass
        class Empty:
            pass

        obj = Empty()
        output = CargoPrinter().print_dataclass(obj, analyze_type(Empty))
        self.assertListEqual(output, [])

    def test_enum_fields(self):
        class Color(Enum):
            RED = "red"
            BLUE = "blue"

        @dataclass
        class WithEnum:
            color: Color

        obj = WithEnum(color=Color.RED)
        output = CargoPrinter().print_dataclass(obj, analyze_type(WithEnum))
        self.assertListEqual(output, ["|color = red"])

    def test_list_of_nested_dataclass(self):
        @dataclass
        class Nested:
            value: str

        @dataclass
        class WithList:
            items: List[Nested] = annotate(ListFieldOptions(max_length=3))

        obj = WithList(items=[Nested(value="item1"), Nested(value="item2")])
        output = CargoPrinter().print_dataclass(obj, analyze_type(WithList))
        self.assertListEqual(
            output,
            [
                "|value1 = item1",
                "|value2 = item2",
                "|value3 = ",
            ],
        )

    def test_nested_list(self):
        @dataclass
        class WithNestedList:
            matrix: List[List[int]] = annotate(ListFieldOptions(max_length=3))

        obj = WithNestedList(matrix=[[1, 2], [3, 4]])
        type_info = analyze_type(WithNestedList)
        output = CargoPrinter().print_dataclass(obj, type_info)
        self.assertListEqual(
            output, ["|matrix1 = [1, 2]", "|matrix2 = [3, 4]", "|matrix3 = "]
        )

    def test_deeply_nested_dataclass(self):
        @dataclass
        class Level3:
            field: str

        @dataclass
        class Level2:
            nested: Level3

        @dataclass
        class Level1:
            nested: Level2

        obj = Level1(nested=Level2(nested=Level3(field="deep_value")))
        output = CargoPrinter().print_dataclass(obj, analyze_type(Level1))
        self.assertListEqual(output, ["|field = deep_value"])

    def test_skip_field(self):
        @desynced_object
        class Obj:
            nested: str = annotate(FieldOptions(skip_field=True))

        obj = Obj(nested="potatoes")
        output = CargoPrinter().print_dataclass(obj, analyze_type(Obj))
        # Field is skipped so should be empty.
        self.assertListEqual(output, [])


class TestDataclassDeclarationPrinter(unittest.TestCase):
    def test_analyze_simple_dataclass(self):
        @dataclass
        class Simple:
            name: str
            age: int

        type_info = analyze_type(Simple)
        self.assertEqual(
            ["|name = String", "|age = Integer"],
            CargoPrinter(mode=CargoPrinter.Mode.DECLARATIONS).print_dataclass(
                dc_obj=None, type_info=type_info
            ),
        )


if __name__ == "__main__":
    unittest.main()
