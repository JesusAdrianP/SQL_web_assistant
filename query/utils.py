from ai_models import GoogleModel
from language_config import LanguageConfig
from translate_language import TranslateLanguage
from utils import parse_gemini_response

configurated_language = LanguageConfig()

async def call_gemini_model(nl_query, db_schema):
    try:
       selected_language = configurated_language.get_config_language()
       if selected_language.get('language') == "Español":
           translator = TranslateLanguage()
           nl_query = translator.translate_to_english(nl_query)
       gemini_model = GoogleModel()
       response = gemini_model.call_SQL_asistant(NL_query=nl_query,schema=db_schema)
       return {"sql_query": parse_gemini_response(response)}
    except Exception as e:
        return {"sql_query": None, "error":f"{e}"}