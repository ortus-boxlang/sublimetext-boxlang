"""
Unit tests for spec/suite and property navigation (symbols.py).
"""

from tests.expectations import expect


class TestFindSpecs:
    SOURCE = (
        'class extends="testbox.system.BaseSpec" {\n'
        '  function run() {\n'
        '    describe( "Math", () => {\n'
        '      it( "adds", () => {} )\n'
        '      xit( \'skipped one\', () => {} )\n'
        '      story( "A story", () => { then( "it works", () => {} ) } )\n'
        '    } )\n'
        '  }\n'
        '  function testLegacy() {}\n'
        '}\n'
    )

    def test_lists_suites_and_specs_in_order(self):
        from src import symbols
        found = [(kind, name) for kind, name, _ in symbols.find_specs(self.SOURCE)]
        expect(found).to_be([
            ("suite", "Math"),
            ("spec", "adds"),
            ("spec", "skipped one"),
            ("suite", "A story"),
            ("spec", "it works"),
            ("spec", "testLegacy"),
        ])

    def test_offsets_point_at_the_call(self):
        from src import symbols
        offsets = {name: offset for _, name, offset in symbols.find_specs(self.SOURCE)}
        expect(self.SOURCE[offsets["adds"]:].startswith("it(")).to_be_true()

    def test_no_specs(self):
        from src import symbols
        expect(symbols.find_specs("class { function run() {} }")).to_be_empty()


class TestFindProperties:
    def test_script_forms(self):
        from src import symbols
        text = (
            'class {\n'
            '  property name="userService" inject="UserService";\n'
            '  property string title;\n'
            '  property numeric count default=0;\n'
            '  property wirebox inject="wirebox";\n'
            '}\n'
        )
        names = [name for name, _ in symbols.find_properties(text)]
        expect(names).to_be(["userService", "title", "count", "wirebox"])

    def test_tag_form(self):
        from src import symbols
        text = '<bx:property name="userService" inject="UserService">\n<bx:property name=\'other\'>'
        names = [name for name, _ in symbols.find_properties(text)]
        expect(names).to_be(["userService", "other"])

    def test_attribute_names_are_not_listed_as_properties(self):
        from src import symbols
        names = [name for name, _ in symbols.find_properties('property type="string" name="x" inject="y";')]
        expect(names).to_be(["x"])

    def test_offset_points_at_property_keyword(self):
        from src import symbols
        text = 'class {\n    property string title;\n}'
        (name, offset), = symbols.find_properties(text)
        expect(text[offset:].startswith("property")).to_be_true()

    def test_ignores_property_word_inside_other_code(self):
        from src import symbols
        expect(symbols.find_properties('x = obj.property;\ny = "property name=a;"')).to_be_empty()
