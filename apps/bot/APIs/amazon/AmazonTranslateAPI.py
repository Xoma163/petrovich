import boto3

from petrovich.settings import AMAZON_REGION


class AmazonTranslateAPI:
    @staticmethod
    def get_translate(text, target_lang='ru', source_lang='en'):
        if target_lang != 'ru':
            source_lang = 'ru'
        translate = boto3.client(service_name='translate', region_name=AMAZON_REGION, use_ssl=True)

        result = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang
        )
        return result.get('TranslatedText')
