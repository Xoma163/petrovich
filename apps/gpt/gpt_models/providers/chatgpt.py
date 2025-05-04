from apps.gpt.gpt_models.base import GPTModels, GPTCompletionModel, GPTImageDrawModel, GPTVoiceRecognitionModel, \
    GPTVisionModel


class ChatGPTCompletionModels(GPTModels):
    # o
    O1 = GPTCompletionModel("o1", "o1", 15, 60)
    # O1_PRO = GPTCompletionModel("o1-pro", "o1 pro", 150, 600)
    O1_MINI = GPTCompletionModel("o1-mini", "o1 mini", 1.1, 4.4)
    O3 = GPTCompletionModel("o3", "o3", 10, 40)
    O3_MINI = GPTCompletionModel("o3-mini", "o3 mini", 1.1, 4.4)
    O4_MINI = GPTCompletionModel("o4-mini", "o4 mini", 1.1, 4.4)

    # GPT-4
    GPT_4_1 = GPTCompletionModel("gpt-4.1", "GPT-4.1", 2, 8)
    GPT_4_1_MINI = GPTCompletionModel("gpt-4.1-mini", "GPT-4.1 MINI", 0.4, 1.6)
    GPT_4_1_NANO = GPTCompletionModel("gpt-4.1-nano", "GPT-4.1 NANO", 0.1, 0.4)

    GPT_4_O = GPTCompletionModel("gpt-4o", "GPT-4o", 2.5, 10)
    GPT_4_O_MINI = GPTCompletionModel("gpt-4o-mini", "GPT-4o MINI", 0.15, 0.6)

    GPT_4 = GPTCompletionModel("gpt-4", "GPT-4", 30, 60)
    GPT_4_TURBO = GPTCompletionModel("gpt-4-turbo", "GPT-4 TURBO", 10, 30)
    GPT_4_32K = GPTCompletionModel("gpt-4-32k", "GPT-4 32K", 60, 120)

    GPT_4_5 = GPTCompletionModel("gpt-4.5-preview", "GPT-4.5", 75, 150)

    # GPT-3.5
    GPT_3_5_TURBO_0125 = GPTCompletionModel("gpt-3.5-turbo-0125", "GPT-3.5 TURBO 0125", 0.5, 1.5)
    GPT_3_5_TURBO_1106 = GPTCompletionModel("gpt-3.5-turbo-1106", "GPT-3.5 TURBO 1106", 1, 2)
    GPT_3_5_TURBO_0613 = GPTCompletionModel("gpt-3.5-turbo-0613", "GPT-3.5 TURBO 0613", 1.5, 2)
    GPT_3_5_TURBO_16K_0613 = GPTCompletionModel("gpt-3.5-turbo-16k-0613", "GPT-3.5 TURBO 16K 0613", 3, 4)
    GPT_3_5_TURBO_0301 = GPTCompletionModel("gpt-3.5-turbo-0301", "GPT-3.5 TURBO 16K 0613", 1.5, 2)


class ChatGPTVisionModels(GPTModels):
    # o
    O1 = GPTVisionModel("o1", "o1", 15, 60)
    # + O1_PRO = GPTCompletionModel("o1-pro", "o1 pro", 150, 600)
    O3 = GPTVisionModel("o3", "o3", 10, 40)
    O4_MINI = GPTVisionModel("o4-mini", "o4 mini", 1.1, 4.4)

    # GPT-4
    GPT_4_1 = GPTVisionModel("gpt-4.1", "GPT-4.1", 2, 8)
    GPT_4_1_MINI = GPTVisionModel("gpt-4.1-mini", "GPT-4.1 MINI", 0.4, 1.6)
    GPT_4_1_NANO = GPTVisionModel("gpt-4.1-nano", "GPT-4.1 NANO", 0.1, 0.4)

    GPT_4_O = GPTVisionModel("gpt-4o", "GPT-4o", 2.5, 10)
    GPT_4_O_MINI = GPTVisionModel("gpt-4o-mini", "GPT-4o MINI", 0.15, 0.6)

    GPT_4_5 = GPTVisionModel("gpt-4.5-preview", "GPT-4.5", 75, 150)


#   ToDo: add model "gpt-image-1"


class ChatGPTImageDrawModels(GPTModels):
    DALLE_3_PORTAIR = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.08, width=1024, height=1792)
    DALLE_3_PORTAIR_HD = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.12, width=1792, height=1024)
    DALLE_3_SQUARE = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.04, width=1024, height=1024)
    DALLE_3_SQUARE_HD = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.08, width=1024, height=1024)
    DALLE_3_ALBUM = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.08, width=1792, height=1024)
    DALLE_3_ALBUM_HD = GPTImageDrawModel("dall-e-3", "DALLE 3", image_cost=0.12, width=1792, height=1024)


class ChatGPTVoiceRecognitionModels(GPTModels):
    WHISPER = GPTVoiceRecognitionModel("whisper-1", "whisper-1", voice_recognition_1_min_cost=0.006)


class ChatGPTModels(ChatGPTCompletionModels, ChatGPTVisionModels, ChatGPTImageDrawModels,
                    ChatGPTVoiceRecognitionModels):
    pass
