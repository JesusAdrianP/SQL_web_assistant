from translate import Translator

"""
This class is responsible for translating the input data from Spanish to English.
"""
class TranslateLanguage:
    """
    constructor that initializes the translator object with the source and target language.
    """
    def __init__(self):
        self.translator = Translator(to_lang='EN', from_lang='ES')

    """
    method that translates the input data from Spanish to English.
    Parameters:
        input_data: input data to be translated
    """
    def translate_to_english(self, input_data: str):
        return self.translator.translate(input_data)