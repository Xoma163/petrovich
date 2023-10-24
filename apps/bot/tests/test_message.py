from django.test import TestCase

from apps.bot.classes.messages.message import Message


class MessageTestCase(TestCase):
    def test_empty_message(self):
        message = Message()
        raw_str = ""
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "")
        self.assertEqual(message.clear, "")
        self.assertEqual(message.clear_case, "")

        self.assertEqual(message.args_str, "")
        self.assertEqual(message.args, [])
        self.assertEqual(message.args_str_case, "")
        self.assertEqual(message.args_case, [])

        self.assertEqual(message.keys, [])

    def test_no_arg_message(self):
        message = Message()
        raw_str = "Привет"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет")
        self.assertEqual(message.clear_case, "Привет")

        self.assertEqual(message.args_str, "")
        self.assertEqual(message.args, [])
        self.assertEqual(message.args_str_case, "")
        self.assertEqual(message.args_case, [])

        self.assertEqual(message.keys, [])

    def test_one_arg_message(self):
        message = Message()
        raw_str = "Привет Карл"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет карл")
        self.assertEqual(message.clear_case, "Привет Карл")

        self.assertEqual(message.args_str, "карл")
        self.assertEqual(message.args, ["карл"])
        self.assertEqual(message.args_str_case, "Карл")
        self.assertEqual(message.args_case, ["Карл"])

        self.assertEqual(message.keys, [])

    def test_two_arg_comma_message(self):
        message = Message()
        raw_str = "Привет,Карл Карлович,Карлан"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет,карл")
        self.assertEqual(message.clear, "привет,карл карлович,карлан")
        self.assertEqual(message.clear_case, "Привет,Карл Карлович,Карлан")

        self.assertEqual(message.args_str, "карлович,карлан")
        self.assertEqual(message.args, ["карлович,карлан"])
        self.assertEqual(message.args_str_case, "Карлович,Карлан")
        self.assertEqual(message.args_case, ["Карлович,Карлан"])

        self.assertEqual(message.keys, [])

    def test_two_arg_message(self):
        message = Message()
        raw_str = "Привет Карл Карлович"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет карл карлович")
        self.assertEqual(message.clear_case, "Привет Карл Карлович")

        self.assertEqual(message.args_str, "карл карлович")
        self.assertEqual(message.args, ["карл", "карлович"])
        self.assertEqual(message.args_str_case, "Карл Карлович")
        self.assertEqual(message.args_case, ["Карл", "Карлович"])

        self.assertEqual(message.keys, [])

    def test_one_arg_new_line_message(self):
        message = Message()
        raw_str = "Привет\nКарл"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет\nкарл")
        self.assertEqual(message.clear_case, "Привет\nКарл")

        self.assertEqual(message.args_str, "карл")
        self.assertEqual(message.args, ["карл"])
        self.assertEqual(message.args_str_case, "Карл")
        self.assertEqual(message.args_case, ["Карл"])

        self.assertEqual(message.keys, [])

    def test_two_arg_new_line_message(self):
        message = Message()
        raw_str = "Привет\nКарл\nКарлович"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет\nкарл\nкарлович")
        self.assertEqual(message.clear_case, "Привет\nКарл\nКарлович")

        self.assertEqual(message.args_str, "карл\nкарлович")
        self.assertEqual(message.args, ["карл", "карлович"])
        self.assertEqual(message.args_str_case, "Карл\nКарлович")
        self.assertEqual(message.args_case, ["Карл", "Карлович"])

        self.assertEqual(message.keys, [])

    def test_two_arg_new_line2_message(self):
        message = Message()
        raw_str = "Привет\nКарл Карлович"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет\nкарл карлович")
        self.assertEqual(message.clear_case, "Привет\nКарл Карлович")

        self.assertEqual(message.args_str, "карл карлович")
        self.assertEqual(message.args, ["карл", "карлович"])
        self.assertEqual(message.args_str_case, "Карл Карлович")
        self.assertEqual(message.args_case, ["Карл", "Карлович"])

        self.assertEqual(message.keys, [])

    def test_two_arg_new_line_many_spaces_message(self):
        message = Message()
        raw_str = "Привет\n\n\nКарл\n\nКарлович        123"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет\nкарл\nкарлович 123")
        self.assertEqual(message.clear_case, "Привет\nКарл\nКарлович 123")

        self.assertEqual(message.args_str, "карл\nкарлович 123")
        self.assertEqual(message.args, ['карл', 'карлович', '123'])
        self.assertEqual(message.args_str_case, "Карл\nКарлович 123")
        self.assertEqual(message.args_case, ['Карл', 'Карлович', '123'])

        self.assertEqual(message.keys, [])

    def test_no_arg_keys(self):
        message = Message()
        raw_str = "Привет --debug"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет --debug")
        self.assertEqual(message.clear_case, "Привет --debug")

        self.assertEqual(message.args_str, "")
        self.assertEqual(message.args, [])
        self.assertEqual(message.args_str_case, "")
        self.assertEqual(message.args_case, [])

        self.assertEqual(message.keys, ["debug"])

    def test_one_arg_keys(self):
        message = Message()
        raw_str = "Привет Карл --debug"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет карл --debug")
        self.assertEqual(message.clear_case, "Привет Карл --debug")

        self.assertEqual(message.args_str, "карл")
        self.assertEqual(message.args, ["карл"])
        self.assertEqual(message.args_str_case, "Карл")
        self.assertEqual(message.args_case, ["Карл"])

        self.assertEqual(message.keys, ["debug"])

    def test_two_arg_new_line_many_spaces_keys_case_message(self):
        message = Message()
        raw_str = "Привет\n\n\nКарл\n\nКарлович        123 --DEBUG\n—PROD"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет\nкарл\nкарлович 123 --debug\n—prod")
        self.assertEqual(message.clear_case, "Привет\nКарл\nКарлович 123 --DEBUG\n—PROD")

        self.assertEqual(message.args_str, "карл\nкарлович 123")
        self.assertEqual(message.args, ['карл', 'карлович', '123'])
        self.assertEqual(message.args_str_case, "Карл\nКарлович 123")
        self.assertEqual(message.args_case, ['Карл', 'Карлович', '123'])

        self.assertEqual(message.keys, ["debug", "prod"])

    def test_two_arg_with_space_and_new_line(self):
        message = Message()
        raw_str = "Привет\n\n\nКарл\n\nКарлович    \n    123"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "привет")
        self.assertEqual(message.clear, "привет\nкарл\nкарлович \n 123")
        self.assertEqual(message.clear_case, "Привет\nКарл\nКарлович \n 123")

        self.assertEqual(message.args_str, "карл\nкарлович \n 123")
        self.assertEqual(message.args, ['карл', 'карлович', '123'])
        self.assertEqual(message.args_str_case, "Карл\nКарлович \n 123")
        self.assertEqual(message.args_case, ['Карл', 'Карлович', '123'])

        self.assertEqual(message.keys, [])

    def test_twitter(self):
        message = Message()
        raw_str = "https://twitter.com/blahblah --thread"
        message.parse_raw(raw_str)

        self.assertEqual(message.raw, raw_str)
        self.assertEqual(message.command, "https://twitter.com/blahblah")
        self.assertEqual(message.clear, "https://twitter.com/blahblah --thread")
        self.assertEqual(message.clear_case, "https://twitter.com/blahblah --thread")

        self.assertEqual(message.args_str, "")
        self.assertEqual(message.args, [])
        self.assertEqual(message.args_str_case, "")
        self.assertEqual(message.args_case, [])

        self.assertEqual(message.keys, ['thread'])
